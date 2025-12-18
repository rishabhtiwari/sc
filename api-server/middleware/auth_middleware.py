"""
Authentication Middleware
Validates JWT tokens and injects user context into requests
"""

import logging
import requests
from functools import wraps
from flask import request, jsonify, g
import os

logger = logging.getLogger(__name__)

# Auth service URL
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://ichat-auth-service:8098')
AUTH_SERVICE_TIMEOUT = int(os.getenv('AUTH_SERVICE_TIMEOUT', '5'))


def extract_token_from_header():
    """
    Extract JWT token from Authorization header
    
    Returns:
        Token string or None
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    # Expected format: "Bearer <token>"
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def verify_token_with_auth_service(token):
    """
    Verify token with auth-service

    Args:
        token: JWT token string

    Returns:
        Dictionary with user info if valid, None otherwise
    """
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/api/auth/verify",
            headers={'Authorization': f'Bearer {token}'},
            timeout=AUTH_SERVICE_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                return data.get('user')

        return None

    except requests.exceptions.Timeout:
        logger.error(f"Auth service timeout after {AUTH_SERVICE_TIMEOUT}s")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to auth service")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None


def token_required(f):
    """
    Decorator to require valid JWT token for endpoint
    Injects user context into Flask's g object
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route():
            customer_id = g.customer_id
            user_id = g.user_id
            return jsonify({'message': 'Success'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract token from header
        token = extract_token_from_header()
        
        if not token:
            logger.warning("No token provided in request")
            return jsonify({
                'success': False,
                'error': 'Authentication required. Please provide a valid token.'
            }), 401
        
        # Verify token with auth service
        user_info = verify_token_with_auth_service(token)
        
        if not user_info:
            logger.warning("Invalid or expired token")
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 401
        
        # Inject user context into Flask's g object
        g.customer_id = user_info.get('customer_id')
        g.user_id = user_info.get('user_id')
        g.email = user_info.get('email')
        g.role_id = user_info.get('role_id')
        g.permissions = user_info.get('permissions', [])
        g.user_info = user_info
        
        logger.info(f"Authenticated request: user={g.user_id}, customer={g.customer_id}")
        
        # Call the actual route function
        return f(*args, **kwargs)
    
    return decorated


def permission_required(permission):
    """
    Decorator to require specific permission for endpoint
    Must be used after @token_required
    
    Args:
        permission: Permission string (e.g., 'news.create', 'video.edit')
        
    Usage:
        @app.route('/news', methods=['POST'])
        @token_required
        @permission_required('news.create')
        def create_news():
            return jsonify({'message': 'News created'})
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check if user context exists (token_required should be called first)
            if not hasattr(g, 'permissions'):
                logger.error("permission_required used without token_required")
                return jsonify({
                    'success': False,
                    'error': 'Authentication required'
                }), 401
            
            # Check if user has the required permission
            if permission not in g.permissions:
                logger.warning(f"User {g.user_id} lacks permission: {permission}")
                return jsonify({
                    'success': False,
                    'error': f'Permission denied. Required permission: {permission}'
                }), 403
            
            logger.info(f"Permission check passed: {permission} for user {g.user_id}")
            
            # Call the actual route function
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def optional_auth(f):
    """
    Decorator for endpoints that work with or without authentication
    If token is provided and valid, injects user context
    If no token or invalid token, continues without user context
    
    Usage:
        @app.route('/public-or-private')
        @optional_auth
        def flexible_route():
            if hasattr(g, 'customer_id'):
                # User is authenticated
                return jsonify({'message': 'Authenticated', 'customer': g.customer_id})
            else:
                # User is not authenticated
                return jsonify({'message': 'Public access'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Try to extract token
        token = extract_token_from_header()
        
        if token:
            # Verify token
            user_info = verify_token_with_auth_service(token)
            
            if user_info:
                # Inject user context
                g.customer_id = user_info.get('customer_id')
                g.user_id = user_info.get('user_id')
                g.email = user_info.get('email')
                g.role_id = user_info.get('role_id')
                g.permissions = user_info.get('permissions', [])
                g.user_info = user_info
                
                logger.info(f"Optional auth: Authenticated user={g.user_id}, customer={g.customer_id}")
            else:
                logger.info("Optional auth: Invalid token, proceeding without authentication")
        else:
            logger.info("Optional auth: No token provided, proceeding without authentication")
        
        # Call the actual route function
        return f(*args, **kwargs)
    
    return decorated


def get_user_context():
    """
    Helper function to get current user context from Flask's g object
    
    Returns:
        Dictionary with customer_id, user_id, email, role_id, permissions
        Returns None if no user context exists
    """
    if not hasattr(g, 'customer_id'):
        return None
    
    return {
        'customer_id': g.customer_id,
        'user_id': g.user_id,
        'email': g.email,
        'role_id': g.role_id,
        'permissions': g.permissions
    }


def inject_user_context_to_request_data(data=None):
    """
    Helper function to inject user context into request data
    Adds customer_id, created_by, updated_by fields
    
    Args:
        data: Dictionary to inject context into (optional, uses request.json if not provided)
        
    Returns:
        Dictionary with injected user context
    """
    if data is None:
        data = request.get_json() or {}
    
    if hasattr(g, 'customer_id'):
        data['customer_id'] = g.customer_id
        data['created_by'] = g.user_id
        data['updated_by'] = g.user_id
    
    return data

