#! /usr/bin/env python3


import os
import base64
from cryptography.fernet import Fernet
from flask import current_app
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


def get_encryption_key():
    """
    Retrieves the global encryption key from the application configuration.

    Returns:
        bytes: The encryption key.

    Raises:
        ValueError: If no encryption key is found in the app config.
    """
    key = current_app.config.get('ENCRYPTION_KEY')
    if not key:
        logger.error("No encryption key found in app config")
        raise ValueError("No encryption key found in app config")

    return key.encode('utf-8')


def encrypt_value(value):
    """
    Encrypts a string value using Fernet symmetric encryption with the global key.

    Args:
        value (str): The string value to encrypt.

    Returns:
        str: The encrypted value as a base64 string.

    Raises:
        Exception: If an error occurs during encryption.
    """
    if not value:
        return ""

    try:
        key = get_encryption_key()

        fernet = Fernet(key)

        value_bytes = value.encode('utf-8')
        encrypted_bytes = fernet.encrypt(value_bytes)

        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Error encrypting value: {str(e)}")
        raise


def decrypt_value(encrypted_value):
    """
    Decrypts a base64-encoded string value using Fernet symmetric encryption with the global key.

    Args:
        encrypted_value (str): The encrypted value as a base64 string.

    Returns:
        str: The decrypted value, or an error placeholder if decryption fails.
    """
    if not encrypted_value:
        return ""

    try:
        key = get_encryption_key()

        fernet = Fernet(key)

        encrypted_bytes = encrypted_value.encode('utf-8')
        decrypted_bytes = fernet.decrypt(encrypted_bytes)

        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Error decrypting value: {str(e)}")
        return "[Error: Unable to decrypt value]"


def get_user_key_filename(user_id):
    """
    Generates the filename for a user's TPM-sealed encryption key.

    Args:
        user_id (int): The ID of the user.

    Returns:
        str: The filename for the user's key.
    """
    return f"user_{user_id}_key.sealed"


def ensure_user_key(user_id):
    """
    Ensures a user has a TPM-sealed encryption key, generating one if it doesn't exist.
    If TPM sealing is not enabled or fails, it falls back to the global encryption key.

    Args:
        user_id (int): The ID of the user.

    Returns:
        bytes: The encryption key for the user.
    """
    try:
        from backend.utils.tpm_manager import TPMManager
        secrets_dir = current_app.config.get('TPM_SECRETS_DIR', 'secrets')

        filename = get_user_key_filename(user_id)

        tpm = TPMManager(secrets_dir)
        tpm.generate_or_load_primary_key()

        key_path = Path(secrets_dir) / filename
        if key_path.exists():
            logger.info(f"Using existing key for user {user_id}")
            return tpm.unseal_secret(filename)
        else:
            logger.info(f"Generating new key for user {user_id}")
            key = Fernet.generate_key()
            tpm.seal_secret(key, filename)
            return key
    except Exception as e:
        logger.error(f"Failed to ensure user key: {str(e)}")
        return get_encryption_key()


def encrypt_file(file_data, user_id=None):
    """
    Encrypts file data using Fernet symmetric encryption.
    If TPM sealing is enabled and a user ID is provided, it attempts to use a user-specific,
    TPM-sealed key. Otherwise, it uses the global encryption key.

    Args:
        file_data (bytes): The binary file data to encrypt.
        user_id (int, optional): The ID of the user who owns the file.

    Returns:
        bytes: The encrypted file data.

    Raises:
        Exception: If an error occurs during encryption.
    """
    if not file_data:
        return None

    try:
        should_use_tpm = current_app.config.get('USE_TPM_SEALING', False)

        if should_use_tpm and user_id is not None:
            try:
                key = ensure_user_key(user_id)

                fernet = Fernet(key)

                encrypted_data = fernet.encrypt(file_data)

                header = f"TPM_USER_{user_id}:".encode('utf-8')
                return header + encrypted_data
            except Exception as e:
                logger.warning(f"Failed to use TPM for user key, falling back to regular encryption: {str(e)}")
                key = get_encryption_key()
                fernet = Fernet(key)
                return fernet.encrypt(file_data)
        else:
            key = get_encryption_key()
            fernet = Fernet(key)
            return fernet.encrypt(file_data)
    except Exception as e:
        logger.error(f"Error encrypting file: {str(e)}")
        raise


