"""
Audit Service
Handles audit logging operations
"""

import logging
import uuid
from datetime import datetime
from utils.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)


class AuditService:
    """Service for handling audit log operations"""
    
    def __init__(self):
        self.db = get_mongodb_client()
    
    def log_action(self, customer_id, user_id, action, resource_type, resource_id=None,
                   changes=None, metadata=None, status='success', error_message=None):
        """
        Log an audit action
        
        Args:
            customer_id: Customer ID
            user_id: User ID who performed the action
            action: Action performed (create, read, update, delete, etc.)
            resource_type: Type of resource (news, video, user, etc.)
            resource_id: ID of the affected resource
            changes: Before/after state for updates
            metadata: Additional metadata (IP, user agent, etc.)
            status: Action status (success, failure, error)
            error_message: Error message if action failed
            
        Returns:
            dict: Created audit log
        """
        try:
            # Create audit log document
            audit_log = {
                'log_id': f"log_{uuid.uuid4().hex[:16]}",
                'customer_id': customer_id,
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'changes': changes or {},
                'metadata': metadata or {},
                'status': status,
                'error_message': error_message,
                'timestamp': datetime.utcnow()
            }
            
            # Insert audit log
            self.db.audit_logs.insert_one(audit_log)
            
            logger.debug(f"Audit log created: {action} on {resource_type} by {user_id}")
            
            return {
                'success': True,
                'log_id': audit_log['log_id']
            }
            
        except Exception as e:
            logger.error(f"Create audit log error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to create audit log'
            }
    
    def get_audit_logs(self, customer_id, page=1, page_size=50, filters=None):
        """
        Get audit logs for a customer with pagination
        
        Args:
            customer_id: Customer ID
            page: Page number
            page_size: Items per page
            filters: Filter criteria
            
        Returns:
            dict: List of audit logs with pagination info
        """
        try:
            # Build query
            query = {'customer_id': customer_id}
            
            if filters:
                if 'user_id' in filters:
                    query['user_id'] = filters['user_id']
                if 'action' in filters:
                    query['action'] = filters['action']
                if 'resource_type' in filters:
                    query['resource_type'] = filters['resource_type']
                if 'resource_id' in filters:
                    query['resource_id'] = filters['resource_id']
                if 'status' in filters:
                    query['status'] = filters['status']
                if 'start_date' in filters and 'end_date' in filters:
                    query['timestamp'] = {
                        '$gte': filters['start_date'],
                        '$lte': filters['end_date']
                    }
            
            # Get total count
            total = self.db.audit_logs.count_documents(query)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            
            # Get audit logs
            logs = list(
                self.db.audit_logs.find(query)
                .sort('timestamp', -1)
                .skip(skip)
                .limit(page_size)
            )
            
            # Convert ObjectId to string and enrich with user info
            for log in logs:
                if '_id' in log:
                    log['_id'] = str(log['_id'])
                
                # Get user email
                user = self.db.users.find_one(
                    {'user_id': log.get('user_id')},
                    {'email': 1, 'first_name': 1, 'last_name': 1}
                )
                if user:
                    log['user_email'] = user.get('email')
                    log['user_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            
            return {
                'success': True,
                'logs': logs,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': (total + page_size - 1) // page_size
                }
            }
            
        except Exception as e:
            logger.error(f"Get audit logs error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get audit logs'
            }
    
    def get_audit_log(self, log_id):
        """
        Get audit log by ID
        
        Args:
            log_id: Log ID
            
        Returns:
            dict: Audit log details
        """
        try:
            log = self.db.audit_logs.find_one({'log_id': log_id})
            
            if not log:
                return {
                    'success': False,
                    'error': 'Audit log not found'
                }
            
            # Convert ObjectId to string
            if '_id' in log:
                log['_id'] = str(log['_id'])
            
            # Get user info
            user = self.db.users.find_one(
                {'user_id': log.get('user_id')},
                {'email': 1, 'first_name': 1, 'last_name': 1}
            )
            if user:
                log['user_email'] = user.get('email')
                log['user_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            
            return {
                'success': True,
                'log': log
            }
            
        except Exception as e:
            logger.error(f"Get audit log error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get audit log'
            }

