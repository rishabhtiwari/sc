"""
Multi-Tenant Database Utilities
Helper functions for customer_id filtering and audit tracking in MongoDB operations
"""

from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# System customer ID for system-level operations (jobs, migrations, etc.)
SYSTEM_CUSTOMER_ID = 'customer_system'


def get_customer_id(customer_id: Optional[str] = None) -> str:
    """
    Get customer_id with fallback to system customer
    Enforces multi-tenancy by always returning a valid customer_id

    Args:
        customer_id: Customer ID (if None, returns SYSTEM_CUSTOMER_ID)

    Returns:
        Valid customer_id (never None)
    """
    if customer_id is None or customer_id == '':
        logger.debug(f"No customer_id provided, using system customer: {SYSTEM_CUSTOMER_ID}")
        return SYSTEM_CUSTOMER_ID
    return customer_id


def add_customer_filter(query: Dict[str, Any], customer_id: Optional[str]) -> Dict[str, Any]:
    """
    Add customer_id filter to MongoDB query
    Always adds customer_id filter (uses system customer if not provided)

    Args:
        query: Existing MongoDB query dictionary
        customer_id: Customer ID to filter by (uses SYSTEM_CUSTOMER_ID if None)

    Returns:
        Query dictionary with customer_id filter added
    """
    # Always enforce customer_id filter
    resolved_customer_id = get_customer_id(customer_id)
    query['customer_id'] = resolved_customer_id
    logger.debug(f"Added customer_id filter: {resolved_customer_id}")

    return query


