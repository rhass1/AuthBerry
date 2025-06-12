#! /usr/bin/env python3

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt,
    verify_jwt_in_request
)
from flask_security import login_user, logout_user
from flask_security.utils import verify_password
from functools import wraps
from datetime import datetime

from backend.models.user import User
from backend.models.system import SystemSetting
from backend.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

def secure_setup_only(view_function):
    """
    Decorator to ensure setup is only allowed if no users exist.
    """
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if User.query.count() > 0:
            return jsonify({"msg": "Setup not allowed - users already exist"}), 403
        return view_function(*args, **kwargs)
    return decorated_function

def admin_required(view_function):
    """
    Decorator to ensure only admins can access the admin view.
    """
    @wraps(view_function)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()

        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                return jsonify({"msg": "Invalid user ID format"}), 400

        user = User.query.get(user_id)

        if not user or user.role != 'admin':
            return jsonify({"msg": "Admin access required"}), 403

        return view_function(*args, **kwargs)

    return decorated_function

@auth_bp.route('/check-users-exist', methods=['GET'])
def check_users_exist():
    try:
        users_exist = User.query.count() > 0
        
        response = jsonify({"users_exist": users_exist})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response, 200
    except Exception as e:
        current_app.logger.error(f"Error checking users exist: {str(e)}")
        return jsonify({"users_exist": False, "error": "Database error"}), 500

