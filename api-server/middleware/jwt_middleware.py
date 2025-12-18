"""
JWT Middleware for API Server
Extracts JWT token, decodes it, and injects customer_id/user_id into request headers
This ensures all backend services receive proper multi-tenant context
"""

import logging
import jwt
import os
from flask import request, g
from functools import wraps

logger = logging.getLogger(__name__)

# JWT Configuration (same as auth-service)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')

# System customer fallback
SYSTEM_CUSTOMER_ID = os.getenv('SYSTEM_CUSTOMER_ID', 'customer_system')


def extract_and_inject_jwt_context():
    """
    Before request middleware that:
    1. Extracts JWT token from Authorization header
    2. Decodes it to get customer_id and user_id
    3. Injects these into Flask's g object and request headers
    
    This runs before every request automatically.
    """
    # Skip for health check and root endpoints
    if request.path in ['/', '/api/health', '/health']:
        return
    
    customer_id = None
    user_id = None
    
    # Try to extract from Authorization header
    auth_header = request.headers.get('Authorization')
    
    if auth_header:
        try:
            # Extract token from "Bearer <token>" format
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                
                # Decode JWT token
                try:
                    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                    customer_id = payload.get('customer_id')
                    user_id = payload.get('user_id')
                    
                    logger.debug(f"✅ JWT decoded: customer_id={customer_id}, user_id={user_id}, path={request.path}")
                    
                except jwt.ExpiredSignatureError:
                    logger.warning(f"⚠️ JWT token expired for path={request.path}")
                except jwt.InvalidTokenError as e:
                    logger.warning(f"⚠️ Invalid JWT token for path={request.path}: {str(e)}")
                except Exception as e:
                    logger.error(f"❌ Error decoding JWT token: {str(e)}")
                    
        except Exception as e:
            logger.error(f"❌ Error extracting token from Authorization header: {str(e)}")
    
    # If no customer_id from JWT, check if already in headers (from UI)
    if not customer_id:
        customer_id = request.headers.get('X-Customer-ID')
    
    if not user_id:
        user_id = request.headers.get('X-User-ID')
    
    # Use system customer as fallback if still no customer_id
    if not customer_id:
        customer_id = SYSTEM_CUSTOMER_ID
        logger.debug(f"🔧 No customer_id found, using system customer: {SYSTEM_CUSTOMER_ID}")
    
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

