#! /usr/bin/env python3


import datetime
from datetime import timezone
from sqlalchemy.orm import relationship
from backend.extensions import db
from sqlalchemy import Enum
import enum


class FolderType(enum.Enum):
    REGULAR = "regular"  # For personal organization, doesn't affect sharing
    SHARED = "shared"    # Permissions are inherited by contents


class Folder(db.Model):
    __tablename__ = 'folders'

    folder_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Self-referential relationship for hierarchical folder structure
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.folder_id'), nullable=True)
    # Add description field
    description = db.Column(db.String(1024), nullable=True)
    # Add folder type field
    folder_type = db.Column(
        Enum(FolderType),
        nullable=False,
        default=FolderType.REGULAR,
        server_default=FolderType.REGULAR.value
    )
    created_time = db.Column(db.DateTime, default=datetime.datetime.now(timezone.utc))
    last_modified = db.Column(
        db.DateTime,
        default=datetime.datetime.now(timezone.utc),
        onupdate=datetime.datetime.now(timezone.utc)
    )

    # Relationships
    owner = relationship("User", backref="owned_folders")
    parent = relationship("Folder", backref="subfolders", remote_side=[folder_id])
    secrets = relationship("Secret", back_populates="folder", cascade="all, delete-orphan")
    permissions = relationship(
        "FolderPermission",
        back_populates="folder",
        cascade="all, delete-orphan"
    )
    # Add relationship to Tags
    tags = relationship(
        "Tag",
        secondary="folder_tags",
        back_populates="folders"
    )
    
    # Add cascade delete for secret views
    secret_views = relationship(
        "UserSecretView",
        back_populates="folder",
        cascade="all, delete"
    )
    
    def get_full_path(self):
        """Return the full path of the folder (e.g., /parent/child/grandchild)"""
        path = [self.name]
        current = self.parent
        
        # Prevent infinite loops in case of circular references
        visited = {self.folder_id}
        
        while current and current.folder_id not in visited:
            path.append(current.name)
            visited.add(current.folder_id)
            current = current.parent
            
        return "/" + "/".join(reversed(path))

    @property
    def is_shared_folder(self):
        """Check if this is a shared folder"""
        return self.folder_type == FolderType.SHARED


class FolderPermission(db.Model):
    __tablename__ = 'folder_permissions'

    folder_id = db.Column(
        db.Integer,
        db.ForeignKey('folders.folder_id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
    can_read = db.Column(db.Boolean, default=False)
    can_write = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    # Whether the permission applies to all subfolders
    inherit = db.Column(db.Boolean, default=True)

    # Relationships
    folder = relationship("Folder", back_populates="permissions")
    user = relationship("User", backref="folder_permissions")
