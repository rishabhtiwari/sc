"""
News Fetcher Service
Handles fetching news from seed URLs and processing responses
"""

import requests
import time
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from urllib.parse import urlparse
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import Config, ArticleStatus
from parsers.parser_factory import ParserFactory
from common.utils.multi_tenant_db import (
    build_multi_tenant_query,
    prepare_insert_document,
    prepare_update_document,
    add_customer_filter
)


class NewsFetcherService:
    """
    Service for fetching news from seed URLs and processing responses
    """

    def __init__(self, logger=None):
        self.config = Config
        # Initialize logger - use provided logger or create default one
        if logger is None:
            self.logger = logging.getLogger(__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger

        self.news_client = MongoClient(Config.NEWS_MONGODB_URL)
        self.news_db = self.news_client.get_database()
        self.seed_urls_collection = self.news_db.news_seed_urls
        self.news_collection = self.news_db.news_document

        # Test connection
        self.news_client.admin.command('ping')
        self.logger.info("🔧 NewsFetcherService initialized successfully")

    def fetch_all_due_news(self, is_on_demand: bool = False, job_id: str = None,
                          customer_id: str = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch news from all seed URLs that are due for execution

        Args:
            is_on_demand: If True, skip frequency check for all seed URLs (for manual jobs)
            job_id: Job instance ID for tracking
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)
            user_id: User ID for audit tracking

        Returns:
            Dictionary with execution results and statistics
        """
        results = {
            'total_seed_urls': 0,
            'processed_seed_urls': 0,
            'skipped_seed_urls': 0,
            'total_articles_fetched': 0,
            'total_articles_saved': 0,
            'errors': [],
            'processed_partners': []
        }

        try:
            # Get all active seed URLs filtered by customer_id
            query = build_multi_tenant_query({'is_active': True}, customer_id=customer_id)
            seed_urls = list(self.seed_urls_collection.find(query))
            results['total_seed_urls'] = len(seed_urls)

            for seed_url in seed_urls:
                try:
                    if self._is_seed_url_due(seed_url, is_on_demand):
                        # Process this seed URL and store articles directly in DB
                        fetch_result = self._fetch_and_store_from_seed_url(seed_url, customer_id=customer_id, user_id=user_id)

                        # Update results summary only
                        results['processed_seed_urls'] += 1
                        results['total_articles_fetched'] += fetch_result.get('articles_fetched', 0)
                        results['total_articles_saved'] += fetch_result.get('articles_saved', 0)
                        results['processed_partners'].append({
                            'partner_id': seed_url.get('_id', seed_url.get('partner_id', 'unknown')),
                            'partner_name': seed_url.get('name', seed_url.get('partner_name', 'unknown')),
                            'provider': seed_url.get('provider', 'unknown'),
                            'articles_fetched': fetch_result.get('articles_fetched', 0),
                            'articles_saved': fetch_result.get('articles_saved', 0)
                        })

                        # Update last_fetched_at timestamp
                        self._update_seed_url_last_fetched(seed_url['_id'], user_id=user_id)

                    else:
                        results['skipped_seed_urls'] += 1

                except Exception as e:
                    # Best effort: log error with stacktrace but continue processing
                    import traceback

                    error_details = {
                        'seed_url_id': str(seed_url.get('_id', 'unknown')),
                        'seed_url_name': seed_url.get('name', 'unknown'),
                        'provider': seed_url.get('provider', 'unknown'),
                        'url': seed_url.get('url', 'unknown'),
                        'error': str(e)
                    }

                    self.logger.error(
                        f"❌ Error processing seed URL '{seed_url.get('name', 'unknown')}' ({seed_url.get('provider', 'unknown')}):")
                    self.logger.error(f"   URL: {seed_url.get('url', 'unknown')}")
                    self.logger.error(f"   Error: {str(e)}")
                    self.logger.error(f"   Stacktrace:")
                    self.logger.error(traceback.format_exc())

                    results['errors'].append(error_details)

                    # Continue processing other seed URLs (best effort)

            return results

        except Exception as e:
            results['errors'].append(f"Error in fetch_all_due_news: {str(e)}")
            return results

    def _is_seed_url_due(self, seed_url: Dict[str, Any], is_on_demand: bool = False) -> bool:
        """
        Check if a seed URL is due for execution based on frequency and last_fetched_at

        Args:
            seed_url: Seed URL document from database
            is_on_demand: If True, skip frequency check (for manual/on-demand jobs)

        Returns:
            True if seed URL should be executed, False otherwise
        """
        # For on-demand jobs, always return True (frequency check is skipped)
        if is_on_demand:
            return True

        last_fetched_at = seed_url.get('last_fetched_at')
        frequency_minutes = seed_url.get('frequency_minutes', 60)

        # If never fetched before, it's due
        if last_fetched_at is None:
            return True

        # Calculate if enough time has passed since last fetch
        now = datetime.utcnow()
        time_since_last_fetch = now - last_fetched_at
        required_interval = timedelta(minutes=frequency_minutes)

        return time_since_last_fetch >= required_interval

    def _fetch_and_store_from_seed_url(self, seed_url: Dict[str, Any],
                                       customer_id: str = None,
                                       user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch news from a specific seed URL and store articles directly in database
        Supports multiple categories - if category is an array, fetches news for each category

        Args:
            seed_url: Seed URL document from database
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)
            user_id: User ID for audit tracking

        Returns:
            Dictionary with fetch results
        """
        result = {
            'articles_fetched': 0,
            'articles_saved': 0,
            'errors': []
        }

        try:
            # Check if category is an array (multi-category support)
            category_param = seed_url.get('parameters', {}).get('category', {}).get('default', 'general')
            categories = category_param if isinstance(category_param, list) else [category_param]

            self.logger.info(f"🔍 Processing Seed URL:")
            self.logger.info(f"   Name: {seed_url.get('name', 'N/A')}")
            self.logger.info(f"   Partner: {seed_url.get('partner_name', seed_url.get('provider', 'N/A'))}")
            self.logger.info(f"   Base URL: {seed_url.get('url', 'N/A')}")
            self.logger.info(f"   Categories: {categories}")

            # Fetch news for each category
            for category in categories:
                try:
                    self.logger.info(f"📰 Fetching news for category: {category}")

                    # Build the actual URL with parameters for this category
                    actual_url = self._build_url_with_params(seed_url, category)

                    # Make HTTP request
                    response = requests.get(
                        actual_url,
                        timeout=self.config.HTTP_TIMEOUT,
                        headers={'User-Agent': 'News-Fetcher-Service/1.0'}
                    )
                    response.raise_for_status()

                    # Parse JSON response
                    response_data = response.json()

                    # Get appropriate parser for this provider
                    partner_name = seed_url.get('partner_name', seed_url.get('provider', 'gnews'))
                    parser = ParserFactory.create_parser(partner_name)

                    # Parse the response
                    articles = parser.parse_response(response_data)
                    result['articles_fetched'] += len(articles)

                    # Save articles to database with category information
                    # Pass the current category being processed, not the seed_url
                    saved_count = self._save_articles(articles, category, customer_id=customer_id, user_id=user_id)
                    result['articles_saved'] += saved_count

                    self.logger.info(f"✅ Category '{category}': Fetched {len(articles)} articles, Saved {saved_count}")

                except Exception as e:
                    error_msg = f"Error fetching category '{category}': {str(e)}"
                    self.logger.error(f"❌ {error_msg}")
                    result['errors'].append(error_msg)
                    # Continue with next category even if one fails
                    continue

            return result

        except Exception as e:
            import traceback
            error_msg = f"Error fetching from {seed_url.get('name', 'unknown')} ({seed_url.get('provider', 'unknown')}): {str(e)}"

            self.logger.error(f"❌ Error in _fetch_and_store_from_seed_url:")
            self.logger.error(f"   Seed URL: {seed_url.get('name', 'unknown')}")
            self.logger.error(f"   Provider: {seed_url.get('partner_name', seed_url.get('provider', 'unknown'))}")
            self.logger.error(f"   URL: {seed_url.get('url', 'unknown')}")
            self.logger.error(f"   Error: {str(e)}")
            self.logger.error(f"   Stacktrace:")
            self.logger.error(traceback.format_exc())

            result['errors'].append(error_msg)
            return result

    def _build_url_with_params(self, seed_url: Dict[str, Any], category: str = None) -> str:
        """
        Build the actual URL with query parameters

        Args:
            seed_url: Seed URL document from database
            category: Optional category to override the default (for multi-category support)

        Returns:
            URL with query parameters appended
        """
        base_url = seed_url['url']

        # Extract parameter values from seed URL parameters field
        parameters = seed_url.get('parameters', {})

        # Build actual parameter values using defaults and config
        actual_params = {}

        # Process each parameter definition
        for param_name, param_def in parameters.items():
            if param_name == 'api_key':
                # Use API key from config
                actual_params['apikey'] = self.config.API_KEY
            elif param_name == 'category':
                # Use provided category or default
                if category:
                    actual_params['category'] = category
                else:
                    default_category = param_def.get('default', 'general')
                    # Handle array default (use first element)
                    actual_params['category'] = default_category[0] if isinstance(default_category, list) else default_category
            elif param_name == 'lang':
                # Use default language
                actual_params['lang'] = param_def.get('default', 'en')
            elif param_name == 'country':
                # Use default country
                actual_params['country'] = param_def.get('default', 'in')
            elif param_name == 'max':
                # Use max articles from config or parameter default
                max_articles = getattr(self.config, 'MAX_ARTICLES_PER_FETCH', param_def.get('default', 100))
                actual_params['max'] = max_articles

        # Check for missing placeholders in URL and add defaults
        # This handles cases where seed URL has placeholders but no parameter definitions
        if '{api_key}' in base_url and 'apikey' not in actual_params:
            actual_params['apikey'] = self.config.API_KEY
        if '{lang}' in base_url and 'lang' not in actual_params:
            actual_params['lang'] = seed_url.get('language', 'en')
        if '{country}' in base_url and 'country' not in actual_params:
            actual_params['country'] = seed_url.get('country', 'in')
        if '{max}' in base_url and 'max' not in actual_params:
            actual_params['max'] = getattr(self.config, 'MAX_ARTICLES_PER_FETCH', 100)
        if '{category}' in base_url and 'category' not in actual_params:
            if category:
                actual_params['category'] = category
            else:
                # Try to get from seed URL category field
                seed_category = seed_url.get('category', 'general')
                actual_params['category'] = seed_category[0] if isinstance(seed_category, list) else seed_category

        # Debug: Show parameters being applied
        self.logger.info(f"🔧 URL Building Details:")
        self.logger.info(f"   Base URL Template: {base_url}")
        self.logger.info(f"   Parameter Definitions: {parameters}")
        self.logger.info(f"   Actual Parameter Values: {actual_params}")

        # Replace template placeholders in URL
        actual_url = base_url
        for param_name, param_value in actual_params.items():
            placeholder = f"{{{param_name}}}"
            if placeholder in actual_url:
                actual_url = actual_url.replace(placeholder, str(param_value))

            # Also handle api_key placeholder
            if param_name == 'apikey' and '{api_key}' in actual_url:
                actual_url = actual_url.replace('{api_key}', str(param_value))

        self.logger.info(f"🌐 Final URL: {actual_url}")
        return actual_url

    def _save_articles(self, articles: List[Dict[str, Any]], category: str = None,
                      customer_id: str = None, user_id: Optional[str] = None) -> int:
        """
        Save articles to the news database, avoiding duplicates

        Args:
            articles: List of standardized articles
            category: Category string for the articles (e.g., 'general', 'sports')
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)
            user_id: User ID for audit tracking

        Returns:
            Number of articles actually saved
        """
        saved_count = 0

        # Use provided category or fall back to default
        if not category:
            category = Config.DEFAULT_FILTER_CATEGORY

        for article in articles:
            try:
                # Check if article already exists (by ID and customer_id)
                query = build_multi_tenant_query({'id': article['id']}, customer_id=customer_id)
                existing = self.news_collection.find_one(query)

                if not existing:
                    # Insert new article with status='progress', empty short_summary, and category
                    article['status'] = ArticleStatus.PROGRESS.value
                    article['short_summary'] = ''
                    article['category'] = category

                    # Add multi-tenant fields (customer_id, created_by, updated_by, timestamps)
                    prepare_insert_document(article, customer_id=customer_id, user_id=user_id)

                    self.news_collection.insert_one(article)
                    saved_count += 1
                    self.logger.info(
                        f"✅ Saved new article with category '{category}': {article.get('title', 'N/A')[:50]}...")
                else:
                    # Optionally update existing article with newer data and category
                    update_data = {
                        'status': ArticleStatus.PROGRESS.value,
                        'short_summary': '',
                        'category': category
                    }

                    # Add audit fields for update
                    prepare_update_document(update_data, user_id=user_id)

                    self.news_collection.update_one(
                        query,
                        {'$set': update_data}
                    )
                    self.logger.info(
                        f"🔄 Updated existing article with category '{category}': {article.get('title', 'N/A')[:50]}...")

            except Exception as e:
                self.logger.error(f"Error saving article {article.get('id', 'unknown')}: {str(e)}")
                continue

        return saved_count

    def _update_seed_url_last_fetched(self, seed_url_id, user_id: Optional[str] = None):
        """
        Update the last_fetched_at and last_run timestamps for a seed URL

        Args:
            seed_url_id: MongoDB ObjectId of the seed URL to update
            user_id: User ID for audit tracking
        """
        try:
            now = datetime.utcnow()
            update_data = {
                'last_fetched_at': now,
                'last_run': now,
                'updated_at': now
            }

            # Add updated_by if user_id is provided
            if user_id:
                update_data['updated_by'] = user_id

            self.seed_urls_collection.update_one(
                {'_id': seed_url_id},
                {
                    '$set': update_data,
                    '$inc': {'fetch_count': 1}
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Error updating last_fetched_at for seed URL {seed_url_id}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def _get_mock_data(self) -> Dict[str, Any]:
        """
        Get mock data from file for testing purposes

        Returns:
            Mock response data or None if file doesn't exist
        """
        mock_file_path = "/app/mock_data.json"

        try:
            import json
            import os

            if os.path.exists(mock_file_path):
                self.logger.info(f"📁 Loading mock data from: {mock_file_path}")

                with open(mock_file_path, 'r', encoding='utf-8') as file:
                    content = file.read().strip()

                    # Try to parse as JSON first
                    try:
                        mock_data = json.loads(content)
                        self.logger.info(
                            f"✅ Successfully loaded JSON mock data with {len(mock_data.get('articles', []))} articles")
                        return mock_data
                    except json.JSONDecodeError:
                        # If not JSON, treat as plain text and create a mock structure
                        self.logger.info(f"📝 File is not JSON, creating mock structure from text content")

                        # Create a mock GNews-style response
                        mock_data = {
                            "totalArticles": 1,
                            "articles": [
                                {
                                    "title": "Mock Article from File",
                                    "description": content[:200] + "..." if len(content) > 200 else content,
                                    "content": content,
                                    "url": "https://example.com/mock-article",
                                    "image": "https://example.com/mock-image.jpg",
                                    "publishedAt": "2025-10-19T21:00:00Z",
                                    "source": {
                                        "name": "Mock News Source",
                                        "url": "https://example.com"
                                    }
                                }
                            ]
                        }

                        self.logger.info(f"✅ Created mock structure with content length: {len(content)}")
                        return mock_data
            else:
                self.logger.warning(f"⚠️  Mock file not found: {mock_file_path}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Error loading mock data: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def get_seed_url_status(self, customer_id: str = None) -> List[Dict[str, Any]]:
        """
        Get status of all seed URLs including when they were last run

        Args:
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            List of seed URL status information
        """
        try:
            # Build query with multi-tenant filter
            query = build_multi_tenant_query({}, customer_id=customer_id)
            seed_urls = list(self.seed_urls_collection.find(query))
            status_list = []

            for seed_url in seed_urls:
                status = {
                    'partner_id': seed_url['partner_id'],
                    'partner_name': seed_url['partner_name'],
                    'is_active': seed_url['is_active'],
                    'frequency_minutes': seed_url['frequency_minutes'],
                    'last_run': seed_url.get('last_run'),
                    'is_due': self._is_seed_url_due(seed_url)
                }

                if status['last_run']:
                    now = datetime.utcnow()
                    time_since_last_run = now - status['last_run']
                    status['minutes_since_last_run'] = int(time_since_last_run.total_seconds() / 60)
                else:
                    status['minutes_since_last_run'] = None

                status_list.append(status)

            return status_list

        except Exception as e:
            raise Exception(f"Error getting seed URL status: {str(e)}")

    def close_connections(self):
        """Close database connections"""
        if self.news_client:
            self.news_client.close()
