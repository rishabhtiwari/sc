"""
Product-specific content generation workflow

This workflow handles:
- Product video script generation
- Product-specific prompt templates
- Product data extraction and formatting
"""

import logging
from bson import ObjectId

from common.base_content_generator import BaseContentGenerator
from prompts.product_prompts import PRODUCT_VIDEO_PROMPT

logger = logging.getLogger(__name__)


class ProductWorkflow(BaseContentGenerator):
    """
    Product video generation workflow
    
    Inherits all the base functionality from BaseContentGenerator:
    - AI summary generation
    - Summary parsing
    - Audio generation
    - Template selection
    - Video generation
    
    Customizes:
    - Prompt template for product videos
    - Context building from product data
    """
    
    def get_content_type(self):
        """Return content type identifier"""
        return "product_video"
    
    def get_default_prompt_template(self):
        """Return the default product video prompt template"""
        return PRODUCT_VIDEO_PROMPT
    
    def build_prompt_context(self, product_id):
        """
        Build context data for product prompt formatting
        
        Args:
            product_id: Product ID
            
        Returns:
            dict: Context data with product_name, category, price_info, description
        """
        # Get product from database
        product = self.collection.find_one({'_id': ObjectId(product_id)})
        
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Extract product data
        product_name = product.get('name', 'Unknown Product')
        product_description = product.get('description', 'No description provided')
        product_category = product.get('category', 'General')
        product_price = product.get('price', '')
        product_currency = product.get('currency', 'USD')
        
        # Format price info
        if product_price:
            price_info = f"${product_price} {product_currency}"
        else:
            price_info = "Premium quality"
        
        # Return context for prompt formatting
        return {
            'product_name': product_name,
            'category': product_category,
            'price_info': price_info,
            'description': product_description
        }
    
    # ========== Product-Specific Methods ==========
    
    def get_product(self, product_id, customer_id=None, user_id=None):
        """
        Get product with optional customer/user filtering
        
        Args:
            product_id: Product ID
            customer_id: Optional customer ID for multi-tenancy
            user_id: Optional user ID for multi-tenancy
            
        Returns:
            dict: Product document or None
        """
        query = {'_id': ObjectId(product_id)}
        
        if customer_id:
            query['customer_id'] = customer_id
        if user_id:
            query['user_id'] = user_id
        
        return self.collection.find_one(query)
    
    def create_product(self, product_data, customer_id='default', user_id='default'):
        """
        Create a new product

        Args:
            product_data: Product data dict
            customer_id: Customer ID for multi-tenancy
            user_id: User ID for multi-tenancy

        Returns:
            str: Created product ID
        """
        from datetime import datetime

        product_data['customer_id'] = customer_id
        product_data['user_id'] = user_id
        product_data['created_at'] = datetime.utcnow()
        product_data['updated_at'] = datetime.utcnow()

        # Set initial status to 'draft'
        # Status flow: draft -> summary_generated -> audio_configured -> template_selected -> completed
        product_data['status'] = product_data.get('status', 'draft')

        result = self.collection.insert_one(product_data)
        logger.info(f"Created product {result.inserted_id} with status: {product_data['status']}")

        return str(result.inserted_id)
    
    def update_product(self, product_id, updates, customer_id=None, user_id=None):
        """
        Update product data

        Args:
            product_id: Product ID
            updates: Dict of fields to update
            customer_id: Optional customer ID for filtering
            user_id: Optional user ID for filtering

        Returns:
            bool: True if updated, False otherwise
        """
        from datetime import datetime

        query = {'_id': ObjectId(product_id)}
        if customer_id:
            query['customer_id'] = customer_id
        if user_id:
            query['user_id'] = user_id

        # Process ai_summary - convert JSON structure to sections format
        if 'ai_summary' in updates:
            ai_summary_data = updates['ai_summary']

            # If it's a dict (JSON from frontend), convert to sections format
            if isinstance(ai_summary_data, dict):
                logger.info("Processing ai_summary as JSON structure")

                # Check if it already has sections (already processed)
                if 'sections' not in ai_summary_data:
                    # Convert JSON fields to sections
                    sections = self._parse_json_to_sections(ai_summary_data)

                    # Create structured ai_summary with sections
                    updates['ai_summary'] = {
                        'sections': sections,
                        'content': ai_summary_data,  # Store original JSON
                        'generated_at': datetime.utcnow(),
                        'version': '2.0',
                        'content_type': self.get_content_type()
                    }

                    logger.info(f"Converted JSON to {len(sections)} sections")
                else:
                    # Already has sections, just update timestamp
                    updates['ai_summary']['updated_at'] = datetime.utcnow()

            elif isinstance(ai_summary_data, str):
                # Legacy: plain text format
                logger.info("Processing ai_summary as plain text (legacy)")
                # Keep as-is for backward compatibility
                pass

        updates['updated_at'] = datetime.utcnow()

        result = self.collection.update_one(query, {'$set': updates})
        return result.modified_count > 0

    def _parse_json_to_sections(self, json_data):
        """
        Parse structured JSON content into sections array

        Args:
            json_data: Dict with section fields (e.g., opening_hook, product_introduction, etc.)

        Returns:
            list: Array of section dicts with title, content, order
        """
        if not isinstance(json_data, dict):
            logger.warning(f"raw_content is not a dict: {type(json_data)}")
            return []

        sections = []
        order = 0

        # Common section field names (in order)
        section_fields = [
            'opening_hook',
            'product_introduction',
            'key_features',
            'social_proof',
            'call_to_action',
            'introduction',
            'features',
            'benefits',
            'conclusion',
            'body',
            'summary'
        ]

        # Extract sections in order
        for field in section_fields:
            if field in json_data:
                value = json_data[field]

                # Convert field name to title (e.g., opening_hook -> Opening Hook)
                title = field.replace('_', ' ').title()

                # Format the content
                content = self._format_section_content(value)

                if content:
                    sections.append({
                        'title': title,
                        'content': content,
                        'order': order
                    })
                    order += 1

        # If no known sections found, try to extract all fields
        if not sections:
            for key, value in json_data.items():
                content = self._format_section_content(value)
                if content:
                    title = key.replace('_', ' ').title()
                    sections.append({
                        'title': title,
                        'content': content,
                        'order': order
                    })
                    order += 1

        return sections

    def _format_section_content(self, value):
        """
        Format a section value (string, array, or object) to text

        Args:
            value: The section value

        Returns:
            str: Formatted text content
        """
        if isinstance(value, str):
            return value

        elif isinstance(value, list):
            # Handle array of items
            item_texts = []
            for item in value:
                if isinstance(item, str):
                    item_texts.append(item)
                elif isinstance(item, dict):
                    # Handle objects in array (e.g., key_features with feature_name and description)
                    if 'feature_name' in item and 'description' in item:
                        item_texts.append(f"{item['feature_name']}: {item['description']}")
                    elif 'name' in item and 'description' in item:
                        item_texts.append(f"{item['name']}: {item['description']}")
                    elif 'title' in item and 'content' in item:
                        item_texts.append(f"{item['title']}: {item['content']}")
                    else:
                        # Generic object: join all string values
                        obj_values = [str(v) for v in item.values() if v]
                        if obj_values:
                            item_texts.append(': '.join(obj_values))

            return '\n'.join(item_texts) if item_texts else ''

        elif isinstance(value, dict):
            # Handle nested objects
            obj_texts = []
            for k, v in value.items():
                text = self._format_section_content(v)
                if text:
                    obj_texts.append(text)
            return '\n'.join(obj_texts) if obj_texts else ''

        else:
            # For other types (numbers, booleans, etc.), convert to string
            return str(value) if value is not None else ''

    def update_product_status(self, product_id, status, customer_id=None, user_id=None):
        """
        Update product status

        Valid statuses:
        - draft: Initial state after product creation
        - summary_generated: AI summary has been generated
        - audio_configured: Audio settings configured
        - template_selected: Video template selected
        - completed: Video generation completed

        Args:
            product_id: Product ID
            status: New status value
            customer_id: Optional customer ID for filtering
            user_id: Optional user ID for filtering

        Returns:
            bool: True if updated, False otherwise
        """
        valid_statuses = ['draft', 'summary_generated', 'audio_configured', 'template_selected', 'completed']

        if status not in valid_statuses:
            logger.warning(f"Invalid status: {status}. Valid statuses: {valid_statuses}")
            return False

        logger.info(f"Updating product {product_id} status to: {status}")
        return self.update_product(product_id, {'status': status}, customer_id, user_id)

