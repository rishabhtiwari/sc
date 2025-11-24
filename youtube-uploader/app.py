#!/usr/bin/env python3
"""
YouTube Uploader Service
Provides UI and API for uploading news videos to YouTube
"""

import os
import glob
import logging
import requests
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from config import Config
from services import YouTubeService, YouTubeMetadataBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize MongoDB connection
try:
    mongo_client = MongoClient(Config.MONGODB_URL)
    db = mongo_client[Config.MONGODB_DATABASE]
    news_collection = db[Config.MONGODB_COLLECTION]
    logger.info("✅ Connected to MongoDB")
except Exception as e:
    logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
    raise

# Initialize YouTube service
youtube_service = YouTubeService(Config)

# Initialize metadata builder with LLM service
metadata_builder = YouTubeMetadataBuilder(llm_service_url=Config.LLM_SERVICE_URL)


@app.route('/')
def index():
    """Render main UI"""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """Get upload statistics"""
    try:
        # Count videos ready to upload (have video_path but no youtube_video_id)
        ready_to_upload = news_collection.count_documents({
            'video_path': {'$ne': None},
            'youtube_video_id': {'$exists': False}
        })

        # Count already uploaded videos
        already_uploaded = news_collection.count_documents({
            'youtube_video_id': {'$exists': True, '$ne': None}
        })

        # Count total videos
        total_videos = news_collection.count_documents({
            'video_path': {'$ne': None}
        })

        return jsonify({
            'ready_to_upload': ready_to_upload,
            'already_uploaded': already_uploaded,
            'total_videos': total_videos
        })
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


def _build_compilation_description(news_items, time_of_day):
    """Build description for news compilation video"""
    parts = []

    # Opening
    parts.append(f"Welcome to this {time_of_day}'s top news compilation! Here are the {len(news_items)} most important headlines you need to know about today.")
    parts.append("")

    # List all news titles with timestamps (assuming each news is ~30 seconds)
    parts.append("📋 NEWS HEADLINES:")
    for idx, item in enumerate(news_items, 1):
        timestamp_seconds = (idx - 1) * 30
        minutes = timestamp_seconds // 60
        seconds = timestamp_seconds % 60
        timestamp = f"{minutes}:{seconds:02d}"
        title = item.get('title', 'Untitled')
        parts.append(f"{idx}. [{timestamp}] {title}")

    parts.append("")
    parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    parts.append("🔔 SUBSCRIBE for Daily News Updates!")
    parts.append("👍 LIKE if you found this informative")
    parts.append("💬 COMMENT your thoughts below")
    parts.append("🔗 SHARE with friends and family")
    parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    parts.append("")

    # Hashtags
    parts.append("#News #BreakingNews #LatestNews #HindiNews #India #NewsToday #TopNews #NewsCompilation")
    parts.append("")

    # Keywords
    parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    parts.append("🔍 KEYWORDS:")
    parts.append(f"top news, latest news, breaking news, news today, {time_of_day.lower()} news, hindi news, india news, news compilation, current affairs, news update")
    parts.append("")

    # About
    parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    parts.append("📢 About This Channel:")
    parts.append("Stay updated with the latest news from India and around the world.")
    parts.append("We bring you breaking news, current affairs, and in-depth analysis.")
    parts.append("")

    # Disclaimer
    parts.append("⚠️ Disclaimer:")
    parts.append("This content is for informational purposes only.")

    return "\n".join(parts)


