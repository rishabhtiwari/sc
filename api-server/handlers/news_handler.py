"""
News Handler - Business logic for news operations
"""

import logging
from typing import Dict, Any, Optional
from services.news_service_client import NewsServiceClient


class NewsHandler:
    """Handler for news-related operations"""
    
    def __init__(self):
        self.news_client = NewsServiceClient()
        self.logger = logging.getLogger(__name__)
    
    def get_news(self, 
                 category: Optional[str] = None,
                 language: Optional[str] = None,
                 country: Optional[str] = None,
                 page: int = 1,
                 page_size: int = 10) -> Dict[str, Any]:
        """
        Get news articles with filtering and pagination
        
        Args:
            category: News category filter
            language: Language filter  
            country: Country filter
            page: Page number (1-based)
            page_size: Number of articles per page
            
        Returns:
            Dictionary with news articles and metadata
        """
        try:
            # Validate pagination parameters
            if page < 1:
                return {
                    'status': 'error',
                    'error': 'Page number must be >= 1',
                    'data': None
                }
            
            if page_size < 1 or page_size > 100:
                return {
                    'status': 'error', 
                    'error': 'Page size must be between 1 and 100',
                    'data': None
                }
            
            self.logger.info(f"📰 Getting news: category={category}, language={language}, country={country}, page={page}, page_size={page_size}")
            
            # Call news service
            result = self.news_client.get_news(
                category=category,
                language=language,
                country=country,
                page=page,
                page_size=page_size
            )
            
            if result['status'] == 'success':
                # Add metadata for API response
                data = result['data']
                return {
                    'status': 'success',
                    'message': f"Retrieved {data.get('pagination', {}).get('total_articles', 0)} news articles",
                    'data': data
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f"Error in news handler: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
    
    def get_categories(self) -> Dict[str, Any]:
        """
        Get available news categories
        
        Returns:
            Dictionary with available categories and counts
        """
        try:
            self.logger.info("📂 Getting news categories")
            
            result = self.news_client.get_categories()
            
            if result['status'] == 'success':
                data = result['data']
                categories = data.get('categories', {})
                return {
                    'status': 'success',
                    'message': f"Retrieved {len(categories)} news categories",
                    'data': data
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f"Error getting categories: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
    
    def get_filters(self) -> Dict[str, Any]:
        """
        Get available news filters (languages, countries)
        
        Returns:
            Dictionary with available filters and counts
        """
        try:
            self.logger.info("🔍 Getting news filters")
            
            result = self.news_client.get_filters()
            
            if result['status'] == 'success':
                data = result['data']
                languages = data.get('languages', {})
                countries = data.get('countries', {})
                return {
                    'status': 'success',
                    'message': f"Retrieved {len(languages)} languages and {len(countries)} countries",
                    'data': data
                }
            else:
                return result
                
        except Exception as e:
            error_msg = f"Error getting filters: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
    
    def get_news_health(self) -> Dict[str, Any]:
        """
        Check news service health
        
        Returns:
            Dictionary with health status
        """
        try:
            self.logger.info("❤️ Checking news service health")
            
            result = self.news_client.health_check()
            
            return {
                'status': 'success',
                'message': f"News service is {result['status']}",
                'data': result
            }
                
        except Exception as e:
            error_msg = f"Error checking news health: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': {
                    'status': 'unhealthy',
                    'service': 'news-fetcher',
                    'error': str(e)
                }
            }
