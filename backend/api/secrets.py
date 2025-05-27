#! /usr/bin/env python3


from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import io
from backend.models.user import User
from backend.models.secret import Secret
from backend.models.permission import SecretPermission
from backend.models.enums import SecretType
from backend.extensions import db, socketio
from backend.utils.encryption import encrypt_value, decrypt_value
from backend.services.secret_service import SecretService
from backend.models.folder import Folder, FolderPermission, FolderType
from backend.models.permission import UserSecretView
from backend.models.tag import Tag
from backend.services.ws_service import client_sessions, encrypt_for_client
import json

secrets_bp = Blueprint('secrets', __name__)


def process_tags(tag_names, secret, user_id):
    """Processes and associates tags with a secret."""
    for tag_name in tag_names:
        if not tag_name or not isinstance(tag_name, str):
            continue

        tag_name = tag_name.strip()
        if not tag_name:
            continue

        tag = Tag.query.filter_by(name=tag_name, owner_id=user_id).first()

        if not tag:
            tag = Tag(name=tag_name, owner_id=user_id)
            db.session.add(tag)

        if tag not in secret.tags:
            secret.tags.append(tag)


@secrets_bp.route('/', methods=['GET'])
@jwt_required()
def get_secrets():
    """Retrieves all secrets accessible to the current user, including those they own and those shared with them."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    owned_secrets = Secret.query.filter_by(owner_id=current_user_id).all()

    shared_permissions = SecretPermission.query.filter_by(
        user_id=current_user_id,
        can_read=True
    ).all()

    shared_secret_ids = [p.secret_id for p in shared_permissions]
    shared_secrets = Secret.query.filter(Secret.secret_id.in_(shared_secret_ids)).all()

    accessible_folder_ids = set()
    owned_folders = Folder.query.filter_by(owner_id=current_user_id).all()
    for folder in owned_folders:
        accessible_folder_ids.add(folder.folder_id)

    folder_permissions = FolderPermission.query.filter_by(
        user_id=current_user_id,
        can_read=True
    ).all()
    for perm in folder_permissions:
        accessible_folder_ids.add(perm.folder_id)

    all_secrets = {}

    for secret in owned_secrets:
        all_secrets[secret.secret_id] = secret

    for secret in shared_secrets:
        if secret.secret_id not in all_secrets:
            all_secrets[secret.secret_id] = secret

    user_views = UserSecretView.query.filter(
        UserSecretView.user_id == current_user_id,
        UserSecretView.secret_id.in_([s.secret_id for s in all_secrets.values()])
    ).all()

    user_view_map = {view.secret_id: view.folder_id for view in user_views}

    direct_permission_lookup = {perm.secret_id: True for perm in shared_permissions}

    folder_map = {}
    folder_accessibility = {}

    all_folders = Folder.query.filter(
        (Folder.owner_id == current_user_id) |
        (Folder.folder_id.in_([p.folder_id for p in folder_permissions]))
    ).all()

    for folder in all_folders:
        folder_map[folder.folder_id] = folder.name
        folder_accessibility[folder.folder_id] = True

    secrets_with_tags = []
    for secret in all_secrets.values():
        has_direct_access = secret.owner_id == int(current_user_id) or secret.secret_id in direct_permission_lookup

        tags = []
        if hasattr(secret, 'tags'):
            tags = [tag.name for tag in secret.tags]

        real_folder_id = secret.folder_id

        if secret.secret_id in user_view_map:
            folder_id = user_view_map[secret.secret_id]
            current_app.logger.debug(
                f"Using personal view for secret {secret.secret_id}: folder {folder_id} instead of {real_folder_id}")
        elif secret.owner_id == int(current_user_id):
            folder_id = real_folder_id
        else:
            folder_id = None

        folder_name = folder_map.get(folder_id) if folder_id else None

        secrets_with_tags.append({
            "id": secret.secret_id,
            "name": secret.secret_name,
            "type": secret.secret_type,
            "folder_id": folder_id,
            "folder_name": folder_name,
            "description": secret.description or "",
            "created_time": secret.created_time.isoformat(),
            "last_modified": secret.last_modified.isoformat(),
            "tags": tags,
            "owner_id": secret.owner_id,
            "is_favorite": secret.is_favorite,
            "is_file_secret": secret.is_file_secret,
            "has_direct_access": has_direct_access,
            "real_folder_id": real_folder_id
        })

    return jsonify({
        "secrets": secrets_with_tags
    }), 200


@secrets_bp.route('/', methods=['POST'])
@jwt_required()
def create_secret():
    """Creates a new secret for the current user."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()

    if not all(k in data for k in ('name', 'type', 'value')):
        return jsonify({"msg": "Missing required fields"}), 400

    secret_type = data['type']
    valid_types = [t.value for t in SecretType]
    if secret_type not in valid_types:
        return jsonify({"msg": f"Invalid secret type. Must be one of: {', '.join(valid_types)}"}), 400

    encrypted_value = encrypt_value(data['value'])

    folder_id = None
    if 'folder_id' in data and data['folder_id']:
        try:
            folder_id = int(data['folder_id'])
            folder = Folder.query.get(folder_id)
            if not folder:
                return jsonify({"msg": f"Folder with ID {folder_id} not found"}), 404

            current_app.logger.debug(
                f"Creating secret in folder: {folder_id}, folder owner: {folder.owner_id}, current user: {current_user_id}")

            folder_owner_id = int(folder.owner_id)
            current_user_id_int = int(current_user_id)

            if folder_owner_id == current_user_id_int:
                current_app.logger.debug(
                    f"User {current_user_id} is the owner of folder {folder_id}, allowing secret creation")
            else:
                permission = FolderPermission.query.filter_by(
                    folder_id=folder_id,
                    user_id=current_user_id_int,
                    can_write=True
                ).first()

                if not permission:
                    current_app.logger.warning(
                        f"User {current_user_id} does not have permission to create secrets in folder {folder_id}")
                    return jsonify({"msg": "You don't have permission to add secrets to this folder"}), 403
        except ValueError:
            return jsonify({"msg": "Invalid folder_id format"}), 400

    description = data.get('description', '')

    new_secret = Secret(
        secret_name=data['name'],
        description=description,
        secret_type=secret_type,
        encrypted_secret_value=encrypted_value,
        owner_id=current_user_id,
        folder_id=folder_id
    )

    db.session.add(new_secret)
    db.session.commit()

    if 'tags' in data and isinstance(data['tags'], list):
        process_tags(data['tags'], new_secret, current_user_id)
        db.session.commit()

    UserSecretView.set_user_view(
        user_id=current_user_id,
        secret_id=new_secret.secret_id,
        folder_id=folder_id
    )

    if folder_id:
        folder = Folder.query.get(folder_id)

        if folder and folder.is_shared_folder:
            folder_permissions = FolderPermission.query.filter_by(folder_id=folder_id).all()
            current_app.logger.debug(f"Found {len(folder_permissions)} permissions to inherit for folder {folder_id}")

            for folder_perm in folder_permissions:
                if folder_perm.user_id == int(current_user_id):
                    continue

                secret_perm = SecretPermission(
                    secret_id=new_secret.secret_id,
                    user_id=folder_perm.user_id,
                    can_read=folder_perm.can_read,
                    can_write=folder_perm.can_write,
                    can_delete=folder_perm.can_delete
                )

                db.session.add(secret_perm)
                current_app.logger.debug(
                    f"Inherited permission for user {folder_perm.user_id} on secret {new_secret.secret_id}")

                if folder_perm.can_read:
                    user_view = UserSecretView.get_user_view(folder_perm.user_id, new_secret.secret_id)
                    if user_view:
                        user_view.folder_id = folder_id
                        current_app.logger.debug(
                            f"Updated view for secret {new_secret.secret_id} to folder {folder_id} for user {folder_perm.user_id}")
                    else:
                        UserSecretView.set_user_view(
                            user_id=folder_perm.user_id,
                            secret_id=new_secret.secret_id,
                            folder_id=folder_id
                        )
                        current_app.logger.debug(
                            f"Created view for secret {new_secret.secret_id} in folder {folder_id} for user {folder_perm.user_id}")

            db.session.commit()

    folder_info = None
    if folder_id:
        folder = Folder.query.get(folder_id)
        if folder:
            folder_info = {
                "id": folder.folder_id,
                "name": folder.name,
                "is_shared_folder": folder.is_shared_folder,
                "folder_type": folder.folder_type.value
            }

    tags = []
    if hasattr(new_secret, 'tags'):
        tags = [tag.name for tag in new_secret.tags]

    secret_data = {
        "id": new_secret.secret_id,
        "name": new_secret.secret_name,
        "description": new_secret.description,
        "type": new_secret.secret_type,
        "folder_id": new_secret.folder_id,
        "folder": folder_info,
        "owner_id": new_secret.owner_id,
        "created_time": new_secret.created_time.isoformat(),
        "last_modified": new_secret.last_modified.isoformat(),
        "tags": tags,
        "is_favorite": new_secret.is_favorite,
        "is_file_secret": new_secret.is_file_secret,
        "has_direct_access": True,
        "value": data['value'],
        "permissions": {
            "can_read": True,
            "can_write": True,
            "can_delete": True,
            "is_owner": True,
            "has_direct_access": True
        }
    }

    shared_user_ids = []
    if folder_id and folder and folder.is_shared_folder:
        folder_permissions = FolderPermission.query.filter_by(folder_id=folder_id).all()
        shared_user_ids = [perm.user_id for perm in folder_permissions if perm.user_id != int(current_user_id)]

    secret_data_for_socket = {
        'id': new_secret.secret_id,
        'name': new_secret.secret_name,
        'description': new_secret.description,
        'type': new_secret.secret_type,
        'value': data['value'],
        'folder_id': new_secret.folder_id,
        'user_id': new_secret.owner_id,
        'created_time': new_secret.created_time.isoformat(),
        'last_modified': new_secret.last_modified.isoformat() if new_secret.last_modified else None,
        'is_shared': len(shared_user_ids) > 0,
        'is_favorite': new_secret.is_favorite,
        'tags': [tag.name for tag in new_secret.tags]
    }

    user_sid = None
    for sid, session in client_sessions.items():
        if session.get('user_id') == int(current_user_id):
            user_sid = sid
            break

    if user_sid:
        encrypted_response = encrypt_for_client(user_sid, {'secret': secret_data_for_socket})
        socketio.emit('secret_created', {'encrypted': encrypted_response}, room=user_sid)

    return jsonify(secret_data), 201


