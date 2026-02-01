"""
Asset Routes - Proxy routes for asset service
All /api/assets/* and /api/audio-library/* requests are forwarded to the asset service
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
asset_bp = Blueprint('asset', __name__)
logger = logging.getLogger(__name__)

# Asset service URL
ASSET_SERVICE_URL = 'http://ichat-asset-service:8099'


@asset_bp.route('/assets/upload', methods=['POST'])
def upload_asset():
    """Upload asset file"""
    try:
        logger.info("📤 Asset upload request received")
        logger.info(f"Request files: {list(request.files.keys())}")
        logger.info(f"Request form: {request.form.to_dict()}")
        logger.info(f"Request Content-Type: {request.content_type}")

        headers = get_request_headers_with_context()

        # Forward multipart/form-data request
        files = {}
        if 'file' in request.files:
            file = request.files['file']
            files['file'] = (file.filename, file.stream, file.content_type)
            logger.info(f"📎 File to forward: filename={file.filename}, content_type={file.content_type}")
        else:
            logger.error("❌ No 'file' in request.files!")

        # Get form data
        data = request.form.to_dict()

        # Remove Content-Type header to let requests library set it with boundary
        if 'Content-Type' in headers:
            logger.info(f"Removing Content-Type header: {headers['Content-Type']}")
            del headers['Content-Type']

        logger.info(f"Headers to forward: {headers}")
        logger.info(f"Data to forward: {data}")

        response = requests.post(
            f'{ASSET_SERVICE_URL}/api/assets/upload',
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )

        logger.info(f"Asset service response: status={response.status_code}")
        if response.status_code != 200:
            logger.error(f"Asset service error response: {response.text}")

        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to asset-service upload: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@asset_bp.route('/assets/<asset_id>', methods=['GET'])
def get_asset(asset_id):
    """Get asset metadata"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/assets/{asset_id}',
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to asset-service get: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@asset_bp.route('/assets/<asset_id>/download', methods=['GET'])
def download_asset(asset_id):
    """Download asset file"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/assets/{asset_id}/download',
            headers=headers,
            timeout=60,
            stream=True
        )
        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to asset-service download: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@asset_bp.route('/assets/download/<bucket>/<path:object_path>', methods=['GET'])
def download_asset_by_path(bucket, object_path):
    """Download asset file by bucket and object path (proxy URL)"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/assets/download/{bucket}/{object_path}',
            headers=headers,
            timeout=60,
            stream=True
        )

        # Forward all headers including Content-Type, Content-Disposition, etc.
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers_to_forward = {
            name: value for name, value in response.headers.items()
            if name.lower() not in excluded_headers
        }

        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            headers=headers_to_forward
        )
    except Exception as e:
        logger.error(f"Error proxying to asset-service download by path: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@asset_bp.route('/assets/<asset_id>/url', methods=['GET'])
def get_asset_url(asset_id):
    """Get pre-signed URL for asset"""
    try:
        headers = get_request_headers_with_context()
        params = request.args.to_dict()
        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/assets/{asset_id}/url',
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
        logger.error(f"Error proxying to asset-service url: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@asset_bp.route('/assets/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """Delete asset"""
    try:
        headers = get_request_headers_with_context()
        params = request.args.to_dict()
        response = requests.delete(
            f'{ASSET_SERVICE_URL}/api/assets/{asset_id}',
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
        logger.error(f"Error proxying to asset-service delete: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@asset_bp.route('/assets/', methods=['GET'])
def list_assets():
    """List assets"""
    try:
        headers = get_request_headers_with_context()
        params = request.args.to_dict()
        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/assets/',
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
        logger.error(f"Error proxying to asset-service list: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


# ============================================================================
# Audio Library Routes (Migration Compatible)
# ============================================================================

@asset_bp.route('/audio-library/', methods=['POST'])
def save_to_audio_library():
    """Save audio to library"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{ASSET_SERVICE_URL}/api/audio-library/',
            headers=headers,
            json=request.get_json(),
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to asset-service audio-library save: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@asset_bp.route('/audio-library/', methods=['GET'])
def get_audio_library():
    """Get audio library items"""
    try:
        headers = get_request_headers_with_context()
        params = request.args.to_dict()
        response = requests.get(
            f'{ASSET_SERVICE_URL}/api/audio-library/',
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
        logger.error(f"Error proxying to asset-service audio-library get: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@asset_bp.route('/audio-library/<audio_id>', methods=['DELETE'])
def delete_from_audio_library(audio_id):
    """Delete audio from library"""
    try:
        headers = get_request_headers_with_context()
        response = requests.delete(
            f'{ASSET_SERVICE_URL}/api/audio-library/{audio_id}',
            headers=headers,
            timeout=30
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type')
        )
    except Exception as e:
        logger.error(f"Error proxying to asset-service audio-library delete: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

