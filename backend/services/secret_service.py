#! /usr/bin/env python3


import os
from flask import current_app
from werkzeug.utils import secure_filename
import magic
from backend.models.secret import Secret
from backend.models.permission import SecretPermission, UserSecretView
from backend.models.folder import Folder, FolderPermission
from backend.extensions import db
from backend.utils.encryption import (
    encrypt_file, decrypt_file, get_secure_file_path,
    validate_file_size, validate_file_type, get_file_extension_from_mime,
    get_actual_extension_from_mime, secure_delete_file
)


class SecretService:
    """Service for handling secret operations, particularly file-based secrets."""

    @staticmethod
    def create_file_secret(user_id, file, secret_name, folder_id=None, description=None, tags=None):
        """
        Creates a new file-based secret.

        Args:
            user_id (int): The ID of the user creating the secret.
            file (FileStorage): The file object from Flask's request.files.
            secret_name (str): The name for this secret.
            folder_id (int, optional): The folder ID to place this secret in.
            description (str, optional): A description for this secret.
            tags (list, optional): A list of tags to associate with this secret.

        Returns:
            tuple: (success, result) where success is a boolean and result is the created secret or error message.
        """
        try:
            file_data = file.read()
            file_size = len(file_data)
            original_filename = secure_filename(file.filename)

            if not validate_file_size(file_size):
                max_size_mb = current_app.config.get('MAX_FILE_SIZE', 10 * 1024 * 1024) / (1024 * 1024)
                return False, f"File too large. Maximum allowed size is {max_size_mb}MB."

            mime_type = magic.from_buffer(file_data, mime=True)
            if not validate_file_type(mime_type):
                return False, "Unsupported file type. Only image files (PNG, JPG) are allowed."

            secret_type = get_file_extension_from_mime(mime_type)

            actual_extension = get_actual_extension_from_mime(mime_type)

            encrypted_data = encrypt_file(file_data, user_id)

            relative_path, absolute_path = get_secure_file_path(user_id, actual_extension)

            with open(absolute_path, 'wb') as f:
                f.write(encrypted_data)

            secret = Secret(
                owner_id=user_id,
                secret_name=secret_name,
                secret_type=secret_type,
                folder_id=folder_id,
                description=description,
                file_path=relative_path,
                original_filename=original_filename,
                file_size=file_size,
                file_mime_type=mime_type
            )

            db.session.add(secret)
            db.session.commit()

            if tags:
                from backend.api.secrets import process_tags
                process_tags(tags, secret, user_id)
                db.session.commit()

            if folder_id:
                folder = Folder.query.get(folder_id)

                if folder and folder.is_shared_folder:
                    folder_permissions = FolderPermission.query.filter_by(folder_id=folder_id).all()
                    current_app.logger.debug(
                        f"Found {len(folder_permissions)} permissions to inherit for folder {folder_id}")

                    for folder_perm in folder_permissions:
                        if folder_perm.user_id == int(user_id):
                            continue

                        secret_perm = SecretPermission(
                            secret_id=secret.secret_id,
                            user_id=folder_perm.user_id,
                            can_read=folder_perm.can_read,
                            can_write=folder_perm.can_write,
                            can_delete=folder_perm.can_delete
                        )

                        db.session.add(secret_perm)
                        current_app.logger.debug(
                            f"Inherited permission for user {folder_perm.user_id} on file secret {secret.secret_id}")

                        if folder_perm.can_read:
                            UserSecretView.set_user_view(
                                user_id=folder_perm.user_id,
                                secret_id=secret.secret_id,
                                folder_id=folder_id
                            )
                            current_app.logger.debug(
                                f"Created view for user {folder_perm.user_id} to see file secret {secret.secret_id} in folder {folder_id}")

                    db.session.commit()

            return True, secret

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating file secret: {str(e)}")
            return False, f"Error creating file secret: {str(e)}"

    @staticmethod
    def get_file_content(secret, check_permission_func=None, user_id=None):
        """
        Retrieves the decrypted file content for a given secret.

        Args:
            secret (Secret): The secret object.
            check_permission_func (callable, optional): A function to check user permissions.
            user_id (int, optional): The ID of the user requesting the file.

        Returns:
            tuple: (success, result) where success is a boolean and result is either the file data or an error message.
        """
        try:
            if not secret.is_file_secret or not secret.file_path:
                return False, "This secret does not contain a file."

            if check_permission_func and user_id and not check_permission_func(secret, user_id):
                return False, "You don't have permission to access this file."

            storage_dir = current_app.config.get('FILE_UPLOAD_PATH', 'file_uploads')
            file_path = os.path.join(storage_dir, secret.file_path)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            if not os.path.exists(file_path):
                current_app.logger.error(f"File not found at path: {file_path}")
                return False, "File not found. It may have been deleted or moved."

            try:
                with open(file_path, 'rb') as f:
                    encrypted_data = f.read()

                current_app.logger.info(f"Successfully read encrypted file of size {len(encrypted_data)} bytes")
            except PermissionError:
                current_app.logger.error(f"Permission error reading file: {file_path}")
                return False, "Permission error reading file. Please check file permissions."
            except Exception as e:
                current_app.logger.error(f"Error reading file {file_path}: {str(e)}")
                return False, f"Error reading file: {str(e)}"

            try:
                decrypted_data = decrypt_file(encrypted_data)
                current_app.logger.info(f"Successfully decrypted file of size {len(decrypted_data)} bytes")
            except Exception as e:
                current_app.logger.error(f"Error decrypting file: {str(e)}")
                return False, f"Error decrypting file: {str(e)}"

            return True, {
                'data': decrypted_data,
                'mime_type': secret.file_mime_type,
                'filename': secret.original_filename
            }

        except Exception as e:
            current_app.logger.error(f"Error retrieving file content: {str(e)}")
            return False, f"Error retrieving file content: {str(e)}"

    @staticmethod
    def delete_file_secret(secret):
        """
        Deletes a file-based secret, including the encrypted file from storage and its database record.

        Args:
            secret (Secret): The secret object to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if secret.file_path:
                storage_dir = current_app.config.get('FILE_UPLOAD_PATH', 'file_uploads')
                file_path = os.path.join(storage_dir, secret.file_path)

                secure_delete_file(file_path)

            UserSecretView.query.filter_by(secret_id=secret.secret_id).delete()

            db.session.delete(secret)
            db.session.commit()

            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting file secret: {str(e)}")
            return False

    @staticmethod
    def update_file_secret(secret, file=None, secret_name=None, folder_id=None, description=None, tags=None):
        """
        Updates an existing file-based secret's file content or metadata.

        Args:
            secret (Secret): The secret to update.
            file (FileStorage, optional): The new file content if the file itself is being updated.
            secret_name (str, optional): A new name for the secret.
            folder_id (int, optional): A new folder ID for the secret.
            description (str, optional): A new description for the secret.
            tags (list, optional): A list of new tags for the secret.

        Returns:
            tuple: (success, result) where success is a boolean and result is the updated secret or an error message.
        """
        try:
            if file:
                file_data = file.read()
                file_size = len(file_data)
                original_filename = secure_filename(file.filename)

                if not validate_file_size(file_size):
                    max_size_mb = current_app.config.get('MAX_FILE_SIZE', 10 * 1024 * 1024) / (1024 * 1024)
                    return False, f"File too large. Maximum allowed size is {max_size_mb}MB."

                mime_type = magic.from_buffer(file_data, mime=True)
                if not validate_file_type(mime_type):
                    return False, "Unsupported file type. Only image files (PNG, JPG) are allowed."

                secret_type = get_file_extension_from_mime(mime_type)

                actual_extension = get_actual_extension_from_mime(mime_type)

                if secret.file_path:
                    storage_dir = current_app.config.get('FILE_UPLOAD_PATH', 'file_uploads')
                    old_file_path = os.path.join(storage_dir, secret.file_path)
                    secure_delete_file(old_file_path)

                encrypted_data = encrypt_file(file_data, secret.owner_id)

                relative_path, absolute_path = get_secure_file_path(secret.owner_id, actual_extension)

                with open(absolute_path, 'wb') as f:
                    f.write(encrypted_data)

                secret.file_path = relative_path
                secret.original_filename = original_filename
                secret.file_size = file_size
                secret.file_mime_type = mime_type
                secret.secret_type = secret_type

            if secret_name is not None:
                secret.secret_name = secret_name

            if folder_id is not None:
                secret.folder_id = folder_id

            if description is not None:
                secret.description = description

            db.session.commit()

            if tags is not None:
                secret.tags = []
                db.session.commit()

                from backend.api.secrets import process_tags
                process_tags(tags, secret, secret.owner_id)
                db.session.commit()

            return True, secret

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating file secret: {str(e)}")
            return False, f"Error updating file secret: {str(e)}"

    @staticmethod
    def check_permission(secret, user_id):
        """
        Checks if a user has read permission for a given secret.

        Args:
            secret (Secret): The secret object to check.
            user_id (int): The ID of the user.

        Returns:
            bool: True if the user has permission, False otherwise.
        """
        if secret.owner_id == user_id:
            return True

        permission = SecretPermission.query.filter_by(
            secret_id=secret.secret_id,
            user_id=user_id,
            can_read=True
        ).first()

        return permission is not None
