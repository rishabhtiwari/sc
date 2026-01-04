"""
Product Routes - API Proxy for product video management
Acts as a proxy to forward requests to the inventory-creation-service backend
"""

import logging
import requests
import os
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
product_bp = Blueprint('product', __name__)
logger = logging.getLogger(__name__)

# Service URLs
INVENTORY_CREATION_SERVICE_URL = os.getenv(
    'INVENTORY_CREATION_SERVICE_URL',
    'http://ichat-inventory-creation-service:5001'
)

AUDIO_GENERATION_URL = os.getenv(
    'AUDIO_GENERATION_URL',
    'http://audio-generation-factory:3000'
)


def _convert_to_proxy_url(audio_url):
    """Convert internal audio-generation-factory URL to API proxy URL for browser access

    Examples:
        http://audio-generation-factory:3000/product/123/audio.wav
        -> /api/audio/proxy/product/123/audio.wav

        http://audio-generation-factory:3000/temp/audio.wav
        -> /api/audio/proxy/temp/audio.wav
    """
    if not audio_url:
        return audio_url

    # If it's already a proxy URL, return as-is
    if audio_url.startswith('/api/audio/proxy/'):
        return audio_url

    # Extract the path after the audio service URL
    if audio_url.startswith(AUDIO_GENERATION_URL):
        # Remove the base URL to get the relative path
        relative_path = audio_url[len(AUDIO_GENERATION_URL):]
        # Remove leading slash if present
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        # Return proxy URL
        return f"/api/audio/proxy/{relative_path}"

    # If it's already a relative path, convert to proxy URL
    if audio_url.startswith('/'):
        return f"/api/audio/proxy{audio_url}"

    # Otherwise return as-is
    return audio_url


