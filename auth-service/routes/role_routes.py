"""
Role Routes
Handles role management endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from services.role_service import RoleService
from services.audit_service import AuditService
from middleware.auth_middleware import token_required, customer_admin_required

# Create blueprint
role_bp = Blueprint('role', __name__)

# Initialize services
role_service = RoleService()
audit_service = AuditService()

# Logger
logger = logging.getLogger(__name__)


@role_bp.route('/auth/roles', methods=['GET'])
@token_required
def get_roles():
    """Get list of roles (system + customer-specific)"""
    try:
        customer_id = request.current_user.get('customer_id')
        result = role_service.get_roles(customer_id)
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Get roles error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get roles'}), 500


@role_bp.route('/auth/roles/<role_id>', methods=['GET'])
@token_required
def get_role(role_id):
    """Get role details"""
    try:
        result = role_service.get_role(role_id)
        return jsonify(result), 200 if result['success'] else 404
    except Exception as e:
        logger.error(f"Get role error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get role'}), 500


@role_bp.route('/auth/roles', methods=['POST'])
@token_required
@customer_admin_required
def create_role():
    """Create a custom role (customer admin only)"""
    try:
        data = request.get_json()
        created_by = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')
        
        result = role_service.create_role(data, created_by, customer_id)
        
        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=created_by, action='create',
                resource_type='role', resource_id=result['role']['role_id'],
                metadata={'ip_address': request.remote_addr}
            )
        
        return jsonify(result), 201 if result['success'] else 400
    except Exception as e:
        logger.error(f"Create role error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create role'}), 500


@role_bp.route('/auth/roles/<role_id>', methods=['PUT'])
@token_required
@customer_admin_required
def update_role(role_id):
    """Update custom role (customer admin only)"""
    try:
        data = request.get_json()
        user_id = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')

        result = role_service.update_role(role_id, data)

        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=user_id, action='update',
                resource_type='role', resource_id=role_id, changes={'after': data},
                metadata={'ip_address': request.remote_addr}
            )

        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Update role error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update role'}), 500


@role_bp.route('/auth/roles/<role_id>', methods=['DELETE'])
@token_required
@customer_admin_required
def delete_role(role_id):
    """Delete custom role (customer admin only)"""
    try:
        user_id = request.current_user.get('user_id')
        customer_id = request.current_user.get('customer_id')

        result = role_service.delete_role(role_id)

        if result['success']:
            audit_service.log_action(
                customer_id=customer_id, user_id=user_id, action='delete',
                resource_type='role', resource_id=role_id,
                metadata={'ip_address': request.remote_addr}
            )

        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Delete role error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete role'}), 500


@role_bp.route('/auth/permissions', methods=['GET'])
@token_required
def get_permissions():
    """Get all available permissions"""
    try:
        result = role_service.get_permissions()
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Get permissions error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get permissions'}), 500

