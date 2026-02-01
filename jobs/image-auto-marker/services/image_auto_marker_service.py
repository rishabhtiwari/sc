"""
Image Auto-Marker Service
Handles automatic marking of images as cleaned for customers with auto_mark_cleaned enabled
"""

import os
import sys
import requests
import io
from datetime import datetime
from typing import Dict, Any, Optional
from pymongo import MongoClient
from bson import ObjectId
from PIL import Image

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.utils.multi_tenant_db import (
    build_multi_tenant_query,
    prepare_update_document
)


class ImageAutoMarkerService:
    """Service for automatically marking images as cleaned"""
    
    def __init__(self, config, logger):
        """
        Initialize the Image Auto-Marker Service
        
        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # MongoDB connection
        self.mongo_client = MongoClient(config.MONGODB_URL)
        self.db = self.mongo_client.get_database()
        self.news_collection = self.db.news_document
        self.image_config_collection = self.db.image_config
        
        # Create indexes
        self._create_indexes()
        
        self.logger.info("✅ Image Auto-Marker Service initialized")

    def _download_and_save_image(self, image_url: str, doc_id: str, output_dir: str) -> Optional[str]:
        """
        Download image from URL and save to disk

        Args:
            image_url: URL of the image to download
            doc_id: Document ID for filename
            output_dir: Directory to save the image

        Returns:
            File path of saved image or None if failed
        """
        try:
            self.logger.info(f"📥 Downloading image from: {image_url}")

            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Open image with PIL
            image = Image.open(io.BytesIO(response.content))

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Save to file
            filename = f"{doc_id}_cleaned.png"
            filepath = os.path.join(output_dir, filename)

            image.save(filepath, 'PNG')
            self.logger.info(f"💾 Image saved to: {filepath}")

            return filepath

        except Exception as e:
            self.logger.error(f"❌ Error downloading/saving image: {e}")
            return None

    def _create_indexes(self):
        """Create necessary database indexes"""
        try:
            # Index for image_config collection
            self.image_config_collection.create_index(
                [('customer_id', 1)],
                unique=True
            )
            
            # Index for finding pending images
            self.news_collection.create_index([
                ('customer_id', 1),
                ('image', 1),
                ('clean_image', 1),
                ('short_summary', 1)
            ])
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to create indexes: {e}")
    
    def is_auto_mark_enabled(self, customer_id: str) -> bool:
        """
        Check if auto-mark is enabled for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            bool: True if auto-mark is enabled, False otherwise
        """
        try:
            config = self.image_config_collection.find_one({'customer_id': customer_id})
            
            if not config:
                # No config exists - return default (True)
                return True
            
            return config.get('auto_mark_cleaned', True)
            
        except Exception as e:
            self.logger.error(f"❌ Error checking auto-mark status: {e}")
            return True  # Default to enabled on error
    
    def process_pending_images(self, customer_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Process pending images for a customer
        
        Args:
            customer_id: Customer ID (required for multi-tenant jobs)
            **kwargs: Additional parameters
            
        Returns:
            Dict with processing results
        """
        if not customer_id:
            raise ValueError("customer_id is required")
        
        result = {
            'customer_id': customer_id,
            'images_processed': 0,
            'images_marked': 0,
            'errors': []
        }
        
        try:
            self.logger.info(f"🔍 Processing pending images for customer: {customer_id}")
            
            # Find pending images (have image, have short_summary, no clean_image, not skipped)
            match_criteria = {
                'image': {'$ne': None},
                'clean_image': None,
                '$and': [
                    {'short_summary': {'$ne': None}},
                    {'short_summary': {'$ne': ''}}
                ],
                'watermark_skipped': {'$ne': True},
                'status': {'$ne': 'dont_process'}
            }
            
            # Apply multi-tenant filter
            query = build_multi_tenant_query(match_criteria, customer_id=customer_id)
            
            # Get pending images (limit to batch size)
            pending_images = list(self.news_collection.find(query).limit(self.config.BATCH_SIZE))
            
            if not pending_images:
                self.logger.info(f"✅ No pending images for customer {customer_id}")
                result['message'] = 'No pending images found'
                return result
            
            self.logger.info(f"📸 Found {len(pending_images)} pending images for customer {customer_id}")
            
            # Process each image
            for doc in pending_images:
                try:
                    doc_id = str(doc['_id'])
                    original_image_url = doc.get('image')

                    if not original_image_url:
                        self.logger.warning(f"⚠️ Image {doc_id} has no image URL, skipping")
                        continue

                    # Download and save the image to disk (same as manual mode)
                    output_dir = self.config.OUTPUT_DIR
                    filepath = self._download_and_save_image(original_image_url, doc_id, output_dir)

                    if not filepath:
                        error_msg = f"Failed to download/save image {doc_id}"
                        self.logger.error(f"❌ {error_msg}")
                        result['errors'].append(error_msg)
                        result['images_processed'] += 1
                        continue

                    # Mark as cleaned by setting clean_image to the saved file path
                    update_data = {
                        'clean_image': filepath,
                        'clean_image_updated_at': datetime.utcnow(),
                        'auto_marked_cleaned': True  # Flag to indicate auto-marking
                    }
                    prepare_update_document(update_data, user_id='auto-mark-job')

                    # Update the document
                    base_query = {'_id': ObjectId(doc_id)}
                    update_query = build_multi_tenant_query(base_query, customer_id=customer_id)

                    self.news_collection.update_one(update_query, {'$set': update_data})

                    result['images_marked'] += 1
                    self.logger.info(f"✅ Downloaded and marked image {doc_id} as cleaned (auto-mark)")

                except Exception as e:
                    error_msg = f"Failed to process image {doc.get('_id')}: {str(e)}"
                    self.logger.error(f"❌ {error_msg}")
                    result['errors'].append(error_msg)

                result['images_processed'] += 1
            
            self.logger.info(
                f"✅ Auto-mark completed for customer {customer_id}: "
                f"{result['images_marked']}/{result['images_processed']} images marked"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Auto-mark processing failed for customer {customer_id}: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            result['errors'].append(error_msg)
            raise

