#!/usr/bin/env python3
"""
Frontend Routes - DEPRECATED - Use dedicated service route files instead
This file is kept for backward compatibility only.

NEW ARCHITECTURE:
- Use /api/news/* for news-fetcher service (news_routes.py)
- Use /api/image/* for IOPaint service (image_routes.py)
- Use /api/youtube/* for YouTube uploader service (youtube_routes.py)
- Use /api/videos/* for video generator service (video_routes.py)
- Use /api/news/audio/* for voice generator service (voice_routes.py)
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
import os
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
frontend_bp = Blueprint('frontend', __name__)
logger = logging.getLogger(__name__)


def proxy_request(target_url, method='GET', data=None, files=None, params=None, headers=None):
    """
    Generic proxy function to forward requests to backend services

    Args:
        target_url: Target service URL
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body data
        files: Files to upload
        params: Query parameters
        headers: Request headers (DEPRECATED - use get_request_headers_with_context() instead)

    Returns:
        Response from target service
    """
    try:
        logger.info(f"🔄 Proxying {method} request to: {target_url}")

        # CRITICAL: Use JWT middleware to get headers with customer_id/user_id injected
        # This ensures proper multi-tenant context is forwarded to backend services
        proxy_headers = get_request_headers_with_context()

        # Also forward Content-Type if present in original request
        if request.headers.get('Content-Type'):
            proxy_headers['Content-Type'] = request.headers.get('Content-Type')
        
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
# DEPRECATED PROXY ROUTES - Use dedicated service route files instead
# ============================================================================
# All /frontend/* proxy routes have been removed.
# Use the following instead:
# - /api/news/* for news-fetcher service
# - /api/image/* for IOPaint service
# - /api/youtube/* for YouTube uploader service
# - /api/videos/* for video generator service
# - /api/news/audio/* for voice generator service


# ============================================================================
# NOTE: Service status endpoints have been removed
# Use individual service health endpoints instead:
# - GET /api/news/health for news-fetcher
# - GET /api/image/stats for IOPaint
# - GET /api/youtube/stats for YouTube uploader
# - GET /api/videos/* for video generator
# ============================================================================

