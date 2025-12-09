"""
Video Configuration Routes - Proxy to video-generator service
"""

from flask import Blueprint, request, jsonify
import logging
import requests
import os

# Create blueprint
video_config_bp = Blueprint('video_config', __name__)

# Setup logger
logger = logging.getLogger(__name__)

# Video generator service URL
VIDEO_GENERATOR_URL = os.getenv('VIDEO_GENERATOR_URL', 'http://job-video-generator:8095')


# Helper function to proxy requests
def proxy_to_video_generator(path, method='GET', json_data=None, params=None):
    """Proxy request to video-generator service"""
    try:
        url = f'{VIDEO_GENERATOR_URL}{path}'

        if method == 'GET':
            response = requests.get(url, params=params, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=json_data, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, json=json_data, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=30)
        else:
            return jsonify({'status': 'error', 'error': 'Invalid method'}), 400

        return jsonify(response.json()), response.status_code

    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Timeout connecting to video-generator for {path}")
        return jsonify({'status': 'error', 'error': 'Service timeout'}), 504
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 Cannot connect to video-generator for {path}")
        return jsonify({'status': 'error', 'error': 'Service unavailable'}), 503
    except Exception as e:
        logger.error(f"💥 Error proxying to video-generator: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@video_config_bp.route('/videos/configs', methods=['POST'])
def create_video_config():
    """Proxy: Create a new video configuration"""
    logger.info("📝 POST /videos/configs - Proxying to video-generator")
    return proxy_to_video_generator('/configs', method='POST', json_data=request.get_json())


@video_config_bp.route('/videos/configs', methods=['GET'])
def get_video_configs():
    """Proxy: Get all video configurations"""
    logger.info("📋 GET /videos/configs - Proxying to video-generator")
    return proxy_to_video_generator('/configs', method='GET', params=request.args)


@video_config_bp.route('/videos/configs/<config_id>', methods=['GET'])
def get_video_config(config_id):
    """Proxy: Get a specific video configuration"""
    logger.info(f"🔍 GET /videos/configs/{config_id} - Proxying to video-generator")
    return proxy_to_video_generator(f'/configs/{config_id}', method='GET')


@video_config_bp.route('/videos/configs/<config_id>', methods=['PUT'])
def update_video_config(config_id):
    """Proxy: Update a video configuration"""
    logger.info(f"✏️ PUT /videos/configs/{config_id} - Proxying to video-generator")
    return proxy_to_video_generator(f'/configs/{config_id}', method='PUT', json_data=request.get_json())


@video_config_bp.route('/videos/configs/<config_id>', methods=['DELETE'])
def delete_video_config(config_id):
    """Proxy: Delete a video configuration"""
    logger.info(f"🗑️ DELETE /videos/configs/{config_id} - Proxying to video-generator")
    return proxy_to_video_generator(f'/configs/{config_id}', method='DELETE')


@video_config_bp.route('/videos/configs/<config_id>/merge', methods=['POST'])
def merge_video_config(config_id):
    """Proxy: Trigger video merge for a configuration"""
    logger.info(f"🎬 POST /videos/configs/{config_id}/merge - Proxying to video-generator")
    return proxy_to_video_generator(f'/configs/{config_id}/merge', method='POST', json_data=request.get_json())


@video_config_bp.route('/videos/configs/<config_id>/merge-status', methods=['GET'])
def get_config_merge_status(config_id):
    """Proxy: Get merge status for a configuration"""
    logger.info(f"📊 GET /videos/configs/{config_id}/merge-status - Proxying to video-generator")
    return proxy_to_video_generator(f'/configs/{config_id}/merge-status', method='GET')


@video_config_bp.route('/videos/configs/due', methods=['GET'])
def get_due_configs():
    """Proxy: Get configurations due for processing"""
    logger.info("📅 GET /videos/configs/due - Proxying to video-generator")
    return proxy_to_video_generator('/configs/due', method='GET')


@video_config_bp.route('/videos/available-news', methods=['GET'])
def get_available_news():
    """Proxy: Get list of news articles with videos available for merging"""
    logger.info("📰 GET /videos/available-news - Proxying to video-generator")
    return proxy_to_video_generator('/available-news', method='GET', params=request.args)

