"""
News Query Service
Handles fetching news documents with category filtering and pagination
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from bson import ObjectId

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import Config, ArticleStatus
from common.utils.multi_tenant_db import (
    build_multi_tenant_query,
    prepare_update_document,
    add_customer_filter
)


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
                           status: Optional[str] = None,
                           page: int = 1,
                           page_size: Optional[int] = None,
                           customer_id: str = None) -> Dict[str, Any]:
        """
        Fetch news documents based on category, language, country, and status filters with pagination

        Args:
            category: News category to filter by (None for general only)
            language: Language code to filter by (e.g., 'en', 'es', 'fr')
            country: Country code to filter by (e.g., 'us', 'in', 'uk')
            status: Article status to filter by (e.g., 'completed', 'progress', 'failed')
            page: Page number (1-based)
            page_size: Number of articles per page (defaults to config value)
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)
            customer_id: Customer ID for multi-tenant filtering

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

            # Build query based on category, language, country, and status logic
            base_query = self._build_query(category, language, country, status)

            # Add customer_id filter for multi-tenancy
            query = build_multi_tenant_query(base_query, customer_id=customer_id)

            self.logger.info(f"🔍 Querying news with category='{category}', language='{language}', country='{country}', status='{status}', customer_id='{customer_id}', page={page}, page_size={page_size}")
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
                    'status_filter': status,
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

    def _build_query(self, category: Optional[str], language: Optional[str], country: Optional[str], status: Optional[str] = None) -> Dict[str, Any]:
        """
        Build MongoDB query based on category, language, country, and status logic

        Args:
            category: Category to filter by
            language: Language code to filter by
            country: Country code to filter by
            status: Status to filter by (if None or empty string, shows all statuses; if specific value, filters by that status)

        Returns:
            MongoDB query dictionary
        """
        # Base query: filter by status
        base_query = {}

        # Handle status filtering
        # Note: status can be None (not provided), empty string (all statuses), or a specific value
        if status is not None and status != '':
            # If status is provided and not empty, filter by that specific status
            base_query['status'] = status.lower()
        # If status is None or empty string, don't add status filter (show all statuses)

        # Handle category filtering
        if category is None or category == '':
            # If no category provided (All Categories), don't filter by category
            # This shows all categories
            pass
        elif category.lower() == 'general':
            # If general category requested, return only general category
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
                'content': article.get('content', ''),
                'url': article.get('url', ''),
                'image': article.get('image', ''),
                'publishedAt': article.get('publishedAt', ''),
                'source': article.get('source', {}),
                'category': article.get('category', 'general'),
                'lang': article.get('lang', ''),
                'short_summary': article.get('short_summary', ''),
                'status': article.get('status', ''),
                'created_at': article.get('created_at', ''),
                'updated_at': article.get('updated_at', ''),
                'enriched_at': article.get('enriched_at', '')
            }
            
            formatted.append(formatted_article)
            
        return formatted

    def get_available_categories(self, customer_id: str = None) -> Dict[str, Any]:
        """
        Get list of available categories with article counts

        Args:
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            Dictionary with available categories and their counts
        """
        try:
            from common.utils.multi_tenant_db import build_multi_tenant_query

            # Build match query with customer_id filter
            base_match = {'status': ArticleStatus.COMPLETED.value}
            match_query = build_multi_tenant_query(base_match, customer_id=customer_id)

            # Aggregate to get category counts
            # Use $unwind to handle array categories (some documents have category as array)
            pipeline = [
                {'$match': match_query},
                # Unwind category array if it exists, otherwise keep as single value
                {'$unwind': {
                    'path': '$category',
                    'preserveNullAndEmptyArrays': True
                }},
                {'$group': {
                    '_id': '$category',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]

            self.logger.info(f"🔍 get_available_categories - customer_id: {customer_id}, match_query: {match_query}")
            result = list(self.news_collection.aggregate(pipeline))
            self.logger.info(f"📊 get_available_categories - aggregation result: {result}")

            categories = {}
            total_articles = 0

            for item in result:
                category = item['_id']
                # Handle None or empty category
                if not category:
                    category = 'general'
                # Convert to string if it's somehow still not a string
                category = str(category)

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

    def get_available_filters(self, customer_id: str = None) -> Dict[str, Any]:
        """
        Get list of available languages and countries with article counts

        Args:
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            Dictionary with available languages, countries and their counts
        """
        try:
            from common.utils.multi_tenant_db import build_multi_tenant_query

            # Build match query with customer_id filter
            base_match = {'status': ArticleStatus.COMPLETED.value}
            match_query = build_multi_tenant_query(base_match, customer_id=customer_id)

            # Aggregate to get language counts
            language_pipeline = [
                {'$match': match_query},
                {'$group': {
                    '_id': '$lang',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]

            # Aggregate to get country counts
            country_pipeline = [
                {'$match': match_query},
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

    def update_article(self, article_id: str, update_data: Dict[str, Any],
                      customer_id: str = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a news article by ID

        Args:
            article_id: Article ID (MD5 hash) to update
            update_data: Dictionary containing fields to update
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)
            user_id: User ID for audit tracking

        Returns:
            Dictionary with operation result
        """
        try:
            # Validate article_id is not empty
            if not article_id or not isinstance(article_id, str):
                return {
                    'status': 'error',
                    'error': 'Invalid article ID'
                }

            # Prepare update data
            update_fields = {}

            # Only update fields that are provided and allowed
            allowed_fields = [
                'title', 'description', 'content', 'status',
                'category', 'lang', 'author', 'urlToImage'
            ]

            for field in allowed_fields:
                if field in update_data:
                    update_fields[field] = update_data[field]

            if not update_fields:
                return {
                    'status': 'error',
                    'error': 'No valid fields to update'
                }

            # Add audit fields for update
            prepare_update_document(update_fields, user_id=user_id)

            # Also add legacy updatedAt field for backward compatibility
            update_fields['updatedAt'] = datetime.utcnow()

            self.logger.info(f"📝 Updating article {article_id} with fields: {list(update_fields.keys())}")

            # Build query with customer_id filter for multi-tenancy
            query = build_multi_tenant_query({'id': article_id}, customer_id=customer_id)

            # Update the document using the 'id' field (MD5 hash), not '_id' (ObjectId)
            result = self.news_collection.update_one(
                query,
                {'$set': update_fields}
            )

            if result.matched_count > 0:
                # Fetch the updated article
                updated_article = self.news_collection.find_one({'id': article_id})

                # Format the article for response
                formatted_article = None
                if updated_article:
                    # Convert ObjectId to string
                    if '_id' in updated_article:
                        updated_article['_id'] = str(updated_article['_id'])

                    # Convert datetime objects to ISO strings
                    for date_field in ['created_at', 'updated_at', 'updatedAt', 'enriched_at', 'publishedAt']:
                        if date_field in updated_article and updated_article[date_field]:
                            if hasattr(updated_article[date_field], 'isoformat'):
                                updated_article[date_field] = updated_article[date_field].isoformat()

                    formatted_article = updated_article

                return {
                    'status': 'success',
                    'message': f'Article {article_id} updated successfully',
                    'modified_count': result.modified_count,
                    'article': formatted_article
                }
            else:
                return {
                    'status': 'error',
                    'error': f'Article {article_id} not found'
                }

        except Exception as e:
            self.logger.error(f"❌ Error updating article: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
