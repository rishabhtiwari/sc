"""
Social Media Routes - Proxy routes for Social Media uploader service
All /api/social-media/* requests are forwarded to the Social Media uploader service
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
social_media_bp = Blueprint('social_media', __name__)
logger = logging.getLogger(__name__)

# Social Media uploader service URL
SOCIAL_MEDIA_SERVICE_URL = 'http://ichat-social-media-uploader:8097'


@social_media_bp.route('/social-media/instagram/oauth/initiate', methods=['GET'])
def instagram_oauth_initiate():
    """Initiate Instagram OAuth flow"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{SOCIAL_MEDIA_SERVICE_URL}/api/instagram/oauth/initiate',
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to Instagram OAuth initiate: {str(e)}")
        return jsonify({'error': str(e)}), 500


@social_media_bp.route('/social-media/instagram/oauth/callback', methods=['GET'])
def instagram_oauth_callback():
    """Handle Instagram OAuth callback"""
    try:
        headers = get_request_headers_with_context()
        # Forward query parameters
        params = request.args.to_dict()
        response = requests.get(
            f'{SOCIAL_MEDIA_SERVICE_URL}/api/instagram/oauth/callback',
            headers=headers,
            params=params,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to Instagram OAuth callback: {str(e)}")
        return jsonify({'error': str(e)}), 500


@social_media_bp.route('/social-media/instagram/credentials', methods=['GET'])
def get_instagram_credentials():
    """Get Instagram credentials for current user"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{SOCIAL_MEDIA_SERVICE_URL}/api/instagram/credentials',
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to Instagram credentials: {str(e)}")
        return jsonify({'error': str(e)}), 500


@social_media_bp.route('/social-media/instagram/credentials/<credential_id>', methods=['DELETE'])
def delete_instagram_credential(credential_id):
    """Delete Instagram credential"""
    try:
        headers = get_request_headers_with_context()
        response = requests.delete(
            f'{SOCIAL_MEDIA_SERVICE_URL}/api/instagram/credentials/{credential_id}',
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to Instagram credential delete: {str(e)}")
        return jsonify({'error': str(e)}), 500


@social_media_bp.route('/social-media/<platform>/credentials', methods=['GET'])
def get_platform_credentials(platform):
    """Get credentials for any platform"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{SOCIAL_MEDIA_SERVICE_URL}/api/{platform}/credentials',
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to {platform} credentials: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Health check endpoint
@social_media_bp.route('/social-media/health', methods=['GET'])
def health_check():
    """Health check for social media service"""
    try:
        response = requests.get(f'{SOCIAL_MEDIA_SERVICE_URL}/health', timeout=5)
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Social media service health check failed: {str(e)}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503

