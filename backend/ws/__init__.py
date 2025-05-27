# WebSocket module initialization
from flask import Blueprint

# Create a blueprint for WebSocket event handlers
ws_bp = Blueprint('ws', __name__)

# Import WebSocket event handler files after the blueprint is created
# to avoid circular imports 