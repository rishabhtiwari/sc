"""
News Query Service
Handles fetching news documents with category filtering and pagination
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from config.settings import Config, ArticleStatus


class NewsQueryService:
    """Service for querying news documents with category filtering and pagination"""

    def __init__(self, logger: logging.Logger = None):
        """
        Initialize NewsQueryService
        
        Args:
            logger: Logger instance for logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = Config
        
        # Initialize MongoDB connection for news database
        self.news_client = MongoClient(Config.NEWS_MONGODB_URL)
        self.news_db = self.news_client.get_database()
        self.news_collection = self.news_db.news_document
        
        # Test connection
        self.news_client.admin.command('ping')
        self.logger.info("🔧 NewsQueryService initialized successfully")

    def get_news_by_category(self,
                           category: Optional[str] = None,
                           language: Optional[str] = None,
                           country: Optional[str] = None,
                           page: int = 1,
                           page_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch news documents based on category, language, and country filters with pagination

        Args:
            category: News category to filter by (None for general only)
            language: Language code to filter by (e.g., 'en', 'es', 'fr')
            country: Country code to filter by (e.g., 'us', 'in', 'uk')
            page: Page number (1-based)
            page_size: Number of articles per page (defaults to config value)

        Returns:
            Dictionary with news articles and pagination info
        """
        try:
            # Validate and set page size
            if page_size is None:
                page_size = self.config.DEFAULT_PAGE_SIZE
            elif page_size > self.config.MAX_PAGE_SIZE:
                page_size = self.config.MAX_PAGE_SIZE
            elif page_size < 1:
                page_size = self.config.DEFAULT_PAGE_SIZE
                
            # Validate page number
            if page < 1:
                page = 1
                
            # Calculate skip value for pagination
            skip = (page - 1) * page_size
            
            # Build query based on category, language, and country logic
            query = self._build_query(category, language, country)

            self.logger.info(f"🔍 Querying news with category='{category}', language='{language}', country='{country}', page={page}, page_size={page_size}")
            self.logger.info(f"📋 MongoDB query: {query}")
            
            # Build sort criteria: category first (specific category before general), then by time
            sort_criteria = self._build_sort_criteria(category)
            
            # Execute query with pagination
            cursor = self.news_collection.find(query).sort(sort_criteria).skip(skip).limit(page_size)
            articles = list(cursor)
            
            # Get total count for pagination info
            total_count = self.news_collection.count_documents(query)
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
            has_next = page < total_pages
            has_prev = page > 1
            
            # Format articles for response
            formatted_articles = self._format_articles_for_response(articles)
            
            result = {
                'status': 'success',
                'articles': formatted_articles,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_articles': total_count,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev,
                    'next_page': page + 1 if has_next else None,
                    'prev_page': page - 1 if has_prev else None
                },
                'query_info': {
                    'category_filter': category,
                    'language_filter': language,
                    'country_filter': country,
                    'query_executed': query,
                    'sort_criteria': sort_criteria
                }
            }
            
            self.logger.info(f"✅ Found {len(formatted_articles)} articles (page {page}/{total_pages})")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error querying news by category: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            return {
                'status': 'error',
                'error': str(e),
                'articles': [],
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_articles': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_prev': False,
                    'next_page': None,
                    'prev_page': None
                }
            }

    def _build_query(self, category: Optional[str], language: Optional[str], country: Optional[str]) -> Dict[str, Any]:
        """
        Build MongoDB query based on category, language, and country logic

        Args:
            category: Category to filter by
            language: Language code to filter by
            country: Country code to filter by

        Returns:
            MongoDB query dictionary
        """
        # Base query: only include completed articles (enriched articles)
        base_query = {'status': ArticleStatus.COMPLETED.value}

        # Handle category filtering
        if category is None or category.lower() == 'general':
            # If no category or general requested, return only general category
            base_query['category'] = 'general'
        else:
            # If specific category requested, return that category + general
            # Use $or to get both the specific category and general category
            base_query['$or'] = [
                {'category': category.lower()},
                {'category': 'general'}
            ]

        # Handle language filtering
        if language:
            base_query['lang'] = language.lower()

        # Handle country filtering
        if country:
            base_query['source.country'] = country.lower()

        return base_query

    def _build_sort_criteria(self, category: Optional[str]) -> List[tuple]:
        """
        Build sort criteria: specific category first, then by time (newest first)
        
        Args:
            category: Category being queried
            
        Returns:
            List of sort tuples for MongoDB
        """
        if category is None or category.lower() == 'general':
            # For general-only queries, just sort by time
            return [('created_at', -1)]
        else:
            # For specific category queries, sort by:
            # 1. Category (specific category first, then general)
            # 2. Time (newest first within each category)
            return [
                ('category', 1),  # This will put the specific category before 'general' alphabetically
                ('created_at', -1)
            ]

    def _format_articles_for_response(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format articles for API response
        
        Args:
            articles: Raw articles from database
            
        Returns:
            Formatted articles for response
        """
        formatted = []
        
        for article in articles:
            # Convert ObjectId to string for JSON serialization
            if '_id' in article:
                article['_id'] = str(article['_id'])
                
            # Convert datetime objects to ISO strings
            for date_field in ['created_at', 'updated_at', 'enriched_at']:
                if date_field in article and article[date_field]:
                    article[date_field] = article[date_field].isoformat()
                    
            # Ensure required fields are present
            formatted_article = {
                'id': article.get('id', ''),
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'image': article.get('image', ''),
                'publishedAt': article.get('publishedAt', ''),
                'source': article.get('source', {}),
                'category': article.get('category', 'general'),
                'short_summary': article.get('short_summary', ''),
                'status': article.get('status', ''),
                'created_at': article.get('created_at', ''),
                'updated_at': article.get('updated_at', ''),
                'enriched_at': article.get('enriched_at', '')
            }
            
            formatted.append(formatted_article)
            
        return formatted

    def get_available_categories(self) -> Dict[str, Any]:
        """
        Get list of available categories with article counts

        Returns:
            Dictionary with available categories and their counts
        """
        try:
            # Aggregate to get category counts
            pipeline = [
                {'$match': {'status': ArticleStatus.COMPLETED.value}},
                {'$group': {
                    '_id': '$category',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]

            result = list(self.news_collection.aggregate(pipeline))

            categories = {}
            total_articles = 0

            for item in result:
                category = item['_id'] or 'general'
                count = item['count']
                categories[category] = count
                total_articles += count

            return {
                'status': 'success',
                'categories': categories,
                'total_articles': total_articles
            }

        except Exception as e:
            self.logger.error(f"❌ Error getting available categories: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'categories': {},
                'total_articles': 0
            }

    def get_available_filters(self) -> Dict[str, Any]:
        """
        Get list of available languages and countries with article counts

        Returns:
            Dictionary with available languages, countries and their counts
        """
        try:
            # Aggregate to get language counts
            language_pipeline = [
                {'$match': {'status': ArticleStatus.COMPLETED.value}},
                {'$group': {
                    '_id': '$lang',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]

            # Aggregate to get country counts
            country_pipeline = [
                {'$match': {'status': ArticleStatus.COMPLETED.value}},
                {'$group': {
                    '_id': '$source.country',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]

            language_result = list(self.news_collection.aggregate(language_pipeline))
            country_result = list(self.news_collection.aggregate(country_pipeline))

            languages = {}
            countries = {}

            for item in language_result:
                lang = item['_id'] or 'unknown'
                count = item['count']
                languages[lang] = count

            for item in country_result:
                country = item['_id'] or 'unknown'
                count = item['count']
                countries[country] = count

            return {
                'status': 'success',
                'languages': languages,
                'countries': countries
            }

        except Exception as e:
            self.logger.error(f"❌ Error getting available filters: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'languages': {},
                'countries': {}
            }
