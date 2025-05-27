#! /usr/bin/env python3


import datetime
from datetime import timezone
from sqlalchemy.orm import relationship
from backend.extensions import db
from backend.models.enums import user_role_enum, UserRole
from flask_login import UserMixin
from flask_security import RoleMixin, SQLAlchemyUserDatastore
from PIL import Image
from sqlalchemy.dialects.mysql import MEDIUMTEXT


class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    permissions = db.Column(db.Text)
    
    def get_permissions(self):
        if not self.permissions:
            return []
        return self.permissions.split(',')


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    # New personal information fields
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    # For profile photos:
    # Store directly in the database as base64 encoded string
    profile_photo = db.Column(MEDIUMTEXT, nullable=True)  # Base64 encoded image
    role = db.Column(
        user_role_enum,
        nullable=False,
        default=UserRole.USER.value
    )
    
    # Required for Flask-Security
    email = db.Column(db.String(255), nullable=True, unique=True)
    active = db.Column(db.Boolean(), default=True)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=True)
    confirmed_at = db.Column(db.DateTime())
    
    # Keep the original fields for timestamps
    created_time = db.Column(db.DateTime, default=datetime.datetime.now(timezone.utc))
    last_modified = db.Column(
        db.DateTime,
        default=datetime.datetime.now(timezone.utc),
        onupdate=datetime.datetime.now(timezone.utc)
    )

    # Relationship to SecretPermission
    secret_permissions = relationship(
        "SecretPermission",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Relationships to owned content
    # Note: owned_folders and owned_tags are defined in their respective models as backref
    
    # Relationship to FolderPermission
    # Note: folder_permissions is defined in the FolderPermission model as backref
    
    # Relationship to roles for Flask-Security
    roles = relationship(
        'Role',
        secondary='user_roles',
        backref=db.backref('users', lazy='dynamic')
    )

    @property
    def display_name(self):
        """Returns the user's full name if available, otherwise username"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def set_profile_photo(self, image_data, max_size=300):
        """Store profile photo as base64 in the database after resizing
        
        Args:
            image_data: The raw binary image data
            max_size: Maximum width/height in pixels (default: 300px)
        """
        try:
            # Resize the image to a reasonable size
            import io
            import base64
            
            # Load image from binary data
            img = Image.open(io.BytesIO(image_data))
            
            # Calculate new dimensions while preserving aspect ratio
            width, height = img.size
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                
                # Resize the image
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to PNG format with compression
            output = io.BytesIO()
            img.save(output, format='PNG', optimize=True, quality=85)
            compressed_data = output.getvalue()
            
            # Store as base64 string in the database
            self.profile_photo = base64.b64encode(compressed_data).decode('utf-8')
            
            print(f"Profile photo processed and saved as base64 ({len(self.profile_photo)} chars)")
            return True
            
        except Exception as e:
            print(f"Error processing profile photo: {e}")
            return False


# Association table for User and Role
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


# Setup Flask-Security datastore
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
