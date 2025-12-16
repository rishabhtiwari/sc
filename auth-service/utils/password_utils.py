"""
Password Utilities
Password hashing and validation
"""

import bcrypt
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


def hash_password(password):
    """
    Hash password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    try:
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise


def verify_password(password, password_hash):
    """
    Verify password against hash
    
    Args:
        password: Plain text password
        password_hash: Hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False


def validate_password_strength(password):
    """
    Validate password strength
    
    Args:
        password: Plain text password
        
    Returns:
        Tuple (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
    
    # Add more validation rules as needed
    # - Must contain uppercase
    # - Must contain lowercase
    # - Must contain number
    # - Must contain special character
    
    return True, None

