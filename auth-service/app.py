"""
Auth Service - Main Application
Handles authentication, user management, and authorization
"""

import logging
from flask import Flask, jsonify
from flask_cors import CORS
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Import blueprints
from routes.auth_routes import auth_bp
from routes.customer_routes import customer_bp
from routes.user_routes import user_bp
from routes.role_routes import role_bp
from routes.audit_routes import audit_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(customer_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(role_bp, url_prefix='/api')
app.register_blueprint(audit_bp, url_prefix='/api')

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'auth-service',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': [
                'POST /api/auth/login',
                'POST /api/auth/verify',
                'GET /api/auth/me',
                'POST /api/auth/logout',
                'GET /api/auth/health'
            ],
            'customers': [
                'POST /api/customers',
                'GET /api/customers',
                'GET /api/customers/:id',
                'PUT /api/customers/:id',
                'DELETE /api/customers/:id'
            ],
            'users': [
                'POST /api/users',
                'GET /api/users',
                'GET /api/users/:id',
                'PUT /api/users/:id',
                'DELETE /api/users/:id',
                'POST /api/users/:id/reset-password',
                'POST /api/users/:id/suspend',
                'POST /api/users/:id/activate'
            ],
            'roles': [
                'GET /api/roles',
                'GET /api/roles/:id',
                'POST /api/roles',
                'PUT /api/roles/:id',
                'DELETE /api/roles/:id',
                'GET /api/permissions'
            ],
            'audit': [
                'GET /api/audit-logs',
                'GET /api/audit-logs/:id'
            ]
        }
    }), 200


# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    from datetime import datetime
    
    return jsonify({
        'status': 'healthy',
        'service': 'auth-service',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info(f"🚀 Starting Auth Service on port {settings.PORT}")
    logger.info(f"📊 MongoDB: {settings.MONGODB_HOST}:{settings.MONGODB_PORT}/{settings.MONGODB_DATABASE}")
    logger.info(f"🔐 JWT Algorithm: {settings.JWT_ALGORITHM}")
    
    app.run(
        host='0.0.0.0',
        port=settings.PORT,
        debug=settings.DEBUG
    )

