"""
Product Routes - API Proxy for e-commerce product video management
Acts as a proxy to forward requests to the ecommerce-service backend
"""

import logging
import requests
import os
from flask import Blueprint, request, jsonify
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
product_bp = Blueprint('product', __name__)
logger = logging.getLogger(__name__)

# Service URLs
ECOMMERCE_SERVICE_URL = os.getenv(
    'ECOMMERCE_SERVICE_URL',
    'http://ichat-ecommerce-service:8099'
)


def proxy_to_ecommerce_service(path, method='GET', json_data=None, files=None):
    """Proxy request to ecommerce service"""
    try:
        headers = get_request_headers_with_context()
        url = f"{ECOMMERCE_SERVICE_URL}{path}"

        logger.info(f"🔄 Proxying {method} {url}")

        # Use longer timeout for audio/video generation endpoints (10 minutes)
        # Default timeout for other endpoints (30 seconds)
        timeout = 600 if any(x in path for x in ['/generate-audio', '/generate-video', '/generate-summary']) else 30
        kwargs = {'headers': headers, 'timeout': timeout}

        if files:
            # Handle file uploads - forward files to backend
            files_dict = {}
            for key in files:
                file_list = files.getlist(key)
                if len(file_list) == 1:
                    files_dict[key] = (file_list[0].filename, file_list[0].stream, file_list[0].content_type)
                else:
                    files_dict[key] = [(f.filename, f.stream, f.content_type) for f in file_list]
            kwargs['files'] = files_dict
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
        logger.error(f"❌ Timeout calling ecommerce service: {url}")
        return {'status': 'error', 'message': 'Service timeout'}, 504
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error to ecommerce service: {url}")
        return {'status': 'error', 'message': 'Service unavailable'}, 503
    except Exception as e:
        logger.error(f"❌ Error proxying to ecommerce service: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500


@product_bp.route('/products', methods=['POST'])
def create_product():
    """Proxy: Create a new product"""
    response_data, status_code = proxy_to_ecommerce_service(
        '/api/products', method='POST', json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/products', methods=['GET'])
def get_products():
    """Proxy: Get all products"""
    response_data, status_code = proxy_to_ecommerce_service('/api/products', method='GET')
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Proxy: Get a specific product by ID"""
    response_data, status_code = proxy_to_ecommerce_service(
        f'/api/products/{product_id}', method='GET'
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Proxy: Update a product"""
    response_data, status_code = proxy_to_ecommerce_service(
        f'/api/products/{product_id}', method='PUT', json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Proxy: Delete a product"""
    response_data, status_code = proxy_to_ecommerce_service(
        f'/api/products/{product_id}', method='DELETE'
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/stats', methods=['GET'])
def get_product_stats():
    """Proxy: Get product statistics"""
    response_data, status_code = proxy_to_ecommerce_service('/api/products/stats', method='GET')
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/generate-summary', methods=['POST'])
def generate_summary(product_id):
    """Proxy: Generate AI summary for product"""
    response_data, status_code = proxy_to_ecommerce_service(
        f'/api/products/{product_id}/generate-summary',
        method='POST',
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/upload-media', methods=['POST'])
def upload_media(product_id):
    """Proxy: Upload media files for product"""
    response_data, status_code = proxy_to_ecommerce_service(
        f'/api/products/{product_id}/upload-media',
        method='POST',
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/media', methods=['POST'])
def upload_media_alt(product_id):
    """Proxy: Upload media files for product (alternative endpoint)"""
    response_data, status_code = proxy_to_ecommerce_service(
        f'/api/products/{product_id}/upload-media',
        method='POST',
        files=request.files
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/generate-audio', methods=['POST'])
def generate_audio(product_id):
    """Proxy: Generate audio from AI summary"""
    response_data, status_code = proxy_to_ecommerce_service(
        f'/api/products/{product_id}/generate-audio',
        method='POST',
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/products/<product_id>/generate-video', methods=['POST'])
def generate_video(product_id):
    """Proxy: Generate final product video"""
    response_data, status_code = proxy_to_ecommerce_service(
        f'/api/products/{product_id}/generate-video',
        method='POST',
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@product_bp.route('/audio/preview', methods=['POST'])
def preview_audio():
    """Generate preview audio for voice selection"""
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

        logger.info(f"🎤 Generating preview audio - Model: {model}, Voice: {voice}, Language: {language}")

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

            logger.info(f"✅ Generated preview audio, proxy URL: {audio_url}")

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