def proxy_to_inventory_service(path, method='GET', json_data=None, files=None):
    """Proxy request to inventory creation service"""
    try:
        headers = get_request_headers_with_context()
        url = f"{INVENTORY_CREATION_SERVICE_URL}{path}"

        logger.info(f"🔄 Proxying {method} {url}")

        # Use longer timeout for audio/video generation and AI prompt generation endpoints
        # - 10 minutes for audio/video generation
        # - 2 minutes for AI prompt generation (LLM can take 50-60 seconds)
        # - 30 seconds for other endpoints
        if any(x in path for x in ['/generate-audio', '/generate-video', '/generate-summary']):
            timeout = 600
        elif any(x in path for x in ['/prompt-templates/generate', '/content/generate']):
            timeout = 120
        else:
            timeout = 30
        kwargs = {'headers': headers, 'timeout': timeout}

        if files:
            # Handle file uploads - forward files to backend
            # For multiple files with the same key, we need to use a list of tuples
            files_list = []
            for key in files:
                file_list = files.getlist(key)
                for f in file_list:
                    # Each file is a tuple: (field_name, (filename, file_object, content_type))
                    files_list.append((key, (f.filename, f.stream, f.content_type)))
            kwargs['files'] = files_list
            # Remove Content-Type header to let requests set it with boundary
            if 'Content-Type' in headers:
                del headers['Content-Type']
        elif json_data:
            kwargs['json'] = json_data

        response = requests.request(method, url, **kwargs)

        try:
            return response.json(), response.status_code
        except Exception:
            return {'status': 'error', 'message': response.text}, response.status_code

    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout calling inventory creation service: {url}")
        return {'status': 'error', 'message': 'Service timeout'}, 504
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error to inventory creation service: {url}")
        return {'status': 'error', 'message': 'Service unavailable'}, 503
    except Exception as e:
        logger.error(f"❌ Error proxying to inventory creation service: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500


@product_bp.route('/products', methods=['POST'])
def create_product():
    """Proxy: Create a new product"""
    response_data, status_code = proxy_to_inventory_service(
        '/api/products', method='POST', json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/products', methods=['GET'])
def get_products():
    """Proxy: Get all products"""
    response_data, status_code = proxy_to_inventory_service('/api/products', method='GET')

    # Convert internal audio URLs to proxy URLs for browser access
    if status_code == 200 and response_data.get('status') == 'success':
        products = response_data.get('products', [])
        for product in products:
            # Convert main audio_url
            if 'audio_url' in product:
                product['audio_url'] = _convert_to_proxy_url(product['audio_url'])

            # Convert section_audio_urls array if present
            if 'section_audio_urls' in product:
                product['section_audio_urls'] = [
                    _convert_to_proxy_url(url) for url in product['section_audio_urls']
                ]

    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Proxy: Get a specific product by ID"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/products/{product_id}', method='GET'
    )

    # Convert internal audio URLs to proxy URLs for browser access
    if status_code == 200 and response_data.get('status') == 'success':
        product = response_data.get('product', {})

        # Convert main audio_url
        if 'audio_url' in product:
            product['audio_url'] = _convert_to_proxy_url(product['audio_url'])

        # Convert section_audio_urls array if present
        if 'section_audio_urls' in product:
            product['section_audio_urls'] = [
                _convert_to_proxy_url(url) for url in product['section_audio_urls']
            ]

        # Convert audio URLs in AI summary sections if present
        ai_summary = product.get('ai_summary', {})
        if isinstance(ai_summary, dict):
            sections = ai_summary.get('sections', [])
            for section in sections:
                if 'audio_path' in section:
                    section['audio_path'] = _convert_to_proxy_url(section['audio_path'])

    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Proxy: Update a product"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/products/{product_id}', method='PUT', json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Proxy: Delete a product"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/products/{product_id}', method='DELETE'
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/stats', methods=['GET'])
def get_product_stats():
    """Proxy: Get product statistics"""
    response_data, status_code = proxy_to_inventory_service('/api/products/stats', method='GET')
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/generate-summary', methods=['POST'])
def generate_summary(product_id):
    """Proxy: Generate AI summary for product"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/products/{product_id}/generate-summary',
        method='POST',
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/upload-media', methods=['POST'])
def upload_media(product_id):
    """Proxy: Upload media files for product"""
    # Check if this is a file upload or JSON data
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Handle file upload
        response_data, status_code = proxy_to_inventory_service(
            f'/api/products/{product_id}/upload-media',
            method='POST',
            files=request.files
        )
    else:
        # Handle JSON data (URLs)
        response_data, status_code = proxy_to_inventory_service(
            f'/api/products/{product_id}/upload-media',
            method='POST',
            json_data=request.get_json()
        )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/media', methods=['POST'])
def upload_media_alt(product_id):
    """Proxy: Upload media files for product (alternative endpoint)"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/products/{product_id}/upload-media',
        method='POST',
        files=request.files
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/audio-sections', methods=['GET'])
def get_audio_sections(product_id):
    """Proxy: Get parsed sections from AI summary with smart audio defaults"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/products/{product_id}/audio-sections',
        method='GET'
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/generate-audio', methods=['POST'])
def generate_audio(product_id):
    """Proxy: Generate audio from AI summary"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/products/{product_id}/generate-audio',
        method='POST',
        json_data=request.get_json()
    )

    # Convert internal audio URLs to proxy URLs for browser access
    if status_code == 200 and response_data.get('status') == 'success':
        # Convert main audio_url
        if 'audio_url' in response_data:
            response_data['audio_url'] = _convert_to_proxy_url(response_data['audio_url'])

        # Convert section_audio_urls array
        if 'section_audio_urls' in response_data:
            response_data['section_audio_urls'] = [
                _convert_to_proxy_url(url) for url in response_data['section_audio_urls']
            ]

    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/generate-video', methods=['POST'])
