"""
Image Routes - Proxy routes for IOPaint watermark removal service
All /api/image/* requests are forwarded to the IOPaint service
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
image_bp = Blueprint('image', __name__)
logger = logging.getLogger(__name__)

# IOPaint service URL
IOPAINT_SERVICE_URL = 'http://ichat-iopaint:8096'


@image_bp.route('/image/stats', methods=['GET'])
@image_bp.route('/stats', methods=['GET'])
def get_image_stats():
    """Get IOPaint processing statistics"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{IOPAINT_SERVICE_URL}/api/stats', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to IOPaint stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@image_bp.route('/image/images', methods=['GET'])
@image_bp.route('/images', methods=['GET'])
def get_images():
    """Get list of images"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{IOPAINT_SERVICE_URL}/api/images', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to IOPaint images: {str(e)}")
        return jsonify({'error': str(e)}), 500


@image_bp.route('/image/next', methods=['GET'])
@image_bp.route('/next-image', methods=['GET'])
def get_next_image():
    """Get next image to process"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{IOPAINT_SERVICE_URL}/api/next-image', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to IOPaint next-image: {str(e)}")
        return jsonify({'error': str(e)}), 500


@image_bp.route('/image/process', methods=['POST'])
def process_image():
    """Process image to remove watermark"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{IOPAINT_SERVICE_URL}/api/process',
            json=request.get_json(),
            headers=headers,
            timeout=120
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to IOPaint process: {str(e)}")
        return jsonify({'error': str(e)}), 500


@image_bp.route('/image/save', methods=['POST'])
def save_image():
    """Save processed image"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{IOPAINT_SERVICE_URL}/api/save',
            json=request.get_json(),
            headers=headers,
            timeout=60
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to IOPaint save: {str(e)}")
        return jsonify({'error': str(e)}), 500


@image_bp.route('/image/replace-image', methods=['POST'])
def replace_image():
    """Replace image with new one"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{IOPAINT_SERVICE_URL}/api/replace-image',
            json=request.get_json(),
            headers=headers,
            timeout=60
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to IOPaint replace-image: {str(e)}")
        return jsonify({'error': str(e)}), 500


@image_bp.route('/image/skip', methods=['POST'])
@image_bp.route('/skip', methods=['POST'])
def skip_image():
    """Skip current image"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{IOPAINT_SERVICE_URL}/api/skip',
            json=request.get_json(),
            headers=headers,
            timeout=30
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to IOPaint skip: {str(e)}")
        return jsonify({'error': str(e)}), 500


@image_bp.route('/image/cleaned/<path:filename>', methods=['GET'])
@image_bp.route('/cleaned-image/<path:filename>', methods=['GET'])
def get_cleaned_image(filename):
    """Get cleaned image file (binary)"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{IOPAINT_SERVICE_URL}/api/cleaned-image/{filename}',
            headers=headers,
            timeout=60,
            stream=True
        )
        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except Exception as e:
        logger.error(f"Error proxying to IOPaint cleaned-image: {str(e)}")
        return jsonify({'error': str(e)}), 500


@image_bp.route('/proxy-image', methods=['GET'])
def proxy_image():
    """Proxy image from external URL"""
    try:
        headers = get_request_headers_with_context()
        # Forward query parameters
        params = request.args.to_dict()
        response = requests.get(
            f'{IOPAINT_SERVICE_URL}/api/proxy-image',
            params=params,
            headers=headers,
            timeout=60,
            stream=True
        )
        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except Exception as e:
        logger.error(f"Error proxying to IOPaint proxy-image: {str(e)}")
        return jsonify({'error': str(e)}), 500


@image_bp.route('/proxy-image/<doc_id>', methods=['GET'])
def proxy_image_by_id(doc_id):
    """Proxy image from external URL by document ID"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{IOPAINT_SERVICE_URL}/api/proxy-image/{doc_id}',
            headers=headers,
            timeout=60,
            stream=True
        )
        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except Exception as e:
        logger.error(f"Error proxying to IOPaint proxy-image by ID: {str(e)}")
        return jsonify({'error': str(e)}), 500

