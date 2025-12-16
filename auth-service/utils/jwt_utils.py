"""
JWT Utilities
Token generation and validation
"""

import jwt
import logging
from datetime import datetime, timedelta
from config.settings import settings

logger = logging.getLogger(__name__)


def generate_token(user_id, customer_id, email, role_id, permissions):
    """
    Generate JWT token for authenticated user
    
    Args:
        user_id: User ID
        customer_id: Customer ID
        email: User email
        role_id: Role ID
        permissions: List of permission keys
        
    Returns:
        JWT token string
    """
    try:
        payload = {
            'user_id': user_id,
            'customer_id': customer_id,
            'email': email,
            'role_id': role_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token
        
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        raise


def verify_token(token):
    """
    Verify JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
        
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None


def decode_token_without_verification(token):
    """
    Decode token without verification (for debugging)
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return None

