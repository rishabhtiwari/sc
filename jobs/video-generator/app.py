"""
Video Generation Job Service - Main Application
"""

import os
import sys
import time
from datetime import datetime

# Add common directory to path for job framework
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import send_file, jsonify, request
from common.models.base_job import BaseJob
from common.utils.logger import setup_logger
from common.utils.multi_tenant_db import (
    build_multi_tenant_query,
    prepare_insert_document,
    prepare_update_document,
    extract_user_context_from_headers
)
from config.settings import Config
from services.video_generation_service import VideoGenerationService
from services.video_merge_service import VideoMergeService
from services.logo_service import LogoService
from services.shorts_generation_service import ShortsGenerationService


class VideoGeneratorJob(BaseJob):
    """Video Generation Job that extends BaseJob framework"""

    def __init__(self):
        super().__init__("video-generator", Config)
        self.video_service = VideoGenerationService(self.config, self.logger)
        self.merge_service = VideoMergeService(self.config, self.logger)
        self.logo_service = LogoService()
        self.shorts_service = ShortsGenerationService(self.config, self.logger)

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

    def is_multi_tenant_job(self) -> bool:
        """
        Video generator is a multi-tenant job - runs separately for each customer

        Returns:
            True to enable per-customer job execution
        """
        return True

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

    def _process_scheduled_configs(self, customer_id: str = None):
        """
        Process video configurations that are due for scheduled execution

        Args:
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)
        """
        try:
            self.logger.info("📅 Checking for scheduled video configurations...")

            # Get configurations collection
            configs_collection = self.news_db['long_video_configs']

            # Find configs that are due for processing
            from datetime import datetime
            now = datetime.utcnow()

            # Build query with multi-tenant filter
            base_query = {
                'status': 'completed',
                'frequency': {'$ne': 'none'},
                'nextRunTime': {'$lte': now}
            }
            query = build_multi_tenant_query(base_query, customer_id=customer_id)

            due_configs = list(configs_collection.find(query))

            if not due_configs:
                self.logger.info("📭 No scheduled configurations due for processing")
                return

            self.logger.info(f"📋 Found {len(due_configs)} scheduled configurations to process")

            # Process each configuration
            for config in due_configs:
                try:
                    config_id = str(config['_id'])
                    title = config.get('title', 'Untitled')
                    frequency = config.get('frequency', 'none')

                    self.logger.info(f"🎬 Processing scheduled config: {title} (ID: {config_id}, Frequency: {frequency})")

                    # Update status to processing
                    update_data = {
                        'status': 'processing',
                        'mergeStartedAt': now,
                        'lastRunTime': now,
                        'updatedAt': now
                    }
                    prepare_update_document(update_data, user_id='system')
                    configs_collection.update_one(
                        {'_id': config['_id']},
                        {'$set': update_data}
                    )

                    # Build query filter based on config
                    base_query_filter = {"video_path": {"$exists": True, "$ne": None}}

                    categories = config.get('categories', [])
                    if categories and len(categories) > 0:
                        base_query_filter["category"] = {"$in": categories}

                    country = config.get('country', '')
                    if country:
                        base_query_filter["source.country"] = country

                    language = config.get('language', '')
                    if language:
                        base_query_filter["lang"] = language

                    # Add customer_id filter for multi-tenancy
                    config_customer_id = config.get('customer_id')
                    query_filter = build_multi_tenant_query(base_query_filter, customer_id=config_customer_id)

                    # Get videos
                    video_count = config.get('videoCount', 20)
                    latest_news = list(self.news_collection.find(query_filter)
                                     .sort("publishedAt", -1)
                                     .limit(video_count))

                    if not latest_news:
                        self.logger.warning(f"⚠️ No videos found for config: {title}")
                        update_data = {
                            'status': 'failed',
                            'error': 'No videos found matching criteria',
                            'updatedAt': datetime.utcnow()
                        }
                        prepare_update_document(update_data, user_id='system')
                        configs_collection.update_one(
                            {'_id': config['_id']},
                            {'$set': update_data}
                        )
                        continue

                    # Merge videos
                    self.logger.info(f"🎬 Merging {len(latest_news)} videos for config: {title}")
                    merge_result = self.merge_service.merge_latest_videos(
                        latest_news,
                        title=config.get('title', ''),
                        config_id=str(config['_id']),
                        background_audio_id=config.get('backgroundAudioId')
                    )

                    if merge_result['status'] == 'success':
                        # Calculate next run time
                        next_run_time = self._calculate_next_run_time(now, frequency)
                        run_count = config.get('runCount', 0) + 1

                        # Update config with success
                        update_data = {
                            'status': 'completed',
                            'videoPath': merge_result.get('merged_video_path'),
                            'thumbnailPath': merge_result.get('thumbnail_path'),
                            'mergeCompletedAt': datetime.utcnow(),
                            'nextRunTime': next_run_time,
                            'runCount': run_count,
                            'error': None,
                            'updatedAt': datetime.utcnow()
                        }
                        prepare_update_document(update_data, user_id='system')
                        configs_collection.update_one(
                            {'_id': config['_id']},
                            {'$set': update_data}
                        )
                        self.logger.info(f"✅ Successfully processed config: {title} (Next run: {next_run_time})")
                    else:
                        # Update config with failure
                        update_data = {
                            'status': 'failed',
                            'error': merge_result.get('error', 'Unknown error'),
                            'updatedAt': datetime.utcnow()
                        }
                        prepare_update_document(update_data, user_id='system')
                        configs_collection.update_one(
                            {'_id': config['_id']},
                            {'$set': update_data}
                        )
                        self.logger.error(f"❌ Failed to process config: {title}")

                except Exception as e:
                    self.logger.error(f"💥 Error processing config {config.get('title', 'unknown')}: {str(e)}")
                    try:
                        update_data = {
                            'status': 'failed',
                            'error': str(e),
                            'updatedAt': datetime.utcnow()
                        }
                        prepare_update_document(update_data, user_id='system')
                        configs_collection.update_one(
                            {'_id': config['_id']},
                            {'$set': update_data}
                        )
                    except:
                        pass

        except Exception as e:
            self.logger.error(f"💥 Error in _process_scheduled_configs: {str(e)}")

    def _calculate_next_run_time(self, current_time, frequency):
        """Calculate next run time based on frequency"""
        from datetime import timedelta

        if frequency == 'none':
            return None
        elif frequency == 'hourly':
            return current_time + timedelta(hours=1)
        elif frequency == 'daily':
            return current_time + timedelta(days=1)
        elif frequency == 'weekly':
            return current_time + timedelta(weeks=1)
        elif frequency == 'monthly':
            return current_time + timedelta(days=30)
        else:
            return None

    def run_job(self, job_id: str, is_on_demand: bool = False, **kwargs) -> dict:
        """
        Main job execution method - finds articles with audio but no video and generates videos
        Also processes scheduled video configurations

        Args:
            job_id: Job instance ID for tracking
            is_on_demand: True if this is a manual/on-demand job
            **kwargs: Additional job parameters (customer_id, user_id)
        """
        try:
            # Extract customer_id and user_id from kwargs
            customer_id = kwargs.get('customer_id')
            user_id = kwargs.get('user_id')

            customer_info = f" for customer {customer_id}" if customer_id else ""
            self.logger.info(f"🚀 Starting video generation job {job_id}{customer_info} (on_demand: {is_on_demand})...")
            self.logger.info(f"🔍 DEBUG: run_job called with job_id={job_id}, is_on_demand={is_on_demand}, customer_id={customer_id}")

            # First, process scheduled video configurations
            self._process_scheduled_configs(customer_id=customer_id)

            # Get articles that need video generation
            articles_to_process = self._get_articles_for_video_generation(customer_id=customer_id)

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
            **kwargs: Additional parameters from BaseJob framework (customer_id, user_id)

        Returns:
            Result dictionary with processing outcome
        """
        try:
            article_id = article['id']
            # Extract customer_id from article or kwargs
            customer_id = article.get('customer_id') or kwargs.get('customer_id')

            self.logger.info(f"🎬 Processing video generation for article: {article_id} (customer_id: {customer_id})")

            # Generate video using the video service
            # Skip background music for individual videos - it will be added at shorts/merge level
            result = self.video_service.generate_video_for_article(article, skip_background_music=True, customer_id=customer_id)

            if result['status'] == 'success':
                self.logger.info(f"✅ Video generated successfully for article: {article_id}")

                # Update database with video_path FIRST before generating shorts
                update_data = {
                    'video_path': result['video_path'],
                    'updated_at': datetime.utcnow()
                }
                if result.get('thumbnail_path'):
                    update_data['thumbnail_path'] = result['thumbnail_path']
                if result.get('duration_seconds'):
                    update_data['video_duration_seconds'] = result['duration_seconds']
                if result.get('file_size_mb'):
                    update_data['video_file_size_mb'] = result['file_size_mb']

                # Add audit tracking
                prepare_update_document(update_data, user_id='system')

                # Build query with customer_id filter
                article_customer_id = article.get('customer_id')
                query = build_multi_tenant_query({'id': article_id}, customer_id=article_customer_id)

                self.news_collection.update_one(query, {'$set': update_data})
                self.logger.info(f"✅ Database updated with video_path for article: {article_id}")

                # Also generate YouTube Short
                try:
                    # Get voice information for logging
                    voice_used = article.get('voice', 'unknown')
                    self.logger.info(f"🎬 Generating YouTube Short for article: {article_id} with voice anchor: {voice_used}")

                    # Get paths from result (these are relative paths like /public/...)
                    relative_video_path = result.get('video_path')
                    relative_thumbnail_path = result.get('thumbnail_path')

                    # Convert to absolute filesystem paths
                    video_path = os.path.join('/app', relative_video_path.lstrip('/')) if relative_video_path else None
                    thumbnail_path = os.path.join('/app', relative_thumbnail_path.lstrip('/')) if relative_thumbnail_path else None

                    self.logger.info(f"🔍 Video path: {video_path}")
                    self.logger.info(f"🔍 Thumbnail path: {thumbnail_path}")

                    if video_path and thumbnail_path and os.path.exists(video_path) and os.path.exists(thumbnail_path):
                        # Get subscribe video path (use the one from public directory which has audio)
                        subscribe_video_path = '/app/public/CNINews_Subscribe.mp4'

                        # Get output directory
                        output_dir = os.path.dirname(video_path)

                        # Generate short
                        shorts_result = self.shorts_service.generate_short(
                            news_video_path=video_path,
                            thumbnail_path=thumbnail_path,
                            title=article.get('title', 'News Update'),
                            output_dir=output_dir,
                            subscribe_video_path=subscribe_video_path if os.path.exists(subscribe_video_path) else None
                        )

                        if shorts_result['status'] == 'success':
                            # Update database with shorts path
                            shorts_path = shorts_result['short_path']
                            # Convert to relative path like /public/article_id/short.mp4
                            relative_shorts_path = shorts_path.replace('/app', '')

                            # Add audit tracking
                            update_data = {
                                'shorts_video_path': relative_shorts_path,
                                'updated_at': datetime.utcnow()
                            }
                            prepare_update_document(update_data, user_id='system')

                            # Build query with customer_id filter
                            query = build_multi_tenant_query({'id': article_id}, customer_id=article_customer_id)

                            self.news_collection.update_one(query, {'$set': update_data})

                            self.logger.info(f"✅ YouTube Short generated successfully: {relative_shorts_path}")
                            result['shorts_video_path'] = relative_shorts_path
                        else:
                            self.logger.warning(f"⚠️ Shorts generation failed: {shorts_result.get('error', 'Unknown error')}")
                            result['shorts_error'] = shorts_result.get('error')
                    else:
                        self.logger.warning(f"⚠️ Skipping shorts generation - missing video or thumbnail")

                except Exception as shorts_error:
                    # Don't fail the whole task if shorts generation fails
                    self.logger.error(f"⚠️ Error generating shorts (non-critical): {str(shorts_error)}")
                    result['shorts_error'] = str(shorts_error)

            else:
                self.logger.error(
                    f"❌ Video generation failed for article: {article_id} - {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            error_msg = f"Error processing video generation task: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'article_id': article.get('id', 'unknown')
            }

    def _get_articles_for_video_generation(self, customer_id: str = None) -> list:
        """
        Get articles that have audio and cleaned image but no video generated yet

        Args:
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            List of article documents that need video generation
        """
        try:
            # Query for articles that have audio_paths, clean_image, but no video_path
            base_query = {
                'audio_paths': {'$ne': None, '$exists': True},  # Has audio paths
                'clean_image': {'$ne': None, '$exists': True},  # Has cleaned image
                'video_path': {'$in': [None, '']},  # No video yet
                'status': {'$in': ['completed', 'published']}  # Only process completed articles
            }

            # Add customer_id filter for multi-tenancy
            query = build_multi_tenant_query(base_query, customer_id=customer_id)

            # Get all articles that need video generation
            articles = list(
                self.news_collection.find(query)
                .sort('updated_at', -1)  # Process newest first
            )

            self.logger.info(f"🔍 Found {len(articles)} articles ready for video generation (with audio and cleaned image)")

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
                self.logger.info(f"🔍 DEBUG: Processing result {i + 1}/{len(results)}: {result}")

                article_id = result.get('article_id')
                if not article_id:
                    self.logger.warning(f"⚠️ DEBUG: Result {i + 1} missing article_id: {result}")
                    continue

                self.logger.info(f"🔍 DEBUG: Processing article_id: {article_id}, status: {result.get('status')}")

                if result['status'] == 'success':
                    # Note: video_path and thumbnail_path are already updated in process_single_task
                    # before shorts generation. Here we only update shorts_video_path if available.
                    update_data = {
                        'updated_at': datetime.utcnow()
                    }

                    # Add shorts_video_path if available
                    if result.get('shorts_video_path'):
                        update_data['shorts_video_path'] = result['shorts_video_path']
                        self.logger.info(f"🔍 DEBUG: Adding shorts_video_path to update: {result['shorts_video_path']}")

                    self.logger.info(f"🔍 DEBUG: Final update_data for {article_id}: {update_data}")

                    # Only update if there's something to update beyond updated_at
                    if len(update_data) > 1:
                        # Add audit tracking
                        prepare_update_document(update_data, user_id='system')

                        # Build query with customer_id filter
                        article_customer_id = result.get('customer_id')
                        query = build_multi_tenant_query({'id': article_id}, customer_id=article_customer_id)

                        # Update the document
                        self.logger.info(f"🔍 DEBUG: Executing MongoDB update for article: {article_id}")
                        update_result = self.news_collection.update_one(query, {'$set': update_data})

                        self.logger.info(
                            f"🔍 DEBUG: MongoDB update result - matched: {update_result.matched_count}, modified: {update_result.modified_count}")

                        if update_result.modified_count > 0:
                            success_count += 1
                            self.logger.info(f"✅ Updated database for article: {article_id}")
                        else:
                            self.logger.warning(f"⚠️ No document updated for article: {article_id}")
                    else:
                        # No additional updates needed (video_path already updated in process_single_task)
                        success_count += 1
                        self.logger.info(f"✅ Article {article_id} already updated in process_single_task")
                else:
                    # Log error but don't update database for failed generations
                    self.logger.error(
                        f"❌ Video generation failed for article {article_id}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                self.logger.error(
                    f"💥 Error updating database for article {result.get('article_id', 'unknown')}: {str(e)}")

        self.logger.info(f"🔍 DEBUG: Database update completed. Success count: {success_count}")
        return success_count

    def _setup_routes(self):
        """Setup Flask routes including base routes and video merging routes"""
        # Call parent method to setup base routes
        super()._setup_routes()

        # Add video merging routes
        """Setup additional Flask routes for video merging"""

        @self.app.route('/merge-latest', methods=['POST'])
        def merge_latest_videos():
            """Merge latest news videos into a single video with configuration and alternating male/female anchors"""
            try:
                # Import request first
                from flask import request

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')
                user_id = user_context.get('user_id')

                # Get configuration from request body
                config = request.get_json() or {}

                # Extract configuration parameters
                categories = config.get('categories', [])
                country = config.get('country', '')
                language = config.get('language', '')
                video_count = config.get('videoCount', 20)
                title = config.get('title', '')
                config_id = config.get('config_id')  # Optional: if called from /configs/<id>/merge
                article_ids = config.get('article_ids', [])  # Optional: manually selected article IDs in order

                self.logger.info(f"🎬 Starting merge with config: categories={categories}, country={country}, language={language}, count={video_count}, title={title}, manual_selection={len(article_ids) > 0}, customer_id={customer_id}")

                # Check if manual selection is provided
                if article_ids and len(article_ids) > 0:
                    # Manual selection mode: fetch articles by IDs in the specified order
                    self.logger.info(f"📝 Using manual selection: {len(article_ids)} articles selected")

                    latest_news = []
                    for article_id in article_ids:
                        # Build query with customer_id filter
                        base_query = {"id": article_id, "video_path": {"$exists": True, "$ne": None}}
                        query = build_multi_tenant_query(base_query, customer_id=customer_id)

                        article = self.news_collection.find_one(
                            query,
                            {"id": 1, "title": 1, "video_path": 1, "created_at": 1, "voice": 1, "category": 1, "source.country": 1, "lang": 1}
                        )
                        if article:
                            latest_news.append(article)
                        else:
                            self.logger.warning(f"⚠️ Article {article_id} not found or has no video")

                    self.logger.info(f"✅ Found {len(latest_news)} out of {len(article_ids)} selected articles with videos")
                else:
                    # Automatic selection mode: use filters
                    self.logger.info(f"🤖 Using automatic selection with filters")

                    # Build query filter
                    base_query_filter = {"video_path": {"$exists": True, "$ne": None}}

                    # Add category filter if specified
                    if categories and len(categories) > 0:
                        base_query_filter["category"] = {"$in": categories}

                    # Add country filter if specified
                    if country:
                        base_query_filter["source.country"] = country

                    # Add language filter if specified
                    if language:
                        base_query_filter["lang"] = language

                    # Add customer_id filter for multi-tenancy
                    query_filter = build_multi_tenant_query(base_query_filter, customer_id=customer_id)

                    self.logger.info(f"📋 Query filter: {query_filter}")

                    # Get latest news with videos, including voice field
                    latest_news = list(self.news_collection.find(
                        query_filter,
                        {"id": 1, "title": 1, "video_path": 1, "created_at": 1, "voice": 1, "category": 1, "source.country": 1, "lang": 1}
                    ).sort("created_at", -1).limit(video_count))

                if not latest_news:
                    return jsonify({
                        "error": "No news videos found",
                        "status": "error"
                    }), 404

                self.logger.info(f"📊 Found {len(latest_news)} news videos to merge")

                # Log voice distribution for debugging
                male_count = sum(1 for news in latest_news if news.get('voice') in ['am_adam', 'am_michael', 'bm_george', 'bm_lewis', 'male'])
                female_count = sum(1 for news in latest_news if news.get('voice') in ['af_bella', 'af_nicole', 'af_sarah', 'af_sky', 'bf_emma', 'bf_isabella', 'female'])
                no_voice_count = sum(1 for news in latest_news if not news.get('voice'))
                self.logger.info(f"🎭 Voice distribution: {male_count} male, {female_count} female, {no_voice_count} no voice")

                # Delete old merged video file immediately (before async processing starts)
                # This prevents users from downloading the old video while new one is being created
                import os
                old_video_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news.mp4')
                if os.path.exists(old_video_path):
                    try:
                        os.remove(old_video_path)
                        self.logger.info("🗑️ Deleted old merged video file before starting new merge")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not delete old merged video: {e}")

                # Return immediate response to user with processing status
                from threading import Thread
                import time

                def merge_videos_async():
                    try:
                        self.logger.info("🎬 Starting async video merge process...")
                        start_time = time.time()

                        # Get background audio ID from config if config_id is provided
                        background_audio_id = None
                        if config_id:
                            try:
                                from bson import ObjectId
                                configs_collection = self.news_db['long_video_configs']
                                config_doc = configs_collection.find_one({'_id': ObjectId(config_id)})
                                if config_doc:
                                    background_audio_id = config_doc.get('backgroundAudioId')
                            except Exception as e:
                                self.logger.warning(f"Could not fetch background audio from config: {e}")

                        # Merge videos with title parameter, config_id, background audio, and customer_id
                        result = self.merge_service.merge_latest_videos(
                            latest_news,
                            title=title,
                            config_id=config_id,
                            background_audio_id=background_audio_id,
                            customer_id=customer_id
                        )

                        end_time = time.time()
                        processing_time = round(end_time - start_time, 2)

                        if result['status'] == 'success':
                            self.logger.info(
                                f"✅ Video merge completed successfully in {processing_time} seconds - merged {result['video_count']} videos")

                            # If config_id is provided, update the configuration
                            if config_id:
                                try:
                                    from bson import ObjectId
                                    from datetime import datetime
                                    configs_collection = self.news_db['long_video_configs']

                                    # Prepare update data with audit tracking
                                    update_data = {
                                        'status': 'completed',
                                        'videoPath': result.get('merged_video_path'),
                                        'thumbnailPath': result.get('thumbnail_path'),
                                        'mergeCompletedAt': datetime.utcnow(),
                                        'error': None,
                                        'updatedAt': datetime.utcnow()
                                    }
                                    prepare_update_document(update_data, user_id=user_id or 'system')

                                    configs_collection.update_one(
                                        {'_id': ObjectId(config_id)},
                                        {'$set': update_data}
                                    )
                                    self.logger.info(f"✅ Updated config {config_id} with merge results")
                                except Exception as e:
                                    self.logger.error(f"⚠️ Failed to update config {config_id}: {str(e)}")
                        else:
                            self.logger.error(f"❌ Video merge failed: {result['error']}")

                            # If config_id is provided, update with failure
                            if config_id:
                                try:
                                    from bson import ObjectId
                                    from datetime import datetime
                                    configs_collection = self.news_db['long_video_configs']

                                    # Prepare update data with audit tracking
                                    update_data = {
                                        'status': 'failed',
                                        'error': result.get('error', 'Unknown error'),
                                        'updatedAt': datetime.utcnow()
                                    }
                                    prepare_update_document(update_data, user_id=user_id or 'system')

                                    configs_collection.update_one(
                                        {'_id': ObjectId(config_id)},
                                        {'$set': update_data}
                                    )
                                    self.logger.info(f"✅ Updated config {config_id} with failure status")
                                except Exception as e:
                                    self.logger.error(f"⚠️ Failed to update config {config_id}: {str(e)}")

                    except Exception as e:
                        self.logger.error(f"❌ Error in async video merge: {str(e)}")

                        # If config_id is provided, update with error
                        if config_id:
                            try:
                                from bson import ObjectId
                                from datetime import datetime
                                configs_collection = self.news_db['long_video_configs']

                                # Prepare update data with audit tracking
                                update_data = {
                                    'status': 'failed',
                                    'error': str(e),
                                    'updatedAt': datetime.utcnow()
                                }
                                prepare_update_document(update_data, user_id=user_id or 'system')

                                configs_collection.update_one(
                                    {'_id': ObjectId(config_id)},
                                    {'$set': update_data}
                                )
                            except:
                                pass

                # Start async processing
                thread = Thread(target=merge_videos_async)
                thread.daemon = True
                thread.start()

                return jsonify({
                    "message": f"Video merging started for {len(latest_news)} videos with alternating male/female anchors. This process may take 2-5 minutes depending on video length and quality.",
                    "status": "processing",
                    "video_count": len(latest_news),
                    "voice_distribution": {
                        "male": male_count,
                        "female": female_count,
                        "no_voice": no_voice_count
                    },
                    "estimated_time": "2-5 minutes",
                    "download_url": "/download/latest-20-news.mp4",
                    "note": "Please wait for processing to complete before downloading. Check server logs for progress updates. Videos are ordered with alternating male and female anchor voices."
                })

            except Exception as e:
                self.logger.error(f"❌ Error starting video merge: {str(e)}")
                return jsonify({
                    "error": f"Failed to start video merge: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/merge-status', methods=['GET'])
        def get_merge_status():
            """Check the status of video merging process"""
            try:
                merged_video_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news.mp4')
                thumbnail_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news-thumbnail.jpg')

                if os.path.exists(merged_video_path):
                    # Get file info
                    file_stats = os.stat(merged_video_path)
                    file_size_mb = round(file_stats.st_size / (1024 * 1024), 2)
                    modified_time = time.ctime(file_stats.st_mtime)

                    response = {
                        "status": "completed",
                        "message": "Merged video is ready for download",
                        "file_size_mb": file_size_mb,
                        "last_updated": modified_time,
                        "download_url": "/download/latest-20-news.mp4"
                    }

                    # Add thumbnail info if available
                    if os.path.exists(thumbnail_path):
                        response["thumbnail_url"] = "/download/latest-20-news-thumbnail.jpg"
                        response["thumbnail_available"] = True
                    else:
                        response["thumbnail_available"] = False

                    return jsonify(response)
                else:
                    return jsonify({
                        "status": "not_found",
                        "message": "No merged video found. Please start the merge process first using /merge-latest endpoint."
                    })

            except Exception as e:
                self.logger.error(f"❌ Error checking merge status: {str(e)}")
                return jsonify({
                    "error": f"Failed to check status: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/download/latest-20-news.mp4', methods=['GET'])
        def download_merged_video():
            """Download the merged video file"""
            try:
                merged_video_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news.mp4')

                if not os.path.exists(merged_video_path):
                    return jsonify({
                        "error": "Merged video not found. Please run /merge-latest first.",
                        "status": "error"
                    }), 404

                return send_file(
                    merged_video_path,
                    as_attachment=True,
                    download_name='latest-20-news.mp4',
                    mimetype='video/mp4'
                )

            except Exception as e:
                self.logger.error(f"❌ Error downloading merged video: {str(e)}")
                return jsonify({
                    "error": f"Failed to download video: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/download/latest-20-news-thumbnail.jpg', methods=['GET'])
        def download_thumbnail():
            """Download the thumbnail for the merged video"""
            try:
                thumbnail_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news-thumbnail.jpg')

                if not os.path.exists(thumbnail_path):
                    return jsonify({
                        "error": "Thumbnail not found. Please run /merge-latest first.",
                        "status": "error"
                    }), 404

                return send_file(
                    thumbnail_path,
                    as_attachment=True,
                    download_name='latest-20-news-thumbnail.jpg',
                    mimetype='image/jpeg'
                )

            except Exception as e:
                self.logger.error(f"❌ Error downloading thumbnail: {str(e)}")
                return jsonify({
                    "error": f"Failed to download thumbnail: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/download/configs/<config_id>/<filename>', methods=['GET'])
        def download_config_file(config_id, filename):
            """Download config-specific video or thumbnail file"""
            try:
                # Security: Only allow specific file types
                allowed_files = ['latest.mp4', 'latest-thumbnail.jpg']

                if filename not in allowed_files:
                    return jsonify({
                        "error": f"Invalid filename. Allowed: {', '.join(allowed_files)}",
                        "status": "error"
                    }), 400

                # Construct file path: /public/<config_id>/<filename>
                file_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, config_id, filename)

                if not os.path.exists(file_path):
                    return jsonify({
                        "error": f"File not found: {filename}",
                        "status": "error"
                    }), 404

                # Determine mimetype
                if filename.endswith('.mp4'):
                    mimetype = 'video/mp4'
                elif filename.endswith('.jpg'):
                    mimetype = 'image/jpeg'
                else:
                    mimetype = 'application/octet-stream'

                return send_file(
                    file_path,
                    as_attachment=False,  # Display inline for preview
                    download_name=filename,
                    mimetype=mimetype
                )

            except Exception as e:
                self.logger.error(f"❌ Error downloading config file: {str(e)}")
                return jsonify({
                    "error": f"Failed to download file: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/generate-short', methods=['POST'])
        def generate_short():
            """Generate YouTube Short for a news article with voice anchor information"""
            try:
                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')
                user_id = user_context.get('user_id')

                data = request.get_json() or {}
                article_id = data.get('article_id')

                if not article_id:
                    return jsonify({
                        "error": "article_id is required",
                        "status": "error"
                    }), 400

                self.logger.info(f"🎬 Generating YouTube Short for article: {article_id}")

                # Get article from database with multi-tenant filter
                base_query = {'id': article_id}
                query = build_multi_tenant_query(base_query, customer_id=customer_id)
                article = self.news_collection.find_one(query)

                if not article:
                    return jsonify({
                        "error": f"Article not found: {article_id}",
                        "status": "error"
                    }), 404

                # Check if video exists
                video_path = article.get('video_path')
                if not video_path:
                    return jsonify({
                        "error": "Article does not have a video. Generate video first.",
                        "status": "error"
                    }), 400

                # Get full video path
                if not video_path.startswith('/'):
                    video_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, article_id, os.path.basename(video_path))

                if not os.path.exists(video_path):
                    return jsonify({
                        "error": f"Video file not found: {video_path}",
                        "status": "error"
                    }), 404

                # Get thumbnail path
                output_dir = os.path.join(self.config.VIDEO_OUTPUT_DIR, article_id)
                thumbnail_path = os.path.join(output_dir, 'thumbnail.jpg')

                if not os.path.exists(thumbnail_path):
                    return jsonify({
                        "error": f"Thumbnail not found: {thumbnail_path}",
                        "status": "error"
                    }), 404

                # Get subscribe video path (use the one from public directory which has audio)
                subscribe_video_path = '/app/public/CNINews_Subscribe.mp4'

                # Get voice information for logging
                voice_used = article.get('voice', 'unknown')
                self.logger.info(f"🎭 Generating short with voice anchor: {voice_used}")

                # Generate short
                result = self.shorts_service.generate_short(
                    news_video_path=video_path,
                    thumbnail_path=thumbnail_path,
                    title=article.get('title', 'News Update'),
                    output_dir=output_dir,
                    subscribe_video_path=subscribe_video_path if os.path.exists(subscribe_video_path) else None
                )

                if result['status'] == 'success':
                    # Update database with shorts path
                    shorts_path = result['short_path']
                    # Store relative path
                    relative_shorts_path = os.path.join(article_id, os.path.basename(shorts_path))

                    # Prepare update with audit tracking
                    update_data = {
                        'shorts_video_path': relative_shorts_path,
                        'updated_at': datetime.utcnow()
                    }
                    prepare_update_document(update_data, user_id=user_id or 'system')

                    # Update with multi-tenant filter
                    query = build_multi_tenant_query({'id': article_id}, customer_id=customer_id)
                    self.news_collection.update_one(query, {'$set': update_data}
                    )

                    self.logger.info(f"✅ Short generated and saved: {shorts_path}")

                    return jsonify({
                        "message": "YouTube Short generated successfully",
                        "status": "success",
                        "article_id": article_id,
                        "short_path": relative_shorts_path,
                        "voice_anchor": voice_used,
                        "file_size_mb": result.get('file_size_mb'),
                        "duration": result.get('duration'),
                        "dimensions": result.get('dimensions'),
                        "download_url": f"/download/{article_id}/{os.path.basename(shorts_path)}"
                    })
                else:
                    return jsonify({
                        "error": result.get('error', 'Unknown error'),
                        "status": "error",
                        "article_id": article_id
                    }), 500

            except Exception as e:
                self.logger.error(f"❌ Error generating short: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                return jsonify({
                    "error": f"Failed to generate short: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/generate-logo', methods=['POST'])
        def generate_logo():
            """Generate CNI logo (CNN style)"""
            try:
                from flask import request

                # Get parameters from request
                data = request.get_json() or {}
                size = data.get('size', 500)
                with_border = data.get('with_border', False)

                # Generate logo
                logo_filename = 'cni-logo-border.png' if with_border else 'cni-logo.png'
                logo_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, logo_filename)

                if with_border:
                    border_width = data.get('border_width', 10)
                    self.logo_service.generate_cni_logo_with_border(logo_path, size, border_width)
                else:
                    self.logo_service.generate_cni_logo(logo_path, size)

                return jsonify({
                    "status": "success",
                    "message": "Logo generated successfully",
                    "logo_path": f"/public/{logo_filename}",
                    "download_url": f"/download/{logo_filename}",
                    "size": size,
                    "with_border": with_border
                })

            except Exception as e:
                self.logger.error(f"❌ Error generating logo: {str(e)}")
                return jsonify({
                    "error": f"Failed to generate logo: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/download/<article_id>/<filename>', methods=['GET'])
        def download_article_file(article_id, filename):
            """Download article video or image file"""
            try:
                # Security: Only allow specific file types
                allowed_extensions = ['.mp4', '.jpg', '.png', '.jpeg']
                file_ext = os.path.splitext(filename)[1].lower()

                if file_ext not in allowed_extensions:
                    return jsonify({
                        "error": "Invalid file type",
                        "status": "error"
                    }), 400

                # Construct file path
                file_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, article_id, filename)

                if not os.path.exists(file_path):
                    self.logger.error(f"❌ File not found: {file_path}")
                    return jsonify({
                        "error": "File not found",
                        "status": "error"
                    }), 404

                # Determine mimetype
                mimetype = 'video/mp4' if file_ext == '.mp4' else f'image/{file_ext[1:]}'

                self.logger.info(f"📥 Serving file: {file_path}")
                return send_file(
                    file_path,
                    mimetype=mimetype,
                    as_attachment=True,
                    download_name=filename
                )

            except Exception as e:
                self.logger.error(f"❌ Failed to download file: {str(e)}")
                return jsonify({
                    "error": f"Failed to download file: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/available-news', methods=['GET'])
        def get_available_news():
            """Get list of news articles with videos available for merging"""
            try:
                from flask import request

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')

                # Get query parameters
                limit = int(request.args.get('limit', 100))
                categories = request.args.getlist('categories')
                country = request.args.get('country', '')
                language = request.args.get('language', '')

                # Build query filter
                base_query_filter = {"video_path": {"$exists": True, "$ne": None}}

                # Add filters if specified
                if categories and len(categories) > 0:
                    base_query_filter["category"] = {"$in": categories}
                if country:
                    base_query_filter["source.country"] = country
                if language:
                    base_query_filter["lang"] = language

                # Apply multi-tenant filter
                query_filter = build_multi_tenant_query(base_query_filter, customer_id=customer_id)

                # Get news articles with videos
                articles = list(self.news_collection.find(
                    query_filter,
                    {
                        "id": 1,
                        "title": 1,
                        "video_path": 1,
                        "created_at": 1,
                        "publishedAt": 1,
                        "voice": 1,
                        "category": 1,
                        "source": 1,
                        "lang": 1,
                        "image": 1,
                        "clean_image": 1
                    }
                ).sort("created_at", -1).limit(limit))

                # Format response
                formatted_articles = []
                for article in articles:
                    formatted_articles.append({
                        "id": article.get("id"),
                        "title": article.get("title"),
                        "video_path": article.get("video_path"),
                        "created_at": article.get("created_at"),
                        "publishedAt": article.get("publishedAt"),
                        "voice": article.get("voice"),
                        "category": article.get("category"),
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "language": article.get("lang"),
                        "thumbnail": article.get("clean_image") or article.get("image")
                    })

                return jsonify({
                    "status": "success",
                    "count": len(formatted_articles),
                    "articles": formatted_articles
                })

            except Exception as e:
                self.logger.error(f"❌ Failed to get available news: {str(e)}")
                return jsonify({
                    "error": f"Failed to get available news: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/download/<logo_filename>', methods=['GET'])
        def download_logo(logo_filename):
            """Download generated logo"""
            try:
                # Only allow PNG logo files
                if not logo_filename.endswith('.png') or 'logo' not in logo_filename:
                    return jsonify({
                        "error": "Invalid logo filename",
                        "status": "error"
                    }), 400

                logo_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, logo_filename)

                if not os.path.exists(logo_path):
                    return jsonify({
                        "error": "Logo not found. Please generate it first using /generate-logo",
                        "status": "error"
                    }), 404

                return send_file(
                    logo_path,
                    as_attachment=True,
                    download_name=logo_filename,
                    mimetype='image/png'
                )

            except Exception as e:
                self.logger.error(f"❌ Error downloading logo: {str(e)}")
                return jsonify({
                    "error": f"Failed to download logo: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/test-ken-burns', methods=['POST'])
        def test_ken_burns():
            """Test Ken Burns effect on a single video"""
            try:
                from flask import request

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')
                user_id = user_context.get('user_id')

                self.logger.info("🎬 Testing Ken Burns effect on a video")

                # Get parameters from request
                data = request.get_json() or {}
                article_id = data.get('article_id')

                # If no article_id provided, get the latest article with audio
                if not article_id:
                    base_query = {
                        'audio_paths': {'$ne': None, '$exists': True},
                        'image': {'$ne': None, '$exists': True},
                        'status': {'$in': ['completed', 'published']}
                    }
                    query = build_multi_tenant_query(base_query, customer_id=customer_id)
                    latest_article = self.news_collection.find_one(query, sort=[('created_at', -1)])

                    if not latest_article:
                        return jsonify({
                            "error": "No articles with audio found",
                            "status": "error"
                        }), 404

                    article_id = latest_article['id']
                else:
                    base_query = {'id': article_id}
                    query = build_multi_tenant_query(base_query, customer_id=customer_id)
                    latest_article = self.news_collection.find_one(query)

                    if not latest_article:
                        return jsonify({
                            "error": f"Article {article_id} not found",
                            "status": "error"
                        }), 404

                self.logger.info(f"📊 Testing Ken Burns effect on article: {article_id}")

                # Generate video with Ken Burns effect
                result = self.video_service.generate_video_for_article(latest_article)

                if result['status'] == 'success':
                    # Prepare update with audit tracking
                    update_data = {
                        'video_path': result['video_path'],
                        'updated_at': datetime.utcnow()
                    }
                    prepare_update_document(update_data, user_id=user_id or 'system')

                    # Update database with multi-tenant filter
                    query = build_multi_tenant_query({'id': article_id}, customer_id=customer_id)
                    self.news_collection.update_one(query, {'$set': update_data})

                    return jsonify({
                        "message": "Ken Burns effect test completed successfully",
                        "status": "success",
                        "article_id": article_id,
                        "video_path": result['video_path'],
                        "download_url": f"/download/{os.path.basename(result['video_path'])}",
                        "ken_burns_config": {
                            "enabled": self.config.ENABLE_KEN_BURNS,
                            "zoom_start": self.config.KEN_BURNS_ZOOM_START,
                            "zoom_end": self.config.KEN_BURNS_ZOOM_END,
                            "easing": self.config.KEN_BURNS_EASING
                        }
                    })
                else:
                    return jsonify({
                        "error": result.get('error', 'Unknown error'),
                        "status": "error",
                        "article_id": article_id
                    }), 500

            except Exception as e:
                self.logger.error(f"❌ Error testing Ken Burns effect: {str(e)}")
                return jsonify({
                    "error": f"Failed to test Ken Burns effect: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/test-fade-text', methods=['POST'])
        def test_fade_text():
            """Test Fade Text effect on a single video"""
            try:
                from flask import request

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')
                user_id = user_context.get('user_id')

                self.logger.info("🎬 Testing Fade Text effect on a video")

                # Get parameters from request
                data = request.get_json() or {}
                article_id = data.get('article_id')

                # Optional: Override fade text settings for this test
                fade_in_duration = data.get('fade_in_duration', self.config.FADE_TEXT_IN_DURATION)
                fade_out_duration = data.get('fade_out_duration', self.config.FADE_TEXT_OUT_DURATION)
                fade_type = data.get('fade_type', self.config.FADE_TEXT_TYPE)

                # If no article_id provided, get the latest article with audio
                if not article_id:
                    base_query = {
                        'audio_paths': {'$ne': None, '$exists': True},
                        'image': {'$ne': None, '$exists': True},
                        'status': {'$in': ['completed', 'published']}
                    }
                    query = build_multi_tenant_query(base_query, customer_id=customer_id)
                    latest_article = self.news_collection.find_one(query, sort=[('created_at', -1)])

                    if not latest_article:
                        return jsonify({
                            "error": "No articles with audio found",
                            "status": "error"
                        }), 404

                    article_id = latest_article['id']
                else:
                    base_query = {'id': article_id}
                    query = build_multi_tenant_query(base_query, customer_id=customer_id)
                    latest_article = self.news_collection.find_one(query)

                    if not latest_article:
                        return jsonify({
                            "error": f"Article {article_id} not found",
                            "status": "error"
                        }), 404

                self.logger.info(f"📊 Testing Fade Text effect on article: {article_id}")

                # Temporarily override fade text settings if provided
                original_fade_in = self.config.FADE_TEXT_IN_DURATION
                original_fade_out = self.config.FADE_TEXT_OUT_DURATION
                original_fade_type = self.config.FADE_TEXT_TYPE

                try:
                    self.config.FADE_TEXT_IN_DURATION = float(fade_in_duration)
                    self.config.FADE_TEXT_OUT_DURATION = float(fade_out_duration)
                    self.config.FADE_TEXT_TYPE = fade_type

                    # Generate video with Fade Text effect
                    result = self.video_service.generate_video_for_article(latest_article)
                finally:
                    # Restore original settings
                    self.config.FADE_TEXT_IN_DURATION = original_fade_in
                    self.config.FADE_TEXT_OUT_DURATION = original_fade_out
                    self.config.FADE_TEXT_TYPE = original_fade_type

                if result['status'] == 'success':
                    # Prepare update with audit tracking
                    update_data = {
                        'video_path': result['video_path'],
                        'updated_at': datetime.utcnow()
                    }
                    prepare_update_document(update_data, user_id=user_id or 'system')

                    # Update database with multi-tenant filter
                    query = build_multi_tenant_query({'id': article_id}, customer_id=customer_id)
                    self.news_collection.update_one(query, {'$set': update_data})

                    return jsonify({
                        "message": "Fade Text effect test completed successfully",
                        "status": "success",
                        "article_id": article_id,
                        "video_path": result['video_path'],
                        "download_url": f"/download/{os.path.basename(result['video_path'])}",
                        "fade_text_config": {
                            "enabled": self.config.ENABLE_FADE_TEXT,
                            "fade_in_duration": float(fade_in_duration),
                            "fade_out_duration": float(fade_out_duration),
                            "fade_type": fade_type
                        },
                        "ken_burns_config": {
                            "enabled": self.config.ENABLE_KEN_BURNS,
                            "zoom_start": self.config.KEN_BURNS_ZOOM_START,
                            "zoom_end": self.config.KEN_BURNS_ZOOM_END,
                            "easing": self.config.KEN_BURNS_EASING
                        }
                    })
                else:
                    return jsonify({
                        "error": result.get('error', 'Unknown error'),
                        "status": "error",
                        "article_id": article_id
                    }), 500

            except Exception as e:
                self.logger.error(f"❌ Error testing Fade Text effect: {str(e)}")
                return jsonify({
                    "error": f"Failed to test Fade Text effect: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/test-logo-watermark', methods=['POST'])
        def test_logo_watermark():
            """Test Logo Watermark effect on a single video"""
            try:
                from flask import request

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')
                user_id = user_context.get('user_id')

                self.logger.info("🎬 Testing Logo Watermark effect on a video")

                # Get parameters from request
                data = request.get_json() or {}
                article_id = data.get('article_id')

                # Optional: Override logo watermark settings for this test
                logo_position = data.get('position', self.config.LOGO_POSITION)
                logo_opacity = data.get('opacity', self.config.LOGO_OPACITY)
                logo_scale = data.get('scale', self.config.LOGO_SCALE)
                logo_margin = data.get('margin', self.config.LOGO_MARGIN)

                # If no article_id provided, get the latest article with audio
                if not article_id:
                    base_query = {
                        'audio_paths': {'$ne': None, '$exists': True},
                        'image': {'$ne': None, '$exists': True},
                        'status': {'$in': ['completed', 'published']}
                    }
                    query = build_multi_tenant_query(base_query, customer_id=customer_id)
                    latest_article = self.news_collection.find_one(query, sort=[('created_at', -1)])

                    if not latest_article:
                        return jsonify({
                            "error": "No articles with audio found",
                            "status": "error"
                        }), 404

                    article_id = latest_article['id']
                else:
                    base_query = {'id': article_id}
                    query = build_multi_tenant_query(base_query, customer_id=customer_id)
                    latest_article = self.news_collection.find_one(query)

                    if not latest_article:
                        return jsonify({
                            "error": f"Article {article_id} not found",
                            "status": "error"
                        }), 404

                self.logger.info(f"📊 Testing Logo Watermark effect on article: {article_id}")

                # Temporarily override logo watermark settings if provided
                original_position = self.config.LOGO_POSITION
                original_opacity = self.config.LOGO_OPACITY
                original_scale = self.config.LOGO_SCALE
                original_margin = self.config.LOGO_MARGIN

                try:
                    self.config.LOGO_POSITION = logo_position
                    self.config.LOGO_OPACITY = float(logo_opacity)
                    self.config.LOGO_SCALE = float(logo_scale)
                    self.config.LOGO_MARGIN = int(logo_margin)

                    # Generate video with Logo Watermark effect
                    result = self.video_service.generate_video_for_article(latest_article)
                finally:
                    # Restore original settings
                    self.config.LOGO_POSITION = original_position
                    self.config.LOGO_OPACITY = original_opacity
                    self.config.LOGO_SCALE = original_scale
                    self.config.LOGO_MARGIN = original_margin

                if result['status'] == 'success':
                    # Prepare update with audit tracking
                    update_data = {
                        'video_path': result['video_path'],
                        'updated_at': datetime.utcnow()
                    }
                    prepare_update_document(update_data, user_id=user_id or 'system')

                    # Update database with multi-tenant filter
                    query = build_multi_tenant_query({'id': article_id}, customer_id=customer_id)
                    self.news_collection.update_one(query, {'$set': update_data})

                    return jsonify({
                        "message": "Logo Watermark effect test completed successfully",
                        "status": "success",
                        "article_id": article_id,
                        "video_path": result['video_path'],
                        "download_url": f"/download/{os.path.basename(result['video_path'])}",
                        "logo_watermark_config": {
                            "enabled": self.config.ENABLE_LOGO_WATERMARK,
                            "position": logo_position,
                            "opacity": float(logo_opacity),
                            "scale": float(logo_scale),
                            "margin": int(logo_margin),
                            "logo_path": self.config.LOGO_PATH
                        },
                        "ken_burns_config": {
                            "enabled": self.config.ENABLE_KEN_BURNS,
                            "zoom_start": self.config.KEN_BURNS_ZOOM_START,
                            "zoom_end": self.config.KEN_BURNS_ZOOM_END,
                            "easing": self.config.KEN_BURNS_EASING
                        },
                        "fade_text_config": {
                            "enabled": self.config.ENABLE_FADE_TEXT,
                            "fade_in_duration": self.config.FADE_TEXT_IN_DURATION,
                            "fade_out_duration": self.config.FADE_TEXT_OUT_DURATION,
                            "fade_type": self.config.FADE_TEXT_TYPE
                        }
                    })
                else:
                    return jsonify({
                        "error": result.get('error', 'Unknown error'),
                        "status": "error",
                        "article_id": article_id
                    }), 500

            except Exception as e:
                self.logger.error(f"❌ Error testing Logo Watermark effect: {str(e)}")
                return jsonify({
                    "error": f"Failed to test Logo Watermark effect: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/test-background-music', methods=['POST'])
        def test_background_music():
            """Test Background Music effect on a single video"""
            try:
                from flask import request

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')
                user_id = user_context.get('user_id')

                self.logger.info("🎵 Testing Background Music effect on a video")

                # Get parameters from request
                data = request.get_json() or {}
                article_id = data.get('article_id')

                # Optional: Override background music settings for this test
                music_volume = data.get('music_volume', self.config.BACKGROUND_MUSIC_VOLUME)
                voice_volume = data.get('voice_volume', self.config.VOICE_VOLUME)
                fade_in_duration = data.get('fade_in_duration', self.config.MUSIC_FADE_IN_DURATION)
                fade_out_duration = data.get('fade_out_duration', self.config.MUSIC_FADE_OUT_DURATION)

                # If no article_id provided, get the latest article with audio
                if not article_id:
                    base_query = {
                        'audio_paths': {'$ne': None, '$exists': True},
                        'image': {'$ne': None, '$exists': True},
                        'status': {'$in': ['completed', 'published']}
                    }
                    query = build_multi_tenant_query(base_query, customer_id=customer_id)
                    latest_article = self.news_collection.find_one(query, sort=[('created_at', -1)])

                    if not latest_article:
                        return jsonify({
                            "error": "No articles with audio found",
                            "status": "error"
                        }), 404

                    article_id = latest_article['id']
                else:
                    base_query = {'id': article_id}
                    query = build_multi_tenant_query(base_query, customer_id=customer_id)
                    latest_article = self.news_collection.find_one(query)

                    if not latest_article:
                        return jsonify({
                            "error": f"Article {article_id} not found",
                            "status": "error"
                        }), 404

                self.logger.info(f"📊 Testing Background Music effect on article: {article_id}")

                # Temporarily override background music settings if provided
                original_music_volume = self.config.BACKGROUND_MUSIC_VOLUME
                original_voice_volume = self.config.VOICE_VOLUME
                original_fade_in = self.config.MUSIC_FADE_IN_DURATION
                original_fade_out = self.config.MUSIC_FADE_OUT_DURATION
                original_enabled = self.config.ENABLE_BACKGROUND_MUSIC

                try:
                    # Force enable background music for this test
                    self.config.ENABLE_BACKGROUND_MUSIC = True
                    self.config.BACKGROUND_MUSIC_VOLUME = float(music_volume)
                    self.config.VOICE_VOLUME = float(voice_volume)
                    self.config.MUSIC_FADE_IN_DURATION = float(fade_in_duration)
                    self.config.MUSIC_FADE_OUT_DURATION = float(fade_out_duration)

                    # Generate video with Background Music effect
                    result = self.video_service.generate_video_for_article(latest_article)
                finally:
                    # Restore original settings
                    self.config.ENABLE_BACKGROUND_MUSIC = original_enabled
                    self.config.BACKGROUND_MUSIC_VOLUME = original_music_volume
                    self.config.VOICE_VOLUME = original_voice_volume
                    self.config.MUSIC_FADE_IN_DURATION = original_fade_in
                    self.config.MUSIC_FADE_OUT_DURATION = original_fade_out

                if result['status'] == 'success':
                    # Prepare update with audit tracking
                    update_data = {
                        'video_path': result['video_path'],
                        'updated_at': datetime.utcnow()
                    }
                    prepare_update_document(update_data, user_id=user_id or 'system')

                    # Update database with multi-tenant filter
                    query = build_multi_tenant_query({'id': article_id}, customer_id=customer_id)
                    self.news_collection.update_one(query, {'$set': update_data})

                    return jsonify({
                        "message": "Background Music effect test completed successfully",
                        "status": "success",
                        "article_id": article_id,
                        "video_path": result['video_path'],
                        "download_url": f"/download/{os.path.basename(result['video_path'])}",
                        "background_music_config": {
                            "enabled": True,
                            "music_volume": float(music_volume),
                            "voice_volume": float(voice_volume),
                            "fade_in_duration": float(fade_in_duration),
                            "fade_out_duration": float(fade_out_duration),
                            "music_path": self.config.BACKGROUND_MUSIC_PATH
                        },
                        "other_effects": {
                            "ken_burns": self.config.ENABLE_KEN_BURNS,
                            "fade_text": self.config.ENABLE_FADE_TEXT,
                            "logo_watermark": self.config.ENABLE_LOGO_WATERMARK
                        }
                    })
                else:
                    return jsonify({
                        "error": result.get('error', 'Unknown error'),
                        "status": "error",
                        "article_id": article_id
                    }), 500

            except Exception as e:
                self.logger.error(f"❌ Error testing Background Music effect: {str(e)}")
                return jsonify({
                    "error": f"Failed to test Background Music effect: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/test-transitions', methods=['POST'])
        def test_transitions():
            """Test smooth transitions by merging 2-3 videos with transitions"""
            try:
                from flask import request

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')

                self.logger.info("🎬 Testing Smooth Transitions effect")

                # Get parameters from request
                data = request.get_json() or {}
                transition_type = data.get('transition_type', self.config.TRANSITION_TYPE)
                transition_duration = data.get('transition_duration', self.config.TRANSITION_DURATION)
                video_count = data.get('video_count', 3)  # Default: merge 3 videos

                self.logger.info(f"📊 Testing {transition_type} transition with {video_count} videos")

                # Build query with multi-tenant filter
                base_query = {"video_path": {"$exists": True, "$ne": None}}
                query = build_multi_tenant_query(base_query, customer_id=customer_id)

                # Get latest videos
                latest_news = list(self.news_collection.find(
                    query,
                    {"id": 1, "title": 1, "video_path": 1, "created_at": 1}
                ).sort("created_at", -1).limit(video_count))

                if len(latest_news) < 2:
                    return jsonify({
                        "error": f"Need at least 2 videos to test transitions, found {len(latest_news)}",
                        "status": "error"
                    }), 400

                self.logger.info(f"📊 Found {len(latest_news)} videos for transition test")

                # Temporarily override transition settings
                original_transition_type = self.config.TRANSITION_TYPE
                original_transition_duration = self.config.TRANSITION_DURATION
                original_enable_transitions = self.config.ENABLE_TRANSITIONS

                self.config.TRANSITION_TYPE = transition_type
                self.config.TRANSITION_DURATION = transition_duration
                self.config.ENABLE_TRANSITIONS = True

                try:
                    # Merge videos with transitions
                    result = self.merge_service.merge_latest_videos(latest_news)

                    if result['status'] == 'success':
                        return jsonify({
                            "message": f"Transition test completed successfully with {transition_type}",
                            "status": "success",
                            "video_count": len(latest_news),
                            "merged_video_path": result['merged_video_path'],
                            "download_url": "/download/latest-20-news.mp4",
                            "transition_config": {
                                "enabled": True,
                                "type": transition_type,
                                "duration": transition_duration
                            },
                            "file_size_mb": result.get('file_size_mb', 0),
                            "total_duration": result.get('total_duration', 0)
                        })
                    else:
                        return jsonify({
                            "error": result.get('error', 'Unknown error'),
                            "status": "error"
                        }), 500

                finally:
                    # Restore original settings
                    self.config.TRANSITION_TYPE = original_transition_type
                    self.config.TRANSITION_DURATION = original_transition_duration
                    self.config.ENABLE_TRANSITIONS = original_enable_transitions

            except Exception as e:
                self.logger.error(f"❌ Error testing Transitions: {str(e)}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                return jsonify({
                    "error": f"Failed to test Transitions: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/generate-channel-tagline', methods=['POST'])
        def generate_channel_tagline():
            """Generate CNI News channel subscription tagline audio"""
            try:
                from flask import request
                import requests

                self.logger.info("🎤 Generating CNI News channel subscription tagline audio")

                # Get optional parameters from request
                data = request.get_json() or {}
                text = data.get('text', self.config.CHANNEL_TAGLINE_TEXT)
                model = data.get('model', self.config.CHANNEL_TAGLINE_MODEL)
                voice = data.get('voice', self.config.CHANNEL_TAGLINE_VOICE)
                filename = data.get('filename', self.config.CHANNEL_TAGLINE_FILENAME)

                # Ensure filename has .wav extension
                if not filename.endswith('.wav'):
                    filename += '.wav'

                self.logger.info(f"📝 Text: {text}")
                self.logger.info(f"🤖 Model: {model}")
                self.logger.info(f"🎭 Voice: {voice}")
                self.logger.info(f"📁 Filename: {filename}")

                # Prepare request to audio generation service
                audio_request = {
                    'text': text,
                    'model': model,
                    'voice': voice,
                    'filename': filename,
                    'format': 'wav'
                }

                # Call audio generation service
                audio_service_url = f"{self.config.AUDIO_GENERATION_SERVICE_URL}/tts"
                self.logger.info(f"🔗 Calling audio service: {audio_service_url}")

                response = requests.post(
                    audio_service_url,
                    json=audio_request,
                    timeout=self.config.AUDIO_GENERATION_TIMEOUT
                )

                if response.status_code != 200:
                    error_msg = f"Audio generation service returned status {response.status_code}"
                    self.logger.error(f"❌ {error_msg}")
                    return jsonify({
                        "error": error_msg,
                        "details": response.text,
                        "status": "error"
                    }), response.status_code

                audio_result = response.json()
                self.logger.info(f"✅ Audio generation successful: {audio_result}")

                # The audio file should be saved in the audio-generation service's output directory
                # We'll provide the download URL from the audio service
                return jsonify({
                    "message": "Channel subscription tagline audio generated successfully",
                    "status": "success",
                    "text": text,
                    "model": model,
                    "voice": voice,
                    "filename": filename,
                    "audio_url": audio_result.get('audio_url'),
                    "filepath": audio_result.get('filepath'),
                    "audio_info": audio_result.get('audio_info'),
                    "generation_time_ms": audio_result.get('generation_time_ms'),
                    "download_url": f"{self.config.AUDIO_GENERATION_SERVICE_URL}{audio_result.get('audio_url')}"
                })

            except requests.exceptions.Timeout:
                error_msg = "Audio generation service timeout"
                self.logger.error(f"❌ {error_msg}")
                return jsonify({
                    "error": error_msg,
                    "status": "error"
                }), 504

            except requests.exceptions.ConnectionError:
                error_msg = "Cannot connect to audio generation service"
                self.logger.error(f"❌ {error_msg}")
                return jsonify({
                    "error": error_msg,
                    "status": "error"
                }), 503

            except Exception as e:
                self.logger.error(f"❌ Error generating channel tagline: {str(e)}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                return jsonify({
                    "error": f"Failed to generate channel tagline: {str(e)}",
                    "status": "error"
                }), 500

        @self.app.route('/create-subscribe-video', methods=['POST'])
        def create_subscribe_video():
            """Create CNI News subscribe video with channel tagline audio"""
            try:
                from flask import request
                import requests
                from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip

                self.logger.info("🎬 Creating CNI News subscribe video")

                # Get optional parameters from request
                data = request.get_json() or {}

                # Step 1: Generate the audio first
                self.logger.info("🎤 Step 1: Generating channel tagline audio...")
                audio_request = {
                    'text': data.get('text', self.config.CHANNEL_TAGLINE_TEXT),
                    'model': data.get('model', self.config.CHANNEL_TAGLINE_MODEL),
                    'voice': data.get('voice', self.config.CHANNEL_TAGLINE_VOICE),
                    'filename': self.config.CHANNEL_TAGLINE_FILENAME,
                    'format': 'wav'
                }

                audio_service_url = f"{self.config.AUDIO_GENERATION_SERVICE_URL}/tts"
                audio_response = requests.post(
                    audio_service_url,
                    json=audio_request,
                    timeout=self.config.AUDIO_GENERATION_TIMEOUT
                )

                if audio_response.status_code != 200:
                    error_msg = f"Audio generation failed with status {audio_response.status_code}"
                    self.logger.error(f"❌ {error_msg}")
                    return jsonify({
                        "error": error_msg,
                        "details": audio_response.text,
                        "status": "error"
                    }), audio_response.status_code

                audio_result = audio_response.json()
                audio_url = audio_result.get('audio_url')
                self.logger.info(f"✅ Audio generated: {audio_url}")

                # Step 2: Download the audio file from audio-generation service
                self.logger.info("📥 Step 2: Downloading audio file...")
                audio_download_url = f"{self.config.AUDIO_GENERATION_SERVICE_URL}{audio_url}"
                audio_download_response = requests.get(audio_download_url, timeout=30)

                if audio_download_response.status_code != 200:
                    error_msg = f"Failed to download audio file: {audio_download_response.status_code}"
                    self.logger.error(f"❌ {error_msg}")
                    return jsonify({
                        "error": error_msg,
                        "status": "error"
                    }), 500

                # Save audio file locally
                local_audio_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, self.config.CHANNEL_TAGLINE_FILENAME)
                with open(local_audio_path, 'wb') as f:
                    f.write(audio_download_response.content)
                self.logger.info(f"✅ Audio downloaded to: {local_audio_path}")

                # Step 3: Use existing subscribe video and replace audio
                self.logger.info("🎬 Step 3: Creating subscribe video with new audio...")

                # Path to the existing subscribe video template
                source_video_path = '/app/subscribe/CNINews_Subscribe.mp4'

                if not os.path.exists(source_video_path):
                    error_msg = f"Source subscribe video not found at {source_video_path}"
                    self.logger.error(f"❌ {error_msg}")
                    return jsonify({
                        "error": error_msg,
                        "status": "error"
                    }), 500

                # Load the existing video and new audio
                from moviepy.editor import VideoFileClip

                video_clip = VideoFileClip(source_video_path)
                audio_clip = AudioFileClip(local_audio_path)

                # Get audio duration
                video_duration = audio_clip.duration

                # Adjust video duration to match audio duration
                # If audio is longer, loop the video; if shorter, trim the video
                if video_clip.duration < video_duration:
                    # Loop the video to match audio duration
                    video_clip = video_clip.loop(duration=video_duration)
                else:
                    # Trim the video to match audio duration
                    video_clip = video_clip.subclip(0, video_duration)

                # Replace the audio
                final_video = video_clip.set_audio(audio_clip)

                # Output path
                output_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'CNINews_Subscribe.mp4')

                # Write video file
                self.logger.info(f"💾 Writing video to: {output_path}")
                final_video.write_videofile(
                    output_path,
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    preset='medium',
                    ffmpeg_params=['-pix_fmt', 'yuv420p']
                )

                # Clean up
                audio_clip.close()
                video_clip.close()
                final_video.close()

                self.logger.info(f"✅ Subscribe video created successfully: {output_path}")

                return jsonify({
                    "message": "Subscribe video created successfully",
                    "status": "success",
                    "video_path": "/public/CNINews_Subscribe.mp4",
                    "audio_path": local_audio_path,
                    "duration_seconds": round(video_duration, 2),
                    "download_url": "/download/CNINews_Subscribe.mp4"
                })

            except requests.exceptions.Timeout:
                error_msg = "Audio generation service timeout"
                self.logger.error(f"❌ {error_msg}")
                return jsonify({
                    "error": error_msg,
                    "status": "error"
                }), 504

            except requests.exceptions.ConnectionError:
                error_msg = "Cannot connect to audio generation service"
                self.logger.error(f"❌ {error_msg}")
                return jsonify({
                    "error": error_msg,
                    "status": "error"
                }), 503

            except Exception as e:
                self.logger.error(f"❌ Error creating subscribe video: {str(e)}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                return jsonify({
                    "error": f"Failed to create subscribe video: {str(e)}",
                    "status": "error"
                }), 500

        # Background Audio Library Management Endpoints

        @self.app.route('/background-audio', methods=['GET'])
        def list_background_audio():
            """List all available background audio files for the customer"""
            try:
                import os
                from common.utils.multi_tenant_db import extract_user_context_from_headers

                # Extract customer_id from headers for multi-tenant isolation
                context = extract_user_context_from_headers(request.headers)
                customer_id = context['customer_id']
                user_id = context.get('user_id')

                assets_dir = os.path.join(os.path.dirname(__file__), 'assets')

                # Customer-specific directory
                customer_assets_dir = os.path.join(assets_dir, customer_id)

                # Create customer assets directory if it doesn't exist
                if not os.path.exists(customer_assets_dir):
                    os.makedirs(customer_assets_dir)
                    self.logger.info(f"📁 Created customer assets directory: {customer_assets_dir}")
                    return jsonify({
                        'status': 'success',
                        'count': 0,
                        'audio_files': [],
                        'customer_id': customer_id
                    }), 200

                # List all audio files in customer's assets directory
                audio_extensions = ['.wav', '.mp3', '.m4a', '.aac', '.ogg']
                audio_files = []

                for filename in os.listdir(customer_assets_dir):
                    file_path = os.path.join(customer_assets_dir, filename)
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in audio_extensions:
                            file_stats = os.stat(file_path)
                            audio_files.append({
                                'id': filename,
                                'name': filename,
                                'size': file_stats.st_size,
                                'size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                                'created_at': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                                'modified_at': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                                'extension': ext
                            })

                # Sort by name
                audio_files.sort(key=lambda x: x['name'])

                self.logger.info(f"📋 Found {len(audio_files)} background audio files for customer: {customer_id}")

                return jsonify({
                    'status': 'success',
                    'count': len(audio_files),
                    'audio_files': audio_files,
                    'customer_id': customer_id
                }), 200

            except Exception as e:
                self.logger.error(f"💥 Error listing background audio: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        @self.app.route('/background-audio', methods=['POST'])
        def upload_background_audio():
            """Upload a new background audio file for the customer"""
            try:
                from werkzeug.utils import secure_filename
                import os
                from common.utils.multi_tenant_db import extract_user_context_from_headers

                # Extract customer_id from headers for multi-tenant isolation
                context = extract_user_context_from_headers(request.headers)
                customer_id = context['customer_id']
                user_id = context.get('user_id')

                self.logger.info(f"📤 Upload request for customer: {customer_id}, user: {user_id}")
                self.logger.info(f"📤 Request headers: X-Customer-ID={request.headers.get('X-Customer-ID')}, X-User-ID={request.headers.get('X-User-ID')}")

                # Check if file is in request
                if 'file' not in request.files:
                    return jsonify({
                        'status': 'error',
                        'error': 'No file provided'
                    }), 400

                file = request.files['file']

                self.logger.info(f"📤 Received file: filename='{file.filename}', content_type='{file.content_type}'")

                if file.filename == '':
                    return jsonify({
                        'status': 'error',
                        'error': 'No file selected'
                    }), 400

                # Validate file extension
                audio_extensions = ['.wav', '.mp3', '.m4a', '.aac', '.ogg']
                filename = secure_filename(file.filename)
                ext = os.path.splitext(filename)[1].lower()

                self.logger.info(f"📤 Parsed filename: '{filename}', extension: '{ext}'")

                if ext not in audio_extensions:
                    return jsonify({
                        'status': 'error',
                        'error': f'Invalid file type. Allowed: {", ".join(audio_extensions)}'
                    }), 400

                # Create customer-specific assets directory
                assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
                customer_assets_dir = os.path.join(assets_dir, customer_id)

                if not os.path.exists(customer_assets_dir):
                    os.makedirs(customer_assets_dir)
                    self.logger.info(f"📁 Created customer assets directory: {customer_assets_dir}")

                # Save file to customer's directory
                file_path = os.path.join(customer_assets_dir, filename)

                self.logger.info(f"📁 Customer assets directory: {customer_assets_dir}")
                self.logger.info(f"📁 Target file path: {file_path}")
                self.logger.info(f"📁 File exists check: {os.path.exists(file_path)}")

                # Check if file already exists
                if os.path.exists(file_path):
                    return jsonify({
                        'status': 'error',
                        'error': f'File "{filename}" already exists. Please rename or delete the existing file first.'
                    }), 409

                file.save(file_path)

                # Get file stats
                file_stats = os.stat(file_path)

                self.logger.info(f"✅ Uploaded background audio for customer {customer_id}: {filename} ({file_stats.st_size} bytes)")

                return jsonify({
                    'status': 'success',
                    'message': f'Background audio "{filename}" uploaded successfully',
                    'audio_file': {
                        'id': filename,
                        'name': filename,
                        'size': file_stats.st_size,
                        'size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                        'extension': ext
                    },
                    'customer_id': customer_id
                }), 201

            except Exception as e:
                self.logger.error(f"💥 Error uploading background audio: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        @self.app.route('/background-audio/<audio_id>', methods=['DELETE'])
        def delete_background_audio(audio_id):
            """Delete a background audio file for the customer"""
            try:
                from werkzeug.utils import secure_filename
                import os
                from common.utils.multi_tenant_db import extract_user_context_from_headers

                # Extract customer_id from headers for multi-tenant isolation
                context = extract_user_context_from_headers(request.headers)
                customer_id = context['customer_id']
                user_id = context.get('user_id')

                # Secure the filename
                filename = secure_filename(audio_id)
                assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
                customer_assets_dir = os.path.join(assets_dir, customer_id)
                file_path = os.path.join(customer_assets_dir, filename)

                # Check if file exists
                if not os.path.exists(file_path):
                    return jsonify({
                        'status': 'error',
                        'error': f'Background audio "{filename}" not found for customer {customer_id}'
                    }), 404

                # Delete file
                os.remove(file_path)

                self.logger.info(f"🗑️  Deleted background audio for customer {customer_id}: {filename}")

                return jsonify({
                    'status': 'success',
                    'message': f'Background audio "{filename}" deleted successfully',
                    'customer_id': customer_id
                }), 200

            except Exception as e:
                self.logger.error(f"💥 Error deleting background audio: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        @self.app.route('/background-audio/<audio_id>/download', methods=['GET'])
        def download_background_audio(audio_id):
            """Download a background audio file for the customer"""
            try:
                from werkzeug.utils import secure_filename
                import os
                from common.utils.multi_tenant_db import extract_user_context_from_headers

                # Extract customer_id from headers for multi-tenant isolation
                context = extract_user_context_from_headers(request.headers)
                customer_id = context['customer_id']
                user_id = context.get('user_id')

                # Secure the filename
                filename = secure_filename(audio_id)
                assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
                customer_assets_dir = os.path.join(assets_dir, customer_id)
                file_path = os.path.join(customer_assets_dir, filename)

                # Check if file exists
                if not os.path.exists(file_path):
                    return jsonify({
                        'status': 'error',
                        'error': f'Background audio "{filename}" not found for customer {customer_id}'
                    }), 404

                self.logger.info(f"📥 Downloading background audio for customer {customer_id}: {filename}")

                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=filename
                )

            except Exception as e:
                self.logger.error(f"💥 Error downloading background audio: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        # Video Configuration CRUD Endpoints

        @self.app.route('/configs', methods=['POST'])
        def create_config():
            """Create a new video configuration"""
            try:
                from flask import request
                from datetime import datetime, timedelta

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')
                user_id = user_context.get('user_id')

                config_data = request.get_json()

                # Validate required fields
                if not config_data.get('title'):
                    return jsonify({
                        'status': 'error',
                        'error': 'Title is required'
                    }), 400

                if not config_data.get('videoCount'):
                    return jsonify({
                        'status': 'error',
                        'error': 'Video count is required'
                    }), 400

                # Prepare document
                now = datetime.utcnow()
                frequency = config_data.get('frequency', 'none')

                # Calculate next run time
                next_run_time = None
                if frequency != 'none':
                    if frequency == 'hourly':
                        next_run_time = now + timedelta(hours=1)
                    elif frequency == 'daily':
                        next_run_time = now + timedelta(days=1)
                    elif frequency == 'weekly':
                        next_run_time = now + timedelta(weeks=1)
                    elif frequency == 'monthly':
                        next_run_time = now + timedelta(days=30)

                document = {
                    'title': config_data.get('title'),
                    'categories': config_data.get('categories', []),
                    'country': config_data.get('country', ''),
                    'language': config_data.get('language', ''),
                    'videoCount': config_data.get('videoCount', 20),
                    'frequency': frequency,
                    'status': 'unknown',  # Start with 'unknown' status
                    'videoPath': None,
                    'thumbnailPath': None,
                    'youtubeVideoId': None,
                    'youtubeVideoUrl': None,
                    'backgroundAudioId': config_data.get('backgroundAudioId', None),  # Custom background audio selection
                    'createdAt': now,
                    'updatedAt': now,
                    'lastRunTime': None,
                    'nextRunTime': next_run_time,
                    'mergeStartedAt': None,
                    'mergeCompletedAt': None,
                    'uploadedAt': None,
                    'error': None,
                    'runCount': 0
                }

                # Add multi-tenant fields (customer_id, created_by, updated_by, timestamps)
                prepare_insert_document(document, customer_id=customer_id, user_id=user_id)

                # Insert into database
                configs_collection = self.news_db['long_video_configs']
                result = configs_collection.insert_one(document)

                # Convert ObjectId to string
                document['_id'] = str(result.inserted_id)
                document['createdAt'] = document['createdAt'].isoformat()
                document['updatedAt'] = document['updatedAt'].isoformat()
                if document.get('nextRunTime'):
                    document['nextRunTime'] = document['nextRunTime'].isoformat()

                self.logger.info(f"✅ Created video configuration: {document['title']}")

                return jsonify({
                    'status': 'success',
                    '_id': document['_id'],
                    'config': document
                }), 201

            except Exception as e:
                self.logger.error(f"💥 Error creating config: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        @self.app.route('/configs', methods=['GET'])
        def get_configs():
            """Get all video configurations"""
            try:
                from flask import request

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')

                # Get query parameters
                status = request.args.get('status')
                limit = int(request.args.get('limit', 50))

                # Build query with multi-tenant filter
                base_query = {}
                if status:
                    base_query['status'] = status

                query = build_multi_tenant_query(base_query, customer_id=customer_id)

                # Get configs
                configs_collection = self.news_db['long_video_configs']
                configs = list(configs_collection.find(query).sort('createdAt', -1).limit(limit))

                # Convert ObjectId and datetime to strings
                for config in configs:
                    config['_id'] = str(config['_id'])
                    if config.get('createdAt'):
                        config['createdAt'] = config['createdAt'].isoformat()
                    if config.get('updatedAt'):
                        config['updatedAt'] = config['updatedAt'].isoformat()
                    if config.get('lastRunTime'):
                        config['lastRunTime'] = config['lastRunTime'].isoformat()
                    if config.get('nextRunTime'):
                        config['nextRunTime'] = config['nextRunTime'].isoformat()
                    if config.get('mergeStartedAt'):
                        config['mergeStartedAt'] = config['mergeStartedAt'].isoformat()
                    if config.get('mergeCompletedAt'):
                        config['mergeCompletedAt'] = config['mergeCompletedAt'].isoformat()
                    if config.get('uploadedAt'):
                        config['uploadedAt'] = config['uploadedAt'].isoformat()

                return jsonify({
                    'status': 'success',
                    'count': len(configs),
                    'configs': configs
                }), 200

            except Exception as e:
                self.logger.error(f"💥 Error getting configs: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        @self.app.route('/configs/<config_id>', methods=['GET'])
        def get_config(config_id):
            """Get a specific video configuration"""
            try:
                from bson import ObjectId

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')

                configs_collection = self.news_db['long_video_configs']

                # Build query with customer_id filter
                base_query = {'_id': ObjectId(config_id)}
                query = build_multi_tenant_query(base_query, customer_id=customer_id)

                config = configs_collection.find_one(query)

                if not config:
                    return jsonify({
                        'status': 'error',
                        'error': f'Configuration not found: {config_id}'
                    }), 404

                # Convert ObjectId and datetime to strings
                config['_id'] = str(config['_id'])
                if config.get('createdAt'):
                    config['createdAt'] = config['createdAt'].isoformat()
                if config.get('updatedAt'):
                    config['updatedAt'] = config['updatedAt'].isoformat()
                if config.get('lastRunTime'):
                    config['lastRunTime'] = config['lastRunTime'].isoformat()
                if config.get('nextRunTime'):
                    config['nextRunTime'] = config['nextRunTime'].isoformat()
                if config.get('mergeStartedAt'):
                    config['mergeStartedAt'] = config['mergeStartedAt'].isoformat()
                if config.get('mergeCompletedAt'):
                    config['mergeCompletedAt'] = config['mergeCompletedAt'].isoformat()
                if config.get('uploadedAt'):
                    config['uploadedAt'] = config['uploadedAt'].isoformat()

                return jsonify({
                    'status': 'success',
                    'config': config
                }), 200

            except Exception as e:
                self.logger.error(f"💥 Error getting config: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        @self.app.route('/configs/<config_id>', methods=['PUT'])
        def update_config(config_id):
            """Update a video configuration"""
            try:
                from flask import request
                from bson import ObjectId
                from datetime import datetime

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')
                user_id = user_context.get('user_id')

                update_data = request.get_json()

                # Use prepare_update_document to add updated_by and updated_at
                prepared_updates = prepare_update_document(update_data, user_id=user_id)

                configs_collection = self.news_db['long_video_configs']

                # Build query with customer_id filter
                base_query = {'_id': ObjectId(config_id)}
                query = build_multi_tenant_query(base_query, customer_id=customer_id)

                result = configs_collection.find_one_and_update(
                    query,
                    {'$set': prepared_updates},
                    return_document=True
                )

                if not result:
                    return jsonify({
                        'status': 'error',
                        'error': f'Configuration not found: {config_id}'
                    }), 404

                # Convert ObjectId and datetime to strings
                result['_id'] = str(result['_id'])
                if result.get('createdAt'):
                    result['createdAt'] = result['createdAt'].isoformat()
                if result.get('updatedAt'):
                    result['updatedAt'] = result['updatedAt'].isoformat()
                if result.get('lastRunTime'):
                    result['lastRunTime'] = result['lastRunTime'].isoformat()
                if result.get('nextRunTime'):
                    result['nextRunTime'] = result['nextRunTime'].isoformat()
                if result.get('mergeStartedAt'):
                    result['mergeStartedAt'] = result['mergeStartedAt'].isoformat()
                if result.get('mergeCompletedAt'):
                    result['mergeCompletedAt'] = result['mergeCompletedAt'].isoformat()
                if result.get('uploadedAt'):
                    result['uploadedAt'] = result['uploadedAt'].isoformat()

                self.logger.info(f"✏️ Updated video configuration: {config_id}")

                return jsonify({
                    'status': 'success',
                    'config': result
                }), 200

            except Exception as e:
                self.logger.error(f"💥 Error updating config: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        @self.app.route('/configs/<config_id>', methods=['DELETE'])
        def delete_config(config_id):
            """Delete a video configuration"""
            try:
                from bson import ObjectId

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')

                configs_collection = self.news_db['long_video_configs']

                # Build query with customer_id filter
                base_query = {'_id': ObjectId(config_id)}
                query = build_multi_tenant_query(base_query, customer_id=customer_id)

                result = configs_collection.delete_one(query)

                if result.deleted_count == 0:
                    return jsonify({
                        'status': 'error',
                        'error': f'Configuration not found: {config_id}'
                    }), 404

                self.logger.info(f"🗑️ Deleted video configuration: {config_id}")

                return jsonify({
                    'status': 'success',
                    'message': 'Configuration deleted successfully',
                    'deleted': True,
                    'config_id': config_id
                }), 200

            except Exception as e:
                self.logger.error(f"💥 Error deleting config: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        # Define specific routes BEFORE generic routes to avoid conflicts
        @self.app.route('/configs/due', methods=['GET'])
        def get_due_configs():
            """Get configurations that are due for processing"""
            try:
                from datetime import datetime

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')

                now = datetime.utcnow()
                configs_collection = self.news_db['long_video_configs']

                # Build query with multi-tenant filter
                base_query = {
                    'status': 'completed',
                    'frequency': {'$ne': 'none'},
                    'nextRunTime': {'$lte': now}
                }
                query = build_multi_tenant_query(base_query, customer_id=customer_id)

                due_configs = list(configs_collection.find(query).sort('nextRunTime', 1))

                # Convert ObjectId and datetime to strings
                for config in due_configs:
                    config['_id'] = str(config['_id'])
                    if config.get('createdAt'):
                        config['createdAt'] = config['createdAt'].isoformat()
                    if config.get('updatedAt'):
                        config['updatedAt'] = config['updatedAt'].isoformat()
                    if config.get('lastRunTime'):
                        config['lastRunTime'] = config['lastRunTime'].isoformat()
                    if config.get('nextRunTime'):
                        config['nextRunTime'] = config['nextRunTime'].isoformat()
                    if config.get('mergeStartedAt'):
                        config['mergeStartedAt'] = config['mergeStartedAt'].isoformat()
                    if config.get('mergeCompletedAt'):
                        config['mergeCompletedAt'] = config['mergeCompletedAt'].isoformat()
                    if config.get('uploadedAt'):
                        config['uploadedAt'] = config['uploadedAt'].isoformat()

                self.logger.info(f"📅 Found {len(due_configs)} configurations due for processing")

                return jsonify({
                    'status': 'success',
                    'count': len(due_configs),
                    'configs': due_configs
                }), 200

            except Exception as e:
                self.logger.error(f"💥 Error getting due configs: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        @self.app.route('/configs/<config_id>/merge', methods=['POST'])
        def merge_config(config_id):
            """Trigger video merge for a specific configuration - uses existing /merge-latest endpoint"""
            try:
                from bson import ObjectId
                from datetime import datetime, timedelta
                from flask import request

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')
                user_id = user_context.get('user_id')

                configs_collection = self.news_db['long_video_configs']

                # Build query with customer_id filter
                base_query = {'_id': ObjectId(config_id)}
                query = build_multi_tenant_query(base_query, customer_id=customer_id)

                config = configs_collection.find_one(query)

                if not config:
                    return jsonify({
                        'status': 'error',
                        'error': f'Configuration not found: {config_id}'
                    }), 404

                # Get optional article_ids from request body (for manual selection)
                request_data = request.get_json() or {}
                article_ids = request_data.get('article_ids', [])

                if article_ids:
                    self.logger.info(f"🎯 Manual selection mode: {len(article_ids)} articles selected for config {config_id}")
                else:
                    self.logger.info(f"🤖 Automatic selection mode for config {config_id}")

                # Calculate next run time
                now = datetime.utcnow()
                frequency = config.get('frequency', 'none')
                next_run_time = None
                if frequency != 'none':
                    if frequency == 'hourly':
                        next_run_time = now + timedelta(hours=1)
                    elif frequency == 'daily':
                        next_run_time = now + timedelta(days=1)
                    elif frequency == 'weekly':
                        next_run_time = now + timedelta(weeks=1)
                    elif frequency == 'monthly':
                        next_run_time = now + timedelta(days=30)

                # Update status to processing
                run_count = config.get('runCount', 0) + 1
                update_data = {
                    'status': 'processing',
                    'mergeStartedAt': now,
                    'lastRunTime': now,
                    'nextRunTime': next_run_time,
                    'runCount': run_count,
                    'updatedAt': now
                }
                prepare_update_document(update_data, user_id=user_id or 'system')

                # Use multi-tenant query for update
                configs_collection.update_one(
                    query,
                    {'$set': update_data}
                )

                # Prepare merge config - reuse existing /merge-latest endpoint logic
                merge_config_data = {
                    'categories': config.get('categories', []),
                    'country': config.get('country', ''),
                    'language': config.get('language', ''),
                    'videoCount': config.get('videoCount', 20),
                    'title': config.get('title', ''),
                    'config_id': config_id  # Pass config_id to update after merge
                }

                # Add article_ids if provided (manual selection)
                if article_ids:
                    merge_config_data['article_ids'] = article_ids

                self.logger.info(f"🎬 Triggering merge for config: {config.get('title')} (ID: {config_id})")

                # Call the existing merge_latest_videos function internally
                # We'll make an internal call to reuse the logic
                # Store the original request headers to pass them through
                original_headers = dict(request.headers)

                with self.app.test_request_context(
                    '/merge-latest',
                    method='POST',
                    json=merge_config_data,
                    headers=original_headers
                ):
                    response = merge_latest_videos()

                    # If it's a tuple (response, status_code), extract them
                    if isinstance(response, tuple):
                        response_data = response[0].get_json()
                        status_code = response[1]
                    else:
                        response_data = response.get_json()
                        status_code = 200

                    # Update config based on response
                    if response_data.get('status') == 'error':
                        update_data = {
                            'status': 'failed',
                            'error': response_data.get('error', 'Unknown error'),
                            'updatedAt': datetime.utcnow()
                        }
                        prepare_update_document(update_data, user_id=user_id or 'system')

                        # Use multi-tenant query for update
                        configs_collection.update_one(
                            query,
                            {'$set': update_data}
                        )

                    return jsonify(response_data), status_code

            except Exception as e:
                self.logger.error(f"💥 Error merging config: {str(e)}")

                # Update config status to failed
                try:
                    from bson import ObjectId
                    from datetime import datetime
                    configs_collection = self.news_db['long_video_configs']

                    update_data = {
                        'status': 'failed',
                        'error': str(e),
                        'updatedAt': datetime.utcnow()
                    }
                    prepare_update_document(update_data, user_id=user_id or 'system')

                    # Use multi-tenant query for update
                    configs_collection.update_one(
                        query,
                        {'$set': update_data}
                    )
                except:
                    pass

                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500

        @self.app.route('/configs/<config_id>/merge-status', methods=['GET'])
        def get_config_merge_status(config_id):
            """Check the merge status for a specific configuration"""
            try:
                from bson import ObjectId
                import os

                # Extract user context from headers for multi-tenancy
                user_context = extract_user_context_from_headers(request.headers)
                customer_id = user_context.get('customer_id')

                configs_collection = self.news_db['long_video_configs']

                # Build query with multi-tenant filter
                base_query = {'_id': ObjectId(config_id)}
                query = build_multi_tenant_query(base_query, customer_id=customer_id)
                config = configs_collection.find_one(query)

                if not config:
                    return jsonify({
                        'status': 'error',
                        'error': f'Configuration not found: {config_id}'
                    }), 404

                # Check if video file exists
                video_path = config.get('videoPath')
                video_exists = False
                file_size_mb = 0
                last_updated = None

                if video_path:
                    # Convert public path to filesystem path
                    if video_path.startswith('/public/'):
                        fs_path = os.path.join(
                            self.config.VIDEO_OUTPUT_DIR,
                            video_path.replace('/public/', '')
                        )
                        if os.path.exists(fs_path):
                            video_exists = True
                            file_stats = os.stat(fs_path)
                            file_size_mb = round(file_stats.st_size / (1024 * 1024), 2)
                            last_updated = time.ctime(file_stats.st_mtime)

                response = {
                    'config_id': config_id,
                    'status': config.get('status', 'unknown'),
                    'title': config.get('title', ''),
                    'video_path': video_path,
                    'thumbnail_path': config.get('thumbnailPath'),
                    'video_exists': video_exists,
                    'file_size_mb': file_size_mb if video_exists else None,
                    'last_updated': last_updated,
                    'merge_started_at': config.get('mergeStartedAt'),
                    'merge_completed_at': config.get('mergeCompletedAt'),
                    'error': config.get('error'),
                    'run_count': config.get('runCount', 0),
                    'next_run_time': config.get('nextRunTime')
                }

                return jsonify(response)

            except Exception as e:
                self.logger.error(f"❌ Error checking config merge status: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500


if __name__ == '__main__':
    # Create and run the job service
    job = VideoGeneratorJob()

    # Start the Flask application with job scheduling
    job.run_flask_app()
