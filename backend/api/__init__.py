#! /usr/bin/env python3

from flask import Blueprint, jsonify, current_app
from backend.extensions import db
import time

# Create main API blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Docker health checks and monitoring.
    Returns the health status of the application and its dependencies.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "AuthBerry_Backup API",
        "checks": {
            "database": "unknown",
            "tpm": "unknown"
        }
    }
    
    # Check database connectivity
    try:
        db.engine.execute('SELECT 1')
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = "unhealthy"
        current_app.logger.error(f"Database health check failed: {str(e)}")
    
    # Check TPM availability (basic check)
    try:
        import os
        tpm_devices = ['/dev/tpmrm0', '/dev/tpm0']
        tpm_available = any(os.path.exists(device) for device in tpm_devices)
        health_status["checks"]["tpm"] = "healthy" if tpm_available else "unavailable"
    except Exception as e:
        health_status["checks"]["tpm"] = "error"
        current_app.logger.warning(f"TPM health check failed: {str(e)}")
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code

@api_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint for basic connectivity checks."""
    return jsonify({"message": "pong", "timestamp": time.time()}), 200
