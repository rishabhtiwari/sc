"""
Health Routes - URL routing for health and monitoring endpoints
"""

from flask import Blueprint

from handlers.health_handler import HealthHandler

# Create blueprint for health routes
health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /api/health - Basic health check
    
    Returns:
        JSON response with health status
    """
    return HealthHandler.handle_health_check()


@health_bp.route('/status', methods=['GET'])
def detailed_status():
    """
    GET /api/status - Detailed system status
    
    Returns:
        JSON response with detailed system information
    """
    return HealthHandler.handle_detailed_status()


@health_bp.route('/ping', methods=['GET'])
def ping():
    """
    GET /api/ping - Simple connectivity test
    
    Returns:
        Simple pong response
    """
    return HealthHandler.handle_ping()


# Additional monitoring routes can be added here
@health_bp.route('/version', methods=['GET'])
def version():
    """
    GET /api/version - Get API version information
    
    Returns:
        JSON response with version details
    """
    import time

    from flask import (
        jsonify,
        current_app
    )
    
    return jsonify({
        "name": current_app.config.get('API_TITLE', 'iChat API Server'),
        "version": current_app.config.get('API_VERSION', '2.0.0'),
        "status": "active",
        "timestamp": int(time.time() * 1000)
    }), 200
