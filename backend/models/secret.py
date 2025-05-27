#! /usr/bin/env python3


import datetime
from datetime import timezone
from sqlalchemy.orm import relationship
from backend.extensions import db
from backend.models.enums import secret_type_enum, SecretType


class Secret(db.Model):
    __tablename__ = 'secure_secrets'

    secret_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    secret_name = db.Column(db.String(255), nullable=False)
    encrypted_secret_value = db.Column(db.String(2048), nullable=True)
    secret_type = db.Column(secret_type_enum, nullable=False)
    # New column for folder association
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.folder_id'), nullable=True)
    # Description field to enhance searchability
    description = db.Column(db.String(1024), nullable=True)
    
    # File storage related fields
    file_path = db.Column(db.String(1024), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    file_mime_type = db.Column(db.String(128), nullable=True)
    
    created_time = db.Column(db.DateTime, default=datetime.datetime.now(timezone.utc))
    last_modified = db.Column(
        db.DateTime,
        default=datetime.datetime.now(timezone.utc),
        onupdate=datetime.datetime.now(timezone.utc)
    )

    # Indexes for search performance
    __table_args__ = (
        db.Index('idx_secret_name', 'secret_name'),
        db.Index('idx_secret_folder', 'folder_id'),
        db.Index('idx_secret_owner', 'owner_id'),
    )

    # Relationships
    owner = relationship("User", backref="owned_secrets")
    folder = relationship("Folder", back_populates="secrets")
    
    # Relationship to Secret Permissions
    permissions = relationship(
        "SecretPermission",
        back_populates="secret",
        cascade="all, delete-orphan"
    )
    
    # Relationship to Tags - many-to-many
    tags = relationship(
        "Tag",
        secondary="secret_tags",
        back_populates="secrets"
    )
    
    @property
    def is_file_secret(self):
        """Check if this secret is a file-based secret."""
        return self.secret_type == SecretType.IMAGE.value
        
    @property
    def is_favorite(self):
        """Return favorite status (not currently implemented)."""
        # This is a placeholder as the database doesn't have this column yet
        return False
