"""
News Routes - Proxy routes for news fetcher service
All /api/news/* requests are forwarded to the news fetcher service
"""

import logging
import requests
from flask import Blueprint, request, jsonify, Response
from middleware.jwt_middleware import get_request_headers_with_context

# Create blueprint
news_bp = Blueprint('news', __name__)
logger = logging.getLogger(__name__)

# News fetcher service URL
NEWS_FETCHER_URL = 'http://ichat-news-fetcher:8093'


@news_bp.route('/news', methods=['GET'])
def get_news():
    """
    Get news articles with filtering and pagination

    Query Parameters:
        - category (str, optional): News category filter
        - language (str, optional): Language filter
        - country (str, optional): Country filter
        - status (str, optional): Article status filter (completed, progress, failed)
        - page (int, optional): Page number (default: 1)
        - page_size (int, optional): Articles per page (default: 10, max: 100)

    Returns:
        JSON response with news articles and pagination info
    """
    try:
        logger.info(f"📰 GET /news - Proxying to news-fetcher")

        # Get headers with customer_id/user_id from JWT middleware
        headers = get_request_headers_with_context()

        # Proxy request to news-fetcher service
        response = requests.get(
            f'{NEWS_FETCHER_URL}/news',
            params=request.args,
            headers=headers,
            timeout=30
        )

        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))

    except Exception as e:
        logger.error(f"Error proxying to news-fetcher /news: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@news_bp.route('/news/<article_id>', methods=['PUT'])
def update_news_article(article_id):
    """
    Update a news article by ID

    Path Parameters:
        - article_id (str): MongoDB ObjectId of the article to update

    Request Body:
        JSON object with fields to update (title, description, content, status, etc.)

    Returns:
        JSON response with update result
    """
    try:
        logger.info(f"✏️ PUT /news/{article_id} - Proxying to news-fetcher")

        # Get headers with customer_id/user_id from JWT middleware
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'

        # Proxy request to news-fetcher service
        response = requests.put(
            f'{NEWS_FETCHER_URL}/news/{article_id}',
            json=request.get_json(),
            headers=headers,
            timeout=30
        )

        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))

    except Exception as e:
        logger.error(f"Error proxying to news-fetcher PUT /news/{article_id}: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@news_bp.route('/news/categories', methods=['GET'])
def get_categories():
    """
    Get available news categories with article counts

    Returns:
        JSON response with categories and counts
    """
    try:
        logger.info("📂 GET /news/categories - Proxying to news-fetcher")

        # Get headers with customer_id/user_id from JWT middleware
        headers = get_request_headers_with_context()

        # Proxy request to news-fetcher service
        response = requests.get(
            f'{NEWS_FETCHER_URL}/news/categories',
            headers=headers,
            timeout=30
        )

        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))

    except Exception as e:
        logger.error(f"Error proxying to news-fetcher /news/categories: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@news_bp.route('/news/filters', methods=['GET'])
def get_filters():
    """
    Get available news filters (languages, countries) with counts

    Returns:
        JSON response with available languages and countries
    """
    try:
        logger.info("🔍 GET /news/filters - Proxying to news-fetcher")

        # Get headers with customer_id/user_id from JWT middleware
        headers = get_request_headers_with_context()

        # Proxy request to news-fetcher service
        response = requests.get(
            f'{NEWS_FETCHER_URL}/news/filters',
            headers=headers,
            timeout=30
        )

        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))

    except Exception as e:
        logger.error(f"Error proxying to news-fetcher /news/filters: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@news_bp.route('/news/health', methods=['GET'])
def get_news_health():
    """
    Check news service health status

    Returns:
        JSON response with health status
    """
    try:
        logger.info("❤️ GET /news/health - Proxying to news-fetcher")

        # Get headers with customer_id/user_id from JWT middleware
        headers = get_request_headers_with_context()

        # Proxy request to news-fetcher service
        response = requests.get(
            f'{NEWS_FETCHER_URL}/health',
            headers=headers,
            timeout=10
        )

        return Response(response.content, status=response.status_code, content_type=response.headers.get('Content-Type'))

    except Exception as e:
        logger.error(f"Error proxying to news-fetcher /health: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error', 'service': 'news-fetcher'}), 500


# Video routes have been moved to video_routes.py
# Use /api/videos/* endpoints instead of /api/news/videos/*


@news_bp.route('/news/videos/shorts/<article_id>/<filename>', methods=['GET'])
def download_short_video(article_id, filename):
    """
    Download a YouTube Short video file for a specific article

    Args:
        article_id: The article ID
        filename: The video filename (e.g., short.mp4)

    Returns:
        MP4 video file stream
    """
    import requests
    from flask import Response
    import os

    try:
        logger.info(f"📥 GET /news/videos/shorts/{article_id}/{filename} - Downloading short video")

        # Security: Only allow specific file types
        allowed_extensions = ['.mp4', '.jpg', '.png', '.jpeg']
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext not in allowed_extensions:
            return jsonify({
                'error': 'Invalid file type',
                'status': 'error'
            }), 400

        # Proxy the request to the video generator service
        video_service_url = f"http://ichat-video-generator:8095/download/{article_id}/{filename}"

        response = requests.get(video_service_url, stream=True, timeout=60)

        if response.status_code == 200:
            # Determine mimetype
            mimetype = 'video/mp4' if file_ext == '.mp4' else f'image/{file_ext[1:]}'

            # Stream the video file back to the client
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

            return Response(
                generate(),
                content_type=mimetype,
                headers={
                    'Content-Disposition': f'inline; filename="{filename}"',
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
                    'error': f'Video service returned status {response.status_code}',
                    'status': 'error'
                }), response.status_code

    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to video generation service"
        logger.error(f"🔌 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 503
    except requests.exceptions.Timeout:
        error_msg = "Video download request timed out"
        logger.error(f"⏰ {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 504
    except Exception as e:
        error_msg = f"Error downloading short video: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 500


@news_bp.route('/news/videos/<config_id>/<filename>', methods=['GET'])
def download_config_file(config_id, filename):
    """
    Download config-specific video or thumbnail file

    Args:
        config_id: The configuration ID
        filename: The file name (e.g., latest.mp4, latest-thumbnail.jpg)

    Returns:
        Video or image file stream
    """
    import requests
    from flask import Response
    import os

    try:
        logger.info(f"📥 GET /news/videos/{config_id}/{filename} - Downloading config file")

        # Security: Only allow specific file types
        allowed_files = ['latest.mp4', 'latest-thumbnail.jpg']

        if filename not in allowed_files:
            return jsonify({
                'error': f'Invalid filename. Allowed: {", ".join(allowed_files)}',
                'status': 'error'
            }), 400

        # Proxy the request to the video generator service
        video_service_url = f"http://ichat-video-generator:8095/download/configs/{config_id}/{filename}"

        response = requests.get(video_service_url, stream=True, timeout=60)

        if response.status_code == 200:
            # Determine mimetype
            mimetype = 'video/mp4' if filename.endswith('.mp4') else 'image/jpeg'

            # Stream the file back to the client
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk

            return Response(
                generate(),
                content_type=mimetype,
                headers={
                    'Content-Disposition': f'inline; filename="{filename}"',
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
                    'error': f'Video service returned status {response.status_code}',
                    'status': 'error'
                }), response.status_code

    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to video generation service"
        logger.error(f"🔌 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 503
    except requests.exceptions.Timeout:
        error_msg = "File download request timed out"
        logger.error(f"⏰ {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 504
    except Exception as e:
        error_msg = f"Error downloading config file: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 500


# Error handlers for the news blueprint
@news_bp.errorhandler(404)
def news_not_found(error):
    """Handle 404 errors for news routes"""
    return jsonify({
        'error': 'News endpoint not found',
        'status': 'error'
    }), 404


# ============================================================================
# NEWS-FETCHER JOB MANAGEMENT ENDPOINTS
# ============================================================================

@news_bp.route('/news/seed-urls', methods=['GET', 'POST'])
def manage_seed_urls():
    """Get or create seed URLs for news fetching"""
    import requests
    try:
        headers = get_request_headers_with_context()
        news_fetcher_url = 'http://ichat-news-fetcher:8093'

        if request.method == 'GET':
            response = requests.get(f'{news_fetcher_url}/seed-urls', headers=headers, timeout=30)
        else:  # POST
            headers['Content-Type'] = 'application/json'
            response = requests.post(f'{news_fetcher_url}/seed-urls', json=request.get_json(), headers=headers, timeout=30)

        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error proxying to news-fetcher seed-urls: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@news_bp.route('/news/seed-urls/<partner_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_seed_url(partner_id):
    """Get, update, or delete a specific seed URL"""
    import requests
    try:
        headers = get_request_headers_with_context()
        news_fetcher_url = 'http://ichat-news-fetcher:8093'

        if request.method == 'GET':
            response = requests.get(f'{news_fetcher_url}/seed-urls/{partner_id}', headers=headers, timeout=30)
        elif request.method == 'PUT':
            headers['Content-Type'] = 'application/json'
            response = requests.put(f'{news_fetcher_url}/seed-urls/{partner_id}', json=request.get_json(), headers=headers, timeout=30)
        else:  # DELETE
            response = requests.delete(f'{news_fetcher_url}/seed-urls/{partner_id}', headers=headers, timeout=30)

        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error proxying to news-fetcher seed-url: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@news_bp.route('/news/enrichment/status', methods=['GET'])
def get_enrichment_status():
    """Get news enrichment status"""
    import requests
    try:
        headers = get_request_headers_with_context()
        news_fetcher_url = 'http://ichat-news-fetcher:8093'
        response = requests.get(f'{news_fetcher_url}/enrichment/status', headers=headers, timeout=30)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error proxying to news-fetcher enrichment/status: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@news_bp.route('/news/enrichment/config', methods=['GET', 'PUT'])
def manage_enrichment_config():
    """Get or update news enrichment configuration"""
    import requests
    try:
        headers = get_request_headers_with_context()
        news_fetcher_url = 'http://ichat-news-fetcher:8093'

        if request.method == 'GET':
            response = requests.get(f'{news_fetcher_url}/enrichment/config', headers=headers, timeout=30)
        else:  # PUT
            headers['Content-Type'] = 'application/json'
            response = requests.put(f'{news_fetcher_url}/enrichment/config', json=request.get_json(), headers=headers, timeout=30)

        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error proxying to news-fetcher enrichment/config: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@news_bp.route('/news/run', methods=['POST'])
def run_news_fetch():
    """Trigger news fetch job"""
    import requests
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'
        news_fetcher_url = 'http://ichat-news-fetcher:8093'
        response = requests.post(f'{news_fetcher_url}/run', json=request.get_json(), headers=headers, timeout=300)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error proxying to news-fetcher run: {str(e)}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@news_bp.errorhandler(405)
def news_method_not_allowed(error):
    """Handle 405 errors for news routes"""
    return jsonify({
        'error': 'Method not allowed for news endpoint',
        'status': 'error'
    }), 405
