"""
Product Service - Flask Blueprint for product-specific API endpoints

Handles all product-related operations:
- CRUD operations (create, read, update, delete)
- Statistics
- AI summary generation
- Audio generation
- Media upload and management
- Video generation
"""

import logging
import os
import uuid
from flask import Blueprint, request, jsonify, send_from_directory
from bson import ObjectId
from datetime import datetime

from common.utils import serialize_document

logger = logging.getLogger(__name__)

# Create Blueprint
product_bp = Blueprint('product', __name__, url_prefix='/api/products')


def init_product_service(products_collection, product_workflow, api_server_url):
    """
    Initialize product service with dependencies
    
    Args:
        products_collection: MongoDB collection for products
        product_workflow: ProductWorkflow instance
        api_server_url: External API server URL for generating file URLs
    """
    product_bp.products_collection = products_collection
    product_bp.product_workflow = product_workflow
    product_bp.api_server_url = api_server_url
    logger.info("✅ Product service initialized")


# ========== CRUD Operations ==========

@product_bp.route('', methods=['GET'])
def get_products():
    """Get all products for a customer"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')
        
        products = list(product_bp.products_collection.find({
            'customer_id': customer_id,
            'user_id': user_id
        }).sort('created_at', -1))
        
        for product in products:
            serialize_document(product)
        
        return jsonify({
            'status': 'success',
            'products': products,
            'count': len(products)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting products: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product_bp.route('/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')
        
        product = product_bp.product_workflow.get_product(
            product_id, customer_id, user_id
        )
        
        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404
        
        serialize_document(product)
        
        return jsonify({
            'status': 'success',
            'product': product
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting product: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product_bp.route('', methods=['POST'])
def create_product():
    """Create a new product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        data = request.get_json()

        # Validate required fields - accept both 'name' and 'product_name'
        product_name = data.get('name') or data.get('product_name')
        if not product_name:
            return jsonify({
                'status': 'error',
                'message': 'Product name is required'
            }), 400

        # Normalize to 'name' for backend consistency
        if 'product_name' in data and 'name' not in data:
            data['name'] = data['product_name']

        # Create product using workflow
        product_id = product_bp.product_workflow.create_product(
            data, customer_id, user_id
        )
        
        # Get created product
        product = product_bp.product_workflow.get_product(
            product_id, customer_id, user_id
        )
        serialize_document(product)
        
        return jsonify({
            'status': 'success',
            'message': 'Product created successfully',
            'product': product
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product_bp.route('/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')
        
        data = request.get_json()
        
        # Update using workflow
        updated = product_bp.product_workflow.update_product(
            product_id, data, customer_id, user_id
        )
        
        if not updated:
            return jsonify({
                'status': 'error',
                'message': 'Product not found or not updated'
            }), 404

        # Get updated product
        product = product_bp.product_workflow.get_product(
            product_id, customer_id, user_id
        )
        serialize_document(product)

        return jsonify({
            'status': 'success',
            'message': 'Product updated successfully',
            'product': product
        }), 200

    except Exception as e:
        logger.error(f"Error updating product: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product_bp.route('/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        result = product_bp.products_collection.delete_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if result.deleted_count == 0:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        return jsonify({
            'status': 'success',
            'message': 'Product deleted successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product_bp.route('/stats', methods=['GET'])
def get_product_stats():
    """
    Get product statistics

    Returns counts for:
    - total: All products
    - pending: Products in draft or summary_generated status (not yet started video generation)
    - processing: Products currently being processed (video generation in progress)
    - completed: Products with completed video generation
    - failed: Products with failed video generation
    """
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        # Total products
        total = product_bp.products_collection.count_documents({
            'customer_id': customer_id,
            'user_id': user_id
        })

        # Pending: Products in draft, summary_generated, audio_configured, or template_selected status
        # These are products that haven't started video generation yet
        pending = product_bp.products_collection.count_documents({
            'customer_id': customer_id,
            'user_id': user_id,
            '$or': [
                {'status': 'draft'},
                {'status': 'summary_generated'},
                {'status': 'audio_configured'},
                {'status': 'template_selected'},
                {'generated_video': {'$exists': False}},
                {'generated_video.status': {'$exists': False}},
                {'generated_video.status': 'pending'}
            ]
        })

        # Processing: Products with video generation in progress
        processing = product_bp.products_collection.count_documents({
            'customer_id': customer_id,
            'user_id': user_id,
            'generated_video.status': 'processing'
        })

        # Completed: Products with completed video generation
        completed = product_bp.products_collection.count_documents({
            'customer_id': customer_id,
            'user_id': user_id,
            'generated_video.status': 'completed'
        })

        # Failed: Products with failed video generation
        failed = product_bp.products_collection.count_documents({
            'customer_id': customer_id,
            'user_id': user_id,
            'generated_video.status': 'failed'
        })

        stats = {
            'total': total,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed
        }

        logger.info(f"✅ Product Stats: {stats}")
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200

    except Exception as e:
        logger.error(f"❌ Error fetching stats: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ========== AI Summary Generation ==========

@product_bp.route('/<product_id>/generate-summary', methods=['POST'])
def generate_summary(product_id):
    """
    Generate AI summary for product using ProductWorkflow

    Supports both legacy (custom_prompt) and new template-based generation.

    Request body:
    {
        "regenerate": bool,           # Force regeneration
        "custom_prompt": str,         # Legacy: custom prompt text
        "template_id": str,           # New: prompt template ID
        "use_template": bool          # New: use template-based generation (default: true)
    }
    """
    try:
        logger.info(f"📝 Generating summary for product {product_id}")
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        # Verify product exists and belongs to customer
        product = product_bp.product_workflow.get_product(
            product_id, customer_id, user_id
        )
        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        # Get request data
        data = request.get_json() or {}
        regenerate = data.get('regenerate', False)
        custom_prompt = data.get('custom_prompt')
        template_id = data.get('template_id', 'product_summary_default_v1')
        use_template = data.get('use_template', True)
        template_variables = data.get('template_variables', {})

        # Choose generation method
        if use_template and not custom_prompt:
            # New template-based generation with JSON output
            logger.info(f"Using template-based generation with template: {template_id}")
            logger.info(f"Template variables: {template_variables}")
            result = product_bp.product_workflow.generate_ai_summary_with_template(
                content_id=product_id,
                template_id=template_id,
                customer_id=customer_id,
                regenerate=regenerate,
                template_variables=template_variables
            )
        else:
            # Legacy generation method
            logger.info("Using legacy generation method")
            result = product_bp.product_workflow.generate_ai_summary(
                content_id=product_id,
                custom_prompt=custom_prompt,
                regenerate=regenerate
            )

        if result['status'] == 'error':
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product_bp.route('/<product_id>/audio-sections', methods=['GET'])
def get_audio_sections(product_id):
    """Get parsed sections from AI summary with smart audio defaults"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        # Get product
        product = product_bp.product_workflow.get_product(
            product_id, customer_id, user_id
        )

        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        if not product.get('ai_summary'):
            return jsonify({
                'status': 'error',
                'message': 'No AI summary found. Generate summary first.'
            }), 400

        # Extract AI summary text
        ai_summary = product.get('ai_summary', '')
        if isinstance(ai_summary, dict):
            ai_summary_text = ai_summary.get('full_text', '')
            sections = ai_summary.get('sections', [])
        else:
            ai_summary_text = ai_summary
            sections = product_bp.product_workflow.parse_summary_to_sections(
                ai_summary_text
            )

        if not ai_summary_text and not sections:
            return jsonify({
                'status': 'error',
                'message': 'AI summary text is empty.'
            }), 400

        # Add smart audio configuration to each section
        sections_with_config = []
        for idx, section in enumerate(sections):
            smart_config = product_bp.product_workflow.get_audio_config_for_section(
                section['title'],
                idx,
                len(sections)
            )

            sections_with_config.append({
                'title': section['title'],
                'content': section['content'],
                'order': section['order'],
                'defaultSpeed': smart_config['speed'],
                'description': smart_config['description']
            })

        return jsonify({
            'status': 'success',
            'sections': sections_with_config,
            'totalSections': len(sections_with_config)
        }), 200

    except Exception as e:
        logger.error(f"❌ Error getting audio sections: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ========== Audio Generation ==========

@product_bp.route('/<product_id>/generate-audio', methods=['POST'])
def generate_audio(product_id):
    """Generate audio from AI summary using ProductWorkflow"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        # Verify product exists
        product = product_bp.product_workflow.get_product(
            product_id, customer_id, user_id
        )
        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        # Get audio configuration from request
        data = request.get_json() or {}
        audio_config = {
            'voice': data.get('voice', 'am_adam'),
            'model': data.get('model', 'kokoro-82m'),
            'language': data.get('language', 'en'),
            'sectionPitches': data.get('sectionPitches', {})
        }

        # Use workflow to generate audio
        result = product_bp.product_workflow.generate_audio_for_sections(
            content_id=product_id,
            audio_config=audio_config
        )

        if result['status'] == 'error':
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== Media Upload ==========

@product_bp.route('/<product_id>/upload-media', methods=['POST'])
def upload_media(product_id):
    """Upload media files for product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        logger.info(f"📤 Upload media - Content-Type: {request.content_type}")
        logger.info(f"📤 Request files: {list(request.files.keys())}")

        # Get product
        product = product_bp.products_collection.find_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        # Check if this is a file upload
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle actual file uploads
            if 'files' not in request.files:
                return jsonify({
                    'status': 'error',
                    'message': 'No files provided'
                }), 400

            files = request.files.getlist('files')
            if not files:
                return jsonify({
                    'status': 'error',
                    'message': 'No files provided'
                }), 400

            uploaded_urls = []

            for file in files:
                if file.filename == '':
                    continue

                # Determine if file is video or image
                is_video = (file.content_type and
                           file.content_type.startswith('video/'))
                media_type = 'videos' if is_video else 'images'

                # Create upload directory
                upload_dir = os.path.join(
                    '/app/public/product', product_id, media_type
                )
                os.makedirs(upload_dir, exist_ok=True)

                # Generate unique filename
                file_ext = os.path.splitext(file.filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                file_path = os.path.join(upload_dir, unique_filename)

                # Save file
                file.save(file_path)
                logger.info(f"💾 Saved {media_type[:-1]} file: {file_path}")

                # Generate accessible URL
                file_url = (
                    f"{product_bp.api_server_url}/api/ecommerce/public/"
                    f"product/{product_id}/{media_type}/{unique_filename}"
                )
                uploaded_urls.append(file_url)

            # Update timestamp
            product_bp.products_collection.update_one(
                {'_id': ObjectId(product_id)},
                {'$set': {'updated_at': datetime.utcnow()}}
            )

            logger.info(f"✅ Uploaded {len(uploaded_urls)} files")

            return jsonify({
                'status': 'success',
                'message': f'Uploaded {len(uploaded_urls)} files',
                'urls': uploaded_urls
            }), 200

        else:
            return jsonify({
                'status': 'error',
                'message': 'No files provided. Use multipart/form-data.'
            }), 400

    except Exception as e:
        logger.error(f"❌ Error uploading media: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ========== Video Generation ==========

@product_bp.route('/<product_id>/generate-video', methods=['POST'])
def generate_video(product_id):
    """Generate final product video using ProductWorkflow"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        logger.info(f"🎬 Generating video for product {product_id}")

        # Verify product exists
        product = product_bp.product_workflow.get_product(
            product_id, customer_id, user_id
        )
        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        # Get options from request
        data = request.get_json() or {}
        template_id = data.get('template_id', 'default')
        template_variables = data.get('template_variables', {})
        distribution_mode = data.get('distribution_mode', 'auto')
        section_mapping = data.get('section_mapping', {})

        # Use workflow to generate video
        result = product_bp.product_workflow.generate_video(
            content_id=product_id,
            template_id=template_id,
            template_variables=template_variables,
            distribution_mode=distribution_mode,
            section_mapping=section_mapping
        )

        if result['status'] == 'error':
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error generating video: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product_bp.route('/<product_id>/generate-video-dynamic', methods=['POST'])
def generate_video_dynamic(product_id):
    """
    Generate product video with dynamic number of images

    This endpoint uses the template system to dynamically expand layers
    based on the number of images and section durations.
    """
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        logger.info(f"🎬 Generating dynamic video for product {product_id}")

        # Verify product exists
        product = product_bp.product_workflow.get_product(
            product_id, customer_id, user_id
        )
        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        # Get options from request
        data = request.get_json() or {}
        template_id = data.get('template_id')
        use_section_images = data.get('use_section_images', False)

        if not template_id:
            return jsonify({
                'status': 'error',
                'message': 'template_id is required'
            }), 400

        # Extract AI summary sections
        ai_summary = product.get('ai_summary')
        if not ai_summary or 'sections' not in ai_summary:
            return jsonify({
                'status': 'error',
                'message': 'No AI summary sections found. Generate summary first.'
            }), 400

        sections = ai_summary['sections']

        # Extract images and durations
        product_images = []
        section_durations = []

        for section in sections:
            audio_config = section.get('audio_config', {})
            duration = audio_config.get('duration', 5.0)
            section_durations.append(duration)

            if use_section_images:
                section_images = section.get('images', [])
                if section_images:
                    product_images.extend(section_images)

        # If no section images, use product media_urls
        if not product_images:
            product_images = product.get('media_urls', [])

        if not product_images:
            return jsonify({
                'status': 'error',
                'message': 'No product images found. Upload images first.'
            }), 400

        # Get audio URL
        audio_url = product.get('audio_url')
        if not audio_url:
            return jsonify({
                'status': 'error',
                'message': 'No audio found. Generate audio first.'
            }), 400

        # Build template variables
        total_duration = (sum(section_durations) if section_durations
                         else len(product_images) * 5.0)
        duration_per_image = (total_duration / len(product_images)
                             if product_images else 5.0)

        template_variables = {
            'product_images': product_images,
            'audio_url': audio_url,
            'total_duration': total_duration,
            'duration_per_image': duration_per_image,
            'section_durations': section_durations
        }

        # Use workflow to generate video
        result = product_bp.product_workflow.generate_video(
            content_id=product_id,
            template_id=template_id,
            template_variables=template_variables
        )

        if result['status'] == 'error':
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error generating dynamic video: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