@secrets_bp.route('/<int:secret_id>', methods=['GET'])
@jwt_required()
def get_secret(secret_id):
    """Retrieves a specific secret by its ID."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    secret = Secret.query.get(secret_id)

    if not secret:
        return jsonify({"msg": "Secret not found"}), 404

    has_direct_access = False

    if secret.owner_id == int(current_user_id):
        has_direct_access = True
    else:
        permission = SecretPermission.query.filter_by(
            secret_id=secret_id,
            user_id=current_user_id,
            can_read=True
        ).first()

        if permission:
            has_direct_access = True

    folder_access = False
    if secret.folder_id and not has_direct_access:
        folder = Folder.query.get(secret.folder_id)

        if folder:
            if folder.owner_id == int(current_user_id):
                folder_access = True
            else:
                folder_permission = FolderPermission.query.filter_by(
                    folder_id=secret.folder_id,
                    user_id=current_user_id,
                    can_read=True
                ).first()

                if folder_permission:
                    folder_access = True

    if has_direct_access or folder_access:
        user_view = UserSecretView.get_user_view(current_user_id, secret_id)

        actual_folder_info = None
        viewed_folder_info = None

        if secret.folder_id:
            actual_folder = Folder.query.get(secret.folder_id)
            if actual_folder:
                actual_folder_info = {
                    "id": actual_folder.folder_id,
                    "name": actual_folder.name,
                    "is_shared_folder": actual_folder.is_shared_folder,
                    "folder_type": actual_folder.folder_type.value if actual_folder else None,
                }

        viewed_folder_id = user_view.folder_id if user_view else (
            secret.folder_id if secret.owner_id == int(current_user_id) else None
        )

        if viewed_folder_id:
            viewed_folder = Folder.query.get(viewed_folder_id)
            if viewed_folder:
                viewed_folder_info = {
                    "id": viewed_folder.folder_id,
                    "name": viewed_folder.name,
                    "is_shared_folder": viewed_folder.is_shared_folder,
                    "folder_type": viewed_folder.folder_type.value if viewed_folder else None,
                }

        tags = []
        if hasattr(secret, 'tags'):
            tags = [tag.name for tag in secret.tags]

        decrypted_value = None
        if not secret.is_file_secret:
            try:
                decrypted_value = decrypt_value(secret.encrypted_secret_value)
            except Exception as e:
                current_app.logger.error(f"Decryption error: {str(e)}")
                return jsonify({"msg": "Failed to decrypt secret value"}), 500

        permissions = {
            "can_read": True,
            "can_write": secret.owner_id == int(current_user_id),
            "can_delete": secret.owner_id == int(current_user_id),
            "is_owner": secret.owner_id == int(current_user_id),
            "has_direct_access": has_direct_access
        }

        if not permissions["is_owner"]:
            permission = SecretPermission.query.filter_by(
                secret_id=secret_id,
                user_id=current_user_id
            ).first()

            if permission:
                permissions["can_write"] = permission.can_write
                permissions["can_delete"] = permission.can_delete

        file_info = None
        if secret.is_file_secret:
            file_info = {
                "original_filename": secret.original_filename,
                "file_size": secret.file_size,
                "file_mime_type": secret.file_mime_type
            }

        secret_data = {
            "id": secret.secret_id,
            "name": secret.secret_name,
            "type": secret.secret_type,
            "real_folder_id": secret.folder_id,
            "folder_id": viewed_folder_id,
            "folder": viewed_folder_info,
            "real_folder": actual_folder_info,
            "description": secret.description or "",
            "value": decrypted_value,
            "owner_id": secret.owner_id,
            "created_time": secret.created_time.isoformat(),
            "last_modified": secret.last_modified.isoformat(),
            "tags": tags,
            "permissions": permissions,
            "is_favorite": secret.is_favorite,
            "is_file_secret": secret.is_file_secret,
            "file_info": file_info,
            "has_direct_access": has_direct_access,
            "has_custom_view": user_view is not None
        }

        return jsonify(secret_data), 200
    else:
        return jsonify({"msg": "Access denied"}), 403


@secrets_bp.route('/<int:secret_id>', methods=['PUT'])
@jwt_required()
def update_secret(secret_id):
    """Updates an existing secret's details, including name, description, value, and folder association."""
    current_user_id = get_jwt_identity()

    secret = Secret.query.get(secret_id)
    if not secret:
        return jsonify({"msg": "Secret not found"}), 404

    if int(secret.owner_id) != int(current_user_id):
        permission = SecretPermission.query.filter_by(
            secret_id=secret_id,
            user_id=current_user_id,
            can_write=True
        ).first()

        if not permission:
            return jsonify({"msg": "You don't have permission to update this secret"}), 403

    data = request.get_json()

    old_folder_id = secret.folder_id
    if 'folder_id' in data and data['folder_id'] != old_folder_id:
        new_folder_id = data['folder_id']

        if new_folder_id is not None:
            folder = Folder.query.get(new_folder_id)
            if not folder:
                return jsonify({"msg": "Destination folder not found"}), 404

            if folder.owner_id != int(current_user_id):
                folder_permission = FolderPermission.query.filter_by(
                    folder_id=new_folder_id,
                    user_id=current_user_id,
                    can_write=True
                ).first()

                if not folder_permission:
                    return jsonify({"msg": "You don't have permission to add secrets to this folder"}), 403

            if folder.is_shared_folder:
                folder_permissions = FolderPermission.query.filter_by(
                    folder_id=new_folder_id
                ).all()

                for folder_perm in folder_permissions:
                    if folder_perm.user_id == secret.owner_id:
                        continue

                    secret_perm = SecretPermission.query.filter_by(
                        secret_id=secret_id,
                        user_id=folder_perm.user_id
                    ).first()

                    if secret_perm:
                        secret_perm.can_read = folder_perm.can_read
                        secret_perm.can_write = folder_perm.can_write
                        secret_perm.can_delete = folder_perm.can_delete
                    else:
                        secret_perm = SecretPermission(
                            secret_id=secret_id,
                            user_id=folder_perm.user_id,
                            can_read=folder_perm.can_read,
                            can_write=folder_perm.can_write,
                            can_delete=folder_perm.can_delete
                        )
                        db.session.add(secret_perm)

                    if folder_perm.can_read:
                        user_view = UserSecretView.get_user_view(folder_perm.user_id, secret_id)
                        if user_view:
                            user_view.folder_id = new_folder_id
                            current_app.logger.debug(
                                f"Updated view for secret {secret_id} to folder {new_folder_id} for user {folder_perm.user_id}")
                        else:
                            UserSecretView.set_user_view(
                                user_id=folder_perm.user_id,
                                secret_id=secret_id,
                                folder_id=new_folder_id
                            )
                            current_app.logger.debug(
                                f"Created view for secret {secret_id} in folder {new_folder_id} for user {folder_perm.user_id}")

            db.session.commit()

        secret.folder_id = new_folder_id

        preserve_permissions = True

        if new_folder_id is None or (folder and not folder.is_shared_folder):
            existing_permissions = SecretPermission.query.filter(
                SecretPermission.secret_id == secret_id,
                SecretPermission.user_id != secret.owner_id
            ).all()

            for perm in existing_permissions:
                if not perm.can_read:
                    perm.can_read = True
                    db.session.add(perm)

    if 'name' in data:
        secret.secret_name = data['name']

    if 'description' in data:
        secret.description = data.get('description', '')

    if 'value' in data and not secret.is_file_secret:
        try:
            encrypted_value = encrypt_value(data['value'])
            secret.encrypted_secret_value = encrypted_value
        except Exception as e:
            return jsonify({"msg": f"Failed to encrypt secret: {str(e)}"}), 500

    if 'tags' in data and isinstance(data['tags'], list):
        process_tags(data['tags'], secret, current_user_id)

    try:
        db.session.commit()

        folder_info = None
        if secret.folder_id:
            folder = Folder.query.get(secret.folder_id)
            if folder:
                folder_info = {
                    "id": folder.folder_id,
                    "name": folder.name,
                    "is_shared_folder": folder.is_shared_folder,
                    "folder_type": folder.folder_type.value
                }

        tags = []
        if hasattr(secret, 'tags'):
            tags = [tag.name for tag in secret.tags]

        decrypted_value = None
        if not secret.is_file_secret:
            try:
                decrypted_value = decrypt_value(secret.encrypted_secret_value)
            except Exception as e:
                current_app.logger.error(f"Decryption error: {str(e)}")
                return jsonify({"msg": "Failed to decrypt updated secret value"}), 500

        has_direct_access = secret.owner_id == int(current_user_id)
        if not has_direct_access:
            permission = SecretPermission.query.filter_by(
                secret_id=secret_id,
                user_id=current_user_id
            ).first()

            if permission:
                has_direct_access = True

        users_with_access = []

        permissions = SecretPermission.query.filter_by(secret_id=secret_id).all()
        for perm in permissions:
            if perm.user_id != int(current_user_id) and perm.user_id not in users_with_access:
                users_with_access.append(perm.user_id)

        if secret.folder_id:
            folder = Folder.query.get(secret.folder_id)
            if folder and folder.is_shared_folder:
                folder_permissions = FolderPermission.query.filter_by(folder_id=secret.folder_id).all()
                for perm in folder_permissions:
                    if perm.user_id != int(current_user_id) and perm.user_id not in users_with_access:
                        users_with_access.append(perm.user_id)

        socketio.emit('secret_updated', {
            'secret_id': secret.secret_id,
            'secret_name': secret.secret_name,
            'owner_id': secret.owner_id,
            'folder_id': secret.folder_id,
            'updated_by': current_user_id,
            'users_with_access': users_with_access
        })

        return jsonify({
            "id": secret.secret_id,
            "name": secret.secret_name,
            "description": secret.description,
            "type": secret.secret_type,
            "value": decrypted_value,
            "folder_id": secret.folder_id,
            "folder": folder_info,
            "tags": tags,
            "owner_id": secret.owner_id,
            "is_favorite": secret.is_favorite,
            "is_file_secret": secret.is_file_secret,
            "has_direct_access": has_direct_access
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating secret: {str(e)}")
        return jsonify({"msg": f"Error: {str(e)}"}), 500


@secrets_bp.route('/<int:secret_id>', methods=['DELETE'])
@jwt_required()
def delete_secret(secret_id):
    """Deletes a secret permanently, including its database entry and any associated file content."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    secret = Secret.query.get(secret_id)
    if not secret:
        return jsonify({"msg": "Secret not found"}), 404

    has_permission = False

    if secret.owner_id == int(current_user_id):
        has_permission = True
    else:
        permission = SecretPermission.query.filter_by(
            secret_id=secret_id,
            user_id=current_user_id,
            can_delete=True
        ).first()
        if permission:
            has_permission = True

    if not has_permission:
        return jsonify({"msg": "You don't have permission to delete this secret"}), 403

    folder_id = secret.folder_id

    try:
        UserSecretView.query.filter_by(secret_id=secret_id).delete()

        if secret.is_file_secret and secret.file_path:
            success = SecretService.delete_file_secret(secret)
            if not success:
                return jsonify({"msg": "Failed to delete file secret"}), 500
        else:
            db.session.delete(secret)
            db.session.commit()

        socketio.emit('secret_deleted', {
            'secret_id': secret_id,
            'folder_id': folder_id
        })

        return jsonify({"msg": "Secret deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting secret: {str(e)}")
        return jsonify({"msg": f"Error deleting secret: {str(e)}"}), 500


@secrets_bp.route('/<int:secret_id>/share', methods=['POST'])
@jwt_required()
def share_secret(secret_id):
    """Shares a secret with another user, granting specified permissions."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()

    if not data.get('user_id'):
        return jsonify({"msg": "User ID is required"}), 400

    share_user_id = data.get('user_id')

    share_user = User.query.get(share_user_id)
    if not share_user:
        return jsonify({"msg": "User to share with not found"}), 404

    secret = Secret.query.get(secret_id)
    if not secret:
        return jsonify({"msg": "Secret not found"}), 404

    has_permission = False

    if secret.owner_id == int(current_user_id):
        has_permission = True
    else:
        permission = SecretPermission.query.filter_by(
            secret_id=secret_id,
            user_id=current_user_id,
            can_write=True
        ).first()
        if permission:
            has_permission = True

    if not has_permission:
        return jsonify({"msg": "You don't have permission to share this secret"}), 403

    if int(current_user_id) == int(share_user_id):
        return jsonify({"msg": "You cannot share a secret with yourself"}), 400

    permissions = data.get('permissions', {})

    permission = SecretPermission.query.filter_by(
        secret_id=secret_id,
        user_id=share_user_id
    ).first()

    if permission:
        if 'can_read' in permissions:
            permission.can_read = bool(permissions['can_read'])
        if 'can_write' in permissions:
            permission.can_write = bool(permissions['can_write'])
        if 'can_delete' in permissions:
            permission.can_delete = bool(permissions['can_delete'])
    else:
        permission = SecretPermission(
            secret_id=secret_id,
            user_id=share_user_id,
            can_read=bool(permissions.get('can_read', False)),
            can_write=bool(permissions.get('can_write', False)),
            can_delete=bool(permissions.get('can_delete', False))
        )
        db.session.add(permission)

        user_view = UserSecretView.get_user_view(share_user_id, secret_id)
        if not user_view and permission.can_read:
            UserSecretView.set_user_view(
                user_id=share_user_id,
                secret_id=secret_id,
                folder_id=None
            )

    db.session.commit()

    owner_sid = None
    shared_user_sid = None

    for sid, session in client_sessions.items():
        if session.get('user_id') == int(current_user_id):
            owner_sid = sid
        elif session.get('user_id') == int(share_user_id):
            shared_user_sid = sid

    secret_data = {
        'id': secret.secret_id,
        'name': secret.secret_name,
        'description': secret.description,
        'type': secret.secret_type,
        'folder_id': secret.folder_id,
        'user_id': secret.owner_id,
        'created_time': secret.created_time.isoformat(),
        'last_modified': secret.last_modified.isoformat() if secret.last_modified else None,
        'is_shared': True,
        'is_favorite': secret.is_favorite,
        'tags': [tag.name for tag in secret.tags],
        'permissions': {
            'can_read': permission.can_read,
            'can_write': permission.can_write,
            'can_delete': permission.can_delete
        }
    }

    if owner_sid:
        encrypted_response = encrypt_for_client(owner_sid, {'secret': secret_data})
        socketio.emit('secret_shared', {'encrypted': encrypted_response}, room=owner_sid)
        current_app.logger.info(f"Emitted secret_shared event to owner {current_user_id}")

    if shared_user_sid:
        encrypted_response = encrypt_for_client(shared_user_sid, {'secret': secret_data})
        socketio.emit('secret_shared', {'encrypted': encrypted_response}, room=shared_user_sid)
        current_app.logger.info(f"Emitted secret_shared event to shared user {share_user_id}")

    return jsonify({
        "msg": "Secret shared successfully",
        "permission": {
            "secret_id": permission.secret_id,
            "user_id": permission.user_id,
            "can_read": permission.can_read,
            "can_write": permission.can_write,
            "can_delete": permission.can_delete
        }
    }), 200


@secrets_bp.route('/<int:secret_id>/unshare/<int:user_id>', methods=['DELETE'])
@jwt_required()
def unshare_secret(secret_id, user_id):
    """Removes sharing permissions for a secret from a specific user."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    secret = Secret.query.get(secret_id)
    if not secret:
        return jsonify({"msg": "Secret not found"}), 404

    has_permission = False

    if secret.owner_id == int(current_user_id):
        has_permission = True
    else:
        permission = SecretPermission.query.filter_by(
            secret_id=secret_id,
            user_id=current_user_id,
            can_write=True
        ).first()
        if permission:
            has_permission = True

    if not has_permission:
        return jsonify({"msg": "You don't have permission to unshare this secret"}), 403

    permission = SecretPermission.query.filter_by(
        secret_id=secret_id,
        user_id=user_id
    ).first()

    if not permission:
        return jsonify({"msg": "Share permission not found"}), 404

    user_view = UserSecretView.get_user_view(user_id, secret_id)
    if user_view:
        db.session.delete(user_view)

    db.session.delete(permission)
    db.session.commit()

    socketio.emit('secret_unshared', {
        'secret_id': secret_id,
        'unshared_with_id': user_id
    })

    return jsonify({"msg": "Secret unshared successfully"}), 200


@secrets_bp.route('/file/', methods=['POST'])
@secrets_bp.route('/file', methods=['POST'])
@jwt_required()
def upload_file_secret():
    """Uploads and encrypts a file to be stored as a secret."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    if 'file' not in request.files:
        return jsonify({"msg": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"msg": "No file selected"}), 400

    secret_name = request.form.get('name')
    if not secret_name:
        return jsonify({"msg": "Secret name is required"}), 400

    folder_id = request.form.get('folder_id')
    folder_id = int(folder_id) if folder_id and folder_id.isdigit() else None

    description = request.form.get('description', '')

    tags = []
    if 'tags' in request.form:
        try:
            tags = json.loads(request.form.get('tags', '[]'))
        except json.JSONDecodeError:
            tags = []

    success, result = SecretService.create_file_secret(
        user_id=current_user_id,
        file=file,
        secret_name=secret_name,
        folder_id=folder_id,
        description=description,
        tags=tags
    )

    if not success:
        return jsonify({"msg": result}), 400

    secret = result

    return jsonify({
        "msg": "File uploaded and encrypted successfully",
        "secret": {
            "id": secret.secret_id,
            "name": secret.secret_name,
            "type": secret.secret_type,
            "folder_id": secret.folder_id,
            "description": secret.description or "",
            "created_time": secret.created_time.isoformat(),
            "last_modified": secret.last_modified.isoformat(),
            "owner_id": secret.owner_id,
            "original_filename": secret.original_filename,
            "file_size": secret.file_size,
            "tags": [tag.name for tag in secret.tags] if hasattr(secret, 'tags') else [],
            "is_favorite": secret.is_favorite,
            "is_file_secret": secret.is_file_secret
        }
    }), 201


@secrets_bp.route('/<int:secret_id>/file', methods=['GET'])
@jwt_required()
def download_file_secret(secret_id):
    """Downloads a file secret after decrypting it."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    secret = Secret.query.get(secret_id)
    if not secret:
        return jsonify({"msg": "Secret not found"}), 404

    current_app.logger.info(f"File access request - secret_id: {secret_id}, user_id: {current_user_id}")
    current_app.logger.info(
        f"Secret details - owner_id: {secret.owner_id} ({type(secret.owner_id).__name__}), requester_id: {current_user_id} ({type(current_user_id).__name__})")

    has_permission = False

    owner_id = int(secret.owner_id) if not isinstance(secret.owner_id, int) else secret.owner_id
    user_id = int(current_user_id) if not isinstance(current_user_id, int) else current_user_id

    if owner_id == user_id:
        has_permission = True
        current_app.logger.info(f"Access granted: User {current_user_id} is the owner of secret {secret_id}")
    else:
        permission = SecretPermission.query.filter_by(
            secret_id=secret_id,
            user_id=user_id,
            can_read=True
        ).first()

        if permission:
            has_permission = True
            current_app.logger.info(
                f"Access granted: User {current_user_id} has explicit read permission for secret {secret_id}")
        else:
            if secret.folder_id:
                folder_permission = FolderPermission.query.filter_by(
                    folder_id=secret.folder_id,
                    user_id=user_id,
                    can_read=True
                ).first()

                if folder_permission:
                    has_permission = True
                    current_app.logger.info(
                        f"Access granted: User {current_user_id} has folder-level permission for secret {secret_id} in folder {secret.folder_id}")

    if not has_permission:
        current_app.logger.warning(f"Unauthorized access attempt to file secret {secret_id} by user {current_user_id}")
        return jsonify({"msg": "Unauthorized access"}), 403

    current_app.logger.info(f"Retrieving file content for secret {secret_id}")
    success, result = SecretService.get_file_content(
        secret=secret,
        check_permission_func=None,
        user_id=None
    )

    if not success:
        current_app.logger.error(f"Error retrieving file content: {result}")
        return jsonify({"msg": result}), 400

    file_data = result['data']
    mime_type = result['mime_type']
    filename = result['filename']

    current_app.logger.info(
        f"Successfully retrieved file for secret {secret_id}, size: {len(file_data)} bytes, type: {mime_type}")

    file_stream = io.BytesIO(file_data)
    file_stream.seek(0)

    return send_file(
        file_stream,
        mimetype=mime_type,
        as_attachment=True,
        download_name=filename
    )


@secrets_bp.route('/<int:secret_id>/revoke-access/<int:revoke_user_id>', methods=['DELETE'])
@jwt_required()
def revoke_secret_access(secret_id, revoke_user_id):
    """Revokes a specific user's access to a secret."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    secret = Secret.query.get(secret_id)
    if not secret:
        return jsonify({"msg": "Secret not found"}), 404

    has_permission = False

    if secret.owner_id == int(current_user_id):
        has_permission = True
    else:
        permission = SecretPermission.query.filter_by(
            secret_id=secret_id,
            user_id=current_user_id,
            can_write=True
        ).first()
        if permission:
            has_permission = True

    if not has_permission:
        return jsonify({"msg": "You don't have permission to revoke access to this secret"}), 403

    permission_to_revoke = SecretPermission.query.filter_by(
        secret_id=secret_id,
        user_id=revoke_user_id
    ).first()

    if not permission_to_revoke:
        return jsonify({"msg": "User does not have access to this secret"}), 404

    db.session.delete(permission_to_revoke)
    db.session.commit()

    current_app.logger.info(f"User {current_user_id} revoked access for user {revoke_user_id} to secret {secret_id}")

    return jsonify({"msg": "Access successfully revoked"}), 200


@secrets_bp.route('/<int:secret_id>/shared-users', methods=['GET'])
@jwt_required()
def get_secret_shared_users(secret_id):
    """Retrieves a list of all users a secret is shared with."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    secret = Secret.query.get(secret_id)
    if not secret:
        return jsonify({"msg": "Secret not found"}), 404

    if secret.owner_id != int(current_user_id):
        permission = SecretPermission.query.filter_by(
            secret_id=secret_id,
            user_id=current_user_id,
            can_read=True
        ).first()

        if not permission:
            return jsonify({"msg": "Unauthorized access"}), 403

    permissions = SecretPermission.query.filter_by(secret_id=secret_id).all()

    shared_users = []
    for perm in permissions:
        user = User.query.get(perm.user_id)
        if user:
            shared_users.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "can_read": perm.can_read,
                "can_write": perm.can_write,
                "can_delete": perm.can_delete
            })

    return jsonify({
        "shared_users": shared_users
    }), 200


@secrets_bp.route('/file/<int:secret_id>/', methods=['PUT'])
@secrets_bp.route('/file/<int:secret_id>', methods=['PUT'])
@jwt_required()
def update_file_secret(secret_id):
    """Updates an existing file secret, allowing for a new file upload or metadata changes."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    secret = Secret.query.get(secret_id)
    if not secret:
        return jsonify({"msg": "Secret not found"}), 404

    if secret.owner_id != current_user_id:
        permission = SecretPermission.query.filter_by(
            secret_id=secret_id,
            user_id=current_user_id,
            can_write=True
        ).first()

        if not permission:
            return jsonify({"msg": "You don't have permission to update this secret"}), 403

    update_params = {}

    if 'file' in request.files and request.files['file'].filename != '':
        update_params['file'] = request.files['file']

    if 'name' in request.form:
        update_params['secret_name'] = request.form.get('name')

    if 'folder_id' in request.form:
        folder_id = request.form.get('folder_id')
        update_params['folder_id'] = int(folder_id) if folder_id and folder_id.isdigit() else None

    if 'description' in request.form:
        update_params['description'] = request.form.get('description')

    if 'tags' in request.form:
        try:
            update_params['tags'] = json.loads(request.form.get('tags', '[]'))
        except json.JSONDecodeError:
            update_params['tags'] = []

    success, result = SecretService.update_file_secret(secret, **update_params)

    if not success:
        return jsonify({"msg": result}), 400

    secret = result

    users_with_access = []

    permissions = SecretPermission.query.filter_by(secret_id=secret_id).all()
    for perm in permissions:
        if perm.user_id != current_user_id and perm.user_id not in users_with_access:
            users_with_access.append(perm.user_id)

    if secret.folder_id:
        folder = Folder.query.get(secret.folder_id)
        if folder and folder.is_shared_folder:
            folder_permissions = FolderPermission.query.filter_by(folder_id=secret.folder_id).all()
            for perm in folder_permissions:
                if perm.user_id != current_user_id and perm.user_id not in users_with_access:
                    users_with_access.append(perm.user_id)

    socketio.emit('secret_updated', {
        'secret_id': secret.secret_id,
        'secret_name': secret.secret_name,
        'owner_id': secret.owner_id,
        'folder_id': secret.folder_id,
        'updated_by': current_user_id,
        'users_with_access': users_with_access
    })

    return jsonify({
        "msg": "Secret updated successfully",
        "secret": {
            "id": secret.secret_id,
            "name": secret.secret_name,
            "type": secret.secret_type,
            "folder_id": secret.folder_id,
            "description": secret.description or "",
            "created_time": secret.created_time.isoformat(),
            "last_modified": secret.last_modified.isoformat(),
            "owner_id": secret.owner_id,
            "original_filename": secret.original_filename,
            "file_size": secret.file_size,
            "tags": [tag.name for tag in secret.tags] if hasattr(secret, 'tags') else [],
            "is_favorite": secret.is_favorite,
            "is_file_secret": secret.is_file_secret
        }
    }), 200


@secrets_bp.route('/<int:secret_id>/move', methods=['POST'])
@jwt_required()
def move_secret(secret_id):
    """Moves a secret to a different folder in the user's view."""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        current_app.logger.debug(f"User {current_user_id} attempting to move secret {secret_id}")

        if 'folder_id' not in data:
            return jsonify({"msg": "Folder ID is required"}), 400

        folder_id = data['folder_id']

        secret = Secret.query.get(secret_id)
        if not secret:
            return jsonify({"msg": "Secret not found"}), 404

        is_secret_owner = secret.owner_id == int(current_user_id)
        has_direct_access = False

        if not is_secret_owner:
            any_permission = SecretPermission.query.filter_by(
                secret_id=secret_id,
                user_id=current_user_id
            ).first()

            if not any_permission:
                return jsonify({"msg": "You don't have access to this secret"}), 403

            has_direct_access = True
        else:
            has_direct_access = True

        folder = None
        if folder_id is not None:
            folder = Folder.query.get(folder_id)
            if not folder:
                return jsonify({"msg": "Destination folder not found"}), 404

            if folder.owner_id != int(current_user_id):
                folder_permission = FolderPermission.query.filter_by(
                    folder_id=folder_id,
                    user_id=current_user_id,
                    can_read=True
                ).first()

                if not folder_permission:
                    return jsonify({"msg": "You don't have permission to access this folder"}), 403

        if is_secret_owner:
            old_folder_id = secret.folder_id
            secret.folder_id = folder_id

            UserSecretView.set_user_view(
                user_id=current_user_id,
                secret_id=secret_id,
                folder_id=folder_id
            )

            if folder and folder.is_shared_folder:
                folder_permissions = FolderPermission.query.filter_by(
                    folder_id=folder_id
                ).all()

                for folder_perm in folder_permissions:
                    if folder_perm.user_id == secret.owner_id:
                        continue

                    secret_perm = SecretPermission.query.filter_by(
                        secret_id=secret_id,
                        user_id=folder_perm.user_id
                    ).first()

                    if secret_perm:
                        secret_perm.can_read = folder_perm.can_read
                        secret_perm.can_write = folder_perm.can_write
                        secret_perm.can_delete = folder_perm.can_delete
                    else:
                        secret_perm = SecretPermission(
                            secret_id=secret_id,
                            user_id=folder_perm.user_id,
                            can_read=folder_perm.can_read,
                            can_write=folder_perm.can_write,
                            can_delete=folder_perm.can_delete
                        )
                        db.session.add(secret_perm)

                    if folder_perm.can_read:
                        user_view = UserSecretView.get_user_view(folder_perm.user_id, secret_id)
                        if user_view:
                            user_view.folder_id = folder_id
                            current_app.logger.debug(
                                f"Updated view for secret {secret_id} to folder {folder_id} for user {folder_perm.user_id}")
                        else:
                            UserSecretView.set_user_view(
                                user_id=folder_perm.user_id,
                                secret_id=secret_id,
                                folder_id=folder_id
                            )
                            current_app.logger.debug(
                                f"Created view for secret {secret_id} in folder {folder_id} for user {folder_perm.user_id}")

            if folder_id is None or (folder and not folder.is_shared_folder):
                existing_permissions = SecretPermission.query.filter(
                    SecretPermission.secret_id == secret_id,
                    SecretPermission.user_id != secret.owner_id
                ).all()

                for perm in existing_permissions:
                    if not perm.can_read:
                        perm.can_read = True
                        db.session.add(perm)

            current_app.logger.info(
                f"Owner {current_user_id} moved secret {secret_id} from folder {old_folder_id} to {folder_id}")
        else:
            UserSecretView.set_user_view(
                user_id=current_user_id,
                secret_id=secret_id,
                folder_id=folder_id
            )

            current_app.logger.info(
                f"User {current_user_id} updated their view of secret {secret_id} to folder {folder_id}")

        db.session.commit()

        users_to_notify = []
        if folder_id is not None and folder and folder.is_shared_folder:
            folder_permissions = FolderPermission.query.filter_by(folder_id=folder_id).all()
            for perm in folder_permissions:
                if perm.user_id != int(current_user_id) and perm.user_id not in users_to_notify:
                    users_to_notify.append(perm.user_id)

            socketio.emit('secret_moved', {
                'secret_id': secret.secret_id,
                'secret_name': secret.secret_name,
                'owner_id': secret.owner_id,
                'folder_id': folder_id,
                'moved_by': current_user_id,
                'users_to_notify': users_to_notify
            })

        return jsonify({
            "msg": "Secret moved successfully",
            "folder_id": folder_id,
            "is_view_only": not is_secret_owner
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error moving secret: {str(e)}")
        return jsonify({"msg": f"Error: {str(e)}"}), 500
