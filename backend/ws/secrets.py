#! /usr/bin/env python3


from flask import current_app, request
from flask_socketio import emit
from backend.extensions import socketio, db
from backend.services.ws_service import decrypt_from_client, encrypt_for_client, client_sessions
from backend.models.secret import Secret
from backend.services.secrets_service import SecretsService
from backend.models.tag import Tag
from backend.models.user import User


@socketio.on('get_secrets')
def handle_get_secrets(data):
    """
    Retrieves secrets for the authenticated user, optionally filtered by folder.
    It decrypts incoming filter parameters, queries accessible secrets,
    and sends back the encrypted secret data.
    """
    sid = request.sid

    if sid not in client_sessions or 'user_id' not in client_sessions[sid]:
        emit('error', {'message': 'Authentication required'})
        return

    user_id = client_sessions[sid]['user_id']

    try:
        decrypted_data = None
        folder_id = None

        if 'encrypted' in data:
            decrypted_data = decrypt_from_client(sid, data['encrypted'])
            folder_id = decrypted_data.get('folder_id')

        query = Secret.query.filter(
            (Secret.user_id == user_id) |
            (Secret.shared_with.any(id=user_id))
        )

        if folder_id:
            query = query.filter(Secret.folder_id == folder_id)

        secrets = query.all()

        secrets_data = [{
            'id': secret.id,
            'name': secret.name,
            'description': secret.description,
            'username': secret.username,
            'password': secret.password,
            'url': secret.url,
            'notes': secret.notes,
            'folder_id': secret.folder_id,
            'user_id': secret.user_id,
            'created_at': secret.created_at.isoformat(),
            'updated_at': secret.updated_at.isoformat() if secret.updated_at else None,
            'is_shared': len(secret.shared_with) > 0,
            'is_favorite': secret.is_favorite,
            'tags': [tag.name for tag in secret.tags]
        } for secret in secrets]

        encrypted_response = encrypt_for_client(sid, {'secrets': secrets_data})

        emit('secrets', {'encrypted': encrypted_response})

    except Exception as e:
        current_app.logger.error(f"Error getting secrets: {str(e)}")
        emit('error', {'message': 'Failed to get secrets'})


@socketio.on('get_secret')
def handle_get_secret(data):
    """
    Retrieves a specific secret by ID for the authenticated user.
    It decrypts the secret ID, queries the secret, and sends back the encrypted secret data.
    """
    sid = request.sid

    if sid not in client_sessions or 'user_id' not in client_sessions[sid]:
        emit('error', {'message': 'Authentication required'})
        return

    user_id = client_sessions[sid]['user_id']

    try:
        decrypted_data = decrypt_from_client(sid, data['encrypted'])
        secret_id = decrypted_data.get('secret_id')

        if not secret_id:
            emit('error', {'message': 'Secret ID is required'})
            return

        secret = Secret.query.filter(
            Secret.id == secret_id,
            ((Secret.user_id == user_id) | (Secret.shared_with.any(id=user_id)))
        ).first()

        if not secret:
            encrypted_response = encrypt_for_client(sid, {'error': 'Secret not found'})
            emit('secret_error', {'encrypted': encrypted_response})
            return

        secret_data = {
            'id': secret.id,
            'name': secret.name,
            'description': secret.description,
            'username': secret.username,
            'password': secret.password,
            'url': secret.url,
            'notes': secret.notes,
            'folder_id': secret.folder_id,
            'user_id': secret.user_id,
            'created_at': secret.created_at.isoformat(),
            'updated_at': secret.updated_at.isoformat() if secret.updated_at else None,
            'is_shared': len(secret.shared_with) > 0,
            'is_favorite': secret.is_favorite,
            'tags': [tag.name for tag in secret.tags],
            'shared_with': [{
                'id': user.id,
                'username': user.username
            } for user in secret.shared_with]
        }

        encrypted_response = encrypt_for_client(sid, {'secret': secret_data})

        emit('secret', {'encrypted': encrypted_response})

    except Exception as e:
        current_app.logger.error(f"Error getting secret: {str(e)}")
        emit('error', {'message': 'Failed to get secret'})


