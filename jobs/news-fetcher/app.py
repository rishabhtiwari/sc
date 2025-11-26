#!/usr/bin/env python3
"""
News Fetcher Job Service
Fetches news from various seed URLs and processes them using factory pattern parsers
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from flask import jsonify, request, render_template, send_from_directory
from typing import List

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models.base_job import BaseJob
from config.settings import Config, JobStatus
from services.news_fetcher_service import NewsFetcherService
from services.news_enrichment_service import NewsEnrichmentService
from services.news_query_service import NewsQueryService

class NewsFetcherJob(BaseJob):
    """
    News Fetcher Job Implementation
    Extends BaseJob to provide news fetching functionality
    """

    def __init__(self):
        super().__init__('news-fetcher', Config)

        # Fix Flask template and static folder paths
        # The BaseJob creates Flask app with __name__ from base_job module
        # We need to set the correct paths for this specific job
        app_dir = os.path.dirname(os.path.abspath(__file__))
        self.app.template_folder = os.path.join(app_dir, 'templates')
        self.app.static_folder = os.path.join(app_dir, 'static')

        self.news_fetcher_service = NewsFetcherService(logger=self.logger)
        self.news_enrichment_service = NewsEnrichmentService(Config, logger=self.logger)
        self.news_query_service = NewsQueryService(logger=self.logger)

    def get_job_type(self) -> str:
        """Return the job type identifier"""
        return 'news_fetch'

    def get_parallel_tasks(self) -> List[Dict[str, Any]]:
        """
        Define parallel tasks for news fetcher job

        Returns:
            List of task definitions for parallel execution
        """
        return [
            {
                'name': 'news_fetching',
                'function': self.news_fetcher_service.fetch_all_due_news,
                'args': (),
                'kwargs': {}
            },
            {
                'name': 'news_enrichment',
                'function': self.news_enrichment_service.enrich_news_articles,
                'args': (),
                'kwargs': {}
            }
        ]

    def validate_job_params(self, params: Dict[str, Any]) -> List[str]:
        """
        Validate job parameters

        Args:
            params: Job parameters to validate

        Returns:
            List of validation errors (empty if valid)
        """
        # News fetcher doesn't require specific parameters
        # Configuration validation is done in Config.validate_config()
        return []

    def run_job(self, job_id: str, is_on_demand: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Main job execution method - runs parallel tasks for news fetching and enrichment

        Args:
            job_id: Job instance ID for tracking
            is_on_demand: True if this is a manual/on-demand job, False for scheduled jobs
            **kwargs: Additional job parameters

        Returns:
            Job execution results
        """
        try:
            self.logger.info(f"🚀 Starting news fetch job {job_id} with parallel tasks")

            # Check if job was cancelled before starting
            if self.job_instance_service.is_job_cancelled(job_id):
                self.logger.info(f"Job {job_id} was cancelled before execution")
                return {'status': 'cancelled', 'message': 'Job was cancelled'}

            start_time = datetime.utcnow()

            # Execute all parallel tasks
            task_results = self.run_parallel_tasks(job_id, is_on_demand=is_on_demand, **kwargs)

            # Check if job was cancelled during execution
            if self.job_instance_service.is_job_cancelled(job_id):
                self.logger.info(f"Job {job_id} was cancelled during execution")
                return {'status': 'cancelled', 'message': 'Job was cancelled during execution'}

            end_time = datetime.utcnow()

            # Calculate execution time
            execution_time = (end_time - start_time).total_seconds()

            # Extract results from parallel tasks
            fetch_task_result = task_results['task_details'].get('news_fetching', {}).get('result', {})
            enrichment_task_result = task_results['task_details'].get('news_enrichment', {}).get('result', {})

            # Determine job status based on task results
            job_status = JobStatus.COMPLETED.value
            if task_results['failed_tasks'] > 0:
                if task_results['successful_tasks'] == 0:
                    job_status = JobStatus.FAILED.value  # All tasks failed
                else:
                    job_status = JobStatus.PARTIAL_FAILURE.value  # Some tasks failed, some succeeded

            # Prepare job results combining both tasks
            job_results = {
                'job_id': job_id,
                'status': job_status,
                'execution_time_seconds': execution_time,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'parallel_tasks': task_results,
                # News fetching results
                'total_seed_urls': fetch_task_result.get('total_seed_urls', 0),
                'processed_seed_urls': fetch_task_result.get('processed_seed_urls', 0),
                'skipped_seed_urls': fetch_task_result.get('skipped_seed_urls', 0),
                'total_articles_fetched': fetch_task_result.get('total_articles_fetched', 0),
                'total_articles_saved': fetch_task_result.get('total_articles_saved', 0),
                'processed_partners': fetch_task_result.get('processed_partners', []),
                # News enrichment results
                'articles_enriched': enrichment_task_result.get('articles_enriched', 0),
                'articles_failed_enrichment': enrichment_task_result.get('articles_failed', 0),
                'total_articles_processed_for_enrichment': enrichment_task_result.get('articles_processed', 0),
                # Combined errors
                'errors': fetch_task_result.get('errors', []) + enrichment_task_result.get('errors', [])
            }

            # Update job instance with results
            self.job_instance_service.update_job_instance(
                job_id,
                status=job_status,
                result=job_results,
                progress=task_results['successful_tasks'],
                total_items=task_results['total_tasks']
            )

            # Log appropriate message based on job status
            if job_status == 'completed':
                self.logger.info(f"🏁 News job {job_id} completed successfully with parallel tasks. "
                               f"Tasks: {task_results['successful_tasks']}/{task_results['total_tasks']} successful, "
                               f"Fetched: {job_results['total_articles_fetched']} articles, "
                               f"Saved: {job_results['total_articles_saved']} new articles, "
                               f"Enriched: {job_results['articles_enriched']} articles")
            elif job_status == 'partial_failure':
                self.logger.warning(f"⚠️ News job {job_id} completed with partial failures. "
                                  f"Tasks: {task_results['successful_tasks']}/{task_results['total_tasks']} successful, "
                                  f"{task_results['failed_tasks']} failed, "
                                  f"Fetched: {job_results['total_articles_fetched']} articles, "
                                  f"Saved: {job_results['total_articles_saved']} new articles, "
                                  f"Enriched: {job_results['articles_enriched']} articles")
            else:  # failed
                self.logger.error(f"❌ News job {job_id} failed - all parallel tasks failed. "
                                f"Tasks: {task_results['failed_tasks']}/{task_results['total_tasks']} failed")
                # Raise exception so base job framework marks job as failed
                failed_task_errors = []
                for task_name, task_detail in task_results['task_details'].items():
                    if task_detail.get('status') == 'failed':
                        failed_task_errors.append(f"{task_name}: {task_detail.get('error', 'Unknown error')}")

                raise Exception(f"All parallel tasks failed: {'; '.join(failed_task_errors)}")

            return job_results

        except Exception as e:
            error_msg = f"News fetch job {job_id} failed: {str(e)}"
            self.logger.error(error_msg)

            # Update job instance with error
            self.job_instance_service.update_job_instance(
                job_id,
                status=JobStatus.FAILED.value,
                error_message=error_msg
            )

            return {
                'job_id': job_id,
                'status': JobStatus.FAILED.value,
                'error': error_msg,
                'execution_time_seconds': 0
            }

    def get_seed_url_status(self) -> Dict[str, Any]:
        """
        Get status of all seed URLs

        Returns:
            Dictionary with seed URL status information
        """
        try:
            status_list = self.news_fetcher_service.get_seed_url_status()
            return {
                'status': 'success',
                'seed_urls': status_list,
                'total_seed_urls': len(status_list)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'seed_urls': [],
                'total_seed_urls': 0
            }

    def add_seed_url(self, seed_url_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new seed URL to the database

        Args:
            seed_url_data: Dictionary containing seed URL information

        Returns:
            Dictionary with operation result
        """
        try:
            from datetime import datetime
            import uuid

            # Auto-generate partner_id if not provided
            if 'partner_id' not in seed_url_data or not seed_url_data['partner_id']:
                partner_id = str(uuid.uuid4())
            else:
                partner_id = seed_url_data['partner_id']

            # Get frequency_minutes (now directly from input)
            frequency_minutes = seed_url_data.get('frequency_minutes', 60)
            frequency_hours = frequency_minutes / 60

            # Handle category - can be string or array
            category = seed_url_data.get('category', 'general')
            # Ensure category is properly formatted (string or list)
            if isinstance(category, str):
                # If comma-separated string, convert to array
                if ',' in category:
                    category = [c.strip() for c in category.split(',')]
            elif not isinstance(category, list):
                category = 'general'  # Fallback to default

            # Build parameters with category support
            parameters = seed_url_data.get('parameters', {})
            if 'category' in parameters:
                # Update the default value in parameters to support array
                parameters['category']['default'] = category
            else:
                # Add category parameter if not present
                parameters['category'] = {
                    'type': 'string' if isinstance(category, str) else 'array',
                    'required': False,
                    'description': 'News category or categories',
                    'default': category
                }

            # Set default values
            seed_url = {
                'partner_id': partner_id,
                'url': seed_url_data['url'],
                'partner_name': seed_url_data['partner_name'],
                'name': seed_url_data.get('name', seed_url_data['partner_name']),
                'provider': seed_url_data.get('provider', 'gnews'),
                'category': category,
                'country': seed_url_data.get('country', 'in'),
                'language': seed_url_data.get('language', 'en'),
                'frequency_minutes': frequency_minutes,
                'frequency_hours': frequency_hours,
                'is_active': seed_url_data.get('is_active', True),
                'last_run': None,
                'last_fetched_at': None,
                'fetch_count': 0,
                'success_count': 0,
                'error_count': 0,
                'last_error': None,
                'parameters': parameters,
                'metadata': seed_url_data.get('metadata', {
                    'api_params': {
                        'category': category,
                        'country': seed_url_data.get('country', 'in'),
                        'lang': seed_url_data.get('language', 'en')
                    }
                }),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            # Check if partner_id already exists
            existing_partner_id = self.news_fetcher_service.seed_urls_collection.find_one({
                'partner_id': seed_url['partner_id']
            })

            if existing_partner_id:
                return {
                    'status': 'error',
                    'error': f'Seed URL with partner_id "{seed_url["partner_id"]}" already exists'
                }

            # Note: partner_name can be duplicated to support multiple categories for same partner
            # Uniqueness is enforced by URL + metadata combination (category, country, language)

            # Check if URL + metadata combination already exists (as per unique index)
            existing_url_combo = self.news_fetcher_service.seed_urls_collection.find_one({
                'url': seed_url['url'],
                'metadata.api_params': seed_url['metadata'].get('api_params', {})
            })

            if existing_url_combo:
                return {
                    'status': 'error',
                    'error': f'Seed URL with same URL and API parameters already exists'
                }

            # Insert the seed URL
            result = self.news_fetcher_service.seed_urls_collection.insert_one(seed_url)

            return {
                'status': 'success',
                'message': 'Seed URL added successfully',
                'seed_url_id': str(result.inserted_id),
                'partner_id': seed_url['partner_id'],
                'partner_name': seed_url['partner_name']
            }

        except Exception as e:
            self.logger.error(f"Error adding seed URL: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def get_all_seed_urls(self) -> Dict[str, Any]:
        """
        Get all seed URLs from database

        Returns:
            Dictionary with all seed URLs
        """
        try:
            seed_urls = list(self.news_fetcher_service.seed_urls_collection.find())

            # Convert ObjectId to string for JSON serialization
            for seed_url in seed_urls:
                if '_id' in seed_url:
                    seed_url['_id'] = str(seed_url['_id'])
                # Convert datetime to ISO format
                for field in ['created_at', 'updated_at', 'last_run', 'last_fetched_at']:
                    if field in seed_url and seed_url[field]:
                        seed_url[field] = seed_url[field].isoformat()

            return {
                'status': 'success',
                'seed_urls': seed_urls,
                'total': len(seed_urls)
            }
        except Exception as e:
            self.logger.error(f"Error getting seed URLs: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'seed_urls': [],
                'total': 0
            }

    def get_seed_url(self, partner_id: str) -> Dict[str, Any]:
        """
        Get a single seed URL by partner_id

        Args:
            partner_id: Partner ID of the seed URL to retrieve

        Returns:
            Dictionary with seed URL data
        """
        try:
            seed_url = self.news_fetcher_service.seed_urls_collection.find_one({
                'partner_id': partner_id
            })

            if not seed_url:
                return {
                    'status': 'error',
                    'error': f'Seed URL {partner_id} not found'
                }

            # Convert ObjectId to string for JSON serialization
            if '_id' in seed_url:
                seed_url['_id'] = str(seed_url['_id'])

            # Convert datetime to ISO format
            for field in ['created_at', 'updated_at', 'last_run', 'last_fetched_at']:
                if field in seed_url and seed_url[field]:
                    seed_url[field] = seed_url[field].isoformat()

            return {
                'status': 'success',
                'seed_url': seed_url
            }
        except Exception as e:
            self.logger.error(f"Error getting seed URL: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def update_seed_url(self, partner_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing seed URL by partner_id

        Args:
            partner_id: Partner ID of the seed URL to update
            update_data: Dictionary containing fields to update

        Returns:
            Dictionary with operation result
        """
        try:
            # Prepare update data
            update_fields = {}

            # Only update fields that are provided
            allowed_fields = [
                'partner_name', 'name', 'url', 'provider', 'category',
                'country', 'language', 'frequency_minutes', 'is_active'
            ]

            for field in allowed_fields:
                if field in update_data:
                    update_fields[field] = update_data[field]

            # Handle category update - can be string or array
            if 'category' in update_fields:
                category = update_fields['category']
                # If comma-separated string, convert to array
                if isinstance(category, str) and ',' in category:
                    category = [c.strip() for c in category.split(',')]
                    update_fields['category'] = category

                # Update parameters.category.default to match
                # First, get the existing seed URL to preserve other parameters
                existing_seed_url = self.news_fetcher_service.seed_urls_collection.find_one({
                    'partner_id': partner_id
                })

                if existing_seed_url:
                    parameters = existing_seed_url.get('parameters', {})
                    if 'category' in parameters:
                        parameters['category']['default'] = category
                        parameters['category']['type'] = 'string' if isinstance(category, str) else 'array'
                    else:
                        parameters['category'] = {
                            'type': 'string' if isinstance(category, str) else 'array',
                            'required': False,
                            'description': 'News category or categories',
                            'default': category
                        }
                    update_fields['parameters'] = parameters

                    # Also update metadata.api_params.category
                    metadata = existing_seed_url.get('metadata', {})
                    if 'api_params' not in metadata:
                        metadata['api_params'] = {}
                    metadata['api_params']['category'] = category
                    update_fields['metadata'] = metadata

            # Calculate frequency_hours from frequency_minutes if provided
            if 'frequency_minutes' in update_fields:
                update_fields['frequency_hours'] = update_fields['frequency_minutes'] / 60

            # Add updated timestamp
            update_fields['updated_at'] = datetime.utcnow()

            # Update the document
            result = self.news_fetcher_service.seed_urls_collection.update_one(
                {'partner_id': partner_id},
                {'$set': update_fields}
            )

            if result.matched_count > 0:
                return {
                    'status': 'success',
                    'message': f'Seed URL {partner_id} updated successfully',
                    'modified_count': result.modified_count
                }
            else:
                return {
                    'status': 'error',
                    'error': f'Seed URL {partner_id} not found'
                }
        except Exception as e:
            self.logger.error(f"Error updating seed URL: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def delete_seed_url(self, partner_id: str) -> Dict[str, Any]:
        """
        Delete a seed URL by partner_id

        Args:
            partner_id: Partner ID of the seed URL to delete

        Returns:
            Dictionary with operation result
        """
        try:
            result = self.news_fetcher_service.seed_urls_collection.delete_one({
                'partner_id': partner_id
            })

            if result.deleted_count > 0:
                return {
                    'status': 'success',
                    'message': f'Seed URL {partner_id} deleted successfully'
                }
            else:
                return {
                    'status': 'error',
                    'error': f'Seed URL {partner_id} not found'
                }
        except Exception as e:
            self.logger.error(f"Error deleting seed URL: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

# Create job instance
news_fetcher_job = NewsFetcherJob()

# Get Flask app from base job
app = news_fetcher_job.app

# UI Routes
@app.route('/', methods=['GET'])
def index():
    """Render the management UI"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, filename)

# Add custom endpoints
@app.route('/seed-urls/status', methods=['GET'])
def get_seed_urls_status():
    """Get status of all seed URLs"""
    try:
        result = news_fetcher_job.get_seed_url_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/seed-urls', methods=['GET'])
def get_seed_urls():
    """Get all seed URLs"""
    try:
        result = news_fetcher_job.get_all_seed_urls()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/seed-urls', methods=['POST'])
def add_seed_url():
    """Add a new seed URL for news fetching"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'No JSON data provided'
            }), 400

        # Validate required fields (partner_id is auto-generated if not provided)
        required_fields = ['url', 'partner_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'error': f'Missing required field: {field}'
                }), 400

        result = news_fetcher_job.add_seed_url(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/seed-urls/<partner_id>', methods=['GET'])
def get_seed_url(partner_id):
    """Get a single seed URL by partner_id"""
    try:
        result = news_fetcher_job.get_seed_url(partner_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/seed-urls/<partner_id>', methods=['PUT'])
def update_seed_url(partner_id):
    """Update an existing seed URL by partner_id"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'No data provided'
            }), 400

        result = news_fetcher_job.update_seed_url(partner_id, data)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/seed-urls/<partner_id>', methods=['DELETE'])
def delete_seed_url(partner_id):
    """Delete a seed URL by partner_id"""
    try:
        result = news_fetcher_job.delete_seed_url(partner_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/enrichment/status', methods=['GET'])
def get_enrichment_status():
    """Get news enrichment status and statistics"""
    try:
        result = news_fetcher_job.news_enrichment_service.get_enrichment_status()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/news', methods=['GET'])
def get_news():
    """
    Get news articles with category, language, and country filtering and pagination

    Query Parameters:
        category (optional): News category to filter by (e.g., 'sports', 'technology')
                           If not provided or 'general', returns only general category
                           If specific category, returns that category + general
        language (optional): Language code to filter by (e.g., 'en', 'es', 'fr')
        country (optional): Country code to filter by (e.g., 'us', 'in', 'uk')
        page (optional): Page number (default: 1)
        page_size (optional): Number of articles per page (default: 10, max: 50)

    Returns:
        JSON response with news articles and pagination info
    """
    try:
        # Get query parameters
        category = request.args.get('category', Config.DEFAULT_FILTER_CATEGORY)
        language = request.args.get('language', Config.DEFAULT_FILTER_LANGUAGE)
        country = request.args.get('country', Config.DEFAULT_FILTER_COUNTRY)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', type=int)

        # Query news using the news query service
        result = news_fetcher_job.news_query_service.get_news_by_category(
            category=category,
            language=language,
            country=country,
            page=page,
            page_size=page_size
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'articles': [],
            'pagination': {
                'current_page': 1,
                'page_size': 10,
                'total_articles': 0,
                'total_pages': 0,
                'has_next': False,
                'has_prev': False,
                'next_page': None,
                'prev_page': None
            }
        }), 500

@app.route('/news/categories', methods=['GET'])
def get_news_categories():
    """
    Get available news categories with article counts

    Returns:
        JSON response with available categories and their counts
    """
    try:
        result = news_fetcher_job.news_query_service.get_available_categories()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'categories': {},
            'total_articles': 0
        }), 500

@app.route('/news/filters', methods=['GET'])
def get_news_filters():
    """
    Get available news filters (languages and countries) with article counts

    Returns:
        JSON response with available languages and countries and their counts
    """
    try:
        result = news_fetcher_job.news_query_service.get_available_filters()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'languages': {},
            'countries': {}
        }), 500

if __name__ == '__main__':
    try:
        # Validate configuration
        Config.validate_config()

        # Start the job service
        news_fetcher_job.run_flask_app()

    except KeyboardInterrupt:
        news_fetcher_job.logger.info("Shutting down News Fetcher Service")
    except Exception as e:
        news_fetcher_job.logger.error(f"Failed to start News Fetcher Service: {str(e)}")
        sys.exit(1)
