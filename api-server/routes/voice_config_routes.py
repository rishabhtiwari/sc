"""
Voice Configuration Routes - Proxy routes for voice-generator service
All /api/voice/* requests are forwarded to the voice-generator service
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
voice_config_bp = Blueprint('voice_config', __name__)
logger = logging.getLogger(__name__)

# Voice generator service URL
VOICE_GENERATOR_URL = 'http://ichat-voice-generator:8094'


@voice_config_bp.route('/voice/config', methods=['GET'])
def get_voice_config():
    """Get voice configuration for the authenticated customer"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{VOICE_GENERATOR_URL}/api/voice/config',
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to voice config: {str(e)}")
        return jsonify({'error': str(e)}), 500


@voice_config_bp.route('/voice/config', methods=['PUT'])
def update_voice_config():
    """Update voice configuration for the authenticated customer"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.put(
            f'{VOICE_GENERATOR_URL}/api/voice/config',
            json=request.get_json(),
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to voice config update: {str(e)}")
        return jsonify({'error': str(e)}), 500


@voice_config_bp.route('/voice/available-models', methods=['GET'])
def get_available_models():
    """Get list of available TTS models"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{VOICE_GENERATOR_URL}/api/voice/available-models',
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to available models: {str(e)}")
        return jsonify({'error': str(e)}), 500


@voice_config_bp.route('/voice/available', methods=['GET'])
def get_available_voices():
    """Get list of available voices (legacy endpoint)"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{VOICE_GENERATOR_URL}/api/voice/available',
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to available voices: {str(e)}")
        return jsonify({'error': str(e)}), 500


@voice_config_bp.route('/voice/preview', methods=['POST'])
def preview_voice():
    """Preview a voice with sample text"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{VOICE_GENERATOR_URL}/api/voice/preview',
            json=request.get_json(),
            headers=headers,
            timeout=60
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to voice preview: {str(e)}")
        return jsonify({'error': str(e)}), 500


@voice_config_bp.route('/voice/preview/audio/<filename>', methods=['GET'])
def serve_preview_audio(filename):
    """Serve preview audio file"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{VOICE_GENERATOR_URL}/api/voice/preview/audio/{filename}',
            headers=headers,
            timeout=30,
            stream=True
        )
        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type='audio/wav',
            headers={
                'Content-Disposition': f'inline; filename="{filename}"'
            }
        )
    except Exception as e:
        logger.error(f"Error serving preview audio: {str(e)}")
        return jsonify({'error': str(e)}), 500