def generate_video(product_id):
    """Proxy: Generate final product video"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/products/{product_id}/generate-video',
        method='POST',
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/audio/preview', methods=['POST'])
def preview_product_audio():
    """Generate preview audio for product voice selection (legacy endpoint)"""
    try:
        data = request.get_json()
        text = data.get('text', 'Hello! This is a preview of how this voice sounds.')
        model = data.get('model', 'kokoro-82m')
        voice = data.get('voice', 'am_adam')
        language = data.get('language', 'en')

        # Get audio generation service URL
        AUDIO_GENERATION_URL = os.getenv('AUDIO_GENERATION_URL', 'http://audio-generation-factory:3000')
        # Get API server URL for proxy
        API_SERVER_URL = os.getenv('API_SERVER_EXTERNAL_URL', 'http://localhost:8080')

        logger.info(f"🎤 Generating product preview audio - Model: {model}, Voice: {voice}, Language: {language}")

        # Call audio generation service
        response = requests.post(
            f"{AUDIO_GENERATION_URL}/tts",
            json={
                'text': text,
                'model': model,
                'voice': voice,
                'filename': f'preview_{voice}_{language}.wav'
            },
            timeout=600  # 10 minutes for model initialization on first run
        )

        if response.status_code == 200:
            result = response.json()
            # Get the relative audio URL from the response (e.g., /temp/preview_am_adam_en.wav)
            relative_audio_url = result.get('audio_url', '')

            # Convert to API server proxy URL that's accessible from the browser
            # Return a relative URL so it works from the browser: /api/audio/proxy/temp/file.wav
            if relative_audio_url.startswith('/'):
                relative_audio_url = relative_audio_url[1:]  # Remove leading slash

            # Use relative URL for browser compatibility
            audio_url = f"/api/audio/proxy/{relative_audio_url}"

            logger.info(f"✅ Generated product preview audio, proxy URL: {audio_url}")

            return jsonify({
                'status': 'success',
                'audioUrl': audio_url,  # Use camelCase for frontend compatibility
                'voice': voice,
                'model': model,
                'language': language
            }), 200
        else:
            logger.error(f"❌ Audio generation failed: {response.text}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate preview audio'
            }), 500

    except Exception as e:
        logger.error(f"❌ Error generating preview audio: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@product_bp.route('/audio/proxy/<path:audio_path>', methods=['GET'])
def proxy_audio(audio_path):
    """Proxy audio files from audio-generation-factory service

    This endpoint proxies audio files from the internal audio-generation-factory
    service to make them accessible from the browser.

    Example:
        /api/audio/proxy/temp/preview_am_adam_en.wav
        -> http://audio-generation-factory:3000/temp/preview_am_adam_en.wav
    """
    try:
        # Get audio generation service URL
        AUDIO_GENERATION_URL = os.getenv(
            'AUDIO_GENERATION_URL',
            'http://audio-generation-factory:3000'
        )

        # Construct the full URL to the audio file
        audio_url = f"{AUDIO_GENERATION_URL}/{audio_path}"

        logger.info(f"🔊 Proxying audio file: {audio_path}")
        logger.debug(f"   Source URL: {audio_url}")

        # Stream the audio file from the audio generation service
        response = requests.get(
            audio_url,
            stream=True,
            timeout=60
        )

        if response.status_code != 200:
            logger.error(
                f"❌ Failed to fetch audio file: {audio_path} "
                f"(status: {response.status_code})"
            )
            return jsonify({
                'status': 'error',
                'message': 'Audio file not found'
            }), 404

        # Create a streaming response
        from flask import Response

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        # Determine content type based on file extension
        content_type = 'audio/wav'
        if audio_path.endswith('.mp3'):
            content_type = 'audio/mpeg'
        elif audio_path.endswith('.ogg'):
            content_type = 'audio/ogg'

        return Response(
            generate(),
            status=200,
            content_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Accept-Ranges': 'bytes'
            }
        )

    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout fetching audio file: {audio_path}")
        return jsonify({
            'status': 'error',
            'message': 'Request timeout'
        }), 504
    except Exception as e:
        logger.error(f"❌ Error proxying audio file {audio_path}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@product_bp.route('/ecommerce/public/product/<product_id>/images/<filename>', methods=['GET'])
def serve_product_images(product_id, filename):
    """Proxy product image files from inventory creation service"""
    try:
        url = f"{INVENTORY_CREATION_SERVICE_URL}/api/ecommerce/public/product/{product_id}/images/{filename}"
        logger.info(f"🖼️ Proxying product image: {product_id}/{filename}")

        # Get headers with authentication context
        headers = get_request_headers_with_context()

        response = requests.get(url, headers=headers, stream=True, timeout=30)

        if response.status_code != 200:
            logger.error(f"❌ Failed to fetch image: {filename} (status: {response.status_code})")
            return jsonify({'status': 'error', 'message': 'Image not found'}), 404

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        # Determine content type
        content_type = 'image/jpeg'
        if filename.endswith('.png'):
            content_type = 'image/png'
        elif filename.endswith('.gif'):
            content_type = 'image/gif'
        elif filename.endswith('.webp'):
            content_type = 'image/webp'

        return Response(
            generate(),
            status=200,
            content_type=content_type,
            headers={'Cache-Control': 'public, max-age=3600'}
        )

    except Exception as e:
        logger.error(f"❌ Error proxying image {filename}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product_bp.route('/ecommerce/public/product/<product_id>/images/<filename>', methods=['DELETE'])
def delete_product_image(product_id, filename):
    """Proxy: Delete a product image file"""
    logger.info('═══════════════════════════════════════════════════════')
    logger.info('🗑️ [API-SERVER] DELETE image endpoint called')
    logger.info(f'  - Product ID: {product_id}')
    logger.info(f'  - Filename: {filename}')
    logger.info(f'  - Full path: /api/ecommerce/public/product/{product_id}/images/{filename}')

    logger.info('🗑️ [API-SERVER] Proxying to inventory creation service...')
    response_data, status_code = proxy_to_inventory_service(
        f'/api/ecommerce/public/product/{product_id}/images/{filename}',
        method='DELETE'
    )

    logger.info('🗑️ [API-SERVER] Inventory creation service response:')
    logger.info(f'  - Status code: {status_code}')
    logger.info(f'  - Response data: {response_data}')
    logger.info('═══════════════════════════════════════════════════════')

    return jsonify(response_data), status_code


@product_bp.route('/ecommerce/public/product/<product_id>/videos/<filename>', methods=['GET'])
def serve_product_videos(product_id, filename):
    """Proxy product video files from inventory creation service"""
    try:
        url = f"{INVENTORY_CREATION_SERVICE_URL}/api/ecommerce/public/product/{product_id}/videos/{filename}"
        logger.info(f"🎥 Proxying product video: {product_id}/{filename}")

        # Get headers with authentication context
        headers = get_request_headers_with_context()

        response = requests.get(url, headers=headers, stream=True, timeout=60)

        if response.status_code != 200:
            logger.error(f"❌ Failed to fetch video: {filename} (status: {response.status_code})")
            return jsonify({'status': 'error', 'message': 'Video not found'}), 404

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        # Determine content type
        content_type = 'video/mp4'
        if filename.endswith('.webm'):
            content_type = 'video/webm'
        elif filename.endswith('.mov'):
            content_type = 'video/quicktime'

        return Response(
            generate(),
            status=200,
            content_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Accept-Ranges': 'bytes'
            }
        )

    except Exception as e:
        logger.error(f"❌ Error proxying video {filename}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product_bp.route('/ecommerce/public/product/<product_id>/videos/<filename>', methods=['DELETE'])
def delete_product_video(product_id, filename):
    """Proxy: Delete a product video file"""
    logger.info('═══════════════════════════════════════════════════════')
    logger.info(f'🗑️ [API-SERVER] DELETE video endpoint called')
    logger.info(f'  - Product ID: {product_id}')
    logger.info(f'  - Filename: {filename}')
    logger.info(f'  - Full path: /api/ecommerce/public/product/{product_id}/videos/{filename}')

    logger.info(f'🗑️ [API-SERVER] Proxying to inventory creation service...')
    response_data, status_code = proxy_to_inventory_service(
        f'/api/ecommerce/public/product/{product_id}/videos/{filename}',
        method='DELETE'
    )

    logger.info(f'🗑️ [API-SERVER] Inventory creation service response:')
    logger.info(f'  - Status code: {status_code}')
    logger.info(f'  - Response data: {response_data}')
    logger.info('═══════════════════════════════════════════════════════')

    return jsonify(response_data), status_code


@product_bp.route('/ecommerce/public/product/<product_id>/<filename>', methods=['GET'])
def serve_product_files(product_id, filename):
    """Proxy product audio/video files from inventory creation service"""
    try:
        url = f"{INVENTORY_CREATION_SERVICE_URL}/api/ecommerce/public/product/{product_id}/{filename}"
        logger.info(f"🔊 Proxying product file: {product_id}/{filename}")

        # Get headers with authentication context
        headers = get_request_headers_with_context()

        response = requests.get(url, headers=headers, stream=True, timeout=60)

        if response.status_code != 200:
            logger.error(f"❌ Failed to fetch file: {filename} (status: {response.status_code})")
            return jsonify({'status': 'error', 'message': 'File not found'}), 404

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        # Determine content type
        content_type = 'application/octet-stream'
        if filename.endswith('.wav'):
            content_type = 'audio/wav'
        elif filename.endswith('.mp3'):
            content_type = 'audio/mpeg'
        elif filename.endswith('.mp4'):
            content_type = 'video/mp4'
        elif filename.endswith('.webm'):
            content_type = 'video/webm'

        return Response(
            generate(),
            status=200,
            content_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Accept-Ranges': 'bytes'
            }
        )

    except Exception as e:
        logger.error(f"❌ Error proxying file {filename}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== Prompt Template Routes ==========

@product_bp.route('/prompt-templates', methods=['GET'])
def get_prompt_templates():
    """Proxy: Get all prompt templates"""
    response_data, status_code = proxy_to_inventory_service('/api/prompt-templates', method='GET')
    return jsonify(response_data), status_code


@product_bp.route('/prompt-templates/<template_id>', methods=['GET'])
def get_prompt_template(template_id):
    """Proxy: Get a specific prompt template by ID"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/prompt-templates/{template_id}', method='GET'
    )
    return jsonify(response_data), status_code


