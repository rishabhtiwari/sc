"""
Audit Routes
Handles audit log endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime
from services.audit_service import AuditService
from middleware.auth_middleware import token_required, permission_required

# Create blueprint
audit_bp = Blueprint('audit', __name__)

# Initialize service
audit_service = AuditService()

# Logger
logger = logging.getLogger(__name__)


@audit_bp.route('/audit-logs', methods=['GET'])
@token_required
@permission_required('audit.view')
def get_audit_logs():
    """Get audit logs for current customer"""
    try:
        customer_id = request.current_user.get('customer_id')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        
        filters = {}
        if request.args.get('user_id'):
            filters['user_id'] = request.args.get('user_id')
        if request.args.get('action'):
            filters['action'] = request.args.get('action')
        if request.args.get('resource_type'):
            filters['resource_type'] = request.args.get('resource_type')
        if request.args.get('resource_id'):
            filters['resource_id'] = request.args.get('resource_id')
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('start_date') and request.args.get('end_date'):
            try:
                filters['start_date'] = datetime.fromisoformat(request.args.get('start_date'))
                filters['end_date'] = datetime.fromisoformat(request.args.get('end_date'))
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date format'}), 400
        
        result = audit_service.get_audit_logs(customer_id, page, page_size, filters)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Get audit logs error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get audit logs'}), 500


@audit_bp.route('/audit-logs/<log_id>', methods=['GET'])
@token_required
@permission_required('audit.view')
def get_audit_log(log_id):
    """Get audit log details"""
    try:
        result = audit_service.get_audit_log(log_id)
        
        # Check if log belongs to same customer
        if result['success']:
            log_customer_id = result['log'].get('customer_id')
            current_customer_id = request.current_user.get('customer_id')
            role_id = request.current_user.get('role_id')
            
            if role_id != 'role_super_admin' and log_customer_id != current_customer_id:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        return jsonify(result), 200 if result['success'] else 404
        
    except Exception as e:
        logger.error(f"Get audit log error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get audit log'}), 500

