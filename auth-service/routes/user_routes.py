"""
User Routes
Handles user management endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from services.user_service import UserService
from services.audit_service import AuditService
from middleware.auth_middleware import token_required, customer_admin_required, permission_required

# Create blueprint
user_bp = Blueprint('user', __name__)

# Initialize services
user_service = UserService()
audit_service = AuditService()

# Logger
logger = logging.getLogger(__name__)


@user_bp.route('/auth/users', methods=['POST'])
@token_required
@permission_required('user.create')
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        created_by = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')
        
        result = user_service.create_user(data, created_by, customer_id)
        
        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=created_by, action='create',
                resource_type='user', resource_id=result['user']['user_id'],
                metadata={'ip_address': request.remote_addr}
            )
        
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        logger.error(f"Create user error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create user'}), 500


@user_bp.route('/auth/users', methods=['GET'])
@token_required
@permission_required('user.view')
def get_users():
    """Get list of users for current customer"""
    try:
        customer_id = request.current_user.get('customer_id')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('role_id'):
            filters['role_id'] = request.args.get('role_id')
        
        result = user_service.get_users(customer_id, page, page_size, filters)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get users'}), 500


@user_bp.route('/auth/users/<user_id>', methods=['GET'])
@token_required
@permission_required('user.view')
def get_user(user_id):
    """Get user details"""
    try:
        result = user_service.get_user(user_id)
        
        if result['success']:
            user_customer_id = result['user'].get('customer_id')
            current_customer_id = request.current_user.get('customer_id')
            role_id = request.current_user.get('role_id')
            
            if role_id != 'role_super_admin' and user_customer_id != current_customer_id:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        return jsonify(result), 200 if result['success'] else 404
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get user'}), 500


@user_bp.route('/auth/users/<user_id>', methods=['PUT'])
@token_required
@permission_required('user.edit')
def update_user(user_id):
    """Update user"""
    try:
        data = request.get_json()
        current_user_id = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')
        
        result = user_service.update_user(user_id, data)
        
        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=current_user_id, action='update',
                resource_type='user', resource_id=user_id, changes={'after': data},
                metadata={'ip_address': request.remote_addr}
            )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update user'}), 500


@user_bp.route('/auth/users/<user_id>', methods=['DELETE'])
@token_required
@permission_required('user.delete')
def delete_user(user_id):
    """Delete user"""
    try:
        current_user_id = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')
        
        if user_id == current_user_id:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        result = user_service.delete_user(user_id)
        
        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=current_user_id, action='delete',
                resource_type='user', resource_id=user_id,
                metadata={'ip_address': request.remote_addr}
            )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete user'}), 500


@user_bp.route('/auth/users/<user_id>/reset-password', methods=['POST'])
@token_required
@permission_required('user.edit')
def reset_password(user_id):
    """Reset user password"""
    try:
        data = request.get_json()
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({'success': False, 'error': 'new_password is required'}), 400
        
        current_user_id = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')
        
        result = user_service.reset_password(user_id, new_password)
        
        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=current_user_id, action='update',
                resource_type='user', resource_id=user_id, changes={'action': 'password_reset'},
                metadata={'ip_address': request.remote_addr}
            )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to reset password'}), 500


@user_bp.route('/auth/users/<user_id>/suspend', methods=['POST'])
@token_required
@customer_admin_required
def suspend_user(user_id):
    """Suspend user account"""
    try:
        current_user_id = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')
        
        if user_id == current_user_id:
            return jsonify({'success': False, 'error': 'Cannot suspend your own account'}), 400
        
        result = user_service.suspend_user(user_id)
        
        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=current_user_id, action='update',
                resource_type='user', resource_id=user_id, changes={'action': 'suspend'},
                metadata={'ip_address': request.remote_addr}
            )
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Suspend user error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to suspend user'}), 500


@user_bp.route('/auth/users/<user_id>/activate', methods=['POST'])
@token_required
@customer_admin_required
def activate_user(user_id):
    """Activate user account"""
    try:
        current_user_id = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')

        result = user_service.activate_user(user_id)

        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=current_user_id, action='update',
                resource_type='user', resource_id=user_id, changes={'action': 'activate'},
                metadata={'ip_address': request.remote_addr}
            )

        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Activate user error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to activate user'}), 500


@user_bp.route('/auth/users/<user_id>/deactivate', methods=['POST'])
@token_required
@customer_admin_required
def deactivate_user(user_id):
    """Toggle user active status (deactivate if active, activate if inactive)"""
    try:
        current_user_id = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')

        if user_id == current_user_id:
            return jsonify({'success': False, 'error': 'Cannot deactivate your own account'}), 400

        # Get user to check current status
        user = user_service.get_user(user_id)
        if not user.get('success'):
            return jsonify(user), 400

        # Toggle status
        is_active = user.get('user', {}).get('is_active', True)
        if is_active:
            result = user_service.suspend_user(user_id)
            action = 'suspend'
        else:
            result = user_service.activate_user(user_id)
            action = 'activate'

        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=current_user_id, action='update',
                resource_type='user', resource_id=user_id, changes={'action': action},
                metadata={'ip_address': request.remote_addr}
            )

        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Deactivate user error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to toggle user status'}), 500

