"""
Role Service
Handles role management operations
"""

import logging
import uuid
from datetime import datetime
from utils.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)


class RoleService:
    """Service for handling role operations"""
    
    def __init__(self):
        self.db = get_mongodb_client()
    
    def get_roles(self, customer_id=None):
        """
        Get list of roles
        
        Args:
            customer_id: Customer ID (None for system roles)
            
        Returns:
            dict: List of roles
        """
        try:
            # Build query - get system roles and customer-specific roles
            if customer_id:
                query = {
                    '$or': [
                        {'is_system_role': True},
                        {'customer_id': customer_id}
                    ],
                    'is_deleted': {'$ne': True}
                }
            else:
                query = {
                    'is_system_role': True,
                    'is_deleted': {'$ne': True}
                }
            
            # Get roles
            roles = list(self.db.roles.find(query).sort('role_name', 1))
            
            # Convert ObjectId to string
            for role in roles:
                if '_id' in role:
                    role['_id'] = str(role['_id'])
            
            return {
                'success': True,
                'roles': roles
            }
            
        except Exception as e:
            logger.error(f"Get roles error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get roles'
            }
    
    def get_role(self, role_id):
        """
        Get role by ID
        
        Args:
            role_id: Role ID
            
        Returns:
            dict: Role details
        """
        try:
            role = self.db.roles.find_one({
                'role_id': role_id,
                'is_deleted': {'$ne': True}
            })
            
            if not role:
                return {
                    'success': False,
                    'error': 'Role not found'
                }
            
            # Convert ObjectId to string
            if '_id' in role:
                role['_id'] = str(role['_id'])
            
            return {
                'success': True,
                'role': role
            }
            
        except Exception as e:
            logger.error(f"Get role error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get role'
            }
    
    def create_role(self, data, created_by, customer_id):
        """
        Create a custom role (customer-specific)
        
        Args:
            data: Role data
            created_by: User ID who is creating the role
            customer_id: Customer ID
            
        Returns:
            dict: Created role
        """
        try:
            # Validate required fields
            required_fields = ['role_name', 'slug']
            for field in required_fields:
                if field not in data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Check if slug already exists for this customer
            existing = self.db.roles.find_one({
                'customer_id': customer_id,
                'slug': data['slug'],
                'is_deleted': {'$ne': True}
            })
            
            if existing:
                return {
                    'success': False,
                    'error': 'Role slug already exists for this customer'
                }
            
            # Create role document
            role = {
                'role_id': f"role_{uuid.uuid4().hex[:12]}",
                'customer_id': customer_id,
                'role_name': data['role_name'],
                'slug': data['slug'],
                'description': data.get('description'),
                'permissions': data.get('permissions', []),
                'is_system_role': False,
                'is_default': data.get('is_default', False),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'created_by': created_by,
                'is_deleted': False
            }
            
            # Insert role
            self.db.roles.insert_one(role)
            
            logger.info(f"✅ Role created: {role['role_id']} ({role['role_name']})")
            
            # Convert ObjectId to string
            if '_id' in role:
                role['_id'] = str(role['_id'])
            
            return {
                'success': True,
                'role': role
            }
            
        except Exception as e:
            logger.error(f"Create role error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to create role'
            }
    
    def update_role(self, role_id, data):
        """
        Update role (only custom roles can be updated)
        
        Args:
            role_id: Role ID
            data: Update data
            
        Returns:
            dict: Updated role
        """
        try:
            # Check if role exists and is not a system role
            role = self.db.roles.find_one({
                'role_id': role_id,
                'is_deleted': {'$ne': True}
            })
            
            if not role:
                return {
                    'success': False,
                    'error': 'Role not found'
                }
            
            if role.get('is_system_role'):
                return {
                    'success': False,
                    'error': 'Cannot update system roles'
                }
            
            # Build update document
            update_data = {'updated_at': datetime.utcnow()}
            
            # Update allowed fields
            allowed_fields = ['role_name', 'description', 'permissions', 'is_default']
            
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            # Update role
            self.db.roles.update_one(
                {'role_id': role_id},
                {'$set': update_data}
            )
            
            # Get updated role
            updated_role = self.db.roles.find_one({'role_id': role_id})
            
            logger.info(f"✅ Role updated: {role_id}")
            
            # Convert ObjectId to string
            if '_id' in updated_role:
                updated_role['_id'] = str(updated_role['_id'])
            
            return {
                'success': True,
                'role': updated_role
            }
            
        except Exception as e:
            logger.error(f"Update role error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to update role'
            }
    
    def delete_role(self, role_id):
        """
        Delete role (soft delete, only custom roles)
        
        Args:
            role_id: Role ID
            
        Returns:
            dict: Delete result
        """
        try:
            # Check if role exists and is not a system role
            role = self.db.roles.find_one({
                'role_id': role_id,
                'is_deleted': {'$ne': True}
            })
            
            if not role:
                return {
                    'success': False,
                    'error': 'Role not found'
                }
            
            if role.get('is_system_role'):
                return {
                    'success': False,
                    'error': 'Cannot delete system roles'
                }
            
            # Check if any users have this role
            user_count = self.db.users.count_documents({
                'role_id': role_id,
                'is_deleted': {'$ne': True}
            })
            
            if user_count > 0:
                return {
                    'success': False,
                    'error': f'Cannot delete role: {user_count} users have this role'
                }
            
            # Soft delete role
            self.db.roles.update_one(
                {'role_id': role_id},
                {
                    '$set': {
                        'is_deleted': True,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"✅ Role deleted: {role_id}")
            
            return {
                'success': True,
                'message': 'Role deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Delete role error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to delete role'
            }
    
    def get_permissions(self):
        """
        Get all available permissions
        
        Returns:
            dict: List of permissions
        """
        try:
            permissions = list(self.db.permissions.find().sort('category', 1))
            
            # Convert ObjectId to string
            for permission in permissions:
                if '_id' in permission:
                    permission['_id'] = str(permission['_id'])
            
            # Group by category
            grouped = {}
            for perm in permissions:
                category = perm.get('category', 'other')
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(perm)
            
            return {
                'success': True,
                'permissions': permissions,
                'grouped': grouped
            }
            
        except Exception as e:
            logger.error(f"Get permissions error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get permissions'
            }

