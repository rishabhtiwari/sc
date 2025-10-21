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
        
        # Parse pagination parameters with defaults
        try:
            page = int(request.args.get('page', 1))
        except (ValueError, TypeError):
            page = 1
            
        try:
            page_size = int(request.args.get('page_size', 10))
        except (ValueError, TypeError):
            page_size = 10
        
        logger.info(f"📰 GET /news - category={category}, language={language}, country={country}, page={page}, page_size={page_size}")
        
        # Call handler
        result = news_handler.get_news(
            category=category,
            language=language,
            country=country,
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
