"""
News Fetcher Service
Handles fetching news from seed URLs and processing responses
"""

import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from urllib.parse import urlparse
import re

from config.settings import Config, ArticleStatus
from parsers.parser_factory import ParserFactory


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

    def fetch_all_due_news(self, is_on_demand: bool = False, job_id: str = None) -> Dict[str, Any]:
        """
        Fetch news from all seed URLs that are due for execution

        Args:
            is_on_demand: If True, skip frequency check for all seed URLs (for manual jobs)

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
            # Get all active seed URLs
            seed_urls = list(self.seed_urls_collection.find({'is_active': True}))
            results['total_seed_urls'] = len(seed_urls)

            for seed_url in seed_urls:
                try:
                    if self._is_seed_url_due(seed_url, is_on_demand):
                        # Process this seed URL and store articles directly in DB
                        fetch_result = self._fetch_and_store_from_seed_url(seed_url)

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
                        self._update_seed_url_last_fetched(seed_url['_id'])

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

    def _fetch_and_store_from_seed_url(self, seed_url: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch news from a specific seed URL and store articles directly in database

        Args:
            seed_url: Seed URL document from database

        Returns:
            Dictionary with fetch results
        """
        result = {
            'articles_fetched': 0,
            'articles_saved': 0,
            'errors': []
        }

        try:
            # Debug: Show seed URL details
            self.logger.info(f"🔍 Processing Seed URL:")
            self.logger.info(f"   Name: {seed_url.get('name', 'N/A')}")
            self.logger.info(f"   Partner: {seed_url.get('partner_name', seed_url.get('provider', 'N/A'))}")
            self.logger.info(f"   Base URL: {seed_url.get('url', 'N/A')}")
            self.logger.info(f"   API Params: {seed_url.get('metadata', {}).get('api_params', {})}")

            # Build the actual URL with parameters
            actual_url = self._build_url_with_params(seed_url)

            # Make HTTP request
            response = requests.get(
                actual_url,
                timeout=self.config.HTTP_TIMEOUT,
                headers={'User-Agent': 'News-Fetcher-Service/1.0'}
            )
            response.raise_for_status()

            # Parse JSON response
            response_data = response.json()

            # For testing: use mock data if available
            # mock_data = self._get_mock_data()
            # if mock_data:
            #     response_data = mock_data
            # else:
            # Provide valid fallback mock data when mock file is missing
            # response_data = {
            #     "totalArticles": 0,
            #     "articles": []
            # }
            # Get appropriate parser for this provider - handle both partner_name and provider fields
            partner_name = seed_url.get('partner_name', seed_url.get('provider', 'gnews'))
            parser = ParserFactory.create_parser(partner_name)

            # Parse the response
            articles = parser.parse_response(response_data)
            result['articles_fetched'] = len(articles)

            # Save articles to database with category information
            saved_count = self._save_articles(articles, seed_url)
            result['articles_saved'] = saved_count

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

    def _build_url_with_params(self, seed_url: Dict[str, Any]) -> str:
        """
        Build the actual URL with query parameters

        Args:
            seed_url: Seed URL document from database

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
                # Use default category
                actual_params['category'] = param_def.get('default', 'general')
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

    def _save_articles(self, articles: List[Dict[str, Any]], seed_url: Dict[str, Any] = None) -> int:
        """
        Save articles to the news database, avoiding duplicates

        Args:
            articles: List of standardized articles
            seed_url: Seed URL document containing category information

        Returns:
            Number of articles actually saved
        """
        saved_count = 0

        # Extract category from seed URL
        category = Config.DEFAULT_FILTER_CATEGORY  # Default category from config
        if seed_url:
            # Try to get category from metadata.api_params first
            metadata = seed_url.get('metadata', {})
            api_params = metadata.get('api_params', {})
            if 'category' in api_params:
                category = api_params['category']
            # Fallback to direct category field
            elif 'category' in seed_url:
                category = seed_url['category']

        for article in articles:
            try:
                # Check if article already exists (by ID)
                existing = self.news_collection.find_one({'id': article['id']})

                if not existing:
                    # Insert new article with status='progress', empty short_summary, and category
                    article['status'] = ArticleStatus.PROGRESS.value
                    article['short_summary'] = ''
                    article['category'] = category
                    self.news_collection.insert_one(article)
                    saved_count += 1
                    self.logger.info(
                        f"✅ Saved new article with category '{category}': {article.get('title', 'N/A')[:50]}...")
                else:
                    # Optionally update existing article with newer data and category
                    self.news_collection.update_one(
                        {'id': article['id']},
                        {'$set': {
                            'updated_at': datetime.utcnow(),
                            'status': ArticleStatus.PROGRESS.value,
                            'short_summary': '',
                            'category': category
                        }}
                    )
                    self.logger.info(
                        f"🔄 Updated existing article with category '{category}': {article.get('title', 'N/A')[:50]}...")

            except Exception as e:
                self.logger.error(f"Error saving article {article.get('id', 'unknown')}: {str(e)}")
                continue

        return saved_count

    def _update_seed_url_last_fetched(self, seed_url_id):
        """
        Update the last_fetched_at timestamp for a seed URL

        Args:
            seed_url_id: MongoDB ObjectId of the seed URL to update
        """
        try:
            self.seed_urls_collection.update_one(
                {'_id': seed_url_id},
                {
                    '$set': {
                        'last_fetched_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    },
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

    def get_seed_url_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all seed URLs including when they were last run
        
        Returns:
            List of seed URL status information
        """
        try:
            seed_urls = list(self.seed_urls_collection.find())
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
