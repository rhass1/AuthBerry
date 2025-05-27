#! /usr/bin/env python3


from flask import current_app
from flask_socketio import emit, join_room, disconnect
from flask import request
from flask_jwt_extended import decode_token
from functools import wraps
from backend.extensions import socketio
from backend.utils.crypto import CryptoService
from backend.models.user import User

client_sessions = {}


def authenticated_only(f):
    """Decorator that checks if a WebSocket connection is authenticated."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not hasattr(f, 'sid') or f.sid not in client_sessions or 'user_id' not in client_sessions[f.sid]:
            return disconnect()
        return f(*args, **kwargs)

    return wrapped


@socketio.on('connect')
def handle_connect():
    """Handles new client WebSocket connections."""
    sid = request.sid
    current_app.logger.info(f"Client connected: {sid}")


@socketio.on('disconnect')
def handle_disconnect():
    """Handles client WebSocket disconnections."""
    sid = request.sid
    current_app.logger.info(f"Client disconnected: {sid}")

    if sid in client_sessions:
        user_id = client_sessions[sid].get('user_id')
        username = client_sessions[sid].get('username')
        current_app.logger.info(f"Cleaning up session for user {username} (ID: {user_id})")

        del client_sessions[sid]


@socketio.on('initiate_key_exchange')
def handle_key_exchange():
    """Initiates a Diffie-Hellman key exchange with the client."""
    sid = request.sid

    keypair = CryptoService.generate_keypair()

    if sid not in client_sessions:
        client_sessions[sid] = {}

    client_sessions[sid]['private_key'] = keypair['private_key']
    client_sessions[sid]['public_key'] = keypair['public_key']

    emit('server_public_key', {'public_key': keypair['public_key']})


@socketio.on('client_public_key')
def handle_client_public_key(data):
    """Receives the client's public key and completes the key exchange."""
    sid = request.sid

    if sid not in client_sessions:
        emit('error', {'message': 'Session not initialized'})
        return

    if 'public_key' not in data:
        emit('error', {'message': 'Missing client public key'})
        return

    client_public_key = data['public_key']
    client_sessions[sid]['client_public_key'] = client_public_key

    server_private_key = client_sessions[sid]['private_key']
    shared_secret = CryptoService.compute_shared_secret(
        server_private_key,
        client_public_key
    )

    client_sessions[sid]['shared_secret'] = shared_secret

    emit('key_exchange_complete')


@socketio.on('authenticate')
def handle_authenticate(data):
    """Authenticates the user with a provided JWT token."""
    sid = request.sid

    if 'token' not in data:
        emit('auth_error', {'message': 'Missing authentication token'})
        return

    token = data['token']

    try:
        decoded_token = decode_token(token)
        user_id = decoded_token['sub']

        user = User.query.get(int(user_id))

        if not user:
            emit('auth_error', {'message': 'User not found'})
            return

        if sid not in client_sessions:
            client_sessions[sid] = {}

        client_sessions[sid]['user_id'] = user.id
        client_sessions[sid]['username'] = user.username
        client_sessions[sid]['role'] = user.role

        if 'shared_secret' not in client_sessions[sid]:
            emit('auth_error', {'message': 'Key exchange not completed'})
            return

        join_room(f"user_{user.id}")

        emit('authenticated', {'user_id': user.id, 'username': user.username})

    except Exception as e:
        current_app.logger.error(f"Authentication error: {str(e)}")
        emit('auth_error', {'message': 'Invalid or expired token'})


def encrypt_for_client(sid, data):
    """
    Encrypts data for a specific client using their established shared secret.

    Args:
        sid (str): The session ID of the client.
        data (dict): The data to encrypt.

    Returns:
        str: The encrypted data, or None if the shared secret is not established.
    """
    if sid not in client_sessions or 'shared_secret' not in client_sessions[sid]:
        return None

    shared_secret = client_sessions[sid]['shared_secret']
    return CryptoService.encrypt(data, shared_secret)


def decrypt_from_client(sid, encrypted_data):
    """
    Decrypts data received from a specific client using their established shared secret.

    Args:
        sid (str): The session ID of the client.
        encrypted_data (str): The encrypted data to decrypt.

    Returns:
        dict: The decrypted data, or None if the shared secret is not established or decryption fails.
    """
    if sid not in client_sessions or 'shared_secret' not in client_sessions[sid]:
        return None

    shared_secret = client_sessions[sid]['shared_secret']
    return CryptoService.decrypt(encrypted_data, shared_secret)


def has_shared_secret(sid):
    """
    Checks if a client has an established shared secret.

    Args:
        sid (str): The session ID of the client.

    Returns:
        bool: True if a shared secret is established, False otherwise.
    """
    return sid in client_sessions and 'shared_secret' in client_sessions[sid]


def init_ws_service(app):
    """
    Initializes the WebSocket service by registering event handlers.

    Args:
        app (Flask): The Flask application instance.
    """
    try:
        from backend.ws import auth, secrets, folders

        with app.app_context():
            current_app.logger.info("Initializing WebSocket Service")
    except ImportError as e:
        with app.app_context():
            current_app.logger.error(f"Error importing WebSocket modules: {str(e)}")
            current_app.logger.warning("WebSocket service partially initialized")
