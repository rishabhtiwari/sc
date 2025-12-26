"""
Public Service - Flask Blueprint for public file serving endpoints

Handles serving and deletion of media files:
- Images
- Videos
- Audio files
"""

import logging
import os
from flask import Blueprint, request, jsonify, send_from_directory
from bson import ObjectId

logger = logging.getLogger(__name__)

# Create Blueprint
public_bp = Blueprint('public', __name__, url_prefix='/api/ecommerce/public')


def init_public_service(products_collection):
    """
    Initialize public service with dependencies
    
    Args:
        products_collection: MongoDB collection for products
    """
    public_bp.products_collection = products_collection
    logger.info("✅ Public service initialized")


# ========== File Serving ==========

@public_bp.route('/product/<product_id>/images/<filename>', methods=['GET'])
def serve_product_images(product_id, filename):
    """Serve uploaded image files for a product"""
    try:
        product_dir = os.path.join('public', 'product', product_id, 'images')
        return send_from_directory(product_dir, filename)
    except Exception as e:
        logger.error(f"Error serving image: {str(e)}")
        return jsonify({'status': 'error', 'message': 'File not found'}), 404


@public_bp.route('/product/<product_id>/videos/<filename>', methods=['GET'])
def serve_product_videos(product_id, filename):
    """Serve uploaded video files for a product"""
    try:
        product_dir = os.path.join('public', 'product', product_id, 'videos')
        return send_from_directory(product_dir, filename)
    except Exception as e:
        logger.error(f"Error serving video: {str(e)}")
        return jsonify({'status': 'error', 'message': 'File not found'}), 404


@public_bp.route('/product/<product_id>/<filename>', methods=['GET'])
def serve_product_files(product_id, filename):
    """Serve audio/video files for a product"""
    try:
        product_dir = os.path.join('public', 'product', product_id)
        return send_from_directory(product_dir, filename)
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        return jsonify({'status': 'error', 'message': 'File not found'}), 404


# ========== File Deletion ==========

