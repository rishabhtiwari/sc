"""
Authentication Routes
Handles login, token verification, and user info endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from middleware.auth_middleware import token_required

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize service
auth_service = AuthService()

# Logger
logger = logging.getLogger(__name__)


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Login endpoint - authenticate user and return JWT token
    
    Request body:
        {
            "email": "admin@newsautomation.com",
            "password": "admin123"
        }
    
    Response:
        {
            "success": true,
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "user": {
                "user_id": "user_...",
                "customer_id": "customer_...",
                "email": "admin@newsautomation.com",
                "first_name": "Admin",
                "last_name": "User",
                "role_id": "role_super_admin",
                "role_name": "Super Admin",
                "permissions": [...]
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Get client info
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        # Authenticate user
        result = auth_service.login(email, password, ip_address, user_agent)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500


@auth_bp.route('/auth/verify', methods=['POST'])
def verify():
    """
    Verify token endpoint - check if token is valid
    
    Request body:
        {
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    
    Response:
        {
            "valid": true,
            "user": {
                "user_id": "user_...",
                "customer_id": "customer_...",
                "email": "admin@newsautomation.com",
                "role_id": "role_super_admin",
                "permissions": [...]
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                'valid': False,
                'error': 'Token is required'
            }), 400
        
        token = data['token']
        
        # Verify token
        result = auth_service.verify_token(token)
        
        if result.get('valid'):
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({
            'valid': False,
            'error': 'Token verification failed'
        }), 500


@auth_bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """
    Get current user info
    
    Response:
        {
            "success": true,
            "user": {
                "user_id": "user_...",
                "customer_id": "customer_...",
                "email": "admin@newsautomation.com",
                "first_name": "Admin",
                "last_name": "User",
                "role_id": "role_super_admin",
                "role_name": "Super Admin",
                "permissions": [...]
            }
        }
    """
    try:
        user_id = request.current_user.get('user_id')
        
        # Get user details
        result = auth_service.get_current_user(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get user details'
        }), 500


@auth_bp.route('/auth/logout', methods=['POST'])
@token_required
def logout():
    """
    Logout endpoint - invalidate token (client-side only for JWT)
    
    Response:
        {
            "success": true,
            "message": "Logged out successfully"
        }
    """
    try:
        logger.info(f"User logged out: {request.current_user.get('email')}")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Logout failed'
        }), 500


# Health check endpoint
@auth_bp.route('/auth/health', methods=['GET'])
def health():
    """
    Health check endpoint
    
    Response:
        {
            "status": "healthy",
            "service": "auth-service",
            "timestamp": "2025-12-16T10:30:00Z"
        }
    """
    from datetime import datetime
    
    return jsonify({
        'status': 'healthy',
        'service': 'auth-service',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

