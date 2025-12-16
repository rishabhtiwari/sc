"""
Authentication Service
Handles user authentication, login, registration, and token management
"""

import logging
import uuid
from datetime import datetime, timedelta
from utils.mongodb_client import get_mongodb_client
from utils.jwt_utils import generate_token
from utils.password_utils import hash_password, verify_password, validate_password_strength
from config.settings import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self):
        self.db = get_mongodb_client()
    
    def login(self, email, password, ip_address=None, user_agent=None):
        """
        Authenticate user and generate JWT token
        
        Args:
            email: User email
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            dict: Login result with token and user info
        """
        try:
            # Find user by email
            user = self.db.users.find_one({'email': email, 'is_deleted': {'$ne': True}})
            
            if not user:
                logger.warning(f"Login attempt for non-existent user: {email}")
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }
            
            # Check if account is locked
            if user.get('account_locked_until'):
                if user['account_locked_until'] > datetime.utcnow():
                    return {
                        'success': False,
                        'error': 'Account is locked due to too many failed login attempts'
                    }
                else:
                    # Unlock account
                    self.db.users.update_one(
                        {'user_id': user['user_id']},
                        {'$set': {'account_locked_until': None, 'failed_login_attempts': 0}}
                    )
            
            # Check if account is active
            if user.get('status') != 'active':
                return {
                    'success': False,
                    'error': f'Account is {user.get("status")}'
                }
            
            # Verify password
            if not verify_password(password, user['password_hash']):
                # Increment failed login attempts
                failed_attempts = user.get('failed_login_attempts', 0) + 1
                update_data = {
                    'failed_login_attempts': failed_attempts,
                    'updated_at': datetime.utcnow()
                }
                
                # Lock account if too many failed attempts
                if failed_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                    lockout_until = datetime.utcnow() + timedelta(
                        minutes=settings.ACCOUNT_LOCKOUT_DURATION_MINUTES
                    )
                    update_data['account_locked_until'] = lockout_until
                    logger.warning(f"Account locked for user: {email}")
                
                self.db.users.update_one(
                    {'user_id': user['user_id']},
                    {'$set': update_data}
                )
                
                logger.warning(f"Failed login attempt for user: {email}")
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }
            
            # Get user role and permissions
            role = self.db.roles.find_one({'role_id': user['role_id']})
            if not role:
                logger.error(f"Role not found for user: {email}")
                return {
                    'success': False,
                    'error': 'User role not found'
                }
            
            permissions = role.get('permissions', [])
            
            # Generate JWT token
            token = generate_token(
                user_id=user['user_id'],
                customer_id=user['customer_id'],
                email=user['email'],
                role_id=user['role_id'],
                permissions=permissions
            )
            
            # Update user login info
            self.db.users.update_one(
                {'user_id': user['user_id']},
                {
                    '$set': {
                        'last_login_at': datetime.utcnow(),
                        'failed_login_attempts': 0,
                        'account_locked_until': None,
                        'updated_at': datetime.utcnow()
                    },
                    '$inc': {'login_count': 1}
                }
            )
            
            logger.info(f"✅ User logged in: {email}")
            
            # Return success response
            return {
                'success': True,
                'token': token,
                'user': {
                    'user_id': user['user_id'],
                    'customer_id': user['customer_id'],
                    'email': user['email'],
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'role_id': user['role_id'],
                    'role_name': role.get('role_name'),
                    'permissions': permissions
                }
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {
                'success': False,
                'error': 'Login failed'
            }
    
    def verify_token(self, token):
        """
        Verify JWT token and return user info
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Verification result with user info
        """
        from utils.jwt_utils import verify_token as jwt_verify
        
        try:
            payload = jwt_verify(token)
            
            if not payload:
                return {
                    'valid': False,
                    'error': 'Invalid or expired token'
                }
            
            # Verify user still exists and is active
            user = self.db.users.find_one({
                'user_id': payload['user_id'],
                'is_deleted': {'$ne': True}
            })
            
            if not user or user.get('status') != 'active':
                return {
                    'valid': False,
                    'error': 'User not found or inactive'
                }
            
            return {
                'valid': True,
                'user': payload
            }
            
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return {
                'valid': False,
                'error': 'Token verification failed'
            }
    
    def get_current_user(self, user_id):
        """
        Get current user details
        
        Args:
            user_id: User ID
            
        Returns:
            dict: User details
        """
        try:
            user = self.db.users.find_one(
                {'user_id': user_id, 'is_deleted': {'$ne': True}},
                {'password_hash': 0}  # Exclude password hash
            )
            
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Get role details
            role = self.db.roles.find_one({'role_id': user['role_id']})
            
            # Convert ObjectId to string
            if '_id' in user:
                user['_id'] = str(user['_id'])
            
            user['role_name'] = role.get('role_name') if role else None
            user['permissions'] = role.get('permissions', []) if role else []
            
            return {
                'success': True,
                'user': user
            }
            
        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get user details'
            }

