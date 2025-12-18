"""
User Service
Handles user management operations
"""

import logging
import uuid
from datetime import datetime
from utils.mongodb_client import get_mongodb_client
from utils.password_utils import hash_password, validate_password_strength
from config.settings import settings

logger = logging.getLogger(__name__)


class UserService:
    """Service for handling user operations"""
    
    def __init__(self):
        self.db = get_mongodb_client()
    
    def create_user(self, data, created_by, creator_customer_id):
        """
        Create a new user
        
        Args:
            data: User data
            created_by: User ID who is creating the user
            creator_customer_id: Customer ID of the creator
            
        Returns:
            dict: Created user
        """
        try:
            # Validate required fields
            required_fields = ['email', 'password', 'role_id']
            for field in required_fields:
                if field not in data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Validate password strength
            is_valid, error_msg = validate_password_strength(data['password'])
            if not is_valid:
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # Determine customer_id
            customer_id = data.get('customer_id', creator_customer_id)

            # Check if email already exists globally (across all customers)
            existing = self.db.users.find_one({
                'email': data['email'],
                'is_deleted': {'$ne': True}
            })

            if existing:
                return {
                    'success': False,
                    'error': 'Email already exists'
                }
            
            # Verify role exists
            role = self.db.roles.find_one({'role_id': data['role_id']})
            if not role:
                return {
                    'success': False,
                    'error': 'Invalid role_id'
                }
            
            # Hash password
            password_hash = hash_password(data['password'])
            
            # Create user document
            user = {
                'user_id': f"user_{uuid.uuid4().hex[:12]}",
                'customer_id': customer_id,
                'email': data['email'],
                'password_hash': password_hash,
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'role_id': data['role_id'],
                'status': data.get('status', 'active'),
                'email_verified': data.get('email_verified', False),
                'email_verification_token': None,
                'email_verification_expires_at': None,
                'password_reset_token': None,
                'password_reset_expires_at': None,
                'last_login_at': None,
                'login_count': 0,
                'failed_login_attempts': 0,
                'account_locked_until': None,
                'preferences': {
                    'language': data.get('language', 'en'),
                    'timezone': data.get('timezone', 'UTC'),
                    'theme': data.get('theme', 'light'),
                    'notifications': {
                        'email': True,
                        'browser': True
                    }
                },
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'created_by': created_by,
                'is_deleted': False
            }
            
            # Insert user
            self.db.users.insert_one(user)
            
            logger.info(f"✅ User created: {user['user_id']} ({user['email']})")
            
            # Remove password hash from response
            user_response = {k: v for k, v in user.items() if k != 'password_hash'}
            
            # Convert ObjectId to string
            if '_id' in user_response:
                user_response['_id'] = str(user_response['_id'])
            
            # Add role name
            user_response['role_name'] = role.get('role_name')
            
            return {
                'success': True,
                'user': user_response
            }
            
        except Exception as e:
            logger.error(f"Create user error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to create user'
            }
    
    def get_users(self, customer_id, page=1, page_size=20, filters=None):
        """
        Get list of users for a customer with pagination
        
        Args:
            customer_id: Customer ID
            page: Page number
            page_size: Items per page
            filters: Filter criteria
            
        Returns:
            dict: List of users with pagination info
        """
        try:
            # Build query
            query = {
                'customer_id': customer_id,
                'is_deleted': {'$ne': True}
            }
            
            if filters:
                if 'status' in filters:
                    query['status'] = filters['status']
                if 'role_id' in filters:
                    query['role_id'] = filters['role_id']
            
            # Get total count
            total = self.db.users.count_documents(query)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            
            # Get users (exclude password hash)
            users = list(
                self.db.users.find(query, {'password_hash': 0})
                .sort('created_at', -1)
                .skip(skip)
                .limit(page_size)
            )
            
            # Convert ObjectId to string and add role names
            for user in users:
                if '_id' in user:
                    user['_id'] = str(user['_id'])

                # Get role name
                role = self.db.roles.find_one({'role_id': user.get('role_id')})
                user['role_name'] = role.get('role_name') if role else None

                # Add is_active computed field based on status
                user['is_active'] = user.get('status') == 'active'
            
            return {
                'success': True,
                'users': users,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': (total + page_size - 1) // page_size
                }
            }
            
        except Exception as e:
            logger.error(f"Get users error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get users'
            }
    
    def get_user(self, user_id):
        """
        Get user by ID
        
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
            
            # Convert ObjectId to string
            if '_id' in user:
                user['_id'] = str(user['_id'])

            # Get role name
            role = self.db.roles.find_one({'role_id': user.get('role_id')})
            user['role_name'] = role.get('role_name') if role else None

            # Add is_active computed field based on status
            user['is_active'] = user.get('status') == 'active'

            return {
                'success': True,
                'user': user
            }
            
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get user'
            }
    
    def update_user(self, user_id, data):
        """
        Update user
        
        Args:
            user_id: User ID
            data: Update data
            
        Returns:
            dict: Updated user
        """
        try:
            # Check if user exists
            user = self.db.users.find_one({
                'user_id': user_id,
                'is_deleted': {'$ne': True}
            })
            
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Build update document
            update_data = {'updated_at': datetime.utcnow()}
            
            # Update allowed fields
            allowed_fields = [
                'first_name', 'last_name', 'role_id', 'status', 'preferences'
            ]
            
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            # Update user
            self.db.users.update_one(
                {'user_id': user_id},
                {'$set': update_data}
            )
            
            # Get updated user
            updated_user = self.db.users.find_one(
                {'user_id': user_id},
                {'password_hash': 0}
            )
            
            logger.info(f"✅ User updated: {user_id}")
            
            # Convert ObjectId to string
            if '_id' in updated_user:
                updated_user['_id'] = str(updated_user['_id'])
            
            # Get role name
            role = self.db.roles.find_one({'role_id': updated_user.get('role_id')})
            updated_user['role_name'] = role.get('role_name') if role else None
            
            return {
                'success': True,
                'user': updated_user
            }
            
        except Exception as e:
            logger.error(f"Update user error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to update user'
            }

    def delete_user(self, user_id):
        """
        Delete user (soft delete)

        Args:
            user_id: User ID

        Returns:
            dict: Delete result
        """
        try:
            # Check if user exists
            user = self.db.users.find_one({
                'user_id': user_id,
                'is_deleted': {'$ne': True}
            })

            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }

            # Soft delete user
            self.db.users.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'is_deleted': True,
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            logger.info(f"✅ User deleted: {user_id}")

            return {
                'success': True,
                'message': 'User deleted successfully'
            }

        except Exception as e:
            logger.error(f"Delete user error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to delete user'
            }

    def reset_password(self, user_id, new_password):
        """
        Reset user password

        Args:
            user_id: User ID
            new_password: New password

        Returns:
            dict: Reset result
        """
        try:
            # Validate password strength
            is_valid, error_msg = validate_password_strength(new_password)
            if not is_valid:
                return {
                    'success': False,
                    'error': error_msg
                }

            # Check if user exists
            user = self.db.users.find_one({
                'user_id': user_id,
                'is_deleted': {'$ne': True}
            })

            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }

            # Hash new password
            password_hash = hash_password(new_password)

            # Update password
            self.db.users.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'password_hash': password_hash,
                        'password_reset_token': None,
                        'password_reset_expires_at': None,
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            logger.info(f"✅ Password reset for user: {user_id}")

            return {
                'success': True,
                'message': 'Password reset successfully'
            }

        except Exception as e:
            logger.error(f"Reset password error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to reset password'
            }

    def suspend_user(self, user_id):
        """
        Suspend user account

        Args:
            user_id: User ID

        Returns:
            dict: Suspend result
        """
        try:
            result = self.db.users.update_one(
                {'user_id': user_id, 'is_deleted': {'$ne': True}},
                {
                    '$set': {
                        'status': 'suspended',
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            if result.matched_count == 0:
                return {
                    'success': False,
                    'error': 'User not found'
                }

            logger.info(f"✅ User suspended: {user_id}")

            return {
                'success': True,
                'message': 'User suspended successfully'
            }

        except Exception as e:
            logger.error(f"Suspend user error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to suspend user'
            }

    def activate_user(self, user_id):
        """
        Activate user account

        Args:
            user_id: User ID

        Returns:
            dict: Activate result
        """
        try:
            result = self.db.users.update_one(
                {'user_id': user_id, 'is_deleted': {'$ne': True}},
                {
                    '$set': {
                        'status': 'active',
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            if result.matched_count == 0:
                return {
                    'success': False,
                    'error': 'User not found'
                }

            logger.info(f"✅ User activated: {user_id}")

            return {
                'success': True,
                'message': 'User activated successfully'
            }

        except Exception as e:
            logger.error(f"Activate user error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to activate user'
            }

