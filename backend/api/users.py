#! /usr/bin/env python3


from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from backend.models.user import User, Role, user_datastore
from backend.models.enums import UserRole
from backend.extensions import db
from functools import wraps

users_bp = Blueprint('users', __name__)


def admin_required(fn):
    """Decorator to require admin role for endpoints."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        try:
            claims = get_jwt()
            current_app.logger.debug(f"JWT claims: {claims}")

            role = claims.get('role')
            if role != UserRole.ADMIN.value:
                current_app.logger.warning(f"Non-admin role attempted admin action: {role}")
                return jsonify({"msg": "Admin privileges required"}), 403

            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                current_app.logger.warning(f"User not found for ID: {user_id}")
                return jsonify({"msg": "User not found"}), 404

            if user.role != UserRole.ADMIN.value:
                current_app.logger.warning(f"User {user.username} has role {user.role} but JWT claims admin")
                return jsonify({"msg": "Admin privileges required"}), 403

            current_app.logger.info(f"Admin user {user.username} accessed admin endpoint")
            return fn(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"Error in admin_required decorator: {str(e)}")
            return jsonify({"msg": "Authentication error", "error": str(e)}), 401

    return wrapper


@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """Retrieves a list of all users."""
    try:
        users = User.query.all()
        return jsonify({
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role
                } for user in users
            ]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"msg": "Failed to fetch users"}), 500


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Retrieves a specific user's details by ID."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if int(current_user_id) != user_id and (not current_user or current_user.role != UserRole.ADMIN.value):
        return jsonify({"msg": "Unauthorized access"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_photo": user.profile_photo,
            "display_name": user.display_name,
            "created_time": user.created_time.isoformat(),
            "last_modified": user.last_modified.isoformat()
        }
    }), 200


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Updates a user's information. Accessible by the user themselves or an admin."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if int(current_user_id) != user_id and (not current_user or current_user.role != UserRole.ADMIN.value):
        return jsonify({"msg": "Unauthorized access"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()

    if 'role' in data and (not current_user or current_user.role != UserRole.ADMIN.value):
        return jsonify({"msg": "Cannot update role: insufficient permissions"}), 403

    if 'username' in data:
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({"msg": "Username already exists"}), 409
        user.username = data['username']

    if 'first_name' in data:
        user.first_name = data['first_name']

    if 'last_name' in data:
        user.last_name = data['last_name']

    if 'role' in data and current_user and current_user.role == UserRole.ADMIN.value:
        old_role = user.role
        new_role = data['role']

        if old_role != new_role:
            user.role = new_role

            if new_role == UserRole.ADMIN.value:
                admin_role = Role.query.filter_by(name='admin').first()
                if admin_role:
                    user_datastore.add_role_to_user(user, admin_role)
            elif new_role == UserRole.USER.value:
                admin_role = Role.query.filter_by(name='admin').first()
                if admin_role:
                    user_datastore.remove_role_from_user(user, admin_role)

                user_role = Role.query.filter_by(name='user').first()
                if user_role:
                    user_datastore.add_role_to_user(user, user_role)

    db.session.commit()

    return jsonify({
        "msg": "User updated successfully",
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "display_name": user.display_name,
            "profile_photo": user.profile_photo
        }
    }), 200


@users_bp.route('/profile-photo', methods=['POST'])
@jwt_required(optional=True)
def upload_profile_photo():
    """Uploads a profile photo for the current user."""
    auth_header = request.headers.get('Authorization')
    current_app.logger.info(f"Request headers: {dict(request.headers)}")
    current_app.logger.info(f"Auth header received: {auth_header[:20]}..." if auth_header else "No auth header")

    user_id = None
    token = None

    user_id = get_jwt_identity()
    current_app.logger.info(f"JWT identity (standard method): {user_id}")

    if not user_id and auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        current_app.logger.info(f"Extracted token: {token[:20]}...")
        try:
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            user_id = decoded['sub']
            current_app.logger.info(f"Manually decoded JWT, found user_id: {user_id}")
        except Exception as e:
            current_app.logger.error(f"Error manually decoding token: {str(e)}")

    current_app.logger.info(f"Final JWT identity: {user_id}")

    if not user_id:
        current_app.logger.warning("No JWT identity found in token")
        admin_count = User.query.filter_by(role=UserRole.ADMIN.value).count()
        user_count = User.query.count()
        current_app.logger.info(f"Database has {admin_count} admins and {user_count} total users")

        if user_count <= 1:
            user = User.query.first()
            if user:
                current_app.logger.info(f"Allowing profile photo upload for user during setup: {user.username}")
            else:
                return jsonify({"msg": "No users exist in database"}), 404
        else:
            return jsonify({
                "msg": "Authentication required",
                "error_details": {
                    "auth_header": bool(auth_header),
                    "admin_count": admin_count,
                    "user_count": user_count,
                    "auth_header_preview": auth_header[:20] + "..." if auth_header else None
                }
            }), 401
    else:
        user = User.query.get(user_id)
        if not user:
            current_app.logger.warning(f"User with ID {user_id} not found in database")
            return jsonify({"msg": "User not found"}), 404

        current_app.logger.info(f"Using JWT-authenticated user: {user.username}")

    if 'photo' not in request.files:
        return jsonify({"msg": "No photo file provided", "received_keys": list(request.files.keys())}), 400

    photo_file = request.files['photo']
    current_app.logger.info(f"Received file: {photo_file.filename}, type: {photo_file.content_type}")

    if photo_file.filename == '':
        return jsonify({"msg": "No photo file selected"}), 400

    is_valid_image = False
    if (photo_file.content_type.startswith('image/jpeg') or
            photo_file.content_type.startswith('image/png') or
            photo_file.content_type.startswith('image/')):
        is_valid_image = True

    if not is_valid_image:
        return jsonify({
            "msg": "File must be an image",
            "provided_type": photo_file.content_type
        }), 400

    try:
        file_data = photo_file.read()
        current_app.logger.info(f"Read {len(file_data)} bytes from uploaded file")

        user.set_profile_photo(file_data)
        db.session.commit()

        return jsonify({
            "msg": "Profile photo uploaded successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "display_name": user.display_name,
                "profile_photo": user.profile_photo
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error uploading profile photo: {str(e)}")
        return jsonify({"msg": "Failed to upload profile photo", "error": str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Deletes a user. Only accessible by an admin."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or current_user.role != UserRole.ADMIN.value:
        return jsonify({"msg": "Unauthorized access"}), 403

    if int(current_user_id) == user_id:
        return jsonify({"msg": "Cannot delete yourself"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user_datastore.delete_user(user)
    db.session.commit()

    return jsonify({"msg": "User deleted successfully"}), 200


@users_bp.route('/check-admin', methods=['GET'])
@jwt_required()
def check_admin():
    """Checks if the current authenticated user has administrative privileges."""
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()

        user = User.query.get(user_id)

        if not user:
            current_app.logger.warning(f"User not found for ID: {user_id}")
            return jsonify({
                "is_admin": False,
                "error": "User not found",
                "user_id": user_id
            }), 200

        is_admin = user.role == UserRole.ADMIN.value

        claim_role = claims.get('role')
        if claim_role != user.role:
            current_app.logger.warning(f"JWT role claim mismatch: {claim_role} vs DB: {user.role}")

        return jsonify({
            "is_admin": is_admin,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            },
            "jwt_claims": {
                "role": claims.get('role'),
                "username": claims.get('username')
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in admin check: {str(e)}")
        return jsonify({
            "is_admin": False,
            "error": str(e)
        }), 200


@users_bp.route('/auth-test', methods=['GET'])
@jwt_required(optional=True)
def auth_test():
    """Provides authentication details for debugging purposes."""
    auth_header = request.headers.get('Authorization')
    user_id = get_jwt_identity()

    if user_id:
        user = User.query.get(user_id)
        user_info = {
            "id": user.id,
            "username": user.username,
            "role": user.role
        } if user else "User not found in database"
    else:
        user_info = None

    return jsonify({
        "authenticated": user_id is not None,
        "user_id": user_id,
        "auth_header_present": auth_header is not None,
        "auth_header_preview": auth_header[:20] + "..." if auth_header else None,
        "user_info": user_info,
        "request_headers": dict(request.headers)
    }), 200
