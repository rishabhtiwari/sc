"""
Voice Routes - Proxy routes for voice generator service
All /api/news/audio/* requests are forwarded to the voice generator service
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
voice_bp = Blueprint('voice', __name__)
logger = logging.getLogger(__name__)

# Voice generator service URL
VOICE_SERVICE_URL = 'http://ichat-voice-generator:8094'


@voice_bp.route('/news/audio/stats', methods=['GET'])
def get_audio_stats():
    """Get voice generation statistics"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{VOICE_SERVICE_URL}/api/news/audio/stats', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to voice-generator stats: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@voice_bp.route('/news/audio/generate', methods=['POST'])
def generate_audio():
    """Generate audio for news article"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{VOICE_SERVICE_URL}/api/news/audio/generate',
            json=request.get_json(),
            headers=headers,
            timeout=120
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to voice-generator generate: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@voice_bp.route('/news/audio/list', methods=['GET'])
def list_audio():
    """List generated audio files"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{VOICE_SERVICE_URL}/api/news/audio/list', headers=headers, params=request.args, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to voice-generator list: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@voice_bp.route('/news/audio/serve/<path:filename>', methods=['GET'])
def serve_audio(filename):
    """Serve audio file (binary)"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{VOICE_SERVICE_URL}/api/news/audio/serve/{filename}',
            headers=headers,
            timeout=60,
            stream=True
        )
        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'audio/mpeg')
        )
    except Exception as e:
        logger.error(f"Error proxying to voice-generator serve: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

