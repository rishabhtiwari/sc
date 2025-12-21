"""
Multi-Tenant Utilities for Template Service
Helper functions for customer_id filtering and audit tracking
"""

from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# System customer ID for system-level templates
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
        # Update operation - only set updated fields
        data['updated_at'] = now
        if user_id:
            data['updated_by'] = user_id
    else:
        # Create operation - set both created and updated fields
        # Always enforce customer_id for creates
        data['customer_id'] = get_customer_id(customer_id)
        data['created_at'] = now
        data['updated_at'] = now
        if user_id:
            data['created_by'] = user_id
            data['updated_by'] = user_id

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

    # Always add customer_id filter
    add_customer_filter(query, customer_id)

    # Add soft delete filter if needed
    if not include_deleted:
        query['is_active'] = True

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
        Document with customer_id, audit fields, and is_active flag
    """
    # Add customer_id and audit fields (customer_id is always enforced)
    add_audit_fields(data, is_update=False, customer_id=customer_id, user_id=user_id)

    # Add is_active flag if not present
    if 'is_active' not in data:
        data['is_active'] = True

    return data

