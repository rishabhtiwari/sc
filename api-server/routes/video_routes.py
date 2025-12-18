"""
Video Routes - Proxy routes for video generator service
All /api/videos/* requests are forwarded to the video generator service
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
video_bp = Blueprint('video', __name__)
logger = logging.getLogger(__name__)

# Video generator service URL
VIDEO_SERVICE_URL = 'http://ichat-video-generator:8095'


@video_bp.route('/videos/background-audio', methods=['GET'])
def get_background_audio_list():
    """Get list of available background audio files"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{VIDEO_SERVICE_URL}/background-audio', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator background-audio: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/background-audio', methods=['POST'])
def upload_background_audio():
    """Upload new background audio file"""
    try:
        headers = get_request_headers_with_context()
        logger.info(f"📤 Upload background audio - headers to forward: {headers}")
        # Handle file upload
        if 'file' in request.files:
            file_obj = request.files['file']
            logger.info(f"📎 Received file: filename={file_obj.filename}, content_type={file_obj.content_type}")

            # Properly forward the file with its filename preserved
            files = {'file': (file_obj.filename, file_obj.stream, file_obj.content_type)}
            response = requests.post(
                f'{VIDEO_SERVICE_URL}/background-audio',
                files=files,
                data=request.form,
                headers=headers,
                timeout=60
            )
        else:
            headers['Content-Type'] = 'application/json'
            response = requests.post(
                f'{VIDEO_SERVICE_URL}/background-audio',
                json=request.get_json(),
                headers=headers,
                timeout=60
            )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator background-audio upload: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/background-audio/<filename>', methods=['DELETE'])
def delete_background_audio(filename):
    """Delete background audio file"""
    try:
        headers = get_request_headers_with_context()
        response = requests.delete(f'{VIDEO_SERVICE_URL}/background-audio/{filename}', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator background-audio delete: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/background-audio/<filename>/download', methods=['GET'])
def download_background_audio(filename):
    """Download background audio file (binary)"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(
            f'{VIDEO_SERVICE_URL}/background-audio/{filename}/download',
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
        logger.error(f"Error proxying to video-generator background-audio download: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/configs', methods=['GET'])
def get_video_configs():
    """Get list of video configurations"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{VIDEO_SERVICE_URL}/configs', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator configs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/configs', methods=['POST'])
def create_video_config():
    """Create new video configuration"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{VIDEO_SERVICE_URL}/configs',
            json=request.get_json(),
            headers=headers,
            timeout=30
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator configs create: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/configs/<config_id>', methods=['GET'])
def get_video_config(config_id):
    """Get specific video configuration"""
    try:
        headers = get_request_headers_with_context()
        response = requests.get(f'{VIDEO_SERVICE_URL}/configs/{config_id}', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator config get: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/configs/<config_id>', methods=['PUT'])
def update_video_config(config_id):
    """Update video configuration"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.put(
            f'{VIDEO_SERVICE_URL}/configs/{config_id}',
            json=request.get_json(),
            headers=headers,
            timeout=30
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator config update: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/configs/<config_id>', methods=['DELETE'])
def delete_video_config(config_id):
    """Delete video configuration"""
    try:
        headers = get_request_headers_with_context()
        response = requests.delete(f'{VIDEO_SERVICE_URL}/configs/{config_id}', headers=headers, timeout=30)
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator config delete: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/merge', methods=['POST'])
def merge_videos():
    """Merge multiple videos into one"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{VIDEO_SERVICE_URL}/merge',
            json=request.get_json(),
            headers=headers,
            timeout=300
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator merge: {str(e)}")
        return jsonify({'error': str(e)}), 500


@video_bp.route('/videos/recompute', methods=['POST'])
def recompute_videos():
    """Recompute video processing"""
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        response = requests.post(
            f'{VIDEO_SERVICE_URL}/recompute',
            json=request.get_json(),
            headers=headers,
            timeout=300
        )
        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator recompute: {str(e)}")
        return jsonify({'error': str(e)}), 500



@video_bp.route('/videos/merge-latest', methods=['POST'])
def merge_latest_videos():
    """
    Merge latest news videos into a single compilation video with configuration

    Request Body:
        {
            "categories": ["business", "technology"],  // Optional
            "country": "us",  // Optional
            "language": "en",  // Optional
            "videoCount": 20,  // Required
            "title": "Top 20 News Stories"  // Required
        }

    Returns:
        JSON response with merge operation status and details
    """
    try:
        logger.info("🎬 POST /videos/merge-latest - Proxying to video-generator")

        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'

        response = requests.post(
            f'{VIDEO_SERVICE_URL}/merge-latest',
            json=request.get_json(),
            headers=headers,
            timeout=300
        )

        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator merge-latest: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@video_bp.route('/videos/merge-status', methods=['GET'])
def get_video_merge_status():
    """
    Check the status of video merging process

    Returns:
        JSON response with merge status and file info
    """
    try:
        logger.info("🔍 GET /videos/merge-status - Proxying to video-generator")

        headers = get_request_headers_with_context()

        response = requests.get(
            f'{VIDEO_SERVICE_URL}/merge-status',
            headers=headers,
            timeout=30
        )

        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator merge-status: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@video_bp.route('/videos/download', methods=['GET'])
def get_video_download():
    """
    Get download information for the merged video

    Returns:
        JSON response with download URL and file info
    """
    try:
        logger.info("📥 GET /videos/download - Proxying to video-generator")

        headers = get_request_headers_with_context()

        response = requests.get(
            f'{VIDEO_SERVICE_URL}/download',
            headers=headers,
            timeout=30
        )

        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        logger.error(f"Error proxying to video-generator download: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@video_bp.route('/videos/latest-20-news.mp4', methods=['GET'])
def download_latest_news_video():
    """
    Download the latest 20 news compilation video

    Returns:
        MP4 video file stream containing latest news compilation
    """
    try:
        logger.info("📥 GET /videos/latest-20-news.mp4 - Streaming video from video-generator")

        headers = get_request_headers_with_context()

        response = requests.get(
            f'{VIDEO_SERVICE_URL}/download/latest-20-news.mp4',
            headers=headers,
            stream=True,
            timeout=60
        )

        if response.status_code == 200:
            # Stream the video file back to the client
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

            return Response(
                generate(),
                content_type='video/mp4',
                headers={
                    'Content-Disposition': 'attachment; filename="latest-20-news.mp4"',
                    'Content-Length': response.headers.get('Content-Length', ''),
                    'Accept-Ranges': 'bytes'
                }
            )
        else:
            # Handle error response from video service
            try:
                error_data = response.json()
                return jsonify(error_data), response.status_code
            except:
                return jsonify({
                    'error': 'Failed to download video',
                    'status': 'error'
                }), response.status_code

    except Exception as e:
        logger.error(f"Error streaming video from video-generator: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

