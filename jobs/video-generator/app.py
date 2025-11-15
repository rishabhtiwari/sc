"""
Video Generation Job Service - Main Application
"""

import os
import sys
from datetime import datetime

# Add common directory to path for job framework
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from common.models.base_job import BaseJob
from common.utils.logger import setup_logger
from config.settings import Config
from services.video_generation_service import VideoGenerationService


class VideoGeneratorJob(BaseJob):
    """Video Generation Job that extends BaseJob framework"""
    
    def __init__(self):
        super().__init__("video-generator", Config)
        self.video_service = VideoGenerationService(self.config, self.logger)

        # Initialize MongoDB connection
        from pymongo import MongoClient
        self.mongo_client = MongoClient(self.config.MONGODB_URI)

        # Connect to news database for reading articles
        self.news_client = MongoClient(self.config.NEWS_MONGODB_URL)
        self.news_db = self.news_client[self.config.NEWS_MONGODB_DATABASE]
        self.news_collection = self.news_db['news_document']
        
        # Validate configuration
        try:
            self.config.validate_config()
            self.logger.info("✅ Configuration validation passed")
        except ValueError as e:
            self.logger.error(f"❌ Configuration validation failed: {str(e)}")
            raise
    
    def get_job_type(self) -> str:
        """Return the job type identifier"""
        return "video-generator"
    
    def get_service_info(self) -> dict:
        """Return service information"""
        return {
            'name': self.config.SERVICE_NAME,
            'version': self.config.SERVICE_VERSION,
            'description': self.config.SERVICE_DESCRIPTION,
            'job_type': self.get_job_type(),
            'status': 'running',
            'last_run': None,
            'config': {
                'interval_minutes': self.config.JOB_INTERVAL_MINUTES,
                'max_threads': self.config.MAX_THREADS,
                'video_quality': self.config.VIDEO_QUALITY,
                'video_dimensions': f"{self.config.VIDEO_WIDTH}x{self.config.VIDEO_HEIGHT}",
                'video_fps': self.config.VIDEO_FPS
            }
        }
    
    def run_job(self, job_id: str, is_on_demand: bool = False, **kwargs) -> dict:
        """
        Main job execution method - finds articles with audio but no video and generates videos
        """
        try:
            self.logger.info(f"🚀 Starting video generation job {job_id} (on_demand: {is_on_demand})...")
            self.logger.info(f"🔍 DEBUG: run_job called with job_id={job_id}, is_on_demand={is_on_demand}")

            # Get articles that need video generation
            articles_to_process = self._get_articles_for_video_generation()

            if not articles_to_process:
                self.logger.info("📭 No articles found that need video generation")
                result = {
                    'status': 'completed',  # Changed from 'success' to 'completed' for BaseJob framework
                    'message': 'No articles to process',
                    'processed_count': 0,
                    'success_count': 0,
                    'error_count': 0
                }
                self.logger.info(f"🔍 DEBUG: Returning early result: {result}")
                return result

            self.logger.info(f"📋 Found {len(articles_to_process)} articles to process")

            # Store articles for parallel processing
            self.current_articles = articles_to_process

            # Process articles in parallel
            self.logger.info(f"🔍 DEBUG: About to call run_parallel_tasks with job_id: {job_id}")
            results = self.run_parallel_tasks(job_id)

            self.logger.info(f"🔍 DEBUG: Parallel tasks results structure: {type(results)}")
            self.logger.info(f"🔍 DEBUG: Results keys: {results.keys() if isinstance(results, dict) else 'Not a dict'}")

            # Extract actual task results for database updates
            task_results = []
            if isinstance(results, dict) and 'task_details' in results:
                self.logger.info(f"🔍 DEBUG: Found task_details with {len(results['task_details'])} tasks")
                for task_name, task_result in results['task_details'].items():
                    if task_result.get('status') == 'completed':
                        task_results.append(task_result.get('result', {}))
                        self.logger.info(f"🔍 DEBUG: Added result for task {task_name}: {task_result.get('result', {})}")
                    else:
                        self.logger.warning(f"⚠️ DEBUG: Task {task_name} not completed: {task_result.get('status')}")
            else:
                self.logger.warning(f"⚠️ DEBUG: Unexpected results structure: {results}")

            self.logger.info(f"🔍 DEBUG: Extracted {len(task_results)} task results for database update")

            # Update database with results
            self.logger.info(f"🔍 DEBUG: About to call _update_database_with_results")
            success_count = self._update_database_with_results(task_results)
            self.logger.info(f"🔍 DEBUG: _update_database_with_results returned: {success_count}")

            # Calculate statistics
            total_processed = len(task_results)
            error_count = total_processed - success_count

            self.logger.info(f"✅ Video generation job completed")
            self.logger.info(f"📊 Processed: {total_processed}, Success: {success_count}, Errors: {error_count}")

            final_result = {
                'status': 'completed',  # Changed from 'success' to 'completed' for BaseJob framework
                'message': f'Video generation completed',
                'processed_count': total_processed,
                'success_count': success_count,
                'error_count': error_count,
                'timestamp': datetime.utcnow().isoformat()
            }

            self.logger.info(f"🔍 DEBUG: Final result being returned from run_job: {final_result}")
            return final_result

        except Exception as e:
            error_msg = f"Video generation job failed: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            error_result = {
                'status': 'failed',  # Changed from 'error' to 'failed' for BaseJob framework
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.logger.info(f"🔍 DEBUG: Error result being returned from run_job: {error_result}")
            return error_result
    
    def get_parallel_tasks(self) -> list:
        """
        Convert articles into parallel tasks for processing

        Returns:
            List of task dictionaries for parallel processing
        """
        articles = getattr(self, 'current_articles', [])
        tasks = []

        for article in articles:
            task = {
                'name': f"video_generation_{article['id']}",
                'function': self.process_single_task,
                'args': (article,),
                'kwargs': {}
            }
            tasks.append(task)
        
        return tasks
    
    def process_single_task(self, article: dict, job_id: str = None, **kwargs) -> dict:
        """
        Process a single video generation task

        Args:
            article: Article document from database
            job_id: Job ID passed by BaseJob framework
            **kwargs: Additional parameters from BaseJob framework

        Returns:
            Result dictionary with processing outcome
        """
        try:
            article_id = article['id']

            self.logger.info(f"🎬 Processing video generation for article: {article_id}")

            # Generate video using the video service
            result = self.video_service.generate_video_for_article(article)

            if result['status'] == 'success':
                self.logger.info(f"✅ Video generated successfully for article: {article_id}")
            else:
                self.logger.error(f"❌ Video generation failed for article: {article_id} - {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            error_msg = f"Error processing video generation task: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'article_id': article.get('id', 'unknown')
            }
    
    def _get_articles_for_video_generation(self) -> list:
        """
        Get articles that have audio but no video generated yet
        
        Returns:
            List of article documents that need video generation
        """
        try:
            # Query for articles that have audio_paths but no video_path
            query = {
                'audio_paths': {'$ne': None, '$exists': True},  # Has audio paths
                'video_path': {'$in': [None, '']},  # No video yet
                'image': {'$ne': None, '$exists': True},  # Has image URL
                'status': {'$in': ['completed', 'published']}  # Only process completed articles
            }
            
            # Get all articles that need video generation
            articles = list(
                self.news_collection.find(query)
                .sort('updated_at', -1)  # Process newest first
            )
            
            self.logger.info(f"🔍 Found {len(articles)} articles ready for video generation")
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error querying articles for video generation: {str(e)}")
            return []
    
    def _update_database_with_results(self, results: list) -> int:
        """
        Update database with video generation results

        Args:
            results: List of processing results

        Returns:
            Number of successful updates
        """
        self.logger.info(f"🔍 DEBUG: _update_database_with_results called with {len(results)} results")
        success_count = 0

        for i, result in enumerate(results):
            try:
                self.logger.info(f"🔍 DEBUG: Processing result {i+1}/{len(results)}: {result}")

                article_id = result.get('article_id')
                if not article_id:
                    self.logger.warning(f"⚠️ DEBUG: Result {i+1} missing article_id: {result}")
                    continue

                self.logger.info(f"🔍 DEBUG: Processing article_id: {article_id}, status: {result.get('status')}")

                if result['status'] == 'success':
                    # Update article with video path
                    update_data = {
                        'video_path': result['video_path'],
                        'updated_at': datetime.utcnow()
                    }

                    self.logger.info(f"🔍 DEBUG: Base update_data for {article_id}: {update_data}")

                    # Add optional fields if available
                    if result.get('thumbnail_path'):
                        update_data['thumbnail_path'] = result['thumbnail_path']
                    if result.get('duration_seconds'):
                        update_data['video_duration_seconds'] = result['duration_seconds']
                    if result.get('file_size_mb'):
                        update_data['video_file_size_mb'] = result['file_size_mb']

                    self.logger.info(f"🔍 DEBUG: Final update_data for {article_id}: {update_data}")

                    # Update the document
                    self.logger.info(f"🔍 DEBUG: Executing MongoDB update for article: {article_id}")
                    update_result = self.news_collection.update_one(
                        {'id': article_id},
                        {'$set': update_data}
                    )

                    self.logger.info(f"🔍 DEBUG: MongoDB update result - matched: {update_result.matched_count}, modified: {update_result.modified_count}")

                    if update_result.modified_count > 0:
                        success_count += 1
                        self.logger.info(f"✅ Updated database for article: {article_id}")
                    else:
                        self.logger.warning(f"⚠️ No document updated for article: {article_id}")
                else:
                    # Log error but don't update database for failed generations
                    self.logger.error(f"❌ Video generation failed for article {article_id}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                self.logger.error(f"💥 Error updating database for article {result.get('article_id', 'unknown')}: {str(e)}")

        self.logger.info(f"🔍 DEBUG: Database update completed. Success count: {success_count}")
        return success_count


if __name__ == '__main__':
    # Create and run the job service
    job = VideoGeneratorJob()
    
    # Start the Flask application with job scheduling
    job.run_flask_app()
