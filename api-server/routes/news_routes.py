"""
News Routes - REST API endpoints for news operations
"""

import logging
from flask import Blueprint, request, jsonify
from handlers.news_handler import NewsHandler

# Create blueprint
news_bp = Blueprint('news', __name__)

# Initialize handler
news_handler = NewsHandler()
logger = logging.getLogger(__name__)


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
        # Extract query parameters
        category = request.args.get('category')
        language = request.args.get('language')
        country = request.args.get('country')
        status = request.args.get('status')

        # Parse pagination parameters with defaults
        try:
            page = int(request.args.get('page', 1))
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = int(request.args.get('page_size', 10))
        except (ValueError, TypeError):
            page_size = 10

        logger.info(f"📰 GET /news - category={category}, language={language}, country={country}, status={status}, page={page}, page_size={page_size}")

        # Call handler
        result = news_handler.get_news(
            category=category,
            language=language,
            country=country,
            status=status,
            page=page,
            page_size=page_size
        )
        
        # Return response
        if result['status'] == 'success':
            return jsonify(result['data']), 200
        else:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 400
            
    except Exception as e:
        error_msg = f"Error in GET /news: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 500


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
        logger.info(f"✏️ PUT /news/{article_id}")

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No data provided',
                'status': 'error'
            }), 400

        # Call handler
        result = news_handler.update_article(article_id, data)

        # Return response
        if result['status'] == 'success':
            return jsonify(result['data']), 200
        else:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 400

    except Exception as e:
        error_msg = f"Error in PUT /news/{article_id}: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 500


@news_bp.route('/news/categories', methods=['GET'])
def get_categories():
    """
    Get available news categories with article counts
    
    Returns:
        JSON response with categories and counts
    """
    try:
        logger.info("📂 GET /news/categories")
        
        result = news_handler.get_categories()
        
        if result['status'] == 'success':
            return jsonify(result['data']), 200
        else:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 400
            
    except Exception as e:
        error_msg = f"Error in GET /news/categories: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 500


@news_bp.route('/news/filters', methods=['GET'])
def get_filters():
    """
    Get available news filters (languages, countries) with counts
    
    Returns:
        JSON response with available languages and countries
    """
    try:
        logger.info("🔍 GET /news/filters")
        
        result = news_handler.get_filters()
        
        if result['status'] == 'success':
            return jsonify(result['data']), 200
        else:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 400
            
    except Exception as e:
        error_msg = f"Error in GET /news/filters: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 500


@news_bp.route('/news/health', methods=['GET'])
def get_news_health():
    """
    Check news service health status
    
    Returns:
        JSON response with health status
    """
    try:
        logger.info("❤️ GET /news/health")
        
        result = news_handler.get_news_health()
        
        if result['status'] == 'success':
            health_data = result['data']
            if health_data['status'] == 'healthy':
                return jsonify(health_data), 200
            else:
                return jsonify(health_data), 503  # Service Unavailable
        else:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 500
            
    except Exception as e:
        error_msg = f"Error in GET /news/health: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error',
            'service': 'news-fetcher'
        }), 500


@news_bp.route('/news/videos/merge-latest', methods=['POST'])
def merge_latest_videos():
    """
    Merge latest 20 news videos into a single compilation video

    Returns:
        JSON response with merge operation status and details
    """
    try:
        logger.info("🎬 POST /news/videos/merge-latest")

        result = news_handler.merge_latest_videos()

        if result['status'] == 'success':
            return jsonify(result['data']), 200
        else:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 400

    except Exception as e:
        error_msg = f"Error in POST /news/videos/merge-latest: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 500


@news_bp.route('/news/videos/merge-status', methods=['GET'])
def get_video_merge_status():
    """
    Check the status of video merging process

    Returns:
        JSON response with merge status and file info
    """
    try:
        logger.info("🔍 GET /news/videos/merge-status")

        result = news_handler.get_video_merge_status()

        if result['status'] == 'success':
            return jsonify(result['data']), 200
        else:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 400

    except Exception as e:
        error_msg = f"Error in GET /news/videos/merge-status: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 500


@news_bp.route('/news/videos/download', methods=['GET'])
def get_video_download():
    """
    Get download information for the merged video

    Returns:
        JSON response with download URL and file info
    """
    try:
        logger.info("📥 GET /news/videos/download")

        result = news_handler.get_video_download_info()

        if result['status'] == 'success':
            return jsonify(result['data']), 200
        else:
            return jsonify({
                'error': result['error'],
                'status': 'error'
            }), 400

    except Exception as e:
        error_msg = f"Error in GET /news/videos/download: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return jsonify({
            'error': error_msg,
            'status': 'error'
        }), 500


@news_bp.route('/news/videos/latest-20-news.mp4', methods=['GET'])
def download_latest_news_video():
    """
    Download the latest 20 news compilation video

    Returns:
        MP4 video file stream containing latest news compilation
    """
    import requests
    from flask import Response

    try:
        logger.info("📥 GET /news/videos/latest-20-news.mp4 - Downloading latest news compilation video")

        # Proxy the request to the video generator service
        video_service_url = "http://ichat-video-generator:8095/download/latest-20-news.mp4"

        response = requests.get(video_service_url, stream=True, timeout=60)

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
        error_msg = f"Error in GET /news/videos/download/latest-20-news.mp4: {str(e)}"
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


@news_bp.errorhandler(405)
def news_method_not_allowed(error):
    """Handle 405 errors for news routes"""
    return jsonify({
        'error': 'Method not allowed for news endpoint',
        'status': 'error'
    }), 405
