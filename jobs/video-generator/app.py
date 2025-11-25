"""
Video Generation Job Service - Main Application
"""

import os
import sys
import time
from datetime import datetime

# Add common directory to path for job framework
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from flask import send_file, jsonify, request
from common.models.base_job import BaseJob
from common.utils.logger import setup_logger
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

                self.news_collection.update_one(
                    {'id': article_id},
                    {'$set': update_data}
                )
                self.logger.info(f"✅ Database updated with video_path for article: {article_id}")

                # Also generate YouTube Short
                try:
                    self.logger.info(f"🎬 Generating YouTube Short for article: {article_id}")

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

                            self.news_collection.update_one(
                                {'id': article_id},
                                {'$set': {
                                    'shorts_video_path': relative_shorts_path,
                                    'updated_at': datetime.utcnow()
                                }}
                            )

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

    def _get_articles_for_video_generation(self) -> list:
        """
        Get articles that have audio and cleaned image but no video generated yet

        Returns:
            List of article documents that need video generation
        """
        try:
            # Query for articles that have audio_paths, clean_image, but no video_path
            query = {
                'audio_paths': {'$ne': None, '$exists': True},  # Has audio paths
                'clean_image': {'$ne': None, '$exists': True},  # Has cleaned image
                'video_path': {'$in': [None, '']},  # No video yet
                'status': {'$in': ['completed', 'published']}  # Only process completed articles
            }

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
                        # Update the document
                        self.logger.info(f"🔍 DEBUG: Executing MongoDB update for article: {article_id}")
                        update_result = self.news_collection.update_one(
                            {'id': article_id},
                            {'$set': update_data}
                        )

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
            """Merge latest 20 news videos into a single video"""
            try:
                self.logger.info("🎬 Starting merge of latest 20 news videos")

                # Get latest news with videos
                latest_news = list(self.news_collection.find(
                    {"video_path": {"$exists": True, "$ne": None}},
                    {"id": 1, "title": 1, "video_path": 1, "created_at": 1}
                ).sort("created_at", -1).limit(20))

                if not latest_news:
                    return jsonify({
                        "error": "No news videos found",
                        "status": "error"
                    }), 404

                self.logger.info(f"📊 Found {len(latest_news)} news videos to merge")

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

                        # Merge videos
                        result = self.merge_service.merge_latest_videos(latest_news)

                        end_time = time.time()
                        processing_time = round(end_time - start_time, 2)

                        if result['status'] == 'success':
                            self.logger.info(
                                f"✅ Video merge completed successfully in {processing_time} seconds - merged {result['video_count']} videos")
                        else:
                            self.logger.error(f"❌ Video merge failed: {result['error']}")

                    except Exception as e:
                        self.logger.error(f"❌ Error in async video merge: {str(e)}")

                # Start async processing
                thread = Thread(target=merge_videos_async)
                thread.daemon = True
                thread.start()

                return jsonify({
                    "message": f"Video merging started for {len(latest_news)} videos. This process may take 2-5 minutes depending on video length and quality.",
                    "status": "processing",
                    "video_count": len(latest_news),
                    "estimated_time": "2-5 minutes",
                    "download_url": "/download/latest-20-news.mp4",
                    "note": "Please wait for processing to complete before downloading. Check server logs for progress updates."
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

        @self.app.route('/generate-short', methods=['POST'])
        def generate_short():
            """Generate YouTube Short for a news article"""
            try:
                data = request.get_json() or {}
                article_id = data.get('article_id')

                if not article_id:
                    return jsonify({
                        "error": "article_id is required",
                        "status": "error"
                    }), 400

                self.logger.info(f"🎬 Generating YouTube Short for article: {article_id}")

                # Get article from database
                article = self.news_collection.find_one({'id': article_id})

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

                    self.news_collection.update_one(
                        {'id': article_id},
                        {'$set': {
                            'shorts_video_path': relative_shorts_path,
                            'updated_at': datetime.utcnow()
                        }}
                    )

                    self.logger.info(f"✅ Short generated and saved: {shorts_path}")

                    return jsonify({
                        "message": "YouTube Short generated successfully",
                        "status": "success",
                        "article_id": article_id,
                        "short_path": relative_shorts_path,
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

                self.logger.info("🎬 Testing Ken Burns effect on a video")

                # Get parameters from request
                data = request.get_json() or {}
                article_id = data.get('article_id')

                # If no article_id provided, get the latest article with audio
                if not article_id:
                    latest_article = self.news_collection.find_one(
                        {
                            'audio_paths': {'$ne': None, '$exists': True},
                            'image': {'$ne': None, '$exists': True},
                            'status': {'$in': ['completed', 'published']}
                        },
                        sort=[('created_at', -1)]
                    )

                    if not latest_article:
                        return jsonify({
                            "error": "No articles with audio found",
                            "status": "error"
                        }), 404

                    article_id = latest_article['id']
                else:
                    latest_article = self.news_collection.find_one({'id': article_id})

                    if not latest_article:
                        return jsonify({
                            "error": f"Article {article_id} not found",
                            "status": "error"
                        }), 404

                self.logger.info(f"📊 Testing Ken Burns effect on article: {article_id}")

                # Generate video with Ken Burns effect
                result = self.video_service.generate_video_for_article(latest_article)

                if result['status'] == 'success':
                    # Update database with video path
                    self.news_collection.update_one(
                        {'id': article_id},
                        {'$set': {
                            'video_path': result['video_path'],
                            'updated_at': datetime.utcnow()
                        }}
                    )

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
                    latest_article = self.news_collection.find_one(
                        {
                            'audio_paths': {'$ne': None, '$exists': True},
                            'image': {'$ne': None, '$exists': True},
                            'status': {'$in': ['completed', 'published']}
                        },
                        sort=[('created_at', -1)]
                    )

                    if not latest_article:
                        return jsonify({
                            "error": "No articles with audio found",
                            "status": "error"
                        }), 404

                    article_id = latest_article['id']
                else:
                    latest_article = self.news_collection.find_one({'id': article_id})

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
                    # Update database with video path
                    self.news_collection.update_one(
                        {'id': article_id},
                        {'$set': {
                            'video_path': result['video_path'],
                            'updated_at': datetime.utcnow()
                        }}
                    )

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
                    latest_article = self.news_collection.find_one(
                        {
                            'audio_paths': {'$ne': None, '$exists': True},
                            'image': {'$ne': None, '$exists': True},
                            'status': {'$in': ['completed', 'published']}
                        },
                        sort=[('created_at', -1)]
                    )

                    if not latest_article:
                        return jsonify({
                            "error": "No articles with audio found",
                            "status": "error"
                        }), 404

                    article_id = latest_article['id']
                else:
                    latest_article = self.news_collection.find_one({'id': article_id})

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
                    # Update database with video path
                    self.news_collection.update_one(
                        {'id': article_id},
                        {'$set': {
                            'video_path': result['video_path'],
                            'updated_at': datetime.utcnow()
                        }}
                    )

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
                    latest_article = self.news_collection.find_one(
                        {
                            'audio_paths': {'$ne': None, '$exists': True},
                            'image': {'$ne': None, '$exists': True},
                            'status': {'$in': ['completed', 'published']}
                        },
                        sort=[('created_at', -1)]
                    )

                    if not latest_article:
                        return jsonify({
                            "error": "No articles with audio found",
                            "status": "error"
                        }), 404

                    article_id = latest_article['id']
                else:
                    latest_article = self.news_collection.find_one({'id': article_id})

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
                    # Update database with video path
                    self.news_collection.update_one(
                        {'id': article_id},
                        {'$set': {
                            'video_path': result['video_path'],
                            'updated_at': datetime.utcnow()
                        }}
                    )

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

                self.logger.info("🎬 Testing Smooth Transitions effect")

                # Get parameters from request
                data = request.get_json() or {}
                transition_type = data.get('transition_type', self.config.TRANSITION_TYPE)
                transition_duration = data.get('transition_duration', self.config.TRANSITION_DURATION)
                video_count = data.get('video_count', 3)  # Default: merge 3 videos

                self.logger.info(f"📊 Testing {transition_type} transition with {video_count} videos")

                # Get latest videos
                latest_news = list(self.news_collection.find(
                    {"video_path": {"$exists": True, "$ne": None}},
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


if __name__ == '__main__':
    # Create and run the job service
    job = VideoGeneratorJob()

    # Start the Flask application with job scheduling
    job.run_flask_app()
