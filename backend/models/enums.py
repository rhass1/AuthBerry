#! /usr/bin/env python3


import enum
from sqlalchemy import Enum as SQLAlchemyEnum


class UserRole(enum.Enum):
    ADMIN = 'admin'
    USER = 'user'


class SecretType(enum.Enum):
    PLAINTEXT = 'plaintext'
    IMAGE = 'image'  # Combined type for PNG and JPG


# SQL Alchemy Enum types for direct use in models
user_role_enum = SQLAlchemyEnum(
    UserRole.ADMIN.value,
    UserRole.USER.value,
    name='user_role'
)

secret_type_enum = SQLAlchemyEnum(
    SecretType.PLAINTEXT.value,
    SecretType.IMAGE.value,
    name='secret_type_enum'
)