@socketio.on('create_secret')
def handle_create_secret(data):
    """
    Handles WebSocket requests to create a new secret for the authenticated user.
    It decrypts the secret data, creates the new secret in the database,
    and sends back the encrypted new secret data.
    """
    sid = request.sid

    if sid not in client_sessions or 'user_id' not in client_sessions[sid]:
        emit('error', {'message': 'Authentication required'})
        return

    user_id = client_sessions[sid]['user_id']

    try:
        decrypted_data = decrypt_from_client(sid, data['encrypted'])

        new_secret = Secret(
            name=decrypted_data.get('name'),
            description=decrypted_data.get('description', ''),
            username=decrypted_data.get('username', ''),
            password=decrypted_data.get('password', ''),
            url=decrypted_data.get('url', ''),
            notes=decrypted_data.get('notes', ''),
            folder_id=decrypted_data.get('folder_id'),
            user_id=user_id,
            is_favorite=decrypted_data.get('is_favorite', False)
        )

        tags = decrypted_data.get('tags', [])
        if tags:
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                new_secret.tags.append(tag)

        db.session.add(new_secret)
        db.session.commit()

        secret_data = {
            'id': new_secret.id,
            'name': new_secret.name,
            'description': new_secret.description,
            'username': new_secret.username,
            'password': new_secret.password,
            'url': new_secret.url,
            'notes': new_secret.notes,
            'folder_id': new_secret.folder_id,
            'user_id': new_secret.user_id,
            'created_at': new_secret.created_at.isoformat(),
            'updated_at': new_secret.updated_at.isoformat() if new_secret.updated_at else None,
            'is_shared': False,
            'is_favorite': new_secret.is_favorite,
            'tags': [tag.name for tag in new_secret.tags]
        }

        encrypted_response = encrypt_for_client(sid, {'secret': secret_data})

        emit('secret_created', {'encrypted': encrypted_response}, room=sid)

    except Exception as e:
        current_app.logger.error(f"Error creating secret: {str(e)}")
        emit('error', {'message': 'Failed to create secret'})


@socketio.on('get_all_secrets')
def handle_get_all_secrets():
    """
    Retrieves all secrets accessible to the current authenticated user.
    It queries all secrets via the `SecretsService` and sends back the encrypted list.
    """
    sid = request.sid

    if sid not in client_sessions or 'user_id' not in client_sessions[sid]:
        emit('error', {'message': 'Not authenticated'})
        return

    user_id = client_sessions[sid]['user_id']

    try:
        secrets = SecretsService.get_secrets_for_user(user_id)

        try:
            encrypted_response = encrypt_for_client(sid, {'secrets': secrets})
            emit('secrets', {'encrypted': encrypted_response})
        except Exception as e:
            current_app.logger.error(f"Could not encrypt secrets response: {str(e)}")
            current_app.logger.warning(f"Sending unencrypted secrets response for user {user_id}")
            emit('secrets', {'secrets': secrets})

    except Exception as e:
        current_app.logger.error(f"Error fetching secrets: {str(e)}")
        try:
            encrypted_error = encrypt_for_client(sid, {'error': str(e)})
            emit('error', {'encrypted': encrypted_error})
        except Exception as encryption_error:
            current_app.logger.error(f"Could not encrypt error response: {str(encryption_error)}")
            emit('error', {'error': str(e)})