@auth_bp.route('/setup', methods=['POST'])
@secure_setup_only
def setup_admin():
    """
    Setup the admin user.
    """
    data = request.get_json()

    if not data:
        return jsonify({"msg": "No data provided"}), 400

    required_fields = ['username', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "Missing required fields: username, password"}), 400

    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')

    admin_user, error = AuthService.setup_admin(username, password, first_name, last_name)

    if error:
        current_app.logger.error(f"Admin setup failed: {error}")
        return jsonify({"msg": error}), 400

    access_token = create_access_token(
        identity=str(admin_user.id),
        additional_claims={
            'username': admin_user.username,
            'role': admin_user.role
        }
    )
    refresh_token = create_refresh_token(identity=str(admin_user.id))

    login_user(admin_user)

    current_app.logger.info(f"Admin user {username} created successfully")

    profile_photo_url = None
    if admin_user.profile_photo:
        profile_photo_url = f"/api/users/{admin_user.id}/profile-photo"

    return jsonify({
        "success": True,
        "msg": "Admin user created successfully",
        "user": {
            "id": admin_user.id,
            "username": admin_user.username,
            "role": admin_user.role,
            "first_name": admin_user.first_name,
            "last_name": admin_user.last_name,
            "display_name": admin_user.display_name,
            "profile_photo_url": profile_photo_url
        },
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }), 201

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    """
    registration_enabled = SystemSetting.get_setting('registration_enabled', True)

    if not registration_enabled:
        return jsonify({"msg": "User registration is currently disabled"}), 403

    data = request.get_json()

    if not data:
        return jsonify({"msg": "No data provided"}), 400

    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400

    result, error = AuthService.register(username, password, role, first_name, last_name)

    if error:
        current_app.logger.warning(f"Registration failed for user {username}: {error}")
        return jsonify({"msg": error}), 400

    current_app.logger.info(f"User {username} registered successfully")
    return jsonify(result), 201

@auth_bp.route('/registration-status', methods=['GET'])
def get_registration_status():
    """
    Get the registration status (controlled by the admin and can be enabled/disabled).
    """
    registration_enabled = SystemSetting.get_setting('registration_enabled', True)
    return jsonify({"enabled": registration_enabled}), 200

@auth_bp.route('/toggle-registration', methods=['POST'])
@admin_required
def toggle_registration():
    data = request.get_json()
    if not data or 'enabled' not in data:
        return jsonify({"msg": "Missing 'enabled' parameter"}), 400

    enabled = data['enabled']

    if not isinstance(enabled, bool):
        return jsonify({"msg": "'enabled' must be a boolean value"}), 400

    SystemSetting.set_setting('registration_enabled', enabled, 'boolean')

    current_app.logger.info(f"User registration {'enabled' if enabled else 'disabled'} by admin")

    return jsonify({
        "success": True,
        "enabled": enabled,
        "msg": f"User registration {'enabled' if enabled else 'disabled'}"
    }), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login a user.
    """
    data = request.get_json()

    if not data:
        return jsonify({"msg": "No data provided"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Username and password are required"}), 400

    result, error = AuthService.login(username, password)

    if error:
        current_app.logger.warning(f"Login failed for user {username}: {error}")
        return jsonify({"msg": error}), 401

    current_app.logger.info(f"User {username} logged in successfully")

    if 'access_token' in result and 'user' in result:
        formatted_result = {
            'user': result['user'],
            'tokens': {
                'access_token': result['access_token']
            }
        }
        return jsonify(formatted_result), 200

    return jsonify(result), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout a user.
    """
    user_id = get_jwt_identity()
    if isinstance(user_id, str):
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"msg": "Invalid user ID format"}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    success, error = AuthService.logout()

    if error:
        current_app.logger.warning(f"Logout failed for user {user.username}: {error}")
        return jsonify({"msg": error}), 500

    current_app.logger.info(f"User {user.username} logged out successfully")
    return jsonify({"msg": "Logged out successfully"}), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh a user's token.
    """
    try:
        data = request.get_json()
        if not data or 'refresh_token' not in data:
            try:
                verify_jwt_in_request(refresh=True)
                user_id = get_jwt_identity()
            except Exception as e:
                current_app.logger.error(f"JWT verification failed in refresh: {str(e)}")
                return jsonify({"msg": "Invalid refresh token"}), 401
        else:
            refresh_token = data.get('refresh_token')
            try:
                from flask_jwt_extended import decode_token
                decoded = decode_token(refresh_token)

                if decoded.get('type') != 'refresh':
                    current_app.logger.error(f"Token is not a refresh token: {decoded.get('type')}")
                    return jsonify({"msg": "Token is not a refresh token"}), 401

                user_id = decoded.get('sub')
                current_app.logger.info(f"Successfully decoded refresh token for user ID: {user_id}")
            except Exception as e:
                current_app.logger.error(f"Manual refresh token validation failed: {str(e)}")
                return jsonify({"msg": "Invalid refresh token format", "error": str(e)}), 401

        if isinstance(user_id, str):
            try:
                user_id = int(user_id)
            except ValueError:
                current_app.logger.error(f"Invalid user ID format in refresh token: {user_id}")
                return jsonify({"msg": "Invalid user ID format"}), 400

        user = User.query.get(user_id)

        if not user:
            return jsonify({"msg": "User not found"}), 404

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'username': user.username,
                'role': user.role
            }
        )

        current_app.logger.info(f"Refreshed token for user {user.username}")

        return jsonify({
            "access_token": access_token
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in refresh token: {str(e)}")
        return jsonify({"msg": "Token refresh failed", "error": str(e)}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    try:
        auth_header = request.headers.get('Authorization')
        current_app.logger.info(f"ME endpoint - Auth header received: {auth_header[:30]}..." if auth_header else "No auth header")

        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            current_app.logger.info(f"ME endpoint - JWT identity verified: {identity}")
        except Exception as jwt_err:
            current_app.logger.error(f"ME endpoint - JWT verification failed: {str(jwt_err)}")
            return jsonify({"msg": "Invalid token", "error": str(jwt_err)}), 401

        if isinstance(identity, str):
            try:
                identity = int(identity)
            except ValueError:
                current_app.logger.error(f"ME endpoint - Invalid user ID format: {identity}")
                return jsonify({"msg": "Invalid user ID format"}), 400

        try:
            claims = get_jwt()
            current_app.logger.info(f"ME endpoint - JWT claims: {claims}")
        except Exception as claims_err:
            current_app.logger.error(f"ME endpoint - Error getting claims: {str(claims_err)}")

        user = User.query.get(identity)

        if not user:
            current_app.logger.warning(f"JWT contained identity {identity} but no matching user found in database")
            return jsonify({"msg": "User not found"}), 404

        current_app.logger.info(f"User {user.username} (ID: {user.id}) authenticated successfully")

        profile_photo_url = None
        if user.profile_photo:
            profile_photo_url = f"/api/users/{user.id}/profile-photo"

        return jsonify({
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_photo_url": profile_photo_url,
                "display_name": user.display_name,
                "created_time": user.created_time.isoformat() if user.created_time else None
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in /me endpoint: {str(e)}")
        return jsonify({
            "msg": "Authentication error",
            "error": str(e),
            "auth_header_present": request.headers.get('Authorization') is not None
        }), 401

@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """
    Get the authentication status of the current user.
    """
    user_data = None
    is_authenticated = False
    errors = []

    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()

        if identity:
            if isinstance(identity, str):
                try:
                    identity = int(identity)
                except ValueError:
                    errors.append("Invalid user ID format")
                    return jsonify({
                        "isAuthenticated": False,
                        "user": None,
                        "errors": errors if current_app.debug else []
                    }), 200

            user = User.query.get(identity)
            if user:
                is_authenticated = True
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role
                }

    except Exception as e:
        if current_app.debug:
            errors.append(str(e))

    return jsonify({
        "isAuthenticated": is_authenticated,
        "user": user_data,
        "errors": errors if errors and current_app.debug else []
    }), 200

@auth_bp.route('/token-login', methods=['POST'])
def token_login():
    """
    Login a user using a token.
    """
    data = request.get_json()

    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({"msg": "Missing required fields"}), 400

    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "Invalid username or password"}), 401

    if not verify_password(password, user.password_hash):
        current_app.logger.warning(f"Failed login attempt for user {username}: password verification failed")
        return jsonify({"msg": "Invalid username or password"}), 401

    login_user(user)

    additional_claims = {
        "username": user.username,
        "role": user.role,
        "timestamp": datetime.now().isoformat()
    }

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name,
            "profile_photo": user.profile_photo
        },
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }), 200

