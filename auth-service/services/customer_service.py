"""
Customer Service
Handles customer management operations
"""

import logging
import uuid
from datetime import datetime
from utils.mongodb_client import get_mongodb_client
from config.settings import settings

logger = logging.getLogger(__name__)


class CustomerService:
    """Service for handling customer operations"""
    
    def __init__(self):
        self.db = get_mongodb_client()
    
    def create_customer(self, data, created_by):
        """
        Create a new customer
        
        Args:
            data: Customer data
            created_by: User ID who is creating the customer
            
        Returns:
            dict: Created customer
        """
        try:
            # Validate required fields
            required_fields = ['company_name', 'slug']
            for field in required_fields:
                if field not in data:
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Check if slug already exists
            existing = self.db.customers.find_one({'slug': data['slug']})
            if existing:
                return {
                    'success': False,
                    'error': 'Customer slug already exists'
                }
            
            # Create customer document
            customer = {
                'customer_id': f"customer_{uuid.uuid4().hex[:12]}",
                'company_name': data['company_name'],
                'slug': data['slug'],
                'status': data.get('status', 'trial'),
                'subscription': {
                    'plan_type': data.get('plan_type', 'free'),
                    'status': data.get('subscription_status', 'trial'),
                    'trial_ends_at': data.get('trial_ends_at'),
                    'started_at': datetime.utcnow(),
                    'ends_at': data.get('subscription_ends_at')
                },
                'limits': {
                    'max_users': data.get('max_users', 5),
                    'max_videos_per_month': data.get('max_videos_per_month', 100),
                    'max_storage_gb': data.get('max_storage_gb', 10)
                },
                'features': data.get('features', [
                    'news_fetching',
                    'video_generation',
                    'youtube_upload'
                ]),
                'billing': {
                    'email': data.get('billing_email'),
                    'address': data.get('billing_address', {})
                },
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'created_by': created_by,
                'is_deleted': False
            }
            
            # Insert customer
            self.db.customers.insert_one(customer)
            
            logger.info(f"✅ Customer created: {customer['customer_id']}")
            
            # Convert ObjectId to string
            if '_id' in customer:
                customer['_id'] = str(customer['_id'])
            
            return {
                'success': True,
                'customer': customer
            }
            
        except Exception as e:
            logger.error(f"Create customer error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to create customer'
            }
    
    def get_customers(self, page=1, page_size=20, filters=None):
        """
        Get list of customers with pagination
        
        Args:
            page: Page number
            page_size: Items per page
            filters: Filter criteria
            
        Returns:
            dict: List of customers with pagination info
        """
        try:
            # Build query
            query = {'is_deleted': {'$ne': True}}
            
            if filters:
                if 'status' in filters:
                    query['status'] = filters['status']
                if 'plan_type' in filters:
                    query['subscription.plan_type'] = filters['plan_type']
            
            # Get total count
            total = self.db.customers.count_documents(query)
            
            # Calculate pagination
            skip = (page - 1) * page_size
            
            # Get customers
            customers = list(
                self.db.customers.find(query)
                .sort('created_at', -1)
                .skip(skip)
                .limit(page_size)
            )
            
            # Convert ObjectId to string
            for customer in customers:
                if '_id' in customer:
                    customer['_id'] = str(customer['_id'])
            
            return {
                'success': True,
                'customers': customers,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': (total + page_size - 1) // page_size
                }
            }
            
        except Exception as e:
            logger.error(f"Get customers error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get customers'
            }
    
    def get_customer(self, customer_id):
        """
        Get customer by ID
        
        Args:
            customer_id: Customer ID
            
        Returns:
            dict: Customer details
        """
        try:
            customer = self.db.customers.find_one({
                'customer_id': customer_id,
                'is_deleted': {'$ne': True}
            })
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Convert ObjectId to string
            if '_id' in customer:
                customer['_id'] = str(customer['_id'])
            
            return {
                'success': True,
                'customer': customer
            }
            
        except Exception as e:
            logger.error(f"Get customer error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get customer'
            }
    
    def update_customer(self, customer_id, data):
        """
        Update customer
        
        Args:
            customer_id: Customer ID
            data: Update data
            
        Returns:
            dict: Updated customer
        """
        try:
            # Check if customer exists
            customer = self.db.customers.find_one({
                'customer_id': customer_id,
                'is_deleted': {'$ne': True}
            })
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Build update document
            update_data = {'updated_at': datetime.utcnow()}
            
            # Update allowed fields
            allowed_fields = [
                'company_name', 'status', 'limits', 'features', 'billing'
            ]
            
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            # Update subscription fields
            if 'subscription' in data:
                for key, value in data['subscription'].items():
                    update_data[f'subscription.{key}'] = value
            
            # Update customer
            self.db.customers.update_one(
                {'customer_id': customer_id},
                {'$set': update_data}
            )
            
            # Get updated customer
            updated_customer = self.db.customers.find_one({'customer_id': customer_id})
            
            logger.info(f"✅ Customer updated: {customer_id}")
            
            # Convert ObjectId to string
            if '_id' in updated_customer:
                updated_customer['_id'] = str(updated_customer['_id'])
            
            return {
                'success': True,
                'customer': updated_customer
            }
            
        except Exception as e:
            logger.error(f"Update customer error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to update customer'
            }
    
    def delete_customer(self, customer_id):
        """
        Delete customer (soft delete)
        
        Args:
            customer_id: Customer ID
            
        Returns:
            dict: Delete result
        """
        try:
            # Check if customer exists
            customer = self.db.customers.find_one({
                'customer_id': customer_id,
                'is_deleted': {'$ne': True}
            })
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Soft delete customer
            self.db.customers.update_one(
                {'customer_id': customer_id},
                {
                    '$set': {
                        'is_deleted': True,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"✅ Customer deleted: {customer_id}")
            
            return {
                'success': True,
                'message': 'Customer deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Delete customer error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to delete customer'
            }