@public_bp.route('/product/<product_id>/images/<filename>', methods=['DELETE'])
def delete_product_image(product_id, filename):
    """Delete a specific image file from a product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        logger.info(f"🗑️ Deleting image: {product_id}/images/{filename}")

        # Verify product ownership
        product = public_bp.products_collection.find_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        # Remove from MongoDB media_files array
        image_url = f"/api/ecommerce/public/product/{product_id}/images/{filename}"
        media_files = product.get('media_files', [])
        updated_media_files = [
            media for media in media_files
            if media.get('url') != image_url and not media.get('url', '').endswith(f'/images/{filename}')
        ]

        logger.info(f"🗑️ Removed image from media_files: {filename}")
        logger.info(f"  - Before count: {len(media_files)}")
        logger.info(f"  - After count: {len(updated_media_files)}")

        # Remove from template_variables.dynamic_images
        template_variables = product.get('template_variables', {})
        original_images = template_variables.get('dynamic_images', [])
        updated_dynamic_images = [
            url for url in original_images
            if not url.endswith(f'/images/{filename}')
        ]
        template_variables['dynamic_images'] = updated_dynamic_images

        logger.info(f"🗑️ Removed image from template_variables.dynamic_images")
        logger.info(f"  - Before count: {len(original_images)}")
        logger.info(f"  - After count: {len(updated_dynamic_images)}")

        # Remove from section_mapping if it exists
        section_mapping = product.get('section_mapping', {})
        updated_section_mapping = {}
        if section_mapping:
            logger.info(f"🗑️ Cleaning up section_mapping")
            for section_key, media_list in section_mapping.items():
                filtered_list = [
                    media for media in media_list
                    if not media.get('url', '').endswith(f'/images/{filename}')
                ]
                if filtered_list:  # Only keep sections that still have media
                    updated_section_mapping[section_key] = filtered_list
            logger.info(f"  - Updated section_mapping")
        else:
            updated_section_mapping = section_mapping

        # Update product in database
        public_bp.products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {
                'media_files': updated_media_files,
                'template_variables': template_variables,
                'section_mapping': updated_section_mapping
            }}
        )

        logger.info(f"✅ Image deletion complete: {filename}")

        # Try to delete physical file
        file_path = os.path.join(
            '/app/public/product', product_id, 'images', filename
        )
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️ Deleted physical file: {file_path}")
        else:
            logger.warning(f"⚠️ Physical file not found (already deleted): {file_path}")

        return jsonify({
            'status': 'success',
            'message': 'Image deleted successfully',
            'media_files': updated_media_files,
            'template_variables': template_variables,
            'section_mapping': updated_section_mapping
        }), 200

    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@public_bp.route('/product/<product_id>/videos/<filename>', methods=['DELETE'])
def delete_product_video(product_id, filename):
    """Delete a specific video file from a product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        logger.info(f"🗑️ Deleting video: {product_id}/videos/{filename}")

        # Verify product ownership
        product = public_bp.products_collection.find_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        # Remove from MongoDB media_files array
        video_url = f"/api/ecommerce/public/product/{product_id}/videos/{filename}"
        media_files = product.get('media_files', [])
        updated_media_files = [
            media for media in media_files
            if media.get('url') != video_url and not media.get('url', '').endswith(f'/videos/{filename}')
        ]

        logger.info(f"🗑️ Removed video from media_files: {filename}")
        logger.info(f"  - Before count: {len(media_files)}")
        logger.info(f"  - After count: {len(updated_media_files)}")

        # Remove from template_variables.dynamic_videos
        template_variables = product.get('template_variables', {})
        original_videos = template_variables.get('dynamic_videos', [])

        # Find which index was removed for timings array
        removed_index = None
        for i, url in enumerate(original_videos):
            if url.endswith(f'/videos/{filename}'):
                removed_index = i
                break

        updated_dynamic_videos = [
            url for url in original_videos
            if not url.endswith(f'/videos/{filename}')
        ]
        template_variables['dynamic_videos'] = updated_dynamic_videos

        # Also update timings array if it exists
        if removed_index is not None and 'dynamic_videos_timings' in template_variables:
            timings = template_variables.get('dynamic_videos_timings', [])
            if removed_index < len(timings):
                timings.pop(removed_index)
                template_variables['dynamic_videos_timings'] = timings
                logger.info(f"  - Removed timing at index {removed_index}")

        logger.info(f"🗑️ Removed video from template_variables.dynamic_videos")
        logger.info(f"  - Before count: {len(original_videos)}")
        logger.info(f"  - After count: {len(updated_dynamic_videos)}")

        # Remove from section_mapping if it exists
        section_mapping = product.get('section_mapping', {})
        updated_section_mapping = {}
        if section_mapping:
            logger.info(f"🗑️ Cleaning up section_mapping")
            for section_key, media_list in section_mapping.items():
                filtered_list = [
                    media for media in media_list
                    if not media.get('url', '').endswith(f'/videos/{filename}')
                ]
                if filtered_list:  # Only keep sections that still have media
                    updated_section_mapping[section_key] = filtered_list
            logger.info(f"  - Updated section_mapping")
        else:
            updated_section_mapping = section_mapping

        # Update product in database
        public_bp.products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {
                'media_files': updated_media_files,
                'template_variables': template_variables,
                'section_mapping': updated_section_mapping
            }}
        )

        logger.info(f"✅ Video deletion complete: {filename}")

        # Try to delete physical file
        file_path = os.path.join(
            '/app/public/product', product_id, 'videos', filename
        )
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🗑️ Deleted physical file: {file_path}")
        else:
            logger.warning(f"⚠️ Physical file not found (already deleted): {file_path}")

        return jsonify({
            'status': 'success',
            'message': 'Video deleted successfully',
            'media_files': updated_media_files,
            'template_variables': template_variables,
            'section_mapping': updated_section_mapping
        }), 200

    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

