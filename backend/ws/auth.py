#! /usr/bin/env python3


from flask import current_app, request
from flask_socketio import emit
from flask_jwt_extended import create_access_token, create_refresh_token
from backend.extensions import socketio
from backend.services.ws_service import decrypt_from_client, encrypt_for_client, client_sessions, has_shared_secret
from backend.services.auth_service import AuthService
from backend.models.user import User
from datetime import timedelta


@socketio.on('login')
def handle_login(data):
    """
    Handles WebSocket login events. It decrypts the incoming credentials,
    authenticates the user, and if successful, sends back encrypted user data and tokens.
    """
    sid = request.sid
    current_app.logger.info(f"Login request received from {sid}")

    if not has_shared_secret(sid):
        current_app.logger.error(f"Login failed: No shared secret for client {sid}")
        emit('login_error', {'message': 'Secure channel not established'})
        return

    try:
        if not data.get('encrypted'):
            current_app.logger.error(f"Login failed: No encrypted data received from {sid}")
            emit('login_error', {'message': 'Missing encrypted data'})
            return

        try:
            decrypted_data = decrypt_from_client(sid, data['encrypted'])
        except Exception as decrypt_error:
            current_app.logger.error(f"Login failed: Could not decrypt data from {sid}: {str(decrypt_error)}")
            emit('login_error', {'message': 'Failed to decrypt login data'})
            return

        username = decrypted_data.get('username')
        password = decrypted_data.get('password')

        if not username or not password:
            current_app.logger.error(f"Login failed: Missing credentials for {sid}")

            try:
                encrypted_error = encrypt_for_client(sid, {'error': 'Missing credentials'})
                emit('login_error', {'encrypted': encrypted_error})
            except Exception as e:
                current_app.logger.error(f"Could not encrypt error response: {str(e)}")
                emit('login_error', {'error': 'Missing credentials'})
            return

        current_app.logger.info(f"Attempting to authenticate user {username}")
        result, error = AuthService.login(username, password)

        if error:
            current_app.logger.warning(f"Login failed for {username}: {error}")

            try:
                encrypted_error = encrypt_for_client(sid, {'error': error})
                emit('login_error', {'encrypted': encrypted_error})
            except Exception as e:
                current_app.logger.error(f"Could not encrypt error response: {str(e)}")
                emit('login_error', {'error': error})
            return

        client_sessions[sid]['user_id'] = result['user']['id']
        client_sessions[sid]['username'] = result['user']['username']

        access_token = result['access_token']
        refresh_token = create_refresh_token(
            identity=result['user']['id'],
            expires_delta=timedelta(days=7)
        )

        user_data = {
            'user': result['user'],
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }

        current_app.logger.info(f"Login successful for {username} from {sid}")

        try:
            encrypted_response = encrypt_for_client(sid, user_data)
            emit('login_success', {'encrypted': encrypted_response})
        except Exception as e:
            current_app.logger.error(f"Could not encrypt login response: {str(e)}")
            current_app.logger.warning(f"Sending unencrypted login response for {username}")
            emit('login_success', user_data)

    except Exception as e:
        current_app.logger.error(f"Error during login: {str(e)}")
        emit('login_error', {'error': f'Login failed: {str(e)}'})


@socketio.on('register')
def handle_register(data):
    """
    Handles WebSocket registration events. It decrypts user registration details,
    registers the new user, and if successful, sends back encrypted user data and tokens.
    """
    sid = request.sid
    current_app.logger.info(f"Registration request received from {sid}")

    if not has_shared_secret(sid):
        current_app.logger.error(f"Registration failed: No shared secret for client {sid}")
        emit('register_error', {'message': 'Secure channel not established'})
        return

    try:
        if not data.get('encrypted'):
            current_app.logger.error(f"Registration failed: No encrypted data received from {sid}")
            emit('register_error', {'message': 'Missing encrypted data'})
            return

        try:
            decrypted_data = decrypt_from_client(sid, data['encrypted'])
        except Exception as decrypt_error:
            current_app.logger.error(f"Registration failed: Could not decrypt data from {sid}: {str(decrypt_error)}")
            emit('register_error', {'message': 'Failed to decrypt registration data'})
            return

        username = decrypted_data.get('username')
        password = decrypted_data.get('password')
        role = decrypted_data.get('role', 'user')
        first_name = decrypted_data.get('first_name')
        last_name = decrypted_data.get('last_name')

        if not username or not password:
            current_app.logger.error(f"Registration failed: Missing credentials for {sid}")

            try:
                encrypted_error = encrypt_for_client(sid, {'error': 'Missing required fields'})
                emit('register_error', {'encrypted': encrypted_error})
            except Exception as e:
                current_app.logger.error(f"Could not encrypt error response: {str(e)}")
                emit('register_error', {'error': 'Missing required fields'})
            return

        current_app.logger.info(f"Attempting to register user {username}")
        result, error = AuthService.register(
            username=username,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name
        )

        if error:
            current_app.logger.warning(f"Registration failed for {username}: {error}")

            try:
                encrypted_error = encrypt_for_client(sid, {'error': error})
                emit('register_error', {'encrypted': encrypted_error})
            except Exception as e:
                current_app.logger.error(f"Could not encrypt error response: {str(e)}")
                emit('register_error', {'error': error})
            return

        access_token = result['access_token']
        refresh_token = create_refresh_token(
            identity=result['user']['id'],
            expires_delta=timedelta(days=7)
        )

        client_sessions[sid]['user_id'] = result['user']['id']
        client_sessions[sid]['username'] = result['user']['username']

        user_data = {
            'user': result['user'],
            'tokens': {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }

        current_app.logger.info(f"Registration successful for {username} from {sid}")

        try:
            encrypted_response = encrypt_for_client(sid, user_data)
            emit('register_success', {'encrypted': encrypted_response})
        except Exception as e:
            current_app.logger.error(f"Could not encrypt registration response: {str(e)}")
            current_app.logger.warning(f"Sending unencrypted registration response for {username}")
            emit('register_success', user_data)

    except Exception as e:
        current_app.logger.error(f"Error during registration: {str(e)}")
        emit('register_error', {'error': f'Registration failed: {str(e)}'})


@socketio.on('refresh_token')
def handle_refresh_token(data):
    """
    Handles WebSocket token refresh requests. It decrypts the refresh token,
    validates it, generates a new access token, and sends it back encrypted.
    """
    sid = request.sid

    if sid not in client_sessions or 'shared_secret' not in client_sessions[sid]:
        emit('error', {'message': 'Secure connection not established'})
        return

    try:
        decrypted_data = decrypt_from_client(sid, data['encrypted'])
        refresh_token = decrypted_data.get('refresh_token')

        if not refresh_token:
            encrypted_response = encrypt_for_client(sid, {'error': 'Refresh token is required'})
            emit('refresh_error', {'encrypted': encrypted_response})
            return

        user_id = AuthService.validate_refresh_token(refresh_token)

        if not user_id:
            encrypted_response = encrypt_for_client(sid, {'error': 'Invalid or expired refresh token'})
            emit('refresh_error', {'encrypted': encrypted_response})
            return

        user = User.query.get(int(user_id))

        if not user:
            encrypted_response = encrypt_for_client(sid, {'error': 'User not found'})
            emit('refresh_error', {'encrypted': encrypted_response})
            return

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'username': user.username,
                'role': user.role
            }
        )

        encrypted_response = encrypt_for_client(sid, {
            'access_token': access_token
        })

        emit('refresh_success', {'encrypted': encrypted_response})

    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        emit('refresh_error', {'message': 'Token refresh failed'})