def add_audit_fields(data: Dict[str, Any], is_update: bool = False,
                     customer_id: Optional[str] = None,
                     user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add audit tracking fields to data
    Always enforces customer_id for creates (uses system customer if not provided)

    Args:
        data: Data dictionary to add audit fields to
        is_update: If True, only adds updated_by and updated_at. If False, adds created_by and created_at as well
        customer_id: Customer ID (uses SYSTEM_CUSTOMER_ID if None for creates)
        user_id: User ID for audit tracking

    Returns:
        Data dictionary with audit fields added
    """
    now = datetime.utcnow()

    if is_update:
        # For updates, only set updated_by and updated_at
        if user_id:
            data['updated_by'] = user_id
        data['updated_at'] = now
        logger.debug(f"Added update audit fields: updated_by={user_id}, updated_at={now}")
    else:
        # For creates, ALWAYS set customer_id (enforce multi-tenancy)
        resolved_customer_id = get_customer_id(customer_id)
        data['customer_id'] = resolved_customer_id

        if user_id:
            data['created_by'] = user_id
            data['updated_by'] = user_id
        data['created_at'] = now
        data['updated_at'] = now

        # Add soft delete flag
        if 'is_deleted' not in data:
            data['is_deleted'] = False

        logger.debug(f"Added create audit fields: customer_id={resolved_customer_id}, created_by={user_id}, created_at={now}")

    return data


def build_multi_tenant_query(base_query: Optional[Dict[str, Any]] = None,
                             customer_id: Optional[str] = None,
                             include_deleted: bool = False) -> Dict[str, Any]:
    """
    Build a multi-tenant MongoDB query with customer_id filter and soft delete handling
    ALWAYS enforces customer_id filter (uses system customer if not provided)

    Args:
        base_query: Base query dictionary (optional)
        customer_id: Customer ID to filter by (uses SYSTEM_CUSTOMER_ID if None)
        include_deleted: If True, includes soft-deleted records. If False, excludes them

    Returns:
        Complete query dictionary with customer_id and soft delete filters
    """
    if base_query is None:
        query = {}
    else:
        query = base_query.copy()

    # ALWAYS add customer_id filter (enforce multi-tenancy)
    add_customer_filter(query, customer_id)

    # Add soft delete filter
    if not include_deleted:
        query['is_deleted'] = {'$ne': True}

    return query


def prepare_insert_document(data: Dict[str, Any],
                            customer_id: Optional[str] = None,
                            user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Prepare a document for insertion with all required multi-tenant fields
    ALWAYS enforces customer_id (uses system customer if not provided)

    Args:
        data: Document data
        customer_id: Customer ID (uses SYSTEM_CUSTOMER_ID if None)
        user_id: User ID for audit tracking

    Returns:
        Document with customer_id, audit fields, and is_deleted flag
    """
    # Add customer_id and audit fields (customer_id is always enforced)
    add_audit_fields(data, is_update=False, customer_id=customer_id, user_id=user_id)

    return data


def prepare_update_document(data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Prepare a document for update with audit fields
    
    Args:
        data: Update data
        user_id: User ID for audit tracking
        
    Returns:
        Document with updated_by and updated_at fields
    """
    # Add audit fields for update
    add_audit_fields(data, is_update=True, user_id=user_id)
    
    return data


def soft_delete_document(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Prepare update data for soft delete operation
    
    Args:
        user_id: User ID for audit tracking
        
    Returns:
        Update dictionary with is_deleted=True and audit fields
    """
    update_data = {
        'is_deleted': True,
        'deleted_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    if user_id:
        update_data['deleted_by'] = user_id
        update_data['updated_by'] = user_id
    
    logger.info(f"Soft delete prepared: user={user_id}")
    
    return update_data


def extract_user_context_from_request(request_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract user context (customer_id, user_id) from request data
    This is used when backend services receive requests from api-server
    
    Args:
        request_data: Request data dictionary
        
    Returns:
        Dictionary with customer_id and user_id
    """
    return {
        'customer_id': request_data.get('customer_id'),
        'user_id': request_data.get('user_id')
    }


def inject_user_context_to_headers(headers: Dict[str, str], 
                                   customer_id: Optional[str] = None,
                                   user_id: Optional[str] = None) -> Dict[str, str]:
    """
    Inject user context into HTTP headers for service-to-service communication
    
    Args:
        headers: Existing headers dictionary
        customer_id: Customer ID
        user_id: User ID
        
    Returns:
        Headers with X-Customer-ID and X-User-ID added
    """
    if customer_id:
        headers['X-Customer-ID'] = customer_id
    if user_id:
        headers['X-User-ID'] = user_id
    
    return headers


def extract_user_context_from_headers(headers) -> Dict[str, str]:
    """
    Extract user context from HTTP headers
    ALWAYS returns a valid customer_id (uses system customer if not in headers)

    Args:
        headers: Request headers (Flask request.headers or dict)

    Returns:
        Dictionary with customer_id (always present) and user_id (may be None)
    """
    customer_id = None
    user_id = None

    # Handle both Flask headers and dict
    if hasattr(headers, 'get'):
        # First, try to get from X-Customer-ID and X-User-ID headers
        customer_id = headers.get('X-Customer-ID')
        user_id = headers.get('X-User-ID')

        # If not present, try to extract from JWT token in Authorization header
        if not customer_id:
            auth_header = headers.get('Authorization')
            if auth_header:
                try:
                    # Extract token from "Bearer <token>" format
                    parts = auth_header.split()
                    if len(parts) == 2 and parts[0].lower() == 'bearer':
                        token = parts[1]

                        # Decode JWT token to extract customer_id and user_id
                        import jwt
                        import os

                        # Get JWT secret from environment (same as auth-service)
                        jwt_secret = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
                        jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')

                        try:
                            payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
                            customer_id = payload.get('customer_id')
                            user_id = payload.get('user_id')
                            logger.debug(f"Extracted from JWT: customer_id={customer_id}, user_id={user_id}")
                        except jwt.ExpiredSignatureError:
                            logger.warning("JWT token expired")
                        except jwt.InvalidTokenError as e:
                            logger.warning(f"Invalid JWT token: {str(e)}")
                        except Exception as e:
                            logger.error(f"Error decoding JWT token: {str(e)}")
                except Exception as e:
                    logger.error(f"Error extracting token from Authorization header: {str(e)}")

    # Enforce customer_id (use system customer if not provided)
    resolved_customer_id = get_customer_id(customer_id)

    return {
        'customer_id': resolved_customer_id,
        'user_id': user_id
    }