@auth_bp.route('/auth-test', methods=['GET'])
def auth_test():
    """
    Test the authentication status of the current user.
    """
    headers = {k: v for k, v in request.headers.items()}
    cookies = {k: v for k, v in request.cookies.items()}

    auth_header = headers.get('Authorization', '')
    has_bearer_token = auth_header.startswith('Bearer ')

    access_token_cookie = cookies.get('access_token_cookie')
    has_jwt_cookie = bool(access_token_cookie)

    auth_status = {
        "has_bearer_token": has_bearer_token,
        "has_jwt_cookie": has_jwt_cookie,
        "bearer_token_verified": False,
        "jwt_cookie_verified": False,
        "user_info": None
    }

    if has_bearer_token:
        try:
            from flask_jwt_extended import decode_token
            token = auth_header[7:]
            decoded = decode_token(token)
            user_id = decoded.get('sub')

            if isinstance(user_id, str):
                try:
                    user_id = int(user_id)
                except ValueError:
                    current_app.logger.error(f"Invalid user ID format in token: {user_id}")
                    auth_status["bearer_token_error"] = "Invalid user ID format"

            user = User.query.get(user_id) if user_id is not None else None

            if user:
                auth_status["bearer_token_verified"] = True
                auth_status["user_info"] = {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role
                }
                current_app.logger.info(f"Bearer token verified for user {user.username}")
        except Exception as e:
            current_app.logger.error(f"Bearer token verification failed: {str(e)}")
            auth_status["bearer_token_error"] = str(e)

    if not auth_status["bearer_token_verified"] and has_jwt_cookie:
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()

            if isinstance(user_id, str) and user_id:
                try:
                    user_id = int(user_id)
                except ValueError:
                    current_app.logger.error(f"Invalid user ID format in cookie: {user_id}")
                    auth_status["jwt_cookie_error"] = "Invalid user ID format"

            if user_id:
                user = User.query.get(user_id)
                if user:
                    auth_status["jwt_cookie_verified"] = True
                    if not auth_status["user_info"]:
                        auth_status["user_info"] = {
                            "id": user.id,
                            "username": user.username,
                            "role": user.role
                        }
                    current_app.logger.info(f"JWT cookie verified for user {user.username}")
        except Exception as e:
            current_app.logger.error(f"JWT cookie verification failed: {str(e)}")
            auth_status["jwt_cookie_error"] = str(e)

    auth_status["jwt_config"] = {
        "JWT_TOKEN_LOCATION": current_app.config.get('JWT_TOKEN_LOCATION', []),
        "JWT_HEADER_NAME": current_app.config.get('JWT_HEADER_NAME', ''),
        "JWT_HEADER_TYPE": current_app.config.get('JWT_HEADER_TYPE', ''),
        "JWT_COOKIE_CSRF_PROTECT": current_app.config.get('JWT_COOKIE_CSRF_PROTECT', '')
    }

    return jsonify({
        "auth_status": auth_status,
        "headers": headers,
        "cookies": cookies
    }), 200

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """
    Verify a token.
    """
    if not current_app.debug:
        return jsonify({"msg": "Only available in debug mode"}), 403

    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({"msg": "Token required"}), 400

    token = data['token']

    try:
        from flask_jwt_extended import decode_token
        import jwt
        try:
            unverified_payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            current_app.logger.debug(f"Unverified payload: {unverified_payload}")
        except Exception as unverified_err:
            current_app.logger.error(f"Cannot decode token even without verification: {str(unverified_err)}")

        decoded = decode_token(token)

        user_id = decoded.get('sub')
        user = User.query.get(user_id)

        return jsonify({
            "valid": True,
            "decoded": {
                "id": decoded.get('sub'),
                "exp": decoded.get('exp'),
                "iat": decoded.get('iat'),
                "type": decoded.get('type'),
                "role": decoded.get('role', 'not set')
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            } if user else None,
            "debug_info": {
                "jwt_secret_key_length": len(current_app.config.get('JWT_SECRET_KEY', '')),
                "jwt_token_location": current_app.config.get('JWT_TOKEN_LOCATION', []),
                "jwt_header_name": current_app.config.get('JWT_HEADER_NAME', ''),
                "jwt_header_type": current_app.config.get('JWT_HEADER_TYPE', '')
            }
        }), 200
    except Exception as e:
        return jsonify({
            "valid": False,
            "error": str(e),
            "debug_info": {
                "jwt_secret_key_length": len(current_app.config.get('JWT_SECRET_KEY', '')),
                "jwt_token_location": current_app.config.get('JWT_TOKEN_LOCATION', []),
                "jwt_header_name": current_app.config.get('JWT_HEADER_NAME', ''),
                "jwt_header_type": current_app.config.get('JWT_HEADER_TYPE', '')
            }
        }), 200

