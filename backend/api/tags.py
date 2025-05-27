#! /usr/bin/env python3


from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from backend.models.tag import Tag
from backend.extensions import db
from backend.api.utils import check_user_exists

tags_bp = Blueprint('tags', __name__, url_prefix='/api/tags')


@tags_bp.route('/', methods=['GET'])
@jwt_required()
def get_tags():
    """Retrieves all tags belonging to the current user."""
    current_user_id = get_jwt_identity()
    
    check_user_exists(current_user_id)
    
    tags = Tag.query.filter_by(owner_id=current_user_id).all()
    
    return jsonify({
        'success': True,
        'data': [
            {
                'id': tag.tag_id,
                'name': tag.name,
                'created_time': tag.created_time.isoformat()
            } for tag in tags
        ]
    }), 200


@tags_bp.route('/', methods=['POST'])
@jwt_required()
def create_tag():
    """Creates a new tag for the current user."""
    current_user_id = get_jwt_identity()
    
    check_user_exists(current_user_id)
    
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({
            'success': False,
            'message': 'Tag name is required'
        }), 400
    
    tag_name = data.get('name').strip()
    
    if not tag_name:
        return jsonify({
            'success': False,
            'message': 'Tag name cannot be empty'
        }), 400
    
    if len(tag_name) > 50:
        return jsonify({
            'success': False,
            'message': 'Tag name cannot exceed 50 characters'
        }), 400
    
    existing_tag = Tag.query.filter_by(owner_id=current_user_id, name=tag_name).first()
    if existing_tag:
        return jsonify({
            'success': False,
            'message': 'A tag with this name already exists'
        }), 409
    
    tag = Tag(
        name=tag_name,
        owner_id=current_user_id
    )
    
    try:
        db.session.add(tag)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': tag.tag_id,
                'name': tag.name,
                'created_time': tag.created_time.isoformat()
            }
        }), 201
    
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'A tag with this name already exists'
        }), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating tag: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to create tag'
        }), 500


@tags_bp.route('/<int:tag_id>', methods=['DELETE'])
@jwt_required()
def delete_tag(tag_id):
    """Deletes a tag owned by the current user."""
    current_user_id = get_jwt_identity()
    
    check_user_exists(current_user_id)
    
    tag = Tag.query.filter_by(tag_id=tag_id, owner_id=current_user_id).first()
    
    if not tag:
        return jsonify({
            'success': False,
            'message': 'Tag not found'
        }), 404
    
    try:
        db.session.delete(tag)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag deleted successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting tag: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete tag'
        }), 500
