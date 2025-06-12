#! /usr/bin/env python3


from backend.models.secret import Secret
from backend.models.user import User
from backend.extensions import db
from sqlalchemy.exc import SQLAlchemyError
import uuid
import logging

logger = logging.getLogger(__name__)


class SecretsService:
    """Service class for handling secret operations."""

    @staticmethod
    def get_secrets_for_user(user_id):
        """
        Retrieves all secrets accessible to a user, including those they own and those shared with them.

        Args:
            user_id (str): The ID of the user.

        Returns:
            list: A list of secret objects accessible to the user.
        """
        try:
            user_secrets = Secret.query.filter_by(owner_id=user_id).all()

            shared_secrets = Secret.query.join(Secret.shared_with).filter(User.id == user_id).all()

            all_secrets = list(set(user_secrets + shared_secrets))

            for secret in all_secrets:
                secret.has_direct_access = secret.owner_id == user_id

            return all_secrets
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching secrets for user {user_id}: {str(e)}")
            return []

    @staticmethod
    def get_secret_by_id(secret_id, user_id):
        """
        Retrieves a specific secret by its ID if the user has access.

        Args:
            secret_id (str): The ID of the secret.
            user_id (str): The ID of the user requesting access.

        Returns:
            Secret: The requested secret object, or None if not found or no access.
        """
        try:
            secret = Secret.query.filter_by(id=secret_id, owner_id=user_id).first()

            if not secret:
                secret = Secret.query.join(Secret.shared_with).filter(
                    Secret.id == secret_id,
                    User.id == user_id
                ).first()

            if secret:
                secret.has_direct_access = secret.owner_id == user_id

            return secret
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching secret {secret_id} for user {user_id}: {str(e)}")
            return None

    @staticmethod
    def create_secret(user_id, name, secret_type, value, folder_id=None):
        """
        Creates a new secret.

        Args:
            user_id (str): The ID of the owner.
            name (str): The name of the secret.
            secret_type (str): The type of secret (e.g., password, api_key).
            value (str): The secret value.
            folder_id (str, optional): The ID of the folder to place this secret in.

        Returns:
            Secret: The newly created secret object, or None if creation failed.
        """
        try:
            new_id = str(uuid.uuid4())

            new_secret = Secret(
                id=new_id,
                name=name,
                type=secret_type,
                value=value,
                owner_id=user_id,
                folder_id=folder_id
            )

            db.session.add(new_secret)
            db.session.commit()

            new_secret.has_direct_access = True

            return new_secret
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error creating secret for user {user_id}: {str(e)}")
            return None

    @staticmethod
    def update_secret(secret_id, user_id, updates):
        """
        Updates an existing secret.

        Args:
            secret_id (str): The ID of the secret to update.
            user_id (str): The ID of the user making the update.
            updates (dict): A dictionary of fields to update.

        Returns:
            Secret: The updated secret object, or None if the update failed or the user lacks permissions.
        """
        try:
            secret = SecretsService.get_secret_by_id(secret_id, user_id)

            if not secret:
                return None

            if secret.owner_id != user_id:
                has_write_permission = False

                if not has_write_permission:
                    return None

            for key, value in updates.items():
                if hasattr(secret, key):
                    setattr(secret, key, value)

            db.session.commit()
            return secret

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error updating secret {secret_id}: {str(e)}")
            return None

    @staticmethod
    def delete_secret(secret_id, user_id):
        """
        Deletes a secret.

        Args:
            secret_id (str): The ID of the secret to delete.
            user_id (str): The ID of the user making the deletion.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            secret = SecretsService.get_secret_by_id(secret_id, user_id)

            if not secret:
                return False

            if secret.owner_id != user_id:
                has_delete_permission = False

                if not has_delete_permission:
                    return False

            db.session.delete(secret)
            db.session.commit()
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error deleting secret {secret_id}: {str(e)}")
            return False

    @staticmethod
    def share_secret(secret_id, owner_id, shared_with_id, permissions):
        """
        Shares a secret with another user.

        Args:
            secret_id (str): The ID of the secret to share.
            owner_id (str): The ID of the secret owner.
            shared_with_id (str): The ID of the user to share with.
            permissions (dict): A dictionary of permissions (read, write, delete).

        Returns:
            bool: True if sharing was successful, False otherwise.
        """
        try:
            secret = Secret.query.filter_by(id=secret_id, owner_id=owner_id).first()

            if not secret:
                return False

            shared_with_user = User.query.get(shared_with_id)

            if not shared_with_user:
                return False

            secret.shared_with.append(shared_with_user)

            db.session.commit()
            return True

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error sharing secret {secret_id}: {str(e)}")
            return False
