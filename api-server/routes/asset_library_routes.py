"""
Asset Library Routes - Unified proxy routes for all asset libraries
Handles Image Library and Video Library proxy requests to asset-service
(Audio Library is handled in audio_studio_routes.py, Text Library uses assets routes)
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import extract_user_context_from_headers

# Create blueprint
asset_library_bp = Blueprint('asset_library', __name__)
logger = logging.getLogger(__name__)

# Asset service URL
ASSET_SERVICE_URL = 'http://ichat-asset-service:8099'


# ============================================================================
# Image Library Routes
# ============================================================================

@asset_library_bp.route('/image-library/library', methods=['GET'])
def get_image_library():
    """Get image library items"""
    try:
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({'success': False, 'error': 'Missing customer_id or user_id'}), 400

        headers = {
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }
        params = request.args.to_dict()

        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/image-library/library',
            headers=headers,
            params=params,
            timeout=30
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        logger.error(f"Error proxying to image library: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@asset_library_bp.route('/image-library/library', methods=['POST'])
def save_to_image_library():
    """Save image to library"""
    try:
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({'success': False, 'error': 'Missing customer_id or user_id'}), 400

        headers = {
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }

        # Forward query parameters (name, folder, etc.)
        params = request.args.to_dict()

        # Forward multipart form data
        response = requests.post(
            f'{ASSET_SERVICE_URL}/api/image-library/library',
            headers=headers,
            files=request.files,
            data=request.form,
            params=params,  # Forward query parameters
            timeout=60
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        logger.error(f"Error saving to image library: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@asset_library_bp.route('/image-library/library/<image_id>', methods=['DELETE'])
def delete_from_image_library(image_id):
    """Delete image from library"""
    try:
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({'success': False, 'error': 'Missing customer_id or user_id'}), 400

        headers = {
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }

        response = requests.delete(
            f'{ASSET_SERVICE_URL}/api/image-library/library/{image_id}',
            headers=headers,
            timeout=30
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        logger.error(f"Error deleting from image library: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Video Library Routes
# ============================================================================

@asset_library_bp.route('/video-library/library', methods=['GET'])
def get_video_library():
    """Get video library items"""
    try:
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({'success': False, 'error': 'Missing customer_id or user_id'}), 400

        headers = {
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }
        params = request.args.to_dict()

        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/video-library/library',
            headers=headers,
            params=params,
            timeout=30
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        logger.error(f"Error proxying to video library: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@asset_library_bp.route('/video-library/library', methods=['POST'])
def save_to_video_library():
    """Save video to library"""
    try:
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({'success': False, 'error': 'Missing customer_id or user_id'}), 400

        headers = {
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }

        # Forward query parameters (name, duration, folder, etc.)
        params = request.args.to_dict()

        # Forward multipart form data
        response = requests.post(
            f'{ASSET_SERVICE_URL}/api/video-library/library',
            headers=headers,
            files=request.files,
            data=request.form,
            params=params,  # Forward query parameters
            timeout=120  # Longer timeout for video uploads
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        logger.error(f"Error saving to video library: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@asset_library_bp.route('/video-library/library/<video_id>', methods=['DELETE'])
def delete_from_video_library(video_id):
    """Delete video from library"""
    try:
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        if not customer_id or not user_id:
            return jsonify({'success': False, 'error': 'Missing customer_id or user_id'}), 400

        headers = {
            'X-Customer-Id': customer_id,
            'X-User-Id': user_id
        }

        response = requests.delete(
            f'{ASSET_SERVICE_URL}/api/video-library/library/{video_id}',
            headers=headers,
            timeout=30
        )

        return jsonify(response.json()), response.status_code

    except Exception as e:
        logger.error(f"Error deleting from video library: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

