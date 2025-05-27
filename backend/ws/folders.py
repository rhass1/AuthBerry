#! /usr/bin/env python3


from flask import current_app, request
from flask_socketio import emit
from backend.extensions import socketio, db
from backend.services.ws_service import decrypt_from_client, encrypt_for_client, client_sessions
from backend.models.folder import Folder


@socketio.on('get_folders')
def handle_get_folders(data):
    """
    Handles WebSocket requests to retrieve all folders accessible to the authenticated user.
    Folders include those owned by the user and those shared with them.
    """
    sid = request.sid

    if sid not in client_sessions or 'user_id' not in client_sessions[sid]:
        emit('error', {'message': 'Authentication required'})
        return

    user_id = client_sessions[sid]['user_id']

    try:
        query = Folder.query.filter(
            (Folder.user_id == user_id) |
            (Folder.shared_with.any(id=user_id))
        )

        folders = query.all()

        folders_data = [{
            'id': folder.id,
            'name': folder.name,
            'description': folder.description,
            'user_id': folder.user_id,
            'parent_id': folder.parent_id,
            'created_at': folder.created_at.isoformat(),
            'updated_at': folder.updated_at.isoformat() if folder.updated_at else None,
            'is_shared': len(folder.shared_with) > 0,
            'tags': [tag.name for tag in folder.tags]
        } for folder in folders]

        encrypted_response = encrypt_for_client(sid, {'folders': folders_data})

        emit('folders', {'encrypted': encrypted_response})

    except Exception as e:
        current_app.logger.error(f"Error getting folders: {str(e)}")
        emit('error', {'message': 'Failed to get folders'})


@socketio.on('get_folder')
def handle_get_folder(data):
    """
    Handles WebSocket requests to retrieve a specific folder by ID for the authenticated user.
    Includes details about the folder and its accessible secrets.
    """
    sid = request.sid

    if sid not in client_sessions or 'user_id' not in client_sessions[sid]:
        emit('error', {'message': 'Authentication required'})
        return

    user_id = client_sessions[sid]['user_id']

    try:
        decrypted_data = decrypt_from_client(sid, data['encrypted'])
        folder_id = decrypted_data.get('folder_id')

        if not folder_id:
            emit('error', {'message': 'Folder ID is required'})
            return

        folder = Folder.query.filter(
            Folder.id == folder_id,
            ((Folder.user_id == user_id) | (Folder.shared_with.any(id=user_id)))
        ).first()

        if not folder:
            encrypted_response = encrypt_for_client(sid, {'error': 'Folder not found'})
            emit('folder_error', {'encrypted': encrypted_response})
            return

        secrets = []
        for secret in folder.secrets:
            if secret.user_id == user_id or user_id in [u.id for u in secret.shared_with]:
                secrets.append({
                    'id': secret.id,
                    'name': secret.name,
                    'description': secret.description,
                    'username': secret.username,
                    'url': secret.url,
                    'is_favorite': secret.is_favorite,
                    'is_shared': len(secret.shared_with) > 0,
                    'user_id': secret.user_id,
                    'created_at': secret.created_at.isoformat(),
                    'updated_at': secret.updated_at.isoformat() if secret.updated_at else None,
                    'tags': [tag.name for tag in secret.tags]
                })

        folder_data = {
            'id': folder.id,
            'name': folder.name,
            'description': folder.description,
            'user_id': folder.user_id,
            'parent_id': folder.parent_id,
            'created_at': folder.created_at.isoformat(),
            'updated_at': folder.updated_at.isoformat() if folder.updated_at else None,
            'is_shared': len(folder.shared_with) > 0,
            'tags': [tag.name for tag in folder.tags],
            'secrets': secrets,
            'shared_with': [{
                'id': user.id,
                'username': user.username
            } for user in folder.shared_with]
        }

        encrypted_response = encrypt_for_client(sid, {'folder': folder_data})

        emit('folder', {'encrypted': encrypted_response})

    except Exception as e:
        current_app.logger.error(f"Error getting folder: {str(e)}")
        emit('error', {'message': 'Failed to get folder'})


@socketio.on('create_folder')
def handle_create_folder(data):
    """
    Handles WebSocket requests to create a new folder for the authenticated user.
    """
    sid = request.sid

    if sid not in client_sessions or 'user_id' not in client_sessions[sid]:
        emit('error', {'message': 'Authentication required'})
        return

    user_id = client_sessions[sid]['user_id']

    try:
        decrypted_data = decrypt_from_client(sid, data['encrypted'])

        new_folder = Folder(
            name=decrypted_data.get('name'),
            description=decrypted_data.get('description', ''),
            user_id=user_id,
            parent_id=decrypted_data.get('parent_id')
        )

        tags = decrypted_data.get('tags', [])
        if tags:
            from backend.models.tag import Tag
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                new_folder.tags.append(tag)

        db.session.add(new_folder)
        db.session.commit()

        folder_data = {
            'id': new_folder.id,
            'name': new_folder.name,
            'description': new_folder.description,
            'user_id': new_folder.user_id,
            'parent_id': new_folder.parent_id,
            'created_at': new_folder.created_at.isoformat(),
            'updated_at': new_folder.updated_at.isoformat() if new_folder.updated_at else None,
            'is_shared': False,
            'tags': [tag.name for tag in new_folder.tags]
        }

        encrypted_response = encrypt_for_client(sid, {'folder': folder_data})

        emit('folder_created', {'encrypted': encrypted_response})

    except Exception as e:
        current_app.logger.error(f"Error creating folder: {str(e)}")
        emit('error', {'message': 'Failed to create folder'})
