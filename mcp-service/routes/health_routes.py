"""
Health check routes for MCP service
"""
from flask import Blueprint, jsonify
import time
import os
from controllers.health_controller import HealthController

# Create health blueprint
health_bp = Blueprint('health', __name__)

# Initialize controller
health_controller = HealthController()

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return health_controller.health_check()

@health_bp.route('/status', methods=['GET'])
def detailed_status():
    """Detailed service status endpoint"""
    return health_controller.detailed_status()

@health_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({
        "status": "ok",
        "message": "pong",
        "timestamp": int(time.time() * 1000)
    }), 200
