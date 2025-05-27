#! /usr/bin/env python3

from flask import jsonify
from backend.models.user import User

def check_user_exists(user_id):
    """
    Check if a user exists in the database.
    
    Args:
        user_id (int): The ID of the user to check.
    
    Returns:
        User: The user object if found.
    
    Raises:
        HTTPException: 404 error if user not found.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return user 
