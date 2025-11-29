#!/usr/bin/env python3
"""
Frontend Routes - Centralized API proxy for all frontend services
This blueprint provides a unified API gateway for the frontend to access all backend services
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
import os

# Create blueprint
frontend_bp = Blueprint('frontend', __name__)
logger = logging.getLogger(__name__)

# Service URLs from environment variables
NEWS_FETCHER_URL = os.getenv('NEWS_FETCHER_SERVICE_URL', 'http://ichat-news-fetcher:8093')
IOPAINT_URL = os.getenv('IOPAINT_SERVICE_URL', 'http://ichat-iopaint:8096')
YOUTUBE_UPLOADER_URL = os.getenv('YOUTUBE_UPLOADER_SERVICE_URL', 'http://ichat-youtube-uploader:8097')
VOICE_GENERATOR_URL = os.getenv('VOICE_GENERATOR_SERVICE_URL', 'http://ichat-voice-generator:8094')
AUDIO_GENERATION_URL = os.getenv('AUDIO_GENERATION_SERVICE_URL', 'http://audio-generation-factory:3000')

# Request timeout
REQUEST_TIMEOUT = 30


def proxy_request(target_url, method='GET', data=None, files=None, params=None, headers=None):
    """
    Generic proxy function to forward requests to backend services
    
    Args:
        target_url: Target service URL
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body data
        files: Files to upload
        params: Query parameters
        headers: Request headers
        
    Returns:
        Response from target service
    """
    try:
        logger.info(f"🔄 Proxying {method} request to: {target_url}")
        
        # Prepare headers
        proxy_headers = {}
        if headers:
            # Forward relevant headers
            for key in ['Content-Type', 'Authorization']:
                if key in headers:
                    proxy_headers[key] = headers[key]
        
        # Make request to target service
        if method == 'GET':
            response = requests.get(target_url, params=params, headers=proxy_headers, timeout=REQUEST_TIMEOUT)
        elif method == 'POST':
            if files:
                response = requests.post(target_url, data=data, files=files, headers=proxy_headers, timeout=REQUEST_TIMEOUT)
            else:
                response = requests.post(target_url, json=data, headers=proxy_headers, timeout=REQUEST_TIMEOUT)
        elif method == 'PUT':
            response = requests.put(target_url, json=data, headers=proxy_headers, timeout=REQUEST_TIMEOUT)
        elif method == 'DELETE':
            response = requests.delete(target_url, headers=proxy_headers, timeout=REQUEST_TIMEOUT)
        else:
            return jsonify({'error': f'Unsupported method: {method}'}), 400
        
        logger.info(f"✅ Proxy response: {response.status_code}")
        
        # Return response
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
        
    except requests.exceptions.Timeout:
        logger.error(f"⏱️ Request timeout to {target_url}")
        return jsonify({'error': 'Request timeout'}), 504
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 Connection error to {target_url}")
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        logger.error(f"❌ Proxy error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# NEWS FETCHER PROXY ROUTES
# ============================================================================

@frontend_bp.route('/frontend/news-fetcher/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_news_fetcher(subpath):
    """Proxy requests to News Fetcher service"""
    target_url = f"{NEWS_FETCHER_URL}/{subpath}"
    return proxy_request(
        target_url,
        method=request.method,
        data=request.get_json() if request.is_json else request.form,
        params=request.args,
        headers=request.headers
    )


# ============================================================================
# WATERMARK REMOVER (IOPAINT) PROXY ROUTES
# ============================================================================

@frontend_bp.route('/frontend/watermark/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_watermark(subpath):
    """Proxy requests to IOPaint (Watermark Remover) service"""
    target_url = f"{IOPAINT_URL}/{subpath}"
    
    # Handle file uploads for image processing
    files = None
    data = None
    
    if request.files:
        files = {key: (file.filename, file.stream, file.content_type) 
                for key, file in request.files.items()}
        data = request.form
    elif request.is_json:
        data = request.get_json()
    else:
        data = request.form
    
    return proxy_request(
        target_url,
        method=request.method,
        data=data,
        files=files,
        params=request.args,
        headers=request.headers
    )


# ============================================================================
# YOUTUBE UPLOADER PROXY ROUTES
# ============================================================================

@frontend_bp.route('/frontend/youtube/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_youtube(subpath):
    """Proxy requests to YouTube Uploader service"""
    target_url = f"{YOUTUBE_UPLOADER_URL}/{subpath}"
    return proxy_request(
        target_url,
        method=request.method,
        data=request.get_json() if request.is_json else request.form,
        params=request.args,
        headers=request.headers
    )


# ============================================================================
# VOICE GENERATOR PROXY ROUTES
# ============================================================================

@frontend_bp.route('/frontend/voice/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_voice(subpath):
    """Proxy requests to Voice Generator service"""
    target_url = f"{VOICE_GENERATOR_URL}/{subpath}"
    return proxy_request(
        target_url,
        method=request.method,
        data=request.get_json() if request.is_json else request.form,
        params=request.args,
        headers=request.headers
    )


# ============================================================================
# AUDIO GENERATION PROXY ROUTES
# ============================================================================

@frontend_bp.route('/frontend/audio/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_audio(subpath):
    """Proxy requests to Audio Generation service"""
    target_url = f"{AUDIO_GENERATION_URL}/{subpath}"
    return proxy_request(
        target_url,
        method=request.method,
        data=request.get_json() if request.is_json else request.form,
        params=request.args,
        headers=request.headers
    )


# ============================================================================
# SERVICE STATUS ENDPOINTS
# ============================================================================

@frontend_bp.route('/frontend/services/status', methods=['GET'])
def get_services_status():
    """Get status of all backend services"""
    services = {
        'news-fetcher': NEWS_FETCHER_URL,
        'watermark-remover': IOPAINT_URL,
        'youtube-uploader': YOUTUBE_UPLOADER_URL,
        'voice-generator': VOICE_GENERATOR_URL,
        'audio-generation': AUDIO_GENERATION_URL
    }
    
    status = {}
    
    for service_name, service_url in services.items():
        try:
            # Try to ping the service health endpoint
            health_url = f"{service_url}/health"
            response = requests.get(health_url, timeout=5)
            status[service_name] = {
                'status': 'online' if response.status_code == 200 else 'degraded',
                'url': service_url,
                'response_time': response.elapsed.total_seconds() * 1000  # ms
            }
        except Exception as e:
            status[service_name] = {
                'status': 'offline',
                'url': service_url,
                'error': str(e)
            }
    
    return jsonify(status), 200


@frontend_bp.route('/frontend/services/info', methods=['GET'])
def get_services_info():
    """Get information about all available services"""
    return jsonify({
        'services': {
            'news-fetcher': {
                'name': 'News Fetcher Service',
                'url': NEWS_FETCHER_URL,
                'description': 'Fetches and manages news articles from various sources',
                'endpoints': [
                    '/news/fetch/run',
                    '/news/seed-urls',
                    '/enrichment/status'
                ]
            },
            'watermark-remover': {
                'name': 'Watermark Remover (IOPaint)',
                'url': IOPAINT_URL,
                'description': 'AI-powered watermark removal using LAMA model',
                'endpoints': [
                    '/api/stats',
                    '/api/next',
                    '/api/process',
                    '/api/save'
                ]
            },
            'youtube-uploader': {
                'name': 'YouTube Uploader Service',
                'url': YOUTUBE_UPLOADER_URL,
                'description': 'Uploads videos and shorts to YouTube',
                'endpoints': [
                    '/api/stats',
                    '/api/upload-latest-20',
                    '/api/shorts/pending'
                ]
            },
            'voice-generator': {
                'name': 'Voice Generator Service',
                'url': VOICE_GENERATOR_URL,
                'description': 'Generates audio for news articles',
                'endpoints': [
                    '/audio/stats',
                    '/audio/generate'
                ]
            },
            'audio-generation': {
                'name': 'Audio Generation Factory',
                'url': AUDIO_GENERATION_URL,
                'description': 'TTS service using Kokoro-82M and MMS models',
                'endpoints': [
                    '/tts',
                    '/health'
                ]
            }
        }
    }), 200

