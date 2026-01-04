"""
Audio Studio Routes - API endpoints for Audio Studio feature
API Server acts as a proxy with authentication - all business logic in microservices
"""

import logging
import requests
import os
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import extract_user_context_from_headers

# Create blueprint
audio_studio_bp = Blueprint('audio_studio', __name__)
logger = logging.getLogger(__name__)

# Service URLs
AUDIO_GENERATION_URL = os.getenv(
    'AUDIO_GENERATION_URL',
    'http://audio-generation-factory:3000'
)
ASSET_SERVICE_URL = os.getenv(
    'ASSET_SERVICE_URL',
    'http://ichat-asset-service:8099'
)


@audio_studio_bp.route('/audio-studio/library', methods=['GET'])
def get_audio_library():
    """
    Proxy endpoint: Forward get-library request to asset-service
    API Server only handles authentication and proxying
    """
    try:
        # Extract user context from JWT (already validated by middleware)
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing customer_id or user_id'
            }), 400

        logger.info(f"Proxying get-library request to asset-service for customer {customer_id}, user {user_id}")

        # Forward request to asset-service with user context in headers
        headers = {
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }

        # Forward query parameters
        params = request.args.to_dict()

        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/audio-studio/library',
            headers=headers,
            params=params,
            timeout=30
        )

        # Convert MinIO URLs to proxy URLs for browser access
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'audio_files' in data:
                for audio in data['audio_files']:
                    audio_id = audio.get('audio_id')
                    if audio_id:
                        # Replace MinIO URL with proxy URL
                        audio['url'] = f'/api/audio-studio/library/{audio_id}/stream'
                        audio['audio_url'] = f'/api/audio-studio/library/{audio_id}/stream'
            return jsonify(data), 200

        # Return asset-service response
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying to asset-service: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Asset service error: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Error in get_audio_library proxy: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audio_studio_bp.route('/audio-studio/library', methods=['POST'])
def save_to_library():
    """
    Proxy endpoint: Forward save-to-library request to asset-service
    API Server only handles authentication and proxying
    """
    try:
        # Extract user context from JWT (already validated by middleware)
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing customer_id or user_id'
            }), 400

        # Get request data
        data = request.get_json()

        logger.info(f"Proxying save-to-library request to asset-service for customer {customer_id}, user {user_id}")

        # Forward request to asset-service with user context in headers
        headers = {
            'Content-Type': 'application/json',
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }

        response = requests.post(
            f'{ASSET_SERVICE_URL}/api/audio-studio/library',
            json=data,
            headers=headers,
            timeout=30
        )

        # Return asset-service response
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying to asset-service: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Asset service error: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Error in save_to_library proxy: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audio_studio_bp.route('/audio-studio/library/<audio_id>/stream', methods=['GET'])
def stream_library_audio(audio_id):
    """
    Stream audio file from library via asset-service
    This proxies the audio file from MinIO through asset-service
    """
    try:
        # Extract user context from JWT (already validated by middleware)
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing customer_id or user_id'
            }), 400

        logger.info(f"Streaming audio {audio_id} for customer {customer_id}")

        # Forward request to asset-service with user context in headers
        headers = {
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }

        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/audio-studio/library/{audio_id}/stream',
            headers=headers,
            stream=True,
            timeout=60
        )

        if response.status_code != 200:
            logger.error(f"Asset service returned error: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': f'Failed to stream audio: {response.status_code}'
            }), response.status_code

        # Stream the audio file with explicit headers
        flask_response = Response(
            response.iter_content(chunk_size=8192),
            status=200,
            mimetype='audio/wav'
        )
        flask_response.headers['Content-Disposition'] = f'inline; filename="{audio_id}.wav"'
        flask_response.headers['Accept-Ranges'] = 'bytes'
        flask_response.headers['Cache-Control'] = 'no-cache'

        logger.info(f"Streaming response headers: {dict(flask_response.headers)}")

        return flask_response

    except Exception as e:
        logger.error(f"Error streaming audio: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audio_studio_bp.route('/audio-studio/library/<audio_id>', methods=['DELETE'])
def delete_from_library(audio_id):
    """
    Proxy endpoint: Forward delete request to asset-service
    API Server only handles authentication and proxying
    """
    try:
        # Extract user context from JWT (already validated by middleware)
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing customer_id or user_id'
            }), 400

        logger.info(f"Proxying delete request to asset-service for audio {audio_id}")

        # Forward request to asset-service with user context in headers
        headers = {
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }

        response = requests.delete(
            f'{ASSET_SERVICE_URL}/api/audio-studio/library/{audio_id}',
            headers=headers,
            timeout=30
        )

        # Return asset-service response
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying to asset-service: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Asset service error: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Error in delete_from_library proxy: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audio_studio_bp.route('/audio-studio/library/<audio_id>', methods=['PUT'])
def update_library_item(audio_id):
    """
    Proxy endpoint: Forward update request to asset-service
    API Server only handles authentication and proxying
    """
    try:
        # Extract user context from JWT (already validated by middleware)
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing customer_id or user_id'
            }), 400

        # Get request data
        data = request.get_json()

        logger.info(f"Proxying update request to asset-service for audio {audio_id}")

        # Forward request to asset-service with user context in headers
        headers = {
            'Content-Type': 'application/json',
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }

        response = requests.put(
            f'{ASSET_SERVICE_URL}/api/audio-studio/library/{audio_id}',
            json=data,
            headers=headers,
            timeout=30
        )

        # Return asset-service response
        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying to asset-service: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Asset service error: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Error in update_library_item proxy: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audio_studio_bp.route('/audio-studio/config', methods=['GET'])
