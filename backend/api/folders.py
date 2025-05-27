#! /usr/bin/env python3


from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone

from backend.models.user import User
from backend.models.folder import Folder, FolderPermission, FolderType
from backend.models.tag import Tag
from backend.models.secret import Secret
from backend.models.permission import SecretPermission, UserSecretView
from backend.extensions import db, socketio

folders_bp = Blueprint('folders', __name__)


@folders_bp.route('/', methods=['GET'])
@jwt_required()
def get_folders():
    """Retrieves all folders accessible to the current user, including those they own and those shared with them."""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        owned_folders = Folder.query.filter_by(owner_id=current_user_id).all()

        permitted_folders = Folder.query.join(FolderPermission).filter(
            FolderPermission.user_id == current_user_id,
            FolderPermission.can_read == True
        ).all()

        all_folders = {}

        for folder in owned_folders:
            all_folders[folder.folder_id] = {
                "id": folder.folder_id,
                "name": folder.name,
                "description": folder.description,
                "parent_id": folder.parent_id,
                "owner_id": folder.owner_id,
                "is_owner": True,
                "folder_type": folder.folder_type.value,
                "is_shared_folder": folder.is_shared_folder,
                "path": folder.get_full_path(),
                "created_time": folder.created_time.isoformat(),
                "last_modified": folder.last_modified.isoformat(),
                "permissions": {
                    "can_read": True,
                    "can_write": True,
                    "can_delete": True
                },
                "tags": [tag.name for tag in folder.tags]
            }

        for folder in permitted_folders:
            if folder.folder_id not in all_folders:
                permission = next((p for p in folder.permissions if p.user_id == current_user_id), None)

                all_folders[folder.folder_id] = {
                    "id": folder.folder_id,
                    "name": folder.name,
                    "description": folder.description,
                    "parent_id": folder.parent_id,
                    "owner_id": folder.owner_id,
                    "is_owner": False,
                    "folder_type": folder.folder_type.value,
                    "is_shared_folder": folder.is_shared_folder,
                    "path": folder.get_full_path(),
                    "created_time": folder.created_time.isoformat(),
                    "last_modified": folder.last_modified.isoformat(),
                    "permissions": {
                        "can_read": permission.can_read if permission else False,
                        "can_write": permission.can_write if permission else False,
                        "can_delete": permission.can_delete if permission else False
                    },
                    "tags": [tag.name for tag in folder.tags]
                }

        return jsonify({"folders": list(all_folders.values())}), 200

    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_folders: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        current_app.logger.error(f"Error in get_folders: {str(e)}")
        return jsonify({"error": "An error occurred while retrieving folders"}), 500


