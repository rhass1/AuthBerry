#! /usr/bin/env python3


from flask import current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    get_jwt_identity, decode_token
)
from datetime import timedelta

from backend.models.user import User, Role, user_datastore
from backend.models.enums import UserRole
from backend.extensions import db
from flask_security import login_user, logout_user
from flask_security.utils import hash_password, verify_password


class AuthService:
    """
    Provides authentication-related services, including token management,
    user login, registration, and password updates.
    """

    @staticmethod
    def refresh_user_tokens(user_id):
        """
        Generates fresh access and refresh tokens for a given user ID.

        Args:
            user_id (int): The ID of the user for whom to generate tokens.

        Returns:
            tuple: A tuple containing the access_token and refresh_token,
                   or (None, None) if the user does not exist.
        """
        user = User.query.get(user_id)
        if not user:
            return None, None

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "role": user.role,
                "created_at": datetime.utcnow().isoformat()
            },
            expires_delta=timedelta(days=1)
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=7)
        )

        return access_token, refresh_token

    @staticmethod
    def get_current_user():
        """
        Retrieves the current authenticated user based on the JWT identity.

        Returns:
            User: The User object if authenticated, otherwise None.
        """
        user_id = get_jwt_identity()
        if not user_id:
            return None

        return User.query.get(user_id)

    @staticmethod
    def login_user(username, password):
        """
        Authenticates a user with the provided username and password.

        Args:
            username (str): The user's username.
            password (str): The user's plaintext password.

        Returns:
            tuple: A tuple containing (user, access_token, refresh_token) if authentication
                   is successful, otherwise (None, None, None).
        """
        user = User.query.filter_by(username=username).first()
        if not user:
            return None, None, None

        try:
            if not verify_password(password, user.password_hash):
                return None, None, None
        except Exception:
            return None, None, None

        access_token, refresh_token = AuthService.refresh_user_tokens(user.id)

        return user, access_token, refresh_token

    @staticmethod
    def setup_admin(username, password, first_name=None, last_name=None):
        """
        Sets up the initial admin user if no users currently exist in the database.

        Args:
            username (str): The desired username for the admin.
            password (str): The desired plaintext password for the admin.
            first_name (str, optional): The admin's first name. Defaults to None.
            last_name (str, optional): The admin's last name. Defaults to None.

        Returns:
            tuple: A tuple containing (User, None) if the admin is successfully created,
                   or (None, str) with an error message if setup fails or users already exist.
        """
        user_count = User.query.count()
        if user_count > 0:
            return None, "Setup already completed"

        try:
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(
                    name='admin',
                    description='Administrator with full access'
                )
                db.session.add(admin_role)

            user_role = Role.query.filter_by(name='user').first()
            if not user_role:
                user_role = Role(
                    name='user',
                    description='Regular user with limited access'
                )
                db.session.add(user_role)

            db.session.commit()

            password_hash = hash_password(password)
            admin_user = User(
                username=username,
                password_hash=password_hash,
                role=UserRole.ADMIN.value,
                first_name=first_name,
                last_name=last_name,
                active=True
            )

            db.session.add(admin_user)
            db.session.commit()

            user_datastore.add_role_to_user(admin_user, admin_role)
            db.session.commit()

            return admin_user, None
        except Exception as e:
            current_app.logger.error(f"Error creating admin user: {str(e)}")
            db.session.rollback()
            return None, f"Error creating admin user: {str(e)}"

    @staticmethod
    def login(username, password):
        """
        Logs in a user and returns their information along with a JWT access token.

        Args:
            username (str): The user's username.
            password (str): The user's plaintext password.

        Returns:
            tuple: A tuple containing (dict, None) with user data and access token on success,
                   or (None, str) with an error message on failure.
        """
        try:
            user = User.query.filter_by(username=username).first()

            if not user:
                return None, "Invalid username or password"

            if not verify_password(password, user.password_hash):
                current_app.logger.warning(f"Failed login attempt for {username}: password verification failed")
                return None, "Invalid username or password"

            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    'username': user.username,
                    'role': user.role,
                    'profile_photo': user.profile_photo
                }
            )

            login_user(user)

            return {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'display_name': user.display_name,
                    'profile_photo': user.profile_photo
                },
                'access_token': access_token
            }, None

        except Exception as e:
            current_app.logger.error(f"Error in login: {str(e)}")
            return None, f"Error during login: {str(e)}"

    @staticmethod
    def register(username, password, role=UserRole.USER.value, first_name=None, last_name=None):
        """
        Registers a new user with the provided details.

        Args:
            username (str): The desired username.
            password (str): The desired plaintext password.
            role (str, optional): The role for the new user. Defaults to UserRole.USER.value.
            first_name (str, optional): The user's first name. Defaults to None.
            last_name (str, optional): The user's last name. Defaults to None.

        Returns:
            tuple: A tuple containing (dict, None) with new user data and access token on success,
                   or (None, str) with an error message on failure.
        """
        try:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return None, "Username already exists"

            password_hash = hash_password(password)
            new_user = User(
                username=username,
                password_hash=password_hash,
                role=role,
                first_name=first_name,
                last_name=last_name,
                active=True
            )

            db.session.add(new_user)

            if role == UserRole.ADMIN.value:
                admin_role = Role.query.filter_by(name='admin').first()
                if admin_role:
                    user_datastore.add_role_to_user(new_user, admin_role)
            else:
                user_role = Role.query.filter_by(name='user').first()
                if user_role:
                    user_datastore.add_role_to_user(new_user, user_role)

            db.session.commit()

            login_user(new_user)

            access_token = create_access_token(
                identity=str(new_user.id),
                additional_claims={
                    'username': new_user.username,
                    'role': new_user.role,
                    'profile_photo': new_user.profile_photo
                }
            )

            return {
                'user': {
                    'id': new_user.id,
                    'username': new_user.username,
                    'role': new_user.role,
                    'display_name': new_user.display_name,
                    'profile_photo': new_user.profile_photo
                },
                'access_token': access_token
            }, None

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in register: {str(e)}")
            return None, f"Error during registration: {str(e)}"

    @staticmethod
    def logout():
        """
        Logs out the current user.

        Returns:
            tuple: A tuple containing (True, None) on successful logout,
                   or (False, str) with an error message on failure.
        """
        try:
            logout_user()
            return True, None
        except Exception as e:
            current_app.logger.error(f"Error in logout: {str(e)}")
            return False, f"Error during logout: {str(e)}"

    @staticmethod
    def update_password(user_id, current_password, new_password):
        """
        Updates a user's password.

        Args:
            user_id (int): The ID of the user whose password is to be updated.
            current_password (str): The user's current plaintext password.
            new_password (str): The user's new plaintext password.

        Returns:
            tuple: A tuple containing (True, None) on successful password update,
                   or (False, str) with an error message on failure.
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"

            if not verify_password(current_password, user.password_hash):
                current_app.logger.warning(
                    f"Password update failed for user {user.username}: incorrect current password")
                return False, "Current password is incorrect"

            user.password_hash = hash_password(new_password)
            db.session.commit()

            current_app.logger.info(f"Password updated successfully for user {user.username}")
            return True, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating password: {str(e)}")
            return False, f"Error updating password: {str(e)}"

    @staticmethod
    def validate_refresh_token(refresh_token):
        """
        Validates a refresh token and returns the user ID if the token is valid.

        Args:
            refresh_token (str): The refresh token to validate.

        Returns:
            int: The user ID if the token is valid, otherwise None.
        """
        try:
            decoded_token = decode_token(refresh_token)

            user_id = decoded_token.get('sub')

            if not user_id:
                current_app.logger.warning("Refresh token validation failed: no user ID in token")
                return None

            user = User.query.get(int(user_id))

            if not user:
                current_app.logger.warning(f"Refresh token validation failed: user ID {user_id} not found")
                return None

            return user_id

        except Exception as e:
            current_app.logger.error(f"Error validating refresh token: {str(e)}")
            return None