@auth_bp.route('/get-current-user', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get the current user's information.
    """
    user_id = get_jwt_identity()

    if isinstance(user_id, str):
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"msg": "Invalid user ID format"}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    profile_photo_url = None
    if user.profile_photo:
        profile_photo_url = f"/api/users/{user.id}/profile-photo"

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name,
            "profile_photo_url": profile_photo_url,
            "created_time": user.created_time.isoformat() if user.created_time else None
        }
    }), 200

@auth_bp.route('/update-password', methods=['PUT'])
@jwt_required()
def update_password():
    """
    Update the current user's password.
    """
    user_id = get_jwt_identity()

    if isinstance(user_id, str):
        try:
            user_id = int(user_id)
        except ValueError:
            return jsonify({"msg": "Invalid user ID format"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"msg": "No data provided"}), 400

    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({"msg": "Current password and new password are required"}), 400

    if len(new_password) < 8:
        return jsonify({"msg": "New password must be at least 8 characters long"}), 400

    success, error = AuthService.update_password(user_id, current_password, new_password)

    if not success:
        current_app.logger.warning(f"Password update failed for user ID {user_id}: {error}")
        return jsonify({"msg": error}), 401 if "incorrect" in error.lower() else 400

    return jsonify({"msg": "Password updated successfully"}), 200

@auth_bp.route('/check-username-exists', methods=['GET'])
def check_username_exists():
    """
    Check if a username exists.
    """
    username = request.args.get('username')

    if not username:
        return jsonify({"msg": "Username parameter is required"}), 400

    existing_user = User.query.filter_by(username=username).first()

    return jsonify({"exists": existing_user is not None}), 200