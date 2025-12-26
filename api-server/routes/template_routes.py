"""
Template Routes - Proxy to template-service
"""

from flask import Blueprint, request, jsonify, Response
import logging
import requests
import os
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
template_bp = Blueprint('template', __name__)

# Setup logger
logger = logging.getLogger(__name__)

# Template service URL
TEMPLATE_SERVICE_URL = os.getenv('TEMPLATE_SERVICE_URL', 'http://ichat-template-service:5000')


@template_bp.route('/templates', methods=['GET'])
def list_templates():
    """Get list of available templates"""
    try:
        logger.info("📋 GET /templates - Proxying to template-service")
        headers = get_request_headers_with_context()
        
        # Forward query parameters (category filter)
        params = request.args.to_dict()
        
        response = requests.get(
            f'{TEMPLATE_SERVICE_URL}/api/templates',
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
        logger.error(f"Error proxying to template-service list: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/<template_id>', methods=['GET'])
def get_template(template_id):
    """Get specific template details"""
    try:
        logger.info(f"🔍 GET /templates/{template_id} - Proxying to template-service")
        headers = get_request_headers_with_context()
        
        response = requests.get(
            f'{TEMPLATE_SERVICE_URL}/api/templates/{template_id}',
            headers=headers,
            timeout=30
        )
        
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to template-service get: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates', methods=['POST'])
def create_template():
    """Create or update template"""
    try:
        logger.info("✨ POST /templates - Proxying to template-service")
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates',
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
        logger.error(f"Error proxying to template-service create: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete template"""
    try:
        logger.info(f"🗑️ DELETE /templates/{template_id} - Proxying to template-service")
        headers = get_request_headers_with_context()

        response = requests.delete(
            f'{TEMPLATE_SERVICE_URL}/api/templates/{template_id}',
            headers=headers,
            timeout=30
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to template-service delete: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/<template_id>/generate', methods=['POST'])
def generate_video_from_template(template_id):
    """Generate video from template with variables"""
    try:
        logger.info(f"🎬 POST /templates/{template_id}/generate - Proxying to template-service")
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates/{template_id}/generate',
            json=request.get_json(),
            headers=headers,
            timeout=300  # 5 minutes timeout for video generation
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to template-service generate: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/resolve', methods=['POST'])
def resolve_template():
    """Resolve template with variables"""
    try:
        logger.info("🎨 POST /templates/resolve - Proxying to template-service")
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates/resolve',
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
        logger.error(f"Error proxying to template-service resolve: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/preview', methods=['POST'])
def preview_template():
    """Generate preview video from template configuration"""
    try:
        logger.info("🎬 POST /templates/preview - Proxying to template-service")
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates/preview',
            json=request.get_json(),
            headers=headers,
            timeout=300  # 5 minutes timeout for video generation
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to template-service preview: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/preview/video/<filename>', methods=['GET'])
def serve_preview_video(filename):
    """Serve preview video files"""
    try:
        logger.info(f"🎥 GET /templates/preview/video/{filename} - Proxying to template-service")
        headers = get_request_headers_with_context()

        response = requests.get(
            f'{TEMPLATE_SERVICE_URL}/api/templates/preview/video/{filename}',
            headers=headers,
            timeout=60,
            stream=True
        )

        # Create response with proper CORS headers
        flask_response = Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'video/mp4')
        )

        # Add CORS headers explicitly for video files
        flask_response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        flask_response.headers['Access-Control-Allow-Credentials'] = 'true'
        flask_response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        flask_response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

        return flask_response
    except Exception as e:
        logger.error(f"Error serving preview video: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/preview/cleanup', methods=['POST'])
def cleanup_preview():
    """Cleanup temporary preview videos"""
    try:
        logger.info("🧹 POST /templates/preview/cleanup - Proxying to template-service")
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates/preview/cleanup',
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
        logger.error(f"Error proxying to template-service cleanup: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/upload/audio', methods=['POST', 'OPTIONS'])
def upload_audio():
    """Upload audio file for background music"""
    try:
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = Response()
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response, 200

        logger.info("🎵 POST /templates/upload/audio - Proxying to template-service")
        headers = get_request_headers_with_context()

        # Don't set Content-Type for multipart/form-data - let requests handle it
        # Forward the file upload
        files = {}
        if 'file' in request.files:
            file = request.files['file']
            files['file'] = (file.filename, file.stream, file.content_type)

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates/upload/audio',
            files=files,
            headers=headers,
            timeout=60
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying audio upload: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/upload/logo', methods=['POST', 'OPTIONS'])
def upload_logo():
    """Upload logo image file"""
    try:
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = Response()
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response, 200

        logger.info("🏷️ POST /templates/upload/logo - Proxying to template-service")
        headers = get_request_headers_with_context()

        # Don't set Content-Type for multipart/form-data - let requests handle it
        # Forward the file upload
        files = {}
        if 'file' in request.files:
            file = request.files['file']
            files['file'] = (file.filename, file.stream, file.content_type)

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates/upload/logo',
            files=files,
            headers=headers,
            timeout=60
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying logo upload: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/upload/image', methods=['POST', 'OPTIONS'])
def upload_image():
    """Upload image file for layers"""
    try:
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = Response()
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response, 200

        logger.info("🖼️ POST /templates/upload/image - Proxying to template-service")
        headers = get_request_headers_with_context()

        # Forward the file upload
        files = {}
        if 'file' in request.files:
            file = request.files['file']
            files['file'] = (file.filename, file.stream, file.content_type)

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates/upload/image',
            files=files,
            headers=headers,
            timeout=60
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying image upload: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/upload/video', methods=['POST', 'OPTIONS'])
def upload_video():
    """Upload video file for layers"""
    try:
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = Response()
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response, 200

        logger.info("🎥 POST /templates/upload/video - Proxying to template-service")
        headers = get_request_headers_with_context()

        # Forward the file upload
        files = {}
        if 'file' in request.files:
            file = request.files['file']
            files['file'] = (file.filename, file.stream, file.content_type)

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates/upload/video',
            files=files,
            headers=headers,
            timeout=120  # Longer timeout for video uploads
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying video upload: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/preview/thumbnail', methods=['POST', 'OPTIONS'])
def generate_thumbnail():
    """Generate thumbnail from preview video"""
    try:
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = Response()
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response, 200

        logger.info("🖼️ POST /templates/preview/thumbnail - Proxying to template-service")
        headers = get_request_headers_with_context()

        response = requests.post(
            f'{TEMPLATE_SERVICE_URL}/api/templates/preview/thumbnail',
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
        logger.error(f"Error proxying thumbnail generation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/preview/thumbnail/<filename>', methods=['GET'])
def serve_thumbnail(filename):
    """Serve thumbnail image"""
    try:
        logger.info(f"📥 GET /templates/preview/thumbnail/{filename} - Proxying to template-service")

        response = requests.get(
            f'{TEMPLATE_SERVICE_URL}/api/templates/preview/thumbnail/{filename}',
            timeout=30
        )

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'image/jpeg')
        )
    except Exception as e:
        logger.error(f"Error serving thumbnail: {str(e)}")
        return jsonify({'error': str(e)}), 500


@template_bp.route('/templates/assets/<filename>', methods=['GET'])
def serve_asset(filename):
    """Serve asset files (audio, images, etc.)"""
    try:
        logger.info(f"📁 GET /templates/assets/{filename} - Proxying to template-service")
        headers = get_request_headers_with_context()

        response = requests.get(
            f'{TEMPLATE_SERVICE_URL}/api/templates/assets/{filename}',
            headers=headers,
            timeout=60,
            stream=True
        )

        # Create response with proper headers
        flask_response = Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'application/octet-stream')
        )

        # Add CORS headers
        flask_response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        flask_response.headers['Access-Control-Allow-Credentials'] = 'true'

        return flask_response
    except Exception as e:
        logger.error(f"Error serving asset {filename}: {str(e)}")
        return jsonify({'error': str(e)}), 500

