"""
Template Manager Service
Handles template CRUD operations and loading
"""
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from pymongo import MongoClient
from utils.multi_tenant_utils import (
    get_customer_id,
    build_multi_tenant_query,
    prepare_insert_document,
    add_audit_fields
)


class TemplateManager:
    """Service for managing video templates"""

    def __init__(self, template_dir: str, db_client: MongoClient = None, logger=None):
        self.template_dir = template_dir
        self.db_client = db_client
        self.logger = logger
        self._cache = {}  # Simple in-memory cache

        # Get templates collection
        if db_client:
            self.db = db_client['news']
            self.templates_collection = self.db['templates']
    
    def list_templates(self, category: Optional[str] = None, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available templates from MongoDB for a specific customer
        Returns ONLY customer-specific templates (strict multi-tenancy isolation)

        Args:
            category: Filter by category (news, shorts, ecommerce)
            customer_id: Customer ID for multi-tenant filtering

        Returns:
            List of template metadata
        """
        if not self.db_client:
            if self.logger:
                self.logger.error("Database client not available")
            return []

        try:
            # Build query to include ONLY customer's own templates (strict isolation)
            resolved_customer_id = get_customer_id(customer_id)

            base_query = {
                'is_active': True,
                'customer_id': resolved_customer_id  # Only customer's own templates
            }

            if category:
                base_query['category'] = category

            query = base_query

            # Fetch templates from MongoDB
            cursor = self.templates_collection.find(
                query,
                {
                    'template_id': 1,
                    'name': 1,
                    'category': 1,
                    'description': 1,
                    'version': 1,
                    'metadata': 1,
                    'customer_id': 1,  # Include customer_id to identify system vs customer templates
                    'variables': 1,  # Include variables for frontend to display variable inputs
                    '_id': 0
                }
            )

            templates = []
            for template in cursor:
                templates.append({
                    'template_id': template.get('template_id'),
                    'name': template.get('name'),
                    'category': template.get('category'),
                    'description': template.get('description', ''),
                    'version': template.get('version', '1.0.0'),
                    'thumbnail': template.get('metadata', {}).get('thumbnail', ''),
                    'customer_id': template.get('customer_id'),  # Include to identify ownership
                    'tags': template.get('metadata', {}).get('tags', []),
                    'variables': template.get('variables', {})  # Include variables for frontend
                })

            if self.logger:
                resolved_customer_id = get_customer_id(customer_id)
                self.logger.info(f"Listed {len(templates)} templates (category={category}, customer={resolved_customer_id})")

            return templates

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing templates: {e}")
            return []
    
    def load_template(self, category: str, template_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Load template from MongoDB

        Args:
            category: Template category (news, shorts, ecommerce)
            template_id: Template identifier
            use_cache: Whether to use cached version

        Returns:
            Template definition dictionary
        """
        if not self.db_client:
            raise RuntimeError("Database client not available")

        cache_key = f"{category}/{template_id}"

        # Check cache
        if use_cache and cache_key in self._cache:
            if self.logger:
                self.logger.debug(f"Loading template from cache: {cache_key}")
            return self._cache[cache_key]

        try:
            # Load from MongoDB
            template = self.templates_collection.find_one(
                {
                    'template_id': template_id,
                    'category': category,
                    'is_active': True
                },
                {'_id': 0}
            )

            if not template:
                raise FileNotFoundError(f"Template not found: {cache_key}")

            # Cache the template
            self._cache[cache_key] = template

            if self.logger:
                self.logger.info(f"Loaded template from DB: {cache_key}")

            return template

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading template {cache_key}: {e}")
            raise
    
    def get_template_by_id(self, template_id: str, customer_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get template by ID from MongoDB for a specific customer

        Args:
            template_id: Template identifier
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            Template definition or None if not found
        """
        if not self.db_client:
            return None

        try:
            # Build multi-tenant query with customer_id filter
            query = build_multi_tenant_query(
                base_query={'template_id': template_id},
                customer_id=customer_id,
                include_deleted=False
            )

            template = self.templates_collection.find_one(query, {'_id': 0})

            if template and self.logger:
                resolved_customer_id = get_customer_id(customer_id)
                self.logger.info(f"Found template: {template_id} (customer: {resolved_customer_id})")

            return template

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting template {template_id}: {e}")
            return None
    
    def save_template(self, category: str, template_id: str, template: Dict[str, Any],
                      customer_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
        """
        Save template to MongoDB with multi-tenant support

        Args:
            category: Template category
            template_id: Template identifier
            template: Template definition
            customer_id: Customer ID for multi-tenancy (uses SYSTEM_CUSTOMER_ID if None)
            user_id: User ID for audit tracking

        Returns:
            True if successful
        """
        if not self.db_client:
            return False

        try:
            from datetime import datetime

            # Ensure required fields from migration schema
            template['template_id'] = template_id
            template['category'] = category

            # Check if this is an update or create
            resolved_customer_id = get_customer_id(customer_id)
            existing = self.templates_collection.find_one({
                'template_id': template_id,
                'customer_id': resolved_customer_id
            })
            is_update = existing is not None

            # Add audit fields (customer_id, created_at, updated_at, created_by, updated_by)
            add_audit_fields(template, is_update=is_update, customer_id=customer_id, user_id=user_id)

            # Fix: If created_at or updated_at are strings (from frontend), convert them to datetime
            # This happens when editing an existing template - the frontend sends back the serialized dates as strings
            from datetime import datetime
            if 'created_at' in template and isinstance(template['created_at'], str):
                try:
                    # Try parsing ISO format or HTTP date format
                    template['created_at'] = datetime.fromisoformat(template['created_at'].replace('Z', '+00:00'))
                except:
                    try:
                        from email.utils import parsedate_to_datetime
                        template['created_at'] = parsedate_to_datetime(template['created_at'])
                    except:
                        # If parsing fails, use current time
                        template['created_at'] = datetime.utcnow()

            if 'updated_at' in template and isinstance(template['updated_at'], str):
                try:
                    template['updated_at'] = datetime.fromisoformat(template['updated_at'].replace('Z', '+00:00'))
                except:
                    try:
                        from email.utils import parsedate_to_datetime
                        template['updated_at'] = parsedate_to_datetime(template['updated_at'])
                    except:
                        template['updated_at'] = datetime.utcnow()

            # Set defaults for required fields if not present
            if 'is_active' not in template:
                template['is_active'] = True

            if 'version' not in template:
                template['version'] = '1.0.0'

            if 'layers' not in template:
                template['layers'] = []

            if 'variables' not in template:
                template['variables'] = {}

            # Set defaults for optional fields if not present
            if 'description' not in template:
                template['description'] = ''

            if 'aspect_ratio' not in template:
                template['aspect_ratio'] = '16:9'

            if 'resolution' not in template:
                # Set resolution based on aspect ratio
                aspect_ratio = template['aspect_ratio']
                if aspect_ratio == '16:9':
                    template['resolution'] = {'width': 1920, 'height': 1080}
                elif aspect_ratio == '9:16':
                    template['resolution'] = {'width': 1080, 'height': 1920}
                elif aspect_ratio == '1:1':
                    template['resolution'] = {'width': 1080, 'height': 1080}
                elif aspect_ratio == '4:5':
                    template['resolution'] = {'width': 1080, 'height': 1350}
                else:
                    template['resolution'] = {'width': 1920, 'height': 1080}

            if 'effects' not in template:
                template['effects'] = []

            if 'metadata' not in template:
                template['metadata'] = {
                    'author': 'user',
                    'tags': [],
                    'thumbnail': ''
                }

            # Upsert template with customer_id filter
            result = self.templates_collection.update_one(
                {'template_id': template_id, 'customer_id': resolved_customer_id},
                {'$set': template},
                upsert=True
            )

            # Invalidate cache
            cache_key = f"{category}/{template_id}"
            if cache_key in self._cache:
                del self._cache[cache_key]

            if self.logger:
                action = "Updated" if result.matched_count > 0 else "Created"
                self.logger.info(f"{action} template: {cache_key} (customer: {resolved_customer_id})")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving template {category}/{template_id}: {e}")
            return False
    
    def _get_categories(self) -> List[str]:
        """Get list of template categories"""
        categories = []
        if os.path.exists(self.template_dir):
            for item in os.listdir(self.template_dir):
                item_path = os.path.join(self.template_dir, item)
                if os.path.isdir(item_path):
                    categories.append(item)
        return categories
    
    def clear_cache(self):
        """Clear template cache"""
        self._cache = {}
        if self.logger:
            self.logger.info("Template cache cleared")