@socketio.on('get_secret')
def handle_get_secret(data):
    """
    Retrieves a single secret by its ID for the current authenticated user.
    It fetches the secret via `SecretsService` and sends back the encrypted secret data.
    """
    sid = request.sid

    if sid not in client_sessions or 'user_id' not in client_sessions[sid]:
        emit('error', {'message': 'Not authenticated'})
        return

    user_id = client_sessions[sid]['user_id']

    if not data or 'id' not in data:
        try:
            encrypted_error = encrypt_for_client(sid, {'error': 'Secret ID is required'})
            emit('error', {'encrypted': encrypted_error})
        except Exception as e:
            current_app.logger.error(f"Could not encrypt error response: {str(e)}")
            emit('error', {'error': 'Secret ID is required'})
        return

    secret_id = data['id']

    try:
        secret = SecretsService.get_secret_by_id(secret_id, user_id)

        if not secret:
            try:
                encrypted_error = encrypt_for_client(sid, {'error': 'Secret not found or access denied'})
                emit('error', {'encrypted': encrypted_error})
            except Exception as e:
                current_app.logger.error(f"Could not encrypt error response: {str(e)}")
                emit('error', {'error': 'Secret not found or access denied'})
            return

        try:
            encrypted_response = encrypt_for_client(sid, secret)
            emit('secret', {'encrypted': encrypted_response})
        except Exception as e:
            current_app.logger.error(f"Could not encrypt secret response: {str(e)}")
            current_app.logger.warning(f"Sending unencrypted secret response for user {user_id}")
            emit('secret', secret)

    except Exception as e:
        current_app.logger.error(f"Error fetching secret: {str(e)}")
        try:
            encrypted_error = encrypt_for_client(sid, {'error': str(e)})
            emit('error', {'encrypted': encrypted_error})
        except Exception as encryption_error:
            current_app.logger.error(f"Could not encrypt error response: {str(encryption_error)}")
            emit('error', {'error': str(e)})


@socketio.on('share_secret')
def handle_share_secret(data):
    """
    Handles WebSocket requests to share a secret with other users.
    It decrypts sharing details, updates the secret's shared_with relationship,
    and emits the updated secret data to all relevant users.
    """
    sid = request.sid

    if sid not in client_sessions or 'user_id' not in client_sessions[sid]:
        emit('error', {'message': 'Authentication required'})
        return

    user_id = client_sessions[sid]['user_id']

    try:
        decrypted_data = decrypt_from_client(sid, data['encrypted'])
        secret_id = decrypted_data.get('secret_id')
        shared_with = decrypted_data.get('shared_with', [])

        if not secret_id or not shared_with:
            emit('error', {'message': 'Secret ID and shared_with are required'})
            return

        secret = Secret.query.filter_by(id=secret_id, user_id=user_id).first()
        if not secret:
            emit('error', {'message': 'Secret not found or unauthorized'})
            return

        users_to_share = User.query.filter(User.id.in_(shared_with)).all()

        secret.shared_with.extend(users_to_share)
        db.session.commit()

        secret_data = {
            'id': secret.id,
            'name': secret.name,
            'description': secret.description,
            'username': secret.username,
            'password': secret.password,
            'url': secret.url,
            'notes': secret.notes,
            'folder_id': secret.folder_id,
            'user_id': secret.user_id,
            'created_at': secret.created_at.isoformat(),
            'updated_at': secret.updated_at.isoformat() if secret.updated_at else None,
            'is_shared': True,
            'is_favorite': secret.is_favorite,
            'tags': [tag.name for tag in secret.tags],
            'shared_with': [{
                'id': user.id,
                'username': user.username
            } for user in secret.shared_with]
        }

        encrypted_response = encrypt_for_client(sid, {'secret': secret_data})

        emit('secret_shared', {'encrypted': encrypted_response}, room=sid)

        for user in users_to_share:
            for session_sid, session_data in client_sessions.items():
                if session_data.get('user_id') == user.id:
                    user_encrypted = encrypt_for_client(session_sid, {'secret': secret_data})
                    emit('secret_shared', {'encrypted': user_encrypted}, room=session_sid)

    except Exception as e:
        current_app.logger.error(f"Error sharing secret: {str(e)}")
        emit('error', {'message': 'Failed to share secret'})
