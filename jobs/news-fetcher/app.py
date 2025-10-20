#!/usr/bin/env python3
"""
News Fetcher Job Service
Fetches news from various seed URLs and processes them using factory pattern parsers
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models.base_job import BaseJob
from config.settings import Config
from services.news_fetcher_service import NewsFetcherService

class NewsFetcherJob(BaseJob):
    """
    News Fetcher Job Implementation
    Extends BaseJob to provide news fetching functionality
    """

    def __init__(self):
        super().__init__('news-fetcher', Config)
        self.news_fetcher_service = NewsFetcherService(logger=self.logger)

    def get_job_type(self) -> str:
        """Return the job type identifier"""
        return 'news_fetch'

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
        Main job execution method - fetches news from all due seed URLs

        Args:
            job_id: Job instance ID for tracking
            is_on_demand: True if this is a manual/on-demand job, False for scheduled jobs
            **kwargs: Additional job parameters

        Returns:
            Job execution results
        """
        try:
            self.logger.info(f"Starting news fetch job {job_id}")

            # Check if job was cancelled before starting
            if self.job_instance_service.is_job_cancelled(job_id):
                self.logger.info(f"Job {job_id} was cancelled before execution")
                return {'status': 'cancelled', 'message': 'Job was cancelled'}

            # Fetch news from all due seed URLs
            start_time = datetime.utcnow()
            fetch_results = self.news_fetcher_service.fetch_all_due_news(is_on_demand=is_on_demand)

            # Check if job was cancelled during execution
            if self.job_instance_service.is_job_cancelled(job_id):
                self.logger.info(f"Job {job_id} was cancelled during execution")
                return {'status': 'cancelled', 'message': 'Job was cancelled during execution'}

            end_time = datetime.utcnow()

            # Calculate execution time
            execution_time = (end_time - start_time).total_seconds()

            # Prepare job results
            job_results = {
                'job_id': job_id,
                'status': 'completed',
                'execution_time_seconds': execution_time,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_seed_urls': fetch_results['total_seed_urls'],
                'processed_seed_urls': fetch_results['processed_seed_urls'],
                'skipped_seed_urls': fetch_results['skipped_seed_urls'],
                'total_articles_fetched': fetch_results['total_articles_fetched'],
                'total_articles_saved': fetch_results['total_articles_saved'],
                'processed_partners': fetch_results['processed_partners'],
                'errors': fetch_results['errors']
            }

            # Update job instance with results
            self.job_instance_service.update_job_instance(
                job_id,
                status='completed',
                result=job_results,
                progress=fetch_results['processed_seed_urls'],
                total_items=fetch_results['total_seed_urls']
            )

            self.logger.info(f"News fetch job {job_id} completed successfully. "
                           f"Processed {fetch_results['processed_seed_urls']}/{fetch_results['total_seed_urls']} seed URLs, "
                           f"fetched {fetch_results['total_articles_fetched']} articles, "
                           f"saved {fetch_results['total_articles_saved']} new articles")

            return job_results

        except Exception as e:
            error_msg = f"News fetch job {job_id} failed: {str(e)}"
            self.logger.error(error_msg)

            # Update job instance with error
            self.job_instance_service.update_job_instance(
                job_id,
                status='failed',
                error_message=error_msg
            )

            return {
                'job_id': job_id,
                'status': 'failed',
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

# Create job instance
news_fetcher_job = NewsFetcherJob()

# Get Flask app from base job
app = news_fetcher_job.app

# Add custom endpoint for seed URL status
@app.route('/seed-urls/status', methods=['GET'])
def get_seed_urls_status():
    """Get status of all seed URLs"""
    try:
        result = news_fetcher_job.get_seed_url_status()
        return news_fetcher_job.jsonify(result)
    except Exception as e:
        return news_fetcher_job.jsonify({
            'status': 'error',
            'error': str(e)
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
