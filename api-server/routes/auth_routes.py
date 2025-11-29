#!/usr/bin/env python3
"""
Authentication Routes - User authentication and authorization
Provides JWT-based authentication for the API server
"""

import logging
import os
import jwt
import datetime
from functools import wraps
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# Create blueprint
auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# In-memory user store (replace with database in production)
# Format: {username: {password_hash, role, ...}}
USERS = {
    'admin': {
        'password_hash': generate_password_hash('admin123'),  # Change in production!
        'role': 'admin',
        'email': 'admin@newsautomation.com'
    },
    'user': {
        'password_hash': generate_password_hash('user123'),  # Change in production!
        'role': 'user',
        'email': 'user@newsautomation.com'
    }
}


def generate_token(username, role):
    """
    Generate JWT token for authenticated user
    
    Args:
        username: Username
        role: User role
        
    Returns:
        JWT token string
    """
    payload = {
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token):
    """
    Verify JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


def token_required(f):
    """
    Decorator to protect routes with JWT authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Format: "Bearer <token>"
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """
    Decorator to protect routes requiring admin role
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Login endpoint - authenticate user and return JWT token
    
    Request body:
        {
            "username": "admin",
            "password": "admin123"
        }
    
    Response:
        {
            "success": true,
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "user": {
                "username": "admin",
                "role": "admin",
                "email": "admin@newsautomation.com"
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Check if user exists
        user = USERS.get(username)
        if not user:
            logger.warning(f"Login attempt for non-existent user: {username}")
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Verify password
        if not check_password_hash(user['password_hash'], password):
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Generate token
        token = generate_token(username, user['role'])
        
        logger.info(f"✅ User logged in: {username}")
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'username': username,
                'role': user['role'],
                'email': user.get('email', '')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/auth/verify', methods=['GET'])
@token_required
def verify():
    """
    Verify token endpoint - check if token is valid
    
    Response:
        {
            "valid": true,
            "user": {
                "username": "admin",
                "role": "admin"
            }
        }
    """
    return jsonify({
        'valid': True,
        'user': request.current_user
    }), 200


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
    logger.info(f"User logged out: {request.current_user.get('username')}")
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@auth_bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """
    Get current user info
    
    Response:
        {
            "username": "admin",
            "role": "admin",
            "email": "admin@newsautomation.com"
        }
    """
    username = request.current_user.get('username')
    user = USERS.get(username)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'username': username,
        'role': user['role'],
        'email': user.get('email', '')
    }), 200


@auth_bp.route('/auth/users', methods=['GET'])
@admin_required
def get_users():
    """
    Get all users (admin only)
    
    Response:
        {
            "users": [
                {
                    "username": "admin",
                    "role": "admin",
                    "email": "admin@newsautomation.com"
                }
            ]
        }
    """
    users_list = [
        {
            'username': username,
            'role': user['role'],
            'email': user.get('email', '')
        }
        for username, user in USERS.items()
    ]
    
    return jsonify({'users': users_list}), 200


# ============================================================================
# EXAMPLE PROTECTED ENDPOINT
# ============================================================================

@auth_bp.route('/auth/protected', methods=['GET'])
@token_required
def protected_route():
    """
    Example protected route - requires authentication
    """
    return jsonify({
        'message': 'This is a protected route',
        'user': request.current_user
    }), 200


@auth_bp.route('/auth/admin-only', methods=['GET'])
@admin_required
def admin_only_route():
    """
    Example admin-only route - requires admin role
    """
    return jsonify({
        'message': 'This is an admin-only route',
        'user': request.current_user
    }), 200

