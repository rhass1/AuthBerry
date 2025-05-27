#! /usr/bin/env python3


import datetime
from datetime import timezone
from sqlalchemy.orm import relationship
from backend.extensions import db


# Association table for the many-to-many relationship between secrets and tags
secret_tags = db.Table(
    'secret_tags',
    db.Column('secret_id', db.Integer, db.ForeignKey('secure_secrets.secret_id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.tag_id', ondelete='CASCADE'), primary_key=True)
)

# Association table for the many-to-many relationship between folders and tags
folder_tags = db.Table(
    'folder_tags',
    db.Column('folder_id', db.Integer, db.ForeignKey('folders.folder_id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.tag_id', ondelete='CASCADE'), primary_key=True)
)


class Tag(db.Model):
    __tablename__ = 'tags'

    tag_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.datetime.now(timezone.utc))
    
    # Index for faster tag lookups
    __table_args__ = (
        db.Index('idx_tag_name_owner', 'name', 'owner_id', unique=True),
    )

    # Relationships
    owner = relationship("User", backref="owned_tags")
    secrets = relationship(
        "Secret",
        secondary=secret_tags,
        back_populates="tags"
    ) 
    # Add relationship to folders
    folders = relationship(
        "Folder",
        secondary=folder_tags,
        back_populates="tags"
    ) 