@folders_bp.route('/<int:folder_id>', methods=['GET'])
@jwt_required()
def get_folder(folder_id):
    """Retrieves a specific folder by its ID, along with its subfolders and sharing information."""
    try:
        current_user_id = int(get_jwt_identity())
        current_app.logger.debug(f"User {current_user_id} attempting to access folder {folder_id}")

        folder = Folder.query.options(
            joinedload(Folder.tags)
        ).get(folder_id)

        if not folder:
            current_app.logger.warning(f"Folder {folder_id} not found")
            return jsonify({"error": "Folder not found"}), 404

        is_owner = folder.owner_id == current_user_id
        has_permission = False

        if is_owner:
            has_permission = True
            current_app.logger.debug(f"User {current_user_id} is the owner of folder {folder_id}")
        else:
            permission = FolderPermission.query.filter_by(
                folder_id=folder_id,
                user_id=current_user_id
            ).first()

            if permission and permission.can_read:
                has_permission = True
                current_app.logger.debug(f"User {current_user_id} has read permission for folder {folder_id}")
            else:
                current_app.logger.warning(
                    f"Access denied for user {current_user_id} to folder {folder_id}, is_owner={is_owner}, owner_id={folder.owner_id}")

        if not has_permission:
            return jsonify({"error": "Access denied"}), 403

        subfolders = Folder.query.filter_by(parent_id=folder_id).all()

        folder_data = {
            "id": folder.folder_id,
            "name": folder.name,
            "description": folder.description,
            "parent_id": folder.parent_id,
            "owner_id": folder.owner_id,
            "is_owner": is_owner,
            "folder_type": folder.folder_type.value,
            "is_shared_folder": folder.is_shared_folder,
            "path": folder.get_full_path(),
            "created_time": folder.created_time.isoformat(),
            "last_modified": folder.last_modified.isoformat(),
            "subfolders": [
                {
                    "id": subfolder.folder_id,
                    "name": subfolder.name,
                    "parent_id": subfolder.parent_id,
                    "folder_type": subfolder.folder_type.value
                } for subfolder in subfolders
            ],
            "tags": [tag.name for tag in folder.tags],
            "permissions": {
                "can_read": True,
                "can_write": is_owner or (permission and permission.can_write),
                "can_delete": is_owner or (permission and permission.can_delete),
                "can_share": is_owner or (permission and permission.can_write),
                "is_owner": is_owner
            }
        }

        shared_users = []
        for perm in folder.permissions:
            if perm.user_id != current_user_id:
                user = User.query.get(perm.user_id)
                if user:
                    shared_users.append({
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "permissions": {
                            "can_read": perm.can_read,
                            "can_write": perm.can_write,
                            "can_delete": perm.can_delete,
                            "inherit": perm.inherit
                        }
                    })

        folder_data["shared_with"] = shared_users

        current_app.logger.debug(f"Successfully retrieved folder {folder_id} for user {current_user_id}")
        return jsonify(folder_data), 200

    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_folder: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        current_app.logger.error(f"Error in get_folder: {str(e)}")
        return jsonify({"error": "An error occurred while retrieving the folder"}), 500


@folders_bp.route('/', methods=['POST'])
@jwt_required()
def create_folder():
    """Creates a new folder for the current user."""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data.get('name'):
            return jsonify({"error": "Folder name is required"}), 400

        parent_id = data.get('parent_id')

        if parent_id:
            parent_folder = Folder.query.get(parent_id)

            if not parent_folder:
                return jsonify({"error": "Parent folder not found"}), 404

            if parent_folder.owner_id != current_user_id:
                permission = FolderPermission.query.filter_by(
                    folder_id=parent_id,
                    user_id=current_user_id,
                    can_write=True
                ).first()

                if not permission:
                    return jsonify({"error": "You don't have permission to create folders here"}), 403

        folder_type = FolderType.REGULAR
        if data.get('folder_type') == 'shared':
            folder_type = FolderType.SHARED

        folder = Folder(
            name=data['name'],
            description=data.get('description', ''),
            parent_id=parent_id,
            owner_id=current_user_id,
            folder_type=folder_type,
            created_time=datetime.now(timezone.utc),
            last_modified=datetime.now(timezone.utc)
        )

        if 'tags' in data and isinstance(data['tags'], list):
            for tag_name in data['tags']:
                tag = Tag.query.filter_by(name=tag_name, owner_id=current_user_id).first()

                if not tag:
                    tag = Tag(name=tag_name, owner_id=current_user_id)
                    db.session.add(tag)

                folder.tags.append(tag)

        db.session.add(folder)
        db.session.commit()

        folder_data = {
            "id": folder.folder_id,
            "name": folder.name,
            "description": folder.description,
            "parent_id": folder.parent_id,
            "owner_id": folder.owner_id,
            "is_owner": True,
            "folder_type": folder.folder_type.value,
            "is_shared_folder": folder.is_shared_folder,
            "path": folder.get_full_path(),
            "created_time": folder.created_time.isoformat(),
            "last_modified": folder.last_modified.isoformat(),
            "tags": [tag.name for tag in folder.tags]
        }

        socketio.emit('folder_created', {
            'folder': folder_data
        })

        current_app.logger.info(f"User {current_user_id} created folder {folder.folder_id}: {folder.name}")
        return jsonify(folder_data), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in create_folder: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in create_folder: {str(e)}")
        return jsonify({"error": "An error occurred while creating the folder"}), 500


