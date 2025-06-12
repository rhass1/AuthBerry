#! /usr/bin/env python3


import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import logging
from datetime import timedelta
import sqlalchemy
import click

# Import extensions
from backend.extensions import db, migrate, login_manager, jwt, principal, cors, socketio, security
from backend.config import config_dict, Config

# Import models to ensure they are registered with SQLAlchemy
from backend.models.user import User
from backend.models.secret import Secret
from backend.models.folder import Folder, FolderPermission
from backend.models.permission import SecretPermission
from backend.models.tag import Tag, secret_tags, folder_tags
from backend.models.system import SystemSetting


def create_app(config_name=None):
    """Create and initialize the Flask application."""

    # Create Flask app
    app = Flask(__name__)

    # Configure app - always use production configuration
    app.config.from_object(Config)

    # Set the required Flask-JWT-Extended secret keys
    app.config['JWT_SECRET_KEY'] = app.config['JWT_SECRET']
    app.config['SECRET_KEY'] = app.config['APP_SECRET_KEY']
    
    # Configure JWT with secure settings
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Secure cookie settings - always use secure settings
    app.config['JWT_COOKIE_SECURE'] = True
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Extend token expiration for easier testing
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)  # Long refresh token expiration
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True
    app.config['JWT_CSRF_IN_COOKIES'] = True
    app.config['JWT_CSRF_CHECK_FORM'] = True
    
    # JWT Cookie settings - strict for better security
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
    
    # Allow access token in query string for file downloads (if needed)
    app.config['JWT_QUERY_STRING_NAME'] = 'token'
    app.config['JWT_QUERY_STRING_LOCATIONS'] = ['query_string']

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    principal.init_app(app)
    
    # Initialize CORS for all origins in a LAN environment
    cors.init_app(app, 
                 resources={r"/api/*": {"origins": "*"}},
                 supports_credentials=True,
                 expose_headers=['Content-Type', 'Authorization'],
                 allow_headers=['Content-Type', 'Authorization', 'Accept'])
    
    # Initialize SocketIO with CORS support - use gevent mode for single worker
    socketio.init_app(app, cors_allowed_origins="*", async_mode='gevent')

    # Configure login manager
    login_manager.session_protection = "strong"

    # Initialize Flask-Security
    from backend.models.user import user_datastore
    security.init_app(app, user_datastore)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @jwt.invalid_token_loader
    def handle_invalid_token(error):
        return {
            "msg": "Invalid or expired token",
            "error_code": "invalid_token"
        }, 401
        
    # Register API blueprints
    from backend.api import api_bp
    from backend.api.auth import auth_bp
    from backend.api.users import users_bp
    from backend.api.secrets import secrets_bp
    from backend.api.folders import folders_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(secrets_bp, url_prefix='/api/secrets')
    app.register_blueprint(folders_bp, url_prefix='/api/folders')

    # Initialize WebSocket service
    from backend.services.ws_service import init_ws_service
    init_ws_service(app)
    
    # Register WebSocket blueprint
    from backend.ws import ws_bp
    app.register_blueprint(ws_bp)

    # Register CLI commands
    @app.cli.command("cleanup-database")
    def cleanup_database():
        """Clear all user and application data from the database while preserving structure and system settings."""
        click.echo("Starting database cleanup...")
        try:
            # Delete data from association tables first to avoid foreign key constraints
            db.session.execute(db.delete(secret_tags))
            db.session.execute(db.delete(folder_tags))
            
            # Then delete data from other tables
            db.session.execute(db.delete(SecretPermission))
            db.session.execute(db.delete(FolderPermission))
            db.session.execute(db.delete(Secret))
            db.session.execute(db.delete(Folder))
            db.session.execute(db.delete(Tag))
            db.session.execute(db.delete(User))
            
            # Preserve SystemSettings - intentionally not deleting them
            
            # Commit the transaction
            db.session.commit()
            click.echo("Database cleanup completed successfully. System settings have been preserved.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Error during database cleanup: {str(e)}")
            raise

    # NOTE: Database tables are NOT automatically created here
    # You must run migrations manually:
    # docker exec -it auth_berry_flask bash -c "flask db init && flask db migrate && flask db upgrade"

    return app
