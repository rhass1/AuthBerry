#! /usr/bin/env python3


from sqlalchemy.orm import relationship
from backend.extensions import db


class SecretPermission(db.Model):
    __tablename__ = 'secret_permissions'

    secret_id = db.Column(
        db.Integer,
        db.ForeignKey('secure_secrets.secret_id', ondelete='CASCADE', onupdate='CASCADE'),
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

    # Relationships back to Secret and User
    secret = relationship("Secret", back_populates="permissions")
    user = relationship("User", back_populates="secret_permissions")


class UserSecretView(db.Model):
    """
    Stores each user's personal view of where a secret should appear in their folder structure.
    This allows users to organize shared secrets in their own folders without affecting others.
    """
    __tablename__ = 'user_secret_views'

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
    secret_id = db.Column(
        db.Integer,
        db.ForeignKey('secure_secrets.secret_id', ondelete='CASCADE', onupdate='CASCADE'),
        primary_key=True
    )
    folder_id = db.Column(
        db.Integer,
        db.ForeignKey('folders.folder_id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True
    )

    # When this view was created or last modified
    last_modified = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Relationships
    user = relationship("User", backref="secret_views")
    secret = relationship("Secret", backref="user_views")
    folder = relationship("Folder", back_populates="secret_views")

    @classmethod
    def get_user_view(cls, user_id, secret_id):
        """Get a user's view for a specific secret"""
        return cls.query.filter_by(user_id=user_id, secret_id=secret_id).first()

    @classmethod
    def set_user_view(cls, user_id, secret_id, folder_id):
        """Set or update a user's view for a specific secret"""
        view = cls.get_user_view(user_id, secret_id)
        if view:
            view.folder_id = folder_id
        else:
            view = cls(user_id=user_id, secret_id=secret_id, folder_id=folder_id)
            db.session.add(view)
        return view
