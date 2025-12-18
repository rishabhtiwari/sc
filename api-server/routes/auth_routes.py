#!/usr/bin/env python3
"""
Authentication Routes - Proxy to auth-service
Proxies all authentication and user management requests to the auth-service
"""

import logging
import os
import requests
from flask import Blueprint, request, jsonify

# Create blueprint
auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

# Auth service configuration
AUTH_SERVICE_HOST = os.getenv('AUTH_SERVICE_HOST', 'auth-service')
AUTH_SERVICE_PORT = os.getenv('AUTH_SERVICE_PORT', '8098')
AUTH_SERVICE_URL = f'http://{AUTH_SERVICE_HOST}:{AUTH_SERVICE_PORT}'
AUTH_SERVICE_TIMEOUT = 30


def proxy_to_auth_service(path, method='GET', json_data=None, params=None):
    """
    Proxy request to auth-service
    
    Args:
        path: API path (e.g., '/api/auth/login')
        method: HTTP method
        json_data: JSON data for POST/PUT requests
        params: Query parameters
        
    Returns:
        Flask response
    """
    try:
        url = f"{AUTH_SERVICE_URL}{path}"
        
        # Forward all headers from the original request
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}
        
        logger.info(f"Proxying {method} {path} to auth-service: {url}")
        
        # Make request to auth-service
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=AUTH_SERVICE_TIMEOUT)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=json_data, params=params, timeout=AUTH_SERVICE_TIMEOUT)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=json_data, params=params, timeout=AUTH_SERVICE_TIMEOUT)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=params, timeout=AUTH_SERVICE_TIMEOUT)
        else:
            return jsonify({'error': f'Unsupported method: {method}'}), 400
        
        # Return response from auth-service
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to auth-service: {url}")
        return jsonify({'error': 'Auth service timeout'}), 504
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to auth-service: {url}")
        return jsonify({'error': 'Auth service unavailable'}), 503
    except Exception as e:
        logger.error(f"Error proxying to auth-service: {str(e)}")
        return jsonify({'error': f'Auth service error: {str(e)}'}), 500


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Proxy: Login user"""
    return proxy_to_auth_service('/api/auth/login', method='POST', json_data=request.get_json())


@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Proxy: Logout user"""
    return proxy_to_auth_service('/api/auth/logout', method='POST')


@auth_bp.route('/auth/verify', methods=['POST'])
def verify():
    """Proxy: Verify token"""
    return proxy_to_auth_service('/api/auth/verify', method='POST')


@auth_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Proxy: Forgot password"""
    return proxy_to_auth_service('/api/auth/forgot-password', method='POST', json_data=request.get_json())


@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """Proxy: Reset password"""
    return proxy_to_auth_service('/api/auth/reset-password', method='POST', json_data=request.get_json())


# ============================================================================
# CUSTOMER MANAGEMENT ENDPOINTS
# ============================================================================

@auth_bp.route('/auth/customers/register', methods=['POST'])
def register_customer():
    """Proxy: Public customer registration"""
    return proxy_to_auth_service('/api/auth/customers/register', method='POST', json_data=request.get_json())


@auth_bp.route('/auth/customers', methods=['GET'])
def get_customers():
    """Proxy: Get all customers"""
    return proxy_to_auth_service('/api/auth/customers', method='GET', params=request.args)


@auth_bp.route('/auth/customers', methods=['POST'])
def create_customer():
    """Proxy: Create customer"""
    return proxy_to_auth_service('/api/auth/customers', method='POST', json_data=request.get_json())


@auth_bp.route('/auth/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Proxy: Get customer details"""
    return proxy_to_auth_service(f'/api/auth/customers/{customer_id}', method='GET')


@auth_bp.route('/auth/customers/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Proxy: Update customer"""
    return proxy_to_auth_service(f'/api/auth/customers/{customer_id}', method='PUT', json_data=request.get_json())


@auth_bp.route('/auth/customers/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Proxy: Delete customer"""
    return proxy_to_auth_service(f'/api/auth/customers/{customer_id}', method='DELETE')


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@auth_bp.route('/auth/users', methods=['GET'])
def get_users():
    """Proxy: Get all users"""
    return proxy_to_auth_service('/api/auth/users', method='GET', params=request.args)


@auth_bp.route('/auth/users', methods=['POST'])
def create_user():
    """Proxy: Create user"""
    return proxy_to_auth_service('/api/auth/users', method='POST', json_data=request.get_json())


@auth_bp.route('/auth/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Proxy: Get user details"""
    return proxy_to_auth_service(f'/api/auth/users/{user_id}', method='GET')


@auth_bp.route('/auth/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Proxy: Update user"""
    return proxy_to_auth_service(f'/api/auth/users/{user_id}', method='PUT', json_data=request.get_json())


@auth_bp.route('/auth/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Proxy: Delete user"""
    return proxy_to_auth_service(f'/api/auth/users/{user_id}', method='DELETE')


@auth_bp.route('/auth/users/<user_id>/reset-password', methods=['POST'])
def reset_user_password(user_id):
    """Proxy: Reset user password"""
    return proxy_to_auth_service(f'/api/auth/users/{user_id}/reset-password', method='POST', json_data=request.get_json())


@auth_bp.route('/auth/users/<user_id>/deactivate', methods=['POST'])
def deactivate_user(user_id):
    """Proxy: Deactivate user"""
    return proxy_to_auth_service(f'/api/auth/users/{user_id}/deactivate', method='POST')


# ============================================================================
# ROLE MANAGEMENT ENDPOINTS
# ============================================================================

@auth_bp.route('/auth/roles', methods=['GET'])
def get_roles():
    """Proxy: Get all roles"""
    return proxy_to_auth_service('/api/auth/roles', method='GET')


@auth_bp.route('/auth/roles/<role_id>', methods=['GET'])
def get_role(role_id):
    """Proxy: Get role details"""
    return proxy_to_auth_service(f'/api/auth/roles/{role_id}', method='GET')


@auth_bp.route('/auth/permissions', methods=['GET'])
def get_permissions():
    """Proxy: Get all permissions"""
    return proxy_to_auth_service('/api/auth/permissions', method='GET')


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@auth_bp.route('/auth/audit-logs', methods=['GET'])
def get_audit_logs():
    """Proxy: Get audit logs"""
    return proxy_to_auth_service('/api/auth/audit-logs', method='GET', params=request.args)


@auth_bp.route('/auth/audit-logs/<log_id>', methods=['GET'])
def get_audit_log(log_id):
    """Proxy: Get audit log details"""
    return proxy_to_auth_service(f'/api/auth/audit-logs/{log_id}', method='GET')