def decrypt_file(encrypted_data):
    """
    Decrypts file data using Fernet symmetric encryption.
    It attempts to decrypt data that might be TPM-sealed with a user-specific key
    or a legacy TPM-sealed key. If decryption with TPM fails or it's not TPM-sealed,
    it falls back to the global encryption key.

    Args:
        encrypted_data (bytes): The encrypted file data.

    Returns:
        bytes: The decrypted file data.

    Raises:
        Exception: If an error occurs during decryption.
    """
    if not encrypted_data:
        return None

    try:
        if encrypted_data.startswith(b"TPM_USER_"):
            try:
                header_end = encrypted_data.find(b":")
                if header_end == -1:
                    logger.error("Invalid TPM-sealed user data format, missing colon")
                    raise ValueError("Invalid TPM-sealed user data format")

                user_id_str = encrypted_data[9:header_end].decode('utf-8')
                user_id = int(user_id_str)

                actual_encrypted_data = encrypted_data[header_end + 1:]

                logger.info(f"Attempting to decrypt data with user {user_id}'s key")

                from backend.utils.tpm_manager import TPMManager
                secrets_dir = current_app.config.get('TPM_SECRETS_DIR', 'secrets')

                os.makedirs(secrets_dir, exist_ok=True)

                tpm = TPMManager(secrets_dir)
                tpm.generate_or_load_primary_key()

                filename = get_user_key_filename(user_id)

                key = tpm.unseal_secret(filename)
                logger.info(f"Successfully unsealed key for user {user_id}")

                fernet = Fernet(key)
                decrypted_data = fernet.decrypt(actual_encrypted_data)

                return decrypted_data
            except FileNotFoundError as e:
                logger.error(f"User key file not found: {str(e)}, falling back to config key")
                key = get_encryption_key()
                fernet = Fernet(key)
                return fernet.decrypt(encrypted_data)
            except Exception as e:
                logger.error(f"Failed to decrypt with user key: {str(e)}, falling back to config key")
                key = get_encryption_key()
                fernet = Fernet(key)
                return fernet.decrypt(encrypted_data)
        elif encrypted_data.startswith(b"TPM_SEALED:"):
            try:
                header_end = encrypted_data.find(b":", 11)
                if header_end == -1:
                    logger.error("Invalid TPM-sealed data format, missing second colon")
                    raise ValueError("Invalid TPM-sealed data format")

                filename = encrypted_data[11:header_end].decode('utf-8')
                actual_encrypted_data = encrypted_data[header_end + 1:]

                logger.info(f"Attempting to unseal legacy data with TPM using file: {filename}")

                from backend.utils.tpm_manager import TPMManager
                secrets_dir = current_app.config.get('TPM_SECRETS_DIR', 'secrets')

                os.makedirs(secrets_dir, exist_ok=True)

                tpm = TPMManager(secrets_dir)
                tpm.generate_or_load_primary_key()

                key = tpm.unseal_secret(filename)
                logger.info(f"Successfully unsealed legacy key with TPM (length: {len(key)})")

                fernet = Fernet(key)
                decrypted_data = fernet.decrypt(actual_encrypted_data)

                return decrypted_data
            except Exception as e:
                logger.error(f"Failed to unseal with TPM, falling back to config key: {str(e)}")
                key = get_encryption_key()
                fernet = Fernet(key)
                return fernet.decrypt(encrypted_data)
        else:
            key = get_encryption_key()
            fernet = Fernet(key)

            decrypted_data = fernet.decrypt(encrypted_data)

            return decrypted_data
    except Exception as e:
        logger.error(f"Error decrypting file: {str(e)}")
        raise


