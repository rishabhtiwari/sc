"""
Routes for health check endpoints
"""
from flask import Blueprint
from controllers.health_controller import HealthController

# Create blueprint
health_bp = Blueprint('health', __name__)

# Initialize controller
health_controller = HealthController()

# Health check endpoints
@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check"""
    return health_controller.health_check()

@health_bp.route('/status', methods=['GET'])
def service_status():
    """Detailed service status"""
    return health_controller.service_status()