def get_audio_config():
    """Get TTS configuration (models, voices, default settings)"""
    try:
        logger.info("🎛️  GET /audio-studio/config - Fetching TTS configuration")

        # Call audio generation service config endpoint
        response = requests.get(
            f"{AUDIO_GENERATION_URL}/config",
            timeout=30
        )

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            logger.error(f"Failed to get audio config: {response.status_code}")
            return jsonify({
                'success': False,
                'error': 'Failed to get audio configuration'
            }), response.status_code

    except Exception as e:
        logger.error(f"Error getting audio config: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audio_studio_bp.route('/audio/generate', methods=['POST'])
def generate_audio():
    """Generate audio using TTS service"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('text'):
            return jsonify({
                'success': False,
                'error': 'Text is required'
            }), 400

        # Call audio generation service
        # No defaults - let the service use its configured defaults
        response = requests.post(
            f"{AUDIO_GENERATION_URL}/tts",
            json={
                'text': data.get('text'),
                'model': data.get('model'),  # Let service use default if not provided
                'voice': data.get('voice'),  # Let service use default if not provided
                'language': data.get('language'),  # Language code for multi-lingual models
                'speed': data.get('speed', 1.0),
                'format': data.get('format', 'wav')
            },
            timeout=600  # 10 minutes for model initialization
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Audio generated successfully: {result.get('audio_url')}")
            return jsonify(result), 200
        else:
            logger.error(f"Audio generation failed: {response.text}")
            return jsonify({
                'success': False,
                'error': 'Audio generation failed'
            }), response.status_code

    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audio_studio_bp.route('/audio/preview', methods=['POST'])
def preview_audio():
    """
    Generate preview audio for voice selection with caching
    All heavy lifting (cache check, generation, storage) is done by audio-generation service
    """
    try:
        # Extract user context
        user_context = extract_user_context_from_headers()

        data = request.get_json()
        preview_text = 'Hello! This is a preview of how this voice sounds.'
        text = data.get('text', preview_text)
        model = data.get('model')  # No default - let service decide
        voice = data.get('voice')  # No default - let service decide
        language = data.get('language', 'en')

        logger.info(f"🎤 Preview request - Model: {model}, Voice: {voice}, Language: {language}")

        # Call audio generation service preview endpoint (handles caching internally)
        response = requests.post(
            f"{AUDIO_GENERATION_URL}/preview",
            json={
                'text': text,
                'model': model,
                'voice': voice,
                'language': language
            },
            headers={
                'x-customer-id': user_context.get('customer_id', 'default'),
                'x-user-id': user_context.get('user_id', 'default')
            },
            timeout=600  # 10 minutes for model initialization on first run
        )

        if response.status_code == 200:
            result = response.json()

            # If cached, return the MinIO URL directly
            if result.get('cached'):
                logger.info(f"✅ Using cached preview for {voice}")
                return jsonify({
                    'status': 'success',
                    'audioUrl': result.get('audio_url'),
                    'duration': result.get('duration', 0),
                    'cached': True
                }), 200

            # If newly generated and saved to library, return MinIO URL
            if result.get('audio_id'):
                logger.info(f"✅ Preview generated and saved for {voice}")
                return jsonify({
                    'status': 'success',
                    'audioUrl': result.get('audio_url'),
                    'duration': result.get('duration', 0),
                    'cached': False
                }), 200

            # Fallback: return temp URL with proxy
            audio_url = result.get('audio_url', '')
            if audio_url.startswith('/'):
                audio_url = audio_url[1:]  # Remove leading slash

            # Convert to API proxy URL
            proxy_url = f'/api/audio/proxy/{audio_url}'

            return jsonify({
                'status': 'success',
                'audioUrl': proxy_url,
                'duration': result.get('duration', 0),
                'cached': False
            }), 200
        else:
            logger.error(f"Preview generation failed: {response.text}")
            return jsonify({
                'status': 'error',
                'error': 'Preview generation failed'
            }), response.status_code

    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@audio_studio_bp.route('/audio/proxy/<path:filename>', methods=['GET'])
def proxy_audio(filename):
    """Proxy audio files from audio generation service"""
    try:
        # Forward request to audio generation service
        response = requests.get(
            f"{AUDIO_GENERATION_URL}/{filename}",
            stream=True,
            timeout=60
        )

        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'audio/wav')
        )

    except Exception as e:
        logger.error(f"Error proxying audio: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


