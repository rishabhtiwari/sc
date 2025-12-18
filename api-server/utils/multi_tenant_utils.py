"""
Multi-Tenant Utilities
Helper functions for customer_id filtering and audit tracking
"""

from datetime import datetime
from typing import Dict, Any, Optional
from flask import g
import logging

logger = logging.getLogger(__name__)

# System customer ID for system-level operations
SYSTEM_CUSTOMER_ID = 'customer_system'


def get_customer_id(customer_id: Optional[str] = None) -> str:
    """
    Get customer_id with fallback to system customer
    Enforces multi-tenancy by always returning a valid customer_id

    Args:
        customer_id: Customer ID (if None, tries g.customer_id, then falls back to SYSTEM_CUSTOMER_ID)

    Returns:
        Valid customer_id (never None)
    """
    if customer_id is None or customer_id == '':
        # Try to get from Flask request context
        customer_id = getattr(g, 'customer_id', None)

    if customer_id is None or customer_id == '':
        logger.debug(f"No customer_id provided, using system customer: {SYSTEM_CUSTOMER_ID}")
        return SYSTEM_CUSTOMER_ID

    return customer_id


def add_customer_filter(query: Dict[str, Any], customer_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add customer_id filter to MongoDB query
    Always adds customer_id filter (uses system customer if not provided)

    Args:
        query: Existing MongoDB query dictionary
        customer_id: Customer ID to filter by (uses g.customer_id if not provided, then SYSTEM_CUSTOMER_ID)

    Returns:
        Query dictionary with customer_id filter added
    """
    # Always enforce customer_id filter
    resolved_customer_id = get_customer_id(customer_id)
    query['customer_id'] = resolved_customer_id
    logger.debug(f"Added customer_id filter: {resolved_customer_id}")

    return query


def add_audit_fields(data: Dict[str, Any], is_update: bool = False, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add audit tracking fields to data
    
    Args:
        data: Data dictionary to add audit fields to
        is_update: If True, only adds updated_by and updated_at. If False, adds created_by and created_at as well
        user_id: User ID to use (uses g.user_id if not provided)
        
    Returns:
        Data dictionary with audit fields added
    """
    if user_id is None:
        user_id = getattr(g, 'user_id', None)
    
    now = datetime.utcnow()
    
    if is_update:
        # For updates, only set updated_by and updated_at
        if user_id:
            data['updated_by'] = user_id
        data['updated_at'] = now
        logger.debug(f"Added update audit fields: updated_by={user_id}, updated_at={now}")
    else:
        # For creates, set both created and updated fields
        if user_id:
            data['created_by'] = user_id
            data['updated_by'] = user_id
        data['created_at'] = now
        data['updated_at'] = now
        logger.debug(f"Added create audit fields: created_by={user_id}, created_at={now}")
    
    return data


def add_customer_and_audit_fields(data: Dict[str, Any], is_update: bool = False,
                                   customer_id: Optional[str] = None,
                                   user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add both customer_id and audit fields to data

    Args:
        data: Data dictionary to add fields to
        is_update: If True, only adds updated_by and updated_at. If False, adds created_by and created_at as well
        customer_id: Customer ID to use (uses g.customer_id if not provided, then SYSTEM_CUSTOMER_ID)
        user_id: User ID to use (uses g.user_id if not provided)

    Returns:
        Data dictionary with customer_id and audit fields added
    """
    if user_id is None:
        user_id = getattr(g, 'user_id', None)

    # Add customer_id (only for creates, not updates) - ALWAYS enforce customer_id
    if not is_update:
        resolved_customer_id = get_customer_id(customer_id)
        data['customer_id'] = resolved_customer_id
        logger.debug(f"Added customer_id: {resolved_customer_id}")

    # Add audit fields
    add_audit_fields(data, is_update=is_update, user_id=user_id)

    return data


def build_multi_tenant_query(base_query: Optional[Dict[str, Any]] = None,
                             customer_id: Optional[str] = None,
                             include_deleted: bool = False) -> Dict[str, Any]:
    """
    Build a multi-tenant MongoDB query with customer_id filter and soft delete handling
    ALWAYS enforces customer_id filter (uses system customer if not provided)

    Args:
        base_query: Base query dictionary (optional)
        customer_id: Customer ID to filter by (uses g.customer_id if not provided, then SYSTEM_CUSTOMER_ID)
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
        customer_id: Customer ID (uses g.customer_id if not provided, then SYSTEM_CUSTOMER_ID)
        user_id: User ID (uses g.user_id if not provided)

    Returns:
        Document with customer_id, audit fields, and is_deleted flag
    """
    # Add customer_id and audit fields (customer_id is ALWAYS enforced)
    add_customer_and_audit_fields(data, is_update=False, customer_id=customer_id, user_id=user_id)
    
    # Add soft delete flag
    if 'is_deleted' not in data:
        data['is_deleted'] = False
    
    return data


def prepare_update_document(data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Prepare a document for update with audit fields
    
    Args:
        data: Update data
        user_id: User ID (uses g.user_id if not provided)
        
    Returns:
        Document with updated_by and updated_at fields
    """
    # Add audit fields for update
    add_audit_fields(data, is_update=True, user_id=user_id)
    
    return data


def soft_delete_document(customer_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Prepare update data for soft delete operation
    
    Args:
        customer_id: Customer ID (for logging)
        user_id: User ID (uses g.user_id if not provided)
        
    Returns:
        Update dictionary with is_deleted=True and audit fields
    """
    if user_id is None:
        user_id = getattr(g, 'user_id', None)
    
    update_data = {
        'is_deleted': True,
        'deleted_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    if user_id:
        update_data['deleted_by'] = user_id
        update_data['updated_by'] = user_id
    
    logger.info(f"Soft delete prepared: user={user_id}, customer={customer_id}")
    
    return update_data


def get_current_user_context() -> Dict[str, Any]:
    """
    Get current user context from Flask's g object
    
    Returns:
        Dictionary with customer_id, user_id, email, role_id, permissions
        Returns empty dict if no user context exists
    """
    if not hasattr(g, 'customer_id'):
        return {}
    
    return {
        'customer_id': getattr(g, 'customer_id', None),
        'user_id': getattr(g, 'user_id', None),
        'email': getattr(g, 'email', None),
        'role_id': getattr(g, 'role_id', None),
        'permissions': getattr(g, 'permissions', [])
    }


def check_permission(permission: str) -> bool:
    """
    Check if current user has a specific permission
    
    Args:
        permission: Permission string to check (e.g., 'news.create')
        
    Returns:
        True if user has permission, False otherwise
    """
    permissions = getattr(g, 'permissions', [])
    return permission in permissions


def log_audit_action(action: str, resource_type: str, resource_id: str, 
                     details: Optional[Dict[str, Any]] = None):
    """
    Log an audit action (to be implemented with audit_logs collection)
    
    Args:
        action: Action performed (e.g., 'create', 'update', 'delete')
        resource_type: Type of resource (e.g., 'news_article', 'video_config')
        resource_id: ID of the resource
        details: Additional details about the action
    """
    user_context = get_current_user_context()
    
    audit_entry = {
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'customer_id': user_context.get('customer_id'),
        'user_id': user_context.get('user_id'),
        'email': user_context.get('email'),
        'timestamp': datetime.utcnow(),
        'details': details or {}
    }
    
    logger.info(f"Audit log: {action} {resource_type} {resource_id} by {user_context.get('email')}")
    
    # TODO: Insert into audit_logs collection
    # This will be implemented when we add audit logging to the services
    
    return audit_entry

