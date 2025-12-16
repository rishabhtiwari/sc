"""
Authentication Middleware
Decorators for protecting routes with JWT authentication and permissions
"""

import logging
from functools import wraps
from flask import request, jsonify
from utils.jwt_utils import verify_token

logger = logging.getLogger(__name__)


def token_required(f):
    """
    Decorator to protect routes with JWT authentication
    Adds current_user to request object
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # Format: "Bearer <token>"
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({
                    'error': 'Invalid authorization header format',
                    'status': 'error'
                }), 401
        
        if not token:
            return jsonify({
                'error': 'Authentication token is missing',
                'status': 'error'
            }), 401
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            return jsonify({
                'error': 'Invalid or expired token',
                'status': 'error'
            }), 401
        
        # Add user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated


def permission_required(permission_key):
    """
    Decorator to protect routes requiring specific permission
    Must be used after @token_required
    
    Args:
        permission_key: Permission key (e.g., 'news.create')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(request, 'current_user'):
                return jsonify({
                    'error': 'Authentication required',
                    'status': 'error'
                }), 401
            
            # Get user permissions
            user_permissions = request.current_user.get('permissions', [])
            
            # Check if user has required permission
            if permission_key not in user_permissions:
                logger.warning(
                    f"Permission denied: User {request.current_user.get('email')} "
                    f"attempted to access {permission_key}"
                )
                return jsonify({
                    'error': f'Permission denied: {permission_key} required',
                    'status': 'error'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def super_admin_required(f):
    """
    Decorator to protect routes requiring super admin role
    Must be used after @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if user is authenticated
        if not hasattr(request, 'current_user'):
            return jsonify({
                'error': 'Authentication required',
                'status': 'error'
            }), 401
        
        # Check if user has super admin role
        role_id = request.current_user.get('role_id')
        if role_id != 'role_super_admin':
            logger.warning(
                f"Super admin access denied: User {request.current_user.get('email')} "
                f"with role {role_id} attempted to access super admin endpoint"
            )
            return jsonify({
                'error': 'Super admin access required',
                'status': 'error'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated


def customer_admin_required(f):
    """
    Decorator to protect routes requiring customer admin role
    Must be used after @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if user is authenticated
        if not hasattr(request, 'current_user'):
            return jsonify({
                'error': 'Authentication required',
                'status': 'error'
            }), 401
        
        # Check if user has customer admin or super admin role
        role_id = request.current_user.get('role_id')
        if role_id not in ['role_super_admin', 'role_customer_admin']:
            logger.warning(
                f"Customer admin access denied: User {request.current_user.get('email')} "
                f"with role {role_id} attempted to access customer admin endpoint"
            )
            return jsonify({
                'error': 'Customer admin access required',
                'status': 'error'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated

