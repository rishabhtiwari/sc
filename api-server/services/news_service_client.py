"""
News Service Client - Interface to News Fetcher Service
"""

import requests
import logging
from typing import Dict, Any, Optional
from config.app_config import AppConfig


class NewsServiceClient:
    """Client for communicating with the News Fetcher Service"""
    
    def __init__(self):
        self.base_url = AppConfig.NEWS_SERVICE_URL
        self.timeout = AppConfig.NEWS_SERVICE_TIMEOUT
        self.logger = logging.getLogger(__name__)
        
    def get_news(self,
                 category: Optional[str] = None,
                 language: Optional[str] = None,
                 country: Optional[str] = None,
                 status: Optional[str] = None,
                 page: int = 1,
                 page_size: int = 10) -> Dict[str, Any]:
        """
        Get news articles with filtering and pagination

        Args:
            category: News category filter
            language: Language filter
            country: Country filter
            status: Article status filter (completed, progress, failed)
            page: Page number (1-based)
            page_size: Number of articles per page

        Returns:
            Dictionary with news articles and pagination info
        """
        try:
            # Build query parameters
            params = {
                'page': page,
                'page_size': page_size
            }

            if category:
                params['category'] = category
            if language:
                params['language'] = language
            if country:
                params['country'] = country
            if status:
                params['status'] = status
                
            self.logger.info(f"🔍 Fetching news with params: {params}")
            
            response = requests.get(
                f"{self.base_url}/news",
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Successfully fetched {data.get('pagination', {}).get('total_articles', 0)} news articles")
                return {
                    'status': 'success',
                    'data': data
                }
            else:
                error_msg = f"News service returned status {response.status_code}"
                self.logger.error(f"❌ {error_msg}")
                return {
                    'status': 'error',
                    'error': error_msg,
                    'data': None
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"News service request timed out after {self.timeout}s"
            self.logger.error(f"⏰ {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
        except requests.exceptions.ConnectionError:
            error_msg = "Could not connect to news service"
            self.logger.error(f"🔌 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
        except Exception as e:
            error_msg = f"Unexpected error calling news service: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
    
    def get_categories(self) -> Dict[str, Any]:
        """
        Get available news categories with counts
        
        Returns:
            Dictionary with available categories
        """
        try:
            self.logger.info("🔍 Fetching news categories")
            
            response = requests.get(
                f"{self.base_url}/news/categories",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Successfully fetched {len(data.get('categories', {}))} categories")
                return {
                    'status': 'success',
                    'data': data
                }
            else:
                error_msg = f"News service returned status {response.status_code}"
                self.logger.error(f"❌ {error_msg}")
                return {
                    'status': 'error',
                    'error': error_msg,
                    'data': None
                }
                
        except Exception as e:
            error_msg = f"Error fetching categories: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
    
    def get_filters(self) -> Dict[str, Any]:
        """
        Get available news filters (languages, countries) with counts
        
        Returns:
            Dictionary with available filters
        """
        try:
            self.logger.info("🔍 Fetching news filters")
            
            response = requests.get(
                f"{self.base_url}/news/filters",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info("✅ Successfully fetched news filters")
                return {
                    'status': 'success',
                    'data': data
                }
            else:
                error_msg = f"News service returned status {response.status_code}"
                self.logger.error(f"❌ {error_msg}")
                return {
                    'status': 'error',
                    'error': error_msg,
                    'data': None
                }
                
        except Exception as e:
            error_msg = f"Error fetching filters: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if news service is healthy

        Returns:
            Dictionary with health status
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5  # Short timeout for health check
            )

            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'service': 'news-fetcher'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'news-fetcher',
                    'error': f"HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'news-fetcher',
                'error': str(e)
            }

    def update_article(self, article_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a news article by ID

        Args:
            article_id: MongoDB ObjectId of the article to update
            update_data: Dictionary containing fields to update

        Returns:
            Dictionary with operation result
        """
        try:
            self.logger.info(f"✏️ Updating article {article_id}")

            response = requests.put(
                f"{self.base_url}/news/{article_id}",
                json=update_data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Successfully updated article {article_id}")
                return {
                    'status': 'success',
                    'data': data
                }
            else:
                error_msg = f"News service returned status {response.status_code}"
                self.logger.error(f"❌ {error_msg}")
                return {
                    'status': 'error',
                    'error': error_msg,
                    'data': None
                }

        except requests.exceptions.Timeout:
            error_msg = f"News service request timed out after {self.timeout}s"
            self.logger.error(f"⏰ {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
        except requests.exceptions.ConnectionError:
            error_msg = "Could not connect to news service"
            self.logger.error(f"🔌 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
        except Exception as e:
            error_msg = f"Unexpected error updating article: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
