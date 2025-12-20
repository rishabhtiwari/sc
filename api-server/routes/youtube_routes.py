"""
YouTube Routes - Proxy routes for YouTube uploader service
All /api/youtube/* requests are forwarded to the YouTube uploader service
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
youtube_bp = Blueprint('youtube', __name__)
logger = logging.getLogger(__name__)

# YouTube uploader service URL
YOUTUBE_SERVICE_URL = 'http://ichat-youtube-uploader:8097'


@youtube_bp.route('/youtube/stats', methods=['GET'])
def get_youtube_stats():
    """Get YouTube upload statistics"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{YOUTUBE_SERVICE_URL}/api/stats', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/upload-latest-20', methods=['POST'])
def upload_latest_20():
    """Upload latest 20 videos to YouTube"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{YOUTUBE_SERVICE_URL}/api/upload-latest-20',
            json=request.get_json(),
            headers=headers,
            timeout=300
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube upload-latest-20: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/upload-config', methods=['GET'])
def get_upload_config():
    """Get YouTube upload configuration"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{YOUTUBE_SERVICE_URL}/api/upload-config', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube upload-config: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/upload-config', methods=['PUT'])
def update_upload_config():
    """Update YouTube upload configuration"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.put(
            f'{YOUTUBE_SERVICE_URL}/api/upload-config',
            json=request.get_json(),
            headers=headers,
            timeout=30
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube upload-config: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/upload-config/<config_id>', methods=['POST'])
def upload_config_video(config_id):
    """Upload config-specific video to YouTube"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{YOUTUBE_SERVICE_URL}/api/upload-config/{config_id}',
            json=request.get_json(),
            headers=headers,
            timeout=300  # 5 minutes timeout for video upload
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube upload-config/{config_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/shorts/pending', methods=['GET'])
def get_pending_shorts():
    """Get pending YouTube shorts with pagination"""
    try:
        headers = get_request_headers_with_context()
        # Forward query parameters (page, limit) to the backend service
        response = requests.get(f'{YOUTUBE_SERVICE_URL}/api/shorts/pending', headers=headers, params=request.args, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube shorts/pending: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/shorts/upload', methods=['POST'])
def upload_short():
    """Upload a YouTube short"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{YOUTUBE_SERVICE_URL}/api/shorts/upload',
            json=request.get_json(),
            headers=headers,
            timeout=300
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube shorts/upload: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/shorts/upload/<article_id>', methods=['POST'])
def upload_short_by_id(article_id):
    """Upload a specific YouTube short by article ID"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{YOUTUBE_SERVICE_URL}/api/shorts/upload/{article_id}',
            json=request.get_json(),
            headers=headers,
            timeout=300
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube shorts/upload/{article_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/oauth-callback', methods=['GET', 'POST'])
def oauth_callback():
    """Handle YouTube OAuth callback"""
    try:
        headers = get_request_headers_with_context()
        # Forward query parameters
        params = request.args.to_dict()

        # Use the same HTTP method as the incoming request
        if request.method == 'POST':
            # For POST requests, also forward the body
            response = requests.post(
                f'{YOUTUBE_SERVICE_URL}/api/oauth-callback',
                params=params,
                json=request.get_json() if request.is_json else None,
                data=request.form if request.form else None,
                headers=headers,
                timeout=30
            )
        else:
            # For GET requests
            response = requests.get(
                f'{YOUTUBE_SERVICE_URL}/api/oauth-callback',
                params=params,
                headers=headers,
                timeout=30
            )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube oauth-callback: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/auth/start', methods=['POST'])
def start_auth():
    """Start YouTube OAuth flow"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{YOUTUBE_SERVICE_URL}/api/auth/start',
            json=request.get_json(),
            headers=headers,
            timeout=30
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube auth/start: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/credentials', methods=['GET'])
def get_credentials():
    """Get YouTube credentials"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{YOUTUBE_SERVICE_URL}/api/credentials', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube credentials: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/credentials', methods=['POST'])
def save_credentials():
    """Save YouTube credentials"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{YOUTUBE_SERVICE_URL}/api/credentials',
            json=request.get_json(),
            headers=headers,
            timeout=30
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube credentials: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/credentials/<credential_id>', methods=['GET'])
def get_credential_by_id(credential_id):
    """Get specific YouTube credential by ID"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{YOUTUBE_SERVICE_URL}/api/credentials/{credential_id}', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to YouTube credential {credential_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/credentials/<credential_id>', methods=['PUT'])
def update_credential(credential_id):
    """Update specific YouTube credential"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.put(
            f'{YOUTUBE_SERVICE_URL}/api/credentials/{credential_id}',
            json=request.get_json(),
            headers=headers,
            timeout=30
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error updating YouTube credential {credential_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@youtube_bp.route('/youtube/credentials/<credential_id>', methods=['DELETE'])
def delete_credential(credential_id):
    """Delete specific YouTube credential"""
    try:
        headers = get_request_headers_with_context()
        response = requests.delete(f'{YOUTUBE_SERVICE_URL}/api/credentials/{credential_id}', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error deleting YouTube credential {credential_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

