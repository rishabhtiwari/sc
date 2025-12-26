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
        
        result = self.collection.insert_one(product_data)
        logger.info(f"Created product {result.inserted_id}")
        
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
        
        updates['updated_at'] = datetime.utcnow()
        
        result = self.collection.update_one(query, {'$set': updates})
        return result.modified_count > 0