@folders_bp.route('/<int:folder_id>', methods=['PUT'])
@jwt_required()
def update_folder(folder_id):
    """Updates an existing folder's properties, such as name, description, parent, and type."""
    try:
        current_user_id = int(get_jwt_identity())

        data = request.get_json()

        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        is_owner = folder.owner_id == current_user_id

        if not is_owner:
            permission = FolderPermission.query.filter_by(
                folder_id=folder_id,
                user_id=current_user_id,
                can_write=True
            ).first()

            if not permission:
                return jsonify({"error": "You don't have permission to update this folder"}), 403

        if 'name' in data and data['name'] and data['name'].strip():
            folder.name = data['name'].strip()

        if 'description' in data:
            folder.description = data['description']

        if 'parent_id' in data:
            new_parent_id = data['parent_id']

            if new_parent_id == folder_id:
                return jsonify({"error": "A folder cannot be its own parent"}), 400

            if new_parent_id:
                parent_folder = Folder.query.get(new_parent_id)

                if not parent_folder:
                    return jsonify({"error": "Parent folder not found"}), 404

                if parent_folder.owner_id != current_user_id:
                    permission = FolderPermission.query.filter_by(
                        folder_id=new_parent_id,
                        user_id=current_user_id,
                        can_write=True
                    ).first()

                    if not permission:
                        return jsonify({"error": "You don't have permission to move this folder here"}), 403

                ancestor = parent_folder.parent
                visited = {parent_folder.folder_id}

                while ancestor and ancestor.folder_id not in visited:
                    if ancestor.folder_id == folder_id:
                        return jsonify({"error": "Circular reference detected in folder hierarchy"}), 400
                    visited.add(ancestor.folder_id)
                    ancestor = ancestor.parent

            folder.parent_id = new_parent_id

        was_shared_folder = folder.is_shared_folder

        if 'folder_type' in data and folder.owner_id == current_user_id:
            if data['folder_type'] == 'shared':
                folder.folder_type = FolderType.SHARED
            else:
                folder.folder_type = FolderType.REGULAR

        folder.last_modified = datetime.now(timezone.utc)

        if 'tags' in data and isinstance(data['tags'], list):
            folder.tags = []

            for tag_name in data['tags']:
                tag = Tag.query.filter_by(name=tag_name, owner_id=current_user_id).first()

                if not tag:
                    tag = Tag(name=tag_name, owner_id=current_user_id)
                    db.session.add(tag)

                folder.tags.append(tag)

        if not was_shared_folder and folder.is_shared_folder:
            folder_secrets = Secret.query.filter_by(folder_id=folder_id).all()
            current_app.logger.debug(
                f"Found {len(folder_secrets)} secrets to update permissions for in newly shared folder {folder_id}")

            folder_permissions = FolderPermission.query.filter_by(folder_id=folder_id).all()

            for secret in folder_secrets:
                for folder_perm in folder_permissions:
                    if folder_perm.user_id == secret.owner_id:
                        continue

                    existing_perm = SecretPermission.query.filter_by(
                        secret_id=secret.secret_id,
                        user_id=folder_perm.user_id
                    ).first()

                    if existing_perm:
                        existing_perm.can_read = folder_perm.can_read
                        existing_perm.can_write = folder_perm.can_write
                        existing_perm.can_delete = folder_perm.can_delete
                    else:
                        new_perm = SecretPermission(
                            secret_id=secret.secret_id,
                            user_id=folder_perm.user_id,
                            can_read=folder_perm.can_read,
                            can_write=folder_perm.can_write,
                            can_delete=folder_perm.can_delete
                        )
                        db.session.add(new_perm)
                        current_app.logger.debug(
                            f"Added permission for user {folder_perm.user_id} on secret {secret.secret_id} (folder became shared)")

                    if folder_perm.can_read:
                        user_view = UserSecretView.get_user_view(folder_perm.user_id, secret.secret_id)
                        if user_view:
                            user_view.folder_id = folder_id
                            current_app.logger.debug(
                                f"Updated view for secret {secret.secret_id} to folder {folder_id} for user {folder_perm.user_id}")
                        else:
                            UserSecretView.set_user_view(
                                user_id=folder_perm.user_id,
                                secret_id=secret.secret_id,
                                folder_id=folder_id
                            )
                            current_app.logger.debug(
                                f"Created view for secret {secret.secret_id} in folder {folder_id} for user {folder_perm.user_id}")

        db.session.commit()

        return jsonify({
            "id": folder.folder_id,
            "name": folder.name,
            "description": folder.description,
            "parent_id": folder.parent_id,
            "owner_id": folder.owner_id,
            "folder_type": folder.folder_type.value,
            "is_shared_folder": folder.is_shared_folder,
            "path": folder.get_full_path(),
            "created_time": folder.created_time.isoformat(),
            "last_modified": folder.last_modified.isoformat(),
            "tags": [tag.name for tag in folder.tags]
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_folder: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in update_folder: {str(e)}")
        return jsonify({"error": "An error occurred while updating the folder"}), 500


@folders_bp.route('/<int:folder_id>', methods=['DELETE'])
@jwt_required()
def delete_folder(folder_id):
    """Deletes a folder by its ID."""
    try:
        current_user_id = int(get_jwt_identity())

        folder = Folder.query.get(folder_id)

        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        is_owner = folder.owner_id == current_user_id
        has_permission = False

        if is_owner:
            has_permission = True
        else:
            permission = FolderPermission.query.filter_by(
                folder_id=folder_id,
                user_id=current_user_id,
                can_delete=True
            ).first()

            if permission:
                has_permission = True

        if not has_permission:
            return jsonify({"error": "You don't have permission to delete this folder"}), 403

        folder_owner_id = folder.owner_id

        db.session.delete(folder)
        db.session.commit()

        socketio.emit('folder_deleted', {
            'folder_id': folder_id,
            'owner_id': folder_owner_id
        })

        current_app.logger.info(f"User {current_user_id} deleted folder {folder_id}")
        return jsonify({"message": "Folder deleted successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in delete_folder: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in delete_folder: {str(e)}")
        return jsonify({"error": "An error occurred while deleting the folder"}), 500


@folders_bp.route('/<int:folder_id>/share', methods=['POST'])
@jwt_required()
def share_folder(folder_id):
    """Shares a folder with another user, granting specified permissions."""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data.get('user_id'):
            return jsonify({"error": "User ID is required"}), 400

        target_user_id = data.get('user_id')

        permissions = data.get('permissions', {})
        can_read = permissions.get('can_read', True)
        can_write = permissions.get('can_write', False)
        can_delete = permissions.get('can_delete', False)
        inherit = permissions.get('inherit', True)

        if not any([can_read, can_write, can_delete]):
            can_read = True

        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        target_user = User.query.get(target_user_id)
        if not target_user:
            return jsonify({"error": "Target user not found"}), 404

        is_owner = folder.owner_id == current_user_id

        if not is_owner:
            return jsonify({"error": "Only the owner can share this folder"}), 403

        if current_user_id == target_user_id:
            return jsonify({"error": "You cannot share a folder with yourself"}), 400

        existing_permission = FolderPermission.query.filter_by(
            folder_id=folder_id,
            user_id=target_user_id
        ).first()

        if existing_permission:
            existing_permission.can_read = can_read
            existing_permission.can_write = can_write
            existing_permission.can_delete = can_delete
            existing_permission.inherit = inherit
        else:
            permission = FolderPermission(
                folder_id=folder_id,
                user_id=target_user_id,
                can_read=can_read,
                can_write=can_write,
                can_delete=can_delete,
                inherit=inherit
            )
            db.session.add(permission)

        if folder.folder_type != FolderType.SHARED:
            folder.folder_type = FolderType.SHARED
            current_app.logger.debug(f"Updated folder {folder_id} to SHARED type")

        db.session.commit()

        folder_secrets = Secret.query.filter_by(folder_id=folder_id).all()
        current_app.logger.debug(f"Found {len(folder_secrets)} secrets to share in folder {folder_id}")

        for secret in folder_secrets:
            if secret.owner_id == target_user_id:
                continue

            existing_secret_perm = SecretPermission.query.filter_by(
                secret_id=secret.secret_id,
                user_id=target_user_id
            ).first()

            if existing_secret_perm:
                existing_secret_perm.can_read = can_read
                existing_secret_perm.can_write = can_write
                existing_secret_perm.can_delete = can_delete
            else:
                secret_perm = SecretPermission(
                    secret_id=secret.secret_id,
                    user_id=target_user_id,
                    can_read=can_read,
                    can_write=can_write,
                    can_delete=can_delete
                )
                db.session.add(secret_perm)
                current_app.logger.debug(f"Shared secret {secret.secret_id} with user {target_user_id}")

            if can_read:
                user_view = UserSecretView.get_user_view(target_user_id, secret.secret_id)
                if user_view:
                    user_view.folder_id = folder_id
                    current_app.logger.debug(
                        f"Updated view for secret {secret.secret_id} to folder {folder_id} for user {target_user_id}")
                else:
                    UserSecretView.set_user_view(
                        user_id=target_user_id,
                        secret_id=secret.secret_id,
                        folder_id=folder_id
                    )
                    current_app.logger.debug(
                        f"Created view for secret {secret.secret_id} in folder {folder_id} for user {target_user_id}")

        db.session.commit()

        socketio.emit('folder_shared', {
            'folder_id': folder_id,
            'folder_name': folder.name,
            'shared_by': current_user_id,
            'shared_with': target_user_id,
            'permissions': {
                'can_read': can_read,
                'can_write': can_write,
                'can_delete': can_delete,
                'inherit': inherit
            }
        })

        return jsonify({
            "message": "Folder shared successfully",
            "shared_with": {
                "user_id": target_user_id,
                "username": target_user.username,
                "email": target_user.email,
                "permissions": {
                    "can_read": can_read,
                    "can_write": can_write,
                    "can_delete": can_delete,
                    "inherit": inherit
                }
            }
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in share_folder: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in share_folder: {str(e)}")
        return jsonify({"error": "An error occurred while sharing the folder"}), 500


@folders_bp.route('/<int:folder_id>/share/<int:user_id>', methods=['DELETE'])
@jwt_required()
def unshare_folder(folder_id, user_id):
    """Removes sharing permissions for a folder from a specific user."""
    try:
        current_user_id = int(get_jwt_identity())

        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        if folder.owner_id != current_user_id:
            return jsonify({"error": "Only the owner can unshare this folder"}), 403

        permission = FolderPermission.query.filter_by(
            folder_id=folder_id,
            user_id=user_id
        ).first()

        if not permission:
            return jsonify({"error": "Folder is not shared with this user"}), 404

        db.session.delete(permission)

        folder_secrets = Secret.query.filter_by(folder_id=folder_id).all()
        current_app.logger.debug(f"Found {len(folder_secrets)} secrets to check for unsharing in folder {folder_id}")

        for secret in folder_secrets:
            if secret.owner_id == user_id:
                continue

            secret_perm = SecretPermission.query.filter_by(
                secret_id=secret.secret_id,
                user_id=user_id
            ).first()

            if secret_perm:
                db.session.delete(secret_perm)
                current_app.logger.debug(f"Removed permissions for secret {secret.secret_id} from user {user_id}")

            user_view = UserSecretView.get_user_view(user_id, secret.secret_id)
            if user_view:
                db.session.delete(user_view)
                current_app.logger.debug(f"Removed view for secret {secret.secret_id} from user {user_id}")

        remaining_shares = FolderPermission.query.filter_by(folder_id=folder_id).count()
        if remaining_shares == 0 and folder.folder_type == FolderType.SHARED:
            folder.folder_type = FolderType.REGULAR
            current_app.logger.debug(f"Updated folder {folder_id} back to REGULAR type - no more shares")

        db.session.commit()

        socketio.emit('folder_unshared', {
            'folder_id': folder_id,
            'unshared_with_id': user_id
        })

        return jsonify({"message": "Folder unshared successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in unshare_folder: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in unshare_folder: {str(e)}")
        return jsonify({"error": "An error occurred while unsharing the folder"}), 500


@folders_bp.route('/shared', methods=['GET'])
@jwt_required()
def get_shared_folders():
    """Retrieves all folders that have been shared with the current user."""
    try:
        current_user_id = int(get_jwt_identity())

        shared_folders = Folder.query.join(FolderPermission).filter(
            FolderPermission.user_id == current_user_id,
            FolderPermission.can_read == True,
            Folder.owner_id != current_user_id
        ).all()

        result = []
        for folder in shared_folders:
            permission = next((p for p in folder.permissions if p.user_id == current_user_id), None)

            result.append({
                "id": folder.folder_id,
                "name": folder.name,
                "description": folder.description,
                "parent_id": folder.parent_id,
                "owner_id": folder.owner_id,
                "owner": folder.owner.username if folder.owner else "Unknown",
                "path": folder.get_full_path(),
                "created_time": folder.created_time.isoformat(),
                "last_modified": folder.last_modified.isoformat(),
                "permissions": {
                    "can_read": permission.can_read if permission else False,
                    "can_write": permission.can_write if permission else False,
                    "can_delete": permission.can_delete if permission else False,
                    "inherit": permission.inherit if permission else False
                },
                "tags": [tag.name for tag in folder.tags]
            })

        return jsonify({"folders": result}), 200

    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in get_shared_folders: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        current_app.logger.error(f"Error in get_shared_folders: {str(e)}")
        return jsonify({"error": "An error occurred while retrieving shared folders"}), 500


@folders_bp.route('/<int:folder_id>/permissions', methods=['GET'])
@jwt_required()
def get_folder_permissions(folder_id):
    """Retrieves the current user's permissions for a specific folder."""
    try:
        current_user_id = int(get_jwt_identity())

        folder = Folder.query.get(folder_id)
        if not folder:
            return jsonify({"error": "Folder not found"}), 404

        is_owner = folder.owner_id == current_user_id

        if is_owner:
            return jsonify({
                "folder_id": folder_id,
                "permissions": {
                    "can_read": True,
                    "can_write": True,
                    "can_delete": True,
                    "can_share": True,
                    "is_owner": True
                }
            }), 200

        permission = FolderPermission.query.filter_by(
            folder_id=folder_id,
            user_id=current_user_id
        ).first()

        if not permission:
            return jsonify({
                "folder_id": folder_id,
                "permissions": {
                    "can_read": False,
                    "can_write": False,
                    "can_delete": False,
                    "can_share": False,
                    "is_owner": False
                }
            }), 200

        return jsonify({
            "folder_id": folder_id,
            "permissions": {
                "can_read": permission.can_read,
                "can_write": permission.can_write,
                "can_delete": permission.can_delete,
                "can_share": permission.can_write,
                "is_owner": False
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting folder permissions: {str(e)}")
        return jsonify({"error": "An error occurred while getting folder permissions"}), 500