@app.route('/api/upload-latest-20', methods=['POST'])
def upload_latest_20():
    """Upload latest 20 news compilation video to YouTube"""
    try:
        logger.info("📤 Starting upload of latest 20 news compilation video...")

        # Step 1: Generate merged video first by calling video-generator service
        logger.info("🎬 Step 1: Generating merged video...")
        video_generator_url = os.getenv('VIDEO_GENERATOR_URL', 'http://ichat-video-generator:8095')

        try:
            # Start the merge process
            merge_response = requests.post(
                f"{video_generator_url}/merge-latest",
                json={},
                timeout=30  # 30 seconds timeout for starting the process
            )

            if merge_response.status_code == 200:
                merge_result = merge_response.json()
                logger.info(f"✅ Merge process started: {merge_result.get('message', 'Processing...')}")

                # Step 1.5: Poll for merge completion
                logger.info("⏳ Polling for merge completion...")
                max_wait_time = 300  # 5 minutes max wait
                poll_interval = 5  # Check every 5 seconds
                elapsed_time = 0

                while elapsed_time < max_wait_time:
                    time.sleep(poll_interval)
                    elapsed_time += poll_interval

                    try:
                        status_response = requests.get(
                            f"{video_generator_url}/merge-status",
                            timeout=10
                        )

                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            status = status_result.get('status')

                            if status == 'completed':
                                logger.info(f"✅ Merged video ready! Size: {status_result.get('file_size_mb', 'N/A')} MB")
                                break
                            elif status == 'not_found':
                                logger.warning("⚠️ Merge status: not_found, continuing to wait...")
                            else:
                                logger.info(f"⏳ Merge in progress... ({elapsed_time}s elapsed)")
                        else:
                            logger.warning(f"⚠️ Status check returned {status_response.status_code}")

                    except Exception as poll_error:
                        logger.warning(f"⚠️ Error polling status: {str(poll_error)}")

                if elapsed_time >= max_wait_time:
                    logger.warning("⚠️ Merge process timed out after 5 minutes, will try to use existing merged video")
            else:
                logger.warning(f"⚠️ Video generation returned status {merge_response.status_code}, will try to use existing merged video")
        except requests.exceptions.Timeout:
            logger.warning("⚠️ Failed to start merge process (timeout), will try to use existing merged video")
        except Exception as e:
            logger.warning(f"⚠️ Failed to start merged video generation: {str(e)}, will try to use existing merged video")

        # Step 2: Find the merged video file
        logger.info("🔍 Step 2: Finding merged video...")
        latest_merged_video = os.path.join(Config.VIDEO_BASE_PATH, 'latest-20-news.mp4')

        if not os.path.exists(latest_merged_video):
            return jsonify({
                'status': 'error',
                'error': 'No merged video found. Video generation may have failed. Please check video-generator service logs.'
            })

        logger.info(f"✅ Found merged video: {latest_merged_video}")

        # Step 3: Get latest 20 news for metadata generation
        logger.info("📋 Step 3: Fetching news items for metadata...")
        news_items = list(news_collection.find({
            'video_path': {'$ne': None}
        }).sort('publishedAt', -1).limit(20))

        if not news_items:
            return jsonify({
                'status': 'error',
                'error': 'No news items found for metadata generation'
            })

        logger.info(f"✅ Found {len(news_items)} news items for compilation")

        # Step 4: Build compilation metadata
        logger.info("📝 Step 4: Building metadata...")
        current_hour = datetime.now().hour

        # Determine time of day
        if 5 <= current_hour < 12:
            time_of_day = "Morning"
        elif 12 <= current_hour < 17:
            time_of_day = "Afternoon"
        elif 17 <= current_hour < 21:
            time_of_day = "Evening"
        else:
            time_of_day = "Night"

        # Build compilation title
        title = f"📰 Top {len(news_items)} News: This {time_of_day}'s Top Headlines | {datetime.now().strftime('%d %B %Y')}"

        # Build compilation description
        description = _build_compilation_description(news_items, time_of_day)

        # Build tags
        tags = [
            'news compilation',
            'top news',
            'latest news',
            'breaking news',
            'hindi news',
            'news today',
            f'{time_of_day.lower()} news',
            'india news',
            'current affairs',
            'news update',
            'daily news'
        ]

        logger.info(f"✅ Metadata built - Title: {title}")

        # Step 5: Check for thumbnail
        thumbnail_path = os.path.join(Config.VIDEO_BASE_PATH, 'latest-20-news-thumbnail.jpg')
        if os.path.exists(thumbnail_path):
            logger.info(f"✅ Found thumbnail: {thumbnail_path}")
        else:
            logger.warning(f"⚠️ Thumbnail not found: {thumbnail_path}")
            thumbnail_path = None

        # Step 6: Upload to YouTube
        logger.info("📤 Step 6: Uploading to YouTube...")
        upload_result = youtube_service.upload_video(
            video_path=latest_merged_video,
            title=title,
            description=description,
            tags=tags,
            thumbnail_path=thumbnail_path
        )

        if upload_result and upload_result['status'] == 'success':
            logger.info(f"✅ Successfully uploaded compilation: {upload_result['video_url']}")

            return jsonify({
                'status': 'success',
                'message': f'Successfully uploaded compilation of {len(news_items)} news items',
                'video_url': upload_result['video_url'],
                'video_id': upload_result['video_id'],
                'title': title,
                'news_count': len(news_items)
            })
        else:
            error_msg = upload_result.get('error', 'Unknown error') if upload_result else 'Upload failed'
            logger.error(f"❌ Failed to upload compilation: {error_msg}")

            return jsonify({
                'status': 'error',
                'error': error_msg
            })

    except Exception as e:
        logger.error(f"❌ Upload process failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/oauth-callback', methods=['POST'])
def oauth_callback():
    """Handle OAuth authorization code callback"""
    try:
        data = request.get_json()
        auth_code = data.get('code')

        if not auth_code:
            return jsonify({
                'status': 'error',
                'error': 'Authorization code is required'
            }), 400

        logger.info("📝 Received OAuth authorization code")

        # Complete OAuth flow
        if youtube_service.complete_oauth_flow(auth_code):
            return jsonify({
                'status': 'success',
                'message': 'YouTube authentication completed successfully! You can now upload videos.'
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Failed to complete OAuth flow. Please check logs for details.'
            }), 500

    except Exception as e:
        logger.error(f"❌ OAuth callback error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'youtube-uploader'})


if __name__ == '__main__':
    logger.info(f"🚀 Starting YouTube Uploader Service on port {Config.FLASK_PORT}")
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.DEBUG
    )