def get_secure_file_path(user_id, extension=None):
    """
    Generates a secure, unique file path for storing encrypted files.

    Args:
        user_id (int): The ID of the user owning the file.
        extension (str, optional): The file extension (without dot).

    Returns:
        tuple: A tuple containing (relative_path_str, absolute_path_str).
    """
    secure_filename = str(uuid.uuid4())
    if extension:
        secure_filename = f"{secure_filename}.{extension}"

    user_dir = f"user_{user_id}"

    storage_dir = current_app.config.get('FILE_UPLOAD_PATH', 'file_uploads')

    full_dir_path = Path(storage_dir) / user_dir
    os.makedirs(full_dir_path, exist_ok=True)

    relative_path = f"{user_dir}/{secure_filename}"
    absolute_path = full_dir_path / secure_filename

    return str(relative_path), str(absolute_path)


def validate_file_size(file_size):
    """
    Validates that the file size is within the allowed limits defined in the application configuration.

    Args:
        file_size (int): The size of the file in bytes.

    Returns:
        bool: True if the file size is valid, False otherwise.
    """
    max_size = current_app.config.get('MAX_FILE_SIZE', 10 * 1024 * 1024)
    return file_size <= max_size


def validate_file_type(mime_type):
    """
    Validates that the file's MIME type is among the allowed types defined in the application configuration.

    Args:
        mime_type (str): The MIME type of the file.

    Returns:
        bool: True if the file type is allowed, False otherwise.
    """
    allowed_types = current_app.config.get('ALLOWED_FILE_TYPES', {
        'image/png': 'image',
        'image/jpeg': 'image'
    })

    return mime_type in allowed_types


def get_file_extension_from_mime(mime_type):
    """
    Extracts a simplified file type (e.g., 'image') from a given MIME type.

    Args:
        mime_type (str): The MIME type of the file.

    Returns:
        str: The simplified file type, or 'unknown' if not mapped.
    """
    allowed_types = current_app.config.get('ALLOWED_FILE_TYPES', {
        'image/png': 'image',
        'image/jpeg': 'image'
    })

    return allowed_types.get(mime_type, 'unknown')


def get_actual_extension_from_mime(mime_type):
    """
    Extracts the common file extension (e.g., 'png', 'jpg') from a given MIME type.

    Args:
        mime_type (str): The MIME type of the file.

    Returns:
        str: The file extension without a dot, or 'bin' if not mapped.
    """
    extension_map = {
        'image/png': 'png',
        'image/jpeg': 'jpg'
    }

    return extension_map.get(mime_type, 'bin')


def secure_delete_file(file_path):
    """
    Securely deletes a file by overwriting its content with zeros before removal.

    Args:
        file_path (str): The absolute path to the file to delete.

    Returns:
        bool: True if the file was deleted successfully or didn't exist, False otherwise.
    """
    if not os.path.exists(file_path):
        return True

    try:
        size = os.path.getsize(file_path)

        with open(file_path, 'wb') as f:
            f.write(b'\0' * size)

        os.remove(file_path)

        return True
    except Exception as e:
        logger.error(f"Error securely deleting file {file_path}: {str(e)}")
        return False


def ensure_upload_directories():
    """
    Ensures that all necessary directories for file uploads and TPM-sealed secrets exist and are writable.

    Returns:
        bool: True if all directories are successfully created/verified and writable, False otherwise.
    """
    try:
        storage_dir = current_app.config.get('FILE_UPLOAD_PATH', 'file_uploads')
        os.makedirs(storage_dir, exist_ok=True)

        tpm_dir = current_app.config.get('TPM_SECRETS_DIR', 'secrets/tpm')
        os.makedirs(tpm_dir, exist_ok=True)

        test_write_path = os.path.join(storage_dir, '.test_write')
        with open(test_write_path, 'w') as f:
            f.write('test')
        os.remove(test_write_path)

        test_write_path = os.path.join(tpm_dir, '.test_write')
        with open(test_write_path, 'w') as f:
            f.write('test')
        os.remove(test_write_path)

        logger.info(f"Upload directories verified: {storage_dir}, {tpm_dir}")
        return True
    except Exception as e:
        logger.error(f"Error ensuring upload directories: {str(e)}")
        return False
