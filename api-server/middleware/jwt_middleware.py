"""
JWT Middleware for API Server
Extracts JWT token, decodes it, and injects customer_id/user_id into request headers
This ensures all backend services receive proper multi-tenant context
"""

import logging
import jwt
import os
from flask import request, g, jsonify
from functools import wraps

logger = logging.getLogger(__name__)

# JWT Configuration (same as auth-service)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')

# System customer fallback
SYSTEM_CUSTOMER_ID = os.getenv('SYSTEM_CUSTOMER_ID', 'customer_system')

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = [
    '/',
    '/api/health',
    '/health',
    '/api/auth/login',
    '/api/auth/register',
    '/api/auth/verify',
]

# Endpoint patterns that don't require authentication (for file serving)
PUBLIC_ENDPOINT_PATTERNS = [
    '/api/news/videos/shorts/',  # Video file downloads
    '/api/news/videos/',  # Config video/thumbnail downloads
    '/api/news/audio/serve/',  # Audio file downloads
    '/api/templates/preview/video/',  # Template preview video downloads
    '/api/templates/preview/thumbnail/',  # Template preview thumbnail downloads
]


def extract_and_inject_jwt_context():
    """
    Before request middleware that:
    1. Extracts JWT token from Authorization header
    2. Decodes it to get customer_id and user_id
    3. Injects these into Flask's g object and request headers
    4. Enforces authentication for all non-public endpoints

    This runs before every request automatically.
    """
    # Skip authentication for OPTIONS requests (CORS preflight)
    if request.method == 'OPTIONS':
        return

    # Skip authentication for public endpoints
    if request.path in PUBLIC_ENDPOINTS:
        return

    # Skip authentication for public endpoint patterns (prefix match)
    for pattern in PUBLIC_ENDPOINT_PATTERNS:
        if request.path.startswith(pattern):
            logger.debug(f"🔓 Public endpoint pattern matched: {pattern} for path={request.path}")
            return

    customer_id = None
    user_id = None
    token_valid = False
    token = None

    # Try to extract from Authorization header first
    auth_header = request.headers.get('Authorization')

    # If no Authorization header, try query parameter (for media files in <audio>/<video> tags)
    if not auth_header:
        token = request.args.get('token')
        if token:
            logger.debug(f"🔑 Token found in query parameter for path={request.path}")

    if auth_header:
        try:
            # Extract token from "Bearer <token>" format
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]

        except Exception as e:
            logger.error(f"❌ Error extracting token from Authorization header: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Invalid authorization header',
                'code': 'INVALID_AUTH_HEADER'
            }), 401

    # Decode JWT token (from either header or query parameter)
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            customer_id = payload.get('customer_id')
            user_id = payload.get('user_id')
            token_valid = True

            logger.debug(f"✅ JWT decoded: customer_id={customer_id}, user_id={user_id}, path={request.path}")

        except jwt.ExpiredSignatureError:
            logger.warning(f"⚠️ JWT token expired for path={request.path}")
            return jsonify({
                'success': False,
                'error': 'Token expired. Please login again.',
                'code': 'TOKEN_EXPIRED'
            }), 401

        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ Invalid JWT token for path={request.path}: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Invalid token. Please login again.',
                'code': 'INVALID_TOKEN'
            }), 401

        except Exception as e:
            logger.error(f"❌ Error decoding JWT token: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR'
            }), 401

    # If no valid token found, reject the request
    if not token_valid:
        logger.warning(f"🚫 No valid authentication token for path={request.path}")
        return jsonify({
            'success': False,
            'error': 'Authentication required. Please login.',
            'code': 'NO_TOKEN'
        }), 401

    # Inject into Flask's g object for use in route handlers
    g.customer_id = customer_id
    g.user_id = user_id

    # CRITICAL: Inject into request headers so they get forwarded to backend services
    # We need to modify the environ dict since request.headers is immutable
    if customer_id:
        request.environ['HTTP_X_CUSTOMER_ID'] = customer_id
    if user_id:
        request.environ['HTTP_X_USER_ID'] = user_id

    logger.debug(f"🔐 Request context: customer_id={customer_id}, user_id={user_id}, path={request.path}")


def get_request_headers_with_context():
    """
    Helper function to get headers with customer_id and user_id injected
    Use this when making requests to backend services

    Returns:
        dict: Headers with X-Customer-ID and X-User-ID
    """
    headers = {}

    # Get from Flask's g object (set by middleware)
    customer_id = getattr(g, 'customer_id', None)
    user_id = getattr(g, 'user_id', None)

    if customer_id:
        headers['X-Customer-ID'] = customer_id
    if user_id:
        headers['X-User-ID'] = user_id

    # Also forward Authorization header if present
    auth_header = request.headers.get('Authorization')
    if auth_header:
        headers['Authorization'] = auth_header

    return headers


def extract_user_context_from_headers(headers):
    """
    Extract user context (customer_id, user_id) from request headers
    Use this in route handlers to get user context

    Args:
        headers: Flask request.headers object

    Returns:
        dict: Dictionary with customer_id and user_id
    """
    # First try to get from Flask's g object (set by middleware)
    customer_id = getattr(g, 'customer_id', None)
    user_id = getattr(g, 'user_id', None)

    # If not in g, try to extract from headers directly
    if not customer_id:
        customer_id = headers.get('X-Customer-ID')
    if not user_id:
        user_id = headers.get('X-User-ID')

    return {
        'customer_id': customer_id,
        'user_id': user_id
    }

