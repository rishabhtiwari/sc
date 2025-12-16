"""
Customer Routes
Handles customer management endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from services.customer_service import CustomerService
from services.audit_service import AuditService
from middleware.auth_middleware import token_required, super_admin_required

# Create blueprint
customer_bp = Blueprint('customer', __name__)

# Initialize services
customer_service = CustomerService()
audit_service = AuditService()

# Logger
logger = logging.getLogger(__name__)


@customer_bp.route('/customers', methods=['POST'])
@token_required
@super_admin_required
def create_customer():
    """Create a new customer (super admin only)"""
    try:
        data = request.get_json()
        created_by = request.current_user.get('user_id')
        
        result = customer_service.create_customer(data, created_by)
        
        # Log audit
        if result['success']:
            audit_service.log_action(
                customer_id=result['customer']['customer_id'],
                user_id=created_by,
                action='create',
                resource_type='customer',
                resource_id=result['customer']['customer_id'],
                metadata={'ip_address': request.remote_addr}
            )
        
        return jsonify(result), 201 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Create customer error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create customer'}), 500


@customer_bp.route('/customers', methods=['GET'])
@token_required
@super_admin_required
def get_customers():
    """Get list of customers (super admin only)"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('plan_type'):
            filters['plan_type'] = request.args.get('plan_type')
        
        result = customer_service.get_customers(page, page_size, filters)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Get customers error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get customers'}), 500


@customer_bp.route('/customers/<customer_id>', methods=['GET'])
@token_required
def get_customer(customer_id):
    """Get customer details"""
    try:
        # Super admin can view any customer, others can only view their own
        user_customer_id = request.current_user.get('customer_id')
        role_id = request.current_user.get('role_id')
        
        if role_id != 'role_super_admin' and user_customer_id != customer_id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        result = customer_service.get_customer(customer_id)
        
        return jsonify(result), 200 if result['success'] else 404
        
    except Exception as e:
        logger.error(f"Get customer error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get customer'}), 500


@customer_bp.route('/customers/<customer_id>', methods=['PUT'])
@token_required
@super_admin_required
def update_customer(customer_id):
    """Update customer (super admin only)"""
    try:
        data = request.get_json()
        user_id = request.current_user.get('user_id')
        
        result = customer_service.update_customer(customer_id, data)
        
        # Log audit
        if result['success']:
            audit_service.log_action(
                customer_id=customer_id,
                user_id=user_id,
                action='update',
                resource_type='customer',
                resource_id=customer_id,
                changes={'after': data},
                metadata={'ip_address': request.remote_addr}
            )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Update customer error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update customer'}), 500


@customer_bp.route('/customers/<customer_id>', methods=['DELETE'])
@token_required
@super_admin_required
def delete_customer(customer_id):
    """Delete customer (super admin only)"""
    try:
        user_id = request.current_user.get('user_id')
        
        result = customer_service.delete_customer(customer_id)
        
        # Log audit
        if result['success']:
            audit_service.log_action(
                customer_id=customer_id,
                user_id=user_id,
                action='delete',
                resource_type='customer',
                resource_id=customer_id,
                metadata={'ip_address': request.remote_addr}
            )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Delete customer error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete customer'}), 500

