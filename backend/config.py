#! /usr/bin/env python3


import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = PROJECT_ROOT / 'logs'
SECRETS_DIR = PROJECT_ROOT / 'secrets'

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
SECRETS_DIR.mkdir(exist_ok=True, mode=0o700)  # Restrictive permissions for secrets


def get_secret_from_file(filename):
    """
    Unseals the secret from 'secrets/{filename}' using TPM.
    Returns the secret as a UTF-8 decoded string.
    """
    # Import here to avoid circular imports
    from backend.utils.tpm_manager import TPMManager
    
    # Check in environment variables first
    env_name = f"{filename.upper()}_FILE"
    if env_name in os.environ:
        try:
            # Use the TPM to unseal from the environment-specified path
            tpm_mgr = TPMManager(secrets_dir=os.path.dirname(os.environ[env_name]))
            tpm_mgr.generate_or_load_primary_key()
            secret_bytes = tpm_mgr.unseal_secret(filename=os.path.basename(os.environ[env_name]))
            return secret_bytes.decode("utf-8", errors='replace')
        except Exception as e:
            print(f"Error unsealing secret from environment file {env_name}: {str(e)}")
    
    # Try Docker-mounted secrets
    docker_secrets = "/secrets"
    if os.path.exists(f"{docker_secrets}/{filename}"):
        try:
            tpm_mgr = TPMManager(secrets_dir=docker_secrets)
            tpm_mgr.generate_or_load_primary_key()
            secret_bytes = tpm_mgr.unseal_secret(filename=filename)
            return secret_bytes.decode("utf-8", errors='replace')
        except Exception as e:
            print(f"Error unsealing secret from Docker secrets: {str(e)}")
    
    # Fall back to the original location
    try:
        tpm_mgr = TPMManager(secrets_dir=SECRETS_DIR)
        tpm_mgr.generate_or_load_primary_key()
        secret_bytes = tpm_mgr.unseal_secret(filename=filename)
        return secret_bytes.decode("utf-8", errors='replace')
    except Exception as e:
        print(f"Error unsealing secret from app secrets: {str(e)}")
        raise RuntimeError(f"Failed to unseal secret: {filename}")


# Configuration class with production settings
class Config:
    # Logging configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_FILE = LOGS_DIR / 'app.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUPS = 7

    # Database settings
    DB_TYPE = "mariadb"
    DB_CONNECTOR = "pymysql"
    DB_USER = "auth-berry-user"
    DB_HOST = "auth_berry_mariadb"
    DB_PORT = "3306"
    DB_NAME = "auth_berry"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Security settings
    SECURITY_PASSWORD_HASH = 'argon2'
    SECURITY_PASSWORD_SINGLE_HASH = True  # Use single hash for password verification
    MAIL_DEFAULT_SENDER = 'no-reply@authberry.local'  # Default sender for Flask-Security emails

    # Application name
    APP_NAME = 'AuthBerry'
    
    # Get secrets from TPM
    JWT_SECRET = get_secret_from_file("jwt_secret")
    JWT_SECRET_KEY = JWT_SECRET  # For Flask-JWT-Extended
    
    ENCRYPTION_KEY = get_secret_from_file("encryption_key")
    
    APP_SECRET_KEY = get_secret_from_file("app_secret")
    SECRET_KEY = APP_SECRET_KEY  # For Flask
    
    DB_PASSWORD = get_secret_from_file("mariadb_user")
    SECURITY_PASSWORD_SALT = get_secret_from_file("password_salt")
    
    # Database URI - Always MariaDB
    SQLALCHEMY_DATABASE_URI = (
        f"{DB_TYPE}+{DB_CONNECTOR}://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    # JWT configuration
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60  # 1 hour in seconds
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_CSRF_IN_COOKIES = True
    JWT_CSRF_CHECK_FORM = True
    
    # File upload settings
    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB max file size
    FILE_UPLOAD_PATH = os.environ.get('FILE_UPLOAD_PATH', os.path.join(PROJECT_ROOT, 'file_uploads'))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # TPM Configuration
    USE_TPM_SEALING = True
    TPM_SECRETS_DIR = os.environ.get('TPM_SECRETS_DIR', '/app/secrets')
    
    # Allowed file types for upload
    ALLOWED_FILE_TYPES = {
        'image/png': 'image',
        'image/jpeg': 'image'
    }


# Configuration dictionary - keeping this for compatibility but using only one config
config_dict = {
    'development': Config,
    'production': Config,
    'default': Config
}