@product_bp.route('/prompt-templates', methods=['POST'])
def create_prompt_template():
    """Proxy: Create a new prompt template"""
    response_data, status_code = proxy_to_inventory_service(
        '/api/prompt-templates', method='POST', json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/prompt-templates/<template_id>', methods=['PUT'])
def update_prompt_template(template_id):
    """Proxy: Update a prompt template"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/prompt-templates/{template_id}', method='PUT', json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/prompt-templates/<template_id>', methods=['DELETE'])
def delete_prompt_template(template_id):
    """Proxy: Delete a prompt template"""
    response_data, status_code = proxy_to_inventory_service(
        f'/api/prompt-templates/{template_id}', method='DELETE'
    )
    return jsonify(response_data), status_code


@product_bp.route('/prompt-templates/generate', methods=['POST'])
def generate_prompt_template():
    """Proxy: Generate a prompt template using AI"""
    response_data, status_code = proxy_to_inventory_service(
        '/api/prompt-templates/generate', method='POST', json_data=request.get_json()
    )
    return jsonify(response_data), status_code


# ========== Generic Content Generation ==========

@product_bp.route('/content/generate', methods=['POST'])
def generate_content():
    """
    Proxy: Generic content generation endpoint

    This endpoint provides generic LLM content generation using prompt templates.
    It's independent of specific content types (products, blogs, social media, etc.)

    Request Body:
    {
        "template_id": "template_xyz",  // Required if use_template=true
        "template_variables": {          // Variables to fill in the template
            "product_name": "iPhone 15",
            "description": "Latest smartphone...",
            ...
        },
        "use_template": true,            // Use template or custom prompt
        "custom_prompt": "...",          // Optional: custom prompt if use_template=false
        "output_format": "json",         // "json" or "text"
        "temperature": 0.7,              // LLM temperature (0.0-1.0)
        "max_tokens": 2000               // Maximum tokens to generate
    }
    """
    response_data, status_code = proxy_to_inventory_service(
        '/api/content/generate', method='POST', json_data=request.get_json()
    )
    return jsonify(response_data), status_code
