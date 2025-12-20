"""
Template Manager Service
Handles template CRUD operations and loading
"""
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from pymongo import MongoClient


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
    
    def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available templates from MongoDB

        Args:
            category: Filter by category (news, shorts, ecommerce)

        Returns:
            List of template metadata
        """
        if not self.db_client:
            if self.logger:
                self.logger.error("Database client not available")
            return []

        try:
            # Build query
            query = {'is_active': True}
            if category:
                query['category'] = category

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
                    'tags': template.get('metadata', {}).get('tags', [])
                })

            if self.logger:
                self.logger.info(f"Listed {len(templates)} templates (category={category})")

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
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get template by ID from MongoDB

        Args:
            template_id: Template identifier

        Returns:
            Template definition or None if not found
        """
        if not self.db_client:
            return None

        try:
            template = self.templates_collection.find_one(
                {
                    'template_id': template_id,
                    'is_active': True
                },
                {'_id': 0}
            )

            if template and self.logger:
                self.logger.info(f"Found template: {template_id}")

            return template

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting template {template_id}: {e}")
            return None
    
    def save_template(self, category: str, template_id: str, template: Dict[str, Any]) -> bool:
        """
        Save template to MongoDB

        Args:
            category: Template category
            template_id: Template identifier
            template: Template definition

        Returns:
            True if successful
        """
        if not self.db_client:
            return False

        try:
            from datetime import datetime

            # Ensure required fields
            template['template_id'] = template_id
            template['category'] = category
            template['updated_at'] = datetime.utcnow()

            if 'created_at' not in template:
                template['created_at'] = datetime.utcnow()

            if 'is_active' not in template:
                template['is_active'] = True

            # Upsert template
            result = self.templates_collection.update_one(
                {'template_id': template_id},
                {'$set': template},
                upsert=True
            )

            # Invalidate cache
            cache_key = f"{category}/{template_id}"
            if cache_key in self._cache:
                del self._cache[cache_key]

            if self.logger:
                action = "Updated" if result.matched_count > 0 else "Created"
                self.logger.info(f"{action} template: {cache_key}")

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

