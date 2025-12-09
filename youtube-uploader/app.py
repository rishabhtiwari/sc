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
import re
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from config import Config
from services import YouTubeService, YouTubeMetadataBuilder
import spacy

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

# Load spaCy model once at startup
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("✅ spaCy model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load spaCy model: {e}")
    nlp = None

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

# Initialize YouTube service with MongoDB connection
youtube_service = YouTubeService(Config, db)

# Initialize metadata builder (used for Shorts metadata only)
metadata_builder = YouTubeMetadataBuilder()


def _extract_keywords_from_titles(news_items, keywords_per_article=2):
    """
    Extract top keywords from each news article title using spaCy

    Args:
        news_items: List of news items with 'title' field
        keywords_per_article: Number of keywords to extract per article (default: 2)

    Returns:
        List of extracted keywords (2 per article)
    """
    if not nlp:
        logger.warning("⚠️ spaCy model not loaded, returning empty keywords")
        return []

    all_keywords = []

    # Stop words to filter out
    stop_words = {
        'and', 'or', 'but', 'for', 'with', 'from', 'into', 'during', 'including',
        'said', 'says', 'according', 'new', 'old', 'big', 'small', 'good', 'best',
        'after', 'before', 'while', 'when', 'where', 'how', 'why', 'what', 'who',
        'this', 'that', 'these', 'those', 'here', 'there', 'now', 'then',
        'study', 'reveals', 'claims', 'report', 'reports', 'video', 'watch',
        '2024', '2025', 'day', 'days', 'time', 'times', 'year', 'years',
        'amid', 'over', 'under', 'about', 'against', 'between', 'through'
    }

    # Process each news title individually
    for item in news_items:
        title = item.get('title', '')
        if not title:
            continue

        # Extract keywords for this specific article
        article_keywords = []

        # Use spaCy to analyze the title
        doc = nlp(title)

        # Priority 1: Multi-word named entities (PERSON, ORG, GPE, PRODUCT, EVENT)
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'NORP', 'FAC', 'LOC']:
                phrase = ent.text.strip()
                # Remove possessive 's from names
                if phrase.endswith("'s"):
                    phrase = phrase[:-2]
                elif phrase.endswith("'"):
                    phrase = phrase[:-1]
                if len(phrase) > 2 and phrase.lower() not in stop_words:
                    article_keywords.append(('high', phrase.lower()))

        # Priority 2: Consecutive proper nouns (multi-word phrases like "iPhone 16")
        propn_sequence = []
        for token in doc:
            if token.pos_ == 'PROPN' and token.text.lower() not in stop_words:
                propn_sequence.append(token.text)
            elif token.pos_ == 'NUM' and len(propn_sequence) > 0:
                propn_sequence.append(token.text)
            else:
                if len(propn_sequence) >= 2:
                    phrase = ' '.join(propn_sequence)
                    article_keywords.append(('high', phrase.lower()))
                elif len(propn_sequence) == 1 and len(propn_sequence[0]) > 2:
                    article_keywords.append(('medium', propn_sequence[0].lower()))
                propn_sequence = []

        # Don't forget the last sequence
        if len(propn_sequence) >= 2:
            phrase = ' '.join(propn_sequence)
            article_keywords.append(('high', phrase.lower()))
        elif len(propn_sequence) == 1 and len(propn_sequence[0]) > 2:
            article_keywords.append(('medium', propn_sequence[0].lower()))

        # Priority 3: Important common nouns
        for token in doc:
            if token.pos_ == 'NOUN':
                word = token.text.lower()
                if (word not in stop_words and len(word) > 3 and
                    word not in {'home', 'sale', 'update', 'updates', 'news', 'headline', 'headlines'}):
                    article_keywords.append(('low', word))

        # Sort by priority and take top keywords_per_article
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        article_keywords.sort(key=lambda x: priority_order[x[0]])

        # Remove duplicates while preserving priority order
        seen = set()
        unique_article_keywords = []
        for priority, keyword in article_keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_article_keywords.append(keyword)
                if len(unique_article_keywords) >= keywords_per_article:
                    break

        # Add to overall list
        all_keywords.extend(unique_article_keywords)

    logger.info(f"✅ Extracted {len(all_keywords)} keywords ({keywords_per_article} per article) from {len(news_items)} news items")
    return all_keywords


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

        # Count shorts ready to upload (have shorts_video_path but no youtube_shorts_id)
        shorts_ready_to_upload = news_collection.count_documents({
            'shorts_video_path': {'$ne': None},
            '$or': [
                {'youtube_shorts_id': {'$exists': False}},
                {'youtube_shorts_id': None}
            ]
        })

        # Count already uploaded shorts
        shorts_already_uploaded = news_collection.count_documents({
            'youtube_shorts_id': {'$exists': True, '$ne': None}
        })

        # Count total shorts
        total_shorts = news_collection.count_documents({
            'shorts_video_path': {'$ne': None}
        })

        return jsonify({
            'ready_to_upload': ready_to_upload,
            'already_uploaded': already_uploaded,
            'total_videos': total_videos,
            'shorts_ready_to_upload': shorts_ready_to_upload,
            'shorts_already_uploaded': shorts_already_uploaded,
            'total_shorts': total_shorts
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

    # Comprehensive hashtags (first 3 appear above title)
    hashtags = [
        '#News',
        '#BreakingNews',
        '#LatestNews',
        '@CNI-News24',
        '#EnglishNews',
        '#WorldNews',
        '#HindiNews',
        '#India',
        '#NewsToday',
        '#TopNews',
        '#NewsCompilation',
        '#CurrentAffairs',
        '#IndianNews',
        '#GlobalNews',
        '#DailyNews',
        '#NewsUpdate'
    ]
    parts.append(" ".join(hashtags))
    parts.append("")

    # Comprehensive keywords for SEO
    parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    parts.append("🔍 KEYWORDS:")

    # Base keywords (always included)
    base_keywords = [
        "top news",
        "latest news",
        "breaking news",
        "news today",
        f"{time_of_day.lower()} news",
        "english news",
        "world news",
        "hindi news",
        "india news",
        "news compilation",
        "current affairs",
        "news update",
        "daily news",
        "news headlines",
        "top stories",
        "indian news",
        "global news"
    ]

    # Extract content-specific keywords from news titles (top 2 from each)
    content_keywords = _extract_keywords_from_titles(news_items, keywords_per_article=2)

    # Ensure all keywords are strings (not tuples)
    clean_content_keywords = []
    for kw in content_keywords:
        if isinstance(kw, tuple):
            clean_content_keywords.append(kw[1] if len(kw) > 1 else str(kw[0]))
        else:
            clean_content_keywords.append(str(kw))

    # Combine base keywords with content-specific keywords
    all_keywords = base_keywords + clean_content_keywords

    parts.append(", ".join(all_keywords))
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

    # Build description and ensure it's under YouTube's 5000 character limit
    description = "\n".join(parts)

    # YouTube description limit is 5000 characters
    if len(description) > 5000:
        logger.warning(f"⚠️ Description is {len(description)} characters, truncating to 5000")
        # Truncate and add ellipsis
        description = description[:4997] + "..."

    logger.info(f"📝 Description length: {len(description)} characters")
    return description


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

        # Get current time in India timezone (IST - UTC+5:30)
        india_tz = ZoneInfo("Asia/Kolkata")
        india_time = datetime.now(india_tz)
        current_hour = india_time.hour

        # Determine time of day based on India time
        if 5 <= current_hour < 12:
            time_of_day = "Morning"
        elif 12 <= current_hour < 17:
            time_of_day = "Afternoon"
        elif 17 <= current_hour < 21:
            time_of_day = "Evening"
        else:
            time_of_day = "Night"

        # Build compilation title with India date
        title = f"📰 Top {len(news_items)} News: This {time_of_day}'s Top Headlines | {india_time.strftime('%d %B %Y')}"

        # Build compilation description
        description = _build_compilation_description(news_items, time_of_day)

        # Build comprehensive tags for better discoverability
        base_tags = [
            'news compilation',
            'top news',
            'latest news',
            'breaking news',
            'english news',
            'world news',
            'hindi news',
            'india news',
            'news today',
            f'{time_of_day.lower()} news',
            'current affairs',
            'news update',
            'daily news',
            'news headlines',
            'top stories',
            'indian news',
            'global news',
            f'news {india_time.year}',
            'today news',
            'latest update'
        ]

        # Extract content-specific keywords and add to tags (top 2 from each)
        content_keywords = _extract_keywords_from_titles(news_items, keywords_per_article=2)

        # Ensure all keywords are strings (not tuples) and filter out invalid tags
        import re
        clean_keywords = []
        for kw in content_keywords:
            # Convert tuple to string if needed
            if isinstance(kw, tuple):
                keyword_str = kw[1] if len(kw) > 1 else str(kw[0])
            else:
                keyword_str = str(kw)

            # Strip whitespace
            keyword_str = keyword_str.strip()

            # Filter out phrases with more than 2 words
            word_count = len(keyword_str.split())
            if word_count > 2:
                continue

            # Filter out non-ASCII characters (YouTube doesn't accept them in tags)
            if not keyword_str.isascii():
                continue

            # Filter out tags that are too short (less than 2 characters)
            if len(keyword_str) < 2:
                continue

            # Filter out tags with special characters (only allow alphanumeric, space, hyphen)
            # YouTube doesn't allow: < > " ' & etc.
            if not re.match(r'^[a-zA-Z0-9\s\-]+$', keyword_str):
                continue

            # Filter out tags that are just numbers
            if keyword_str.isdigit():
                continue

            clean_keywords.append(keyword_str)

        # Combine base tags with content keywords
        all_tags = base_tags + clean_keywords

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in all_tags:
            tag_lower = tag.lower().strip()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_tags.append(tag)

        # Limit to 35 tags, ensure total tag size is less than 450 characters and each tag is max 30 chars
        tags = []
        total_size = 0
        for tag in unique_tags:
            # Stop if we've reached 35 tags
            if len(tags) >= 35:
                break

            # Skip tags longer than 30 characters (YouTube limit per tag)
            if len(tag) > 30:
                continue

            # Final validation: ensure tag contains only allowed characters
            if not re.match(r'^[a-zA-Z0-9\s\-]+$', tag):
                continue

            tag_size = len(tag)
            if total_size + tag_size + len(tags) <= 450:  # +len(tags) accounts for commas
                tags.append(tag)
                total_size += tag_size
            else:
                break

        logger.info(f"✅ Metadata built - Title: {title}, Tags: {len(tags)}")
        logger.info(f"🏷️ Total tags: {len(tags)}, total size: {total_size} chars")

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


@app.route('/api/upload-config/<config_id>', methods=['POST'])
def upload_config_video(config_id):
    """Upload config-specific video to YouTube"""
    try:
        logger.info(f"📤 Starting upload of config video: {config_id}")

        # Step 1: Get config from database
        logger.info("🔍 Step 1: Fetching config from database...")
        configs_collection = db['long_video_configs']

        from bson import ObjectId
        config = configs_collection.find_one({'_id': ObjectId(config_id)})

        if not config:
            return jsonify({
                'status': 'error',
                'error': f'Configuration not found: {config_id}'
            }), 404

        # Check if config has completed merge
        if config.get('status') != 'completed':
            return jsonify({
                'status': 'error',
                'error': f'Configuration video not ready. Status: {config.get("status", "unknown")}'
            }), 400

        # Get video and thumbnail paths
        video_path_relative = config.get('videoPath')
        thumbnail_path_relative = config.get('thumbnailPath')

        if not video_path_relative:
            return jsonify({
                'status': 'error',
                'error': 'Video path not found in configuration'
            }), 400

        logger.info(f"✅ Found config: {config.get('title')}")
        logger.info(f"📹 Video path: {video_path_relative}")
        logger.info(f"🖼️ Thumbnail path: {thumbnail_path_relative}")

        # Step 2: Convert relative paths to absolute paths
        # video_path_relative is like: /public/692bc0d1efceeab41fab2f55/latest.mp4
        video_path = os.path.join(Config.VIDEO_BASE_PATH, config_id, 'latest.mp4')

        if not os.path.exists(video_path):
            return jsonify({
                'status': 'error',
                'error': f'Video file not found: {video_path}'
            }), 404

        logger.info(f"✅ Found video file: {video_path}")

        # Get thumbnail path if available
        thumbnail_path = None
        if thumbnail_path_relative:
            thumbnail_path = os.path.join(Config.VIDEO_BASE_PATH, config_id, 'latest-thumbnail.jpg')
            if os.path.exists(thumbnail_path):
                logger.info(f"✅ Found thumbnail: {thumbnail_path}")
            else:
                logger.warning(f"⚠️ Thumbnail not found: {thumbnail_path}")
                thumbnail_path = None

        # Step 3: Get news items for this config to build metadata
        logger.info("📋 Step 3: Fetching news items for metadata...")

        # ALWAYS use automatic mode for YouTube metadata generation
        # Manual selection is only for video merging, not for metadata
        # We want to fetch the LATEST news matching the config filters for rich metadata

        # Build query based on config filters
        query = {'status': 'completed'}  # Only get completed articles

        if config.get('categories') and len(config.get('categories', [])) > 0:
            query['category'] = {'$in': config['categories']}

        if config.get('country'):
            # Country is stored as source.country in MongoDB
            query['source.country'] = config['country'].lower()

        if config.get('language'):
            # Language is stored as lang in MongoDB
            query['lang'] = config['language'].lower()

        video_count = config.get('videoCount', 20)

        logger.info(f"🔍 Querying news with filters: {query}")
        news_items = list(news_collection.find(query).sort('publishedAt', -1).limit(video_count))

        logger.info(f"✅ Found {len(news_items)} articles matching filters (country={config.get('country')}, language={config.get('language')}, categories={config.get('categories')})")

        if not news_items:
            logger.warning("⚠️ No news items found, will use minimal metadata")
            logger.warning(f"⚠️ Query filters - categories: {config.get('categories')}, country: {config.get('country')}, language: {config.get('language')}")

        # Step 4: Build metadata
        logger.info("📝 Step 4: Building metadata...")

        # Get current time in India timezone
        india_tz = ZoneInfo("Asia/Kolkata")
        india_time = datetime.now(india_tz)
        current_hour = india_time.hour

        # Determine time of day
        if 5 <= current_hour < 12:
            time_of_day = "Morning"
        elif 12 <= current_hour < 17:
            time_of_day = "Afternoon"
        elif 17 <= current_hour < 21:
            time_of_day = "Evening"
        else:
            time_of_day = "Night"

        # Use custom metadata from config if available, otherwise generate
        # Priority: config metadata > generated metadata

        # Title: Use config title if available, otherwise generate
        if config.get('youtubeTitle'):
            title = config['youtubeTitle']
            logger.info(f"📝 Using custom YouTube title from config: {title}")
        elif config.get('title'):
            # Use config title as-is for YouTube
            title = config['title']
            logger.info(f"📝 Using config title for YouTube: {title}")
        else:
            # Fallback: Generate title
            video_count = config.get('videoCount', len(news_items))
            title = f"📰 Top {video_count} News: This {time_of_day}'s Top Headlines | {india_time.strftime('%d %B %Y')}"
            logger.info(f"📝 Generated title: {title}")

        # Description: Use config description if available, otherwise generate
        if config.get('youtubeDescription'):
            description = config['youtubeDescription']
            logger.info(f"📝 Using custom YouTube description from config ({len(description)} chars)")
        elif news_items and len(news_items) > 0:
            description = _build_compilation_description(news_items, time_of_day)
            logger.info(f"📝 Generated rich description from {len(news_items)} news items ({len(description)} chars)")
            logger.info(f"📝 Description preview: {description[:200]}...")
        else:
            description = f"Watch the latest news compilation: {title}\n\n"
            description += f"📅 Published: {india_time.strftime('%d %B %Y')}\n"
            description += f"🕐 Time: {time_of_day}\n\n"
            description += "Stay informed with the latest news updates!\n\n"
            description += "#News #BreakingNews #LatestNews #NewsUpdate"
            logger.warning(f"⚠️ Using fallback description because news_items is empty ({len(description)} chars)")
            logger.warning(f"⚠️ Config filters - categories: {config.get('categories')}, country: {config.get('country')}, language: {config.get('language')}")

        # Tags: Use config tags if available, otherwise generate
        if config.get('youtubeTags') and len(config.get('youtubeTags', [])) > 0:
            tags = config['youtubeTags']
            logger.info(f"📝 Using custom YouTube tags from config ({len(tags)} tags)")
        else:
            # Build comprehensive tags for better discoverability
            base_tags = [
                'news compilation',
                'top news',
                'latest news',
                'breaking news',
                'english news',
                'world news',
                'hindi news',
                'india news',
                'news today',
                f'{time_of_day.lower()} news',
                'current affairs',
                'news update',
                'daily news',
                'news headlines',
                'top stories',
                'indian news',
                'global news',
                f'news {india_time.year}',
                'today news',
                'latest update'
            ]

            # Extract keywords from news items if available
            if news_items:
                content_keywords = _extract_keywords_from_titles(news_items, keywords_per_article=2)
                clean_keywords = [kw for kw in content_keywords if isinstance(kw, str) and len(kw) >= 2 and kw.isascii()]
                all_tags = base_tags + clean_keywords
            else:
                all_tags = base_tags

            # Remove duplicates and limit tags
            seen = set()
            unique_tags = []
            for tag in all_tags:
                tag_lower = tag.lower().strip()
                if tag_lower not in seen and len(tag) <= 30:
                    seen.add(tag_lower)
                    unique_tags.append(tag)
                    if len(unique_tags) >= 35:
                        break

            tags = unique_tags
            logger.info(f"📝 Generated tags ({len(tags)} tags)")

        logger.info(f"✅ Metadata built - Title: {title}, Tags: {len(tags)}")

        # Step 5: Upload to YouTube
        logger.info("📤 Step 5: Uploading to YouTube...")
        upload_result = youtube_service.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            thumbnail_path=thumbnail_path
        )

        if upload_result and upload_result['status'] == 'success':
            logger.info(f"✅ Successfully uploaded config video: {upload_result['video_url']}")

            # Update config with YouTube info
            configs_collection.update_one(
                {'_id': ObjectId(config_id)},
                {'$set': {
                    'youtubeVideoId': upload_result['video_id'],
                    'youtubeVideoUrl': upload_result['video_url'],
                    'uploadedAt': datetime.utcnow()
                }}
            )

            return jsonify({
                'status': 'success',
                'message': f'Successfully uploaded video: {title}',
                'video_url': upload_result['video_url'],
                'video_id': upload_result['video_id'],
                'title': title,
                'news_count': len(news_items)
            })
        else:
            error_msg = upload_result.get('error', 'Unknown error') if upload_result else 'Upload failed'
            logger.error(f"❌ Failed to upload config video: {error_msg}")

            return jsonify({
                'status': 'error',
                'error': error_msg
            })

    except Exception as e:
        logger.error(f"❌ Upload process failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/shorts/pending', methods=['GET'])
def get_pending_shorts():
    """Get list of shorts ready to upload (not yet uploaded) with pagination"""
    try:
        # Get pagination parameters from query string
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 5))  # Default 5 shorts per page

        # Calculate skip value for pagination
        skip = (page - 1) * limit

        # Query filter
        query_filter = {
            'shorts_video_path': {'$ne': None},
            '$or': [
                {'youtube_shorts_id': {'$exists': False}},
                {'youtube_shorts_id': None}
            ]
        }

        # Get total count
        total_count = news_collection.count_documents(query_filter)

        # Query for news with shorts_video_path but no youtube_shorts_id
        # Sort by publishedAt in descending order (most recent first)
        shorts = list(news_collection.find(
            query_filter,
            {
                'id': 1,
                'title': 1,
                'short_summary': 1,
                'shorts_video_path': 1,
                'publishedAt': 1,
                'image': 1,
                '_id': 0
            }
        ).sort('publishedAt', -1).skip(skip).limit(limit))  # -1 for descending order (most recent first)

        # Calculate pagination metadata
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1

        logger.info(f"📋 Found {len(shorts)} shorts on page {page}/{total_pages} (total: {total_count})")

        return jsonify({
            'status': 'success',
            'count': len(shorts),
            'total': total_count,
            'page': page,
            'limit': limit,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev,
            'shorts': shorts
        })

    except Exception as e:
        logger.error(f"❌ Failed to fetch pending shorts: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/shorts/upload/<article_id>', methods=['POST'])
def upload_short(article_id):
    """Upload a single YouTube Short"""
    try:
        logger.info(f"📤 Starting upload of YouTube Short for article: {article_id}")

        # Fetch article from database
        article = news_collection.find_one({'id': article_id})

        if not article:
            return jsonify({
                'status': 'error',
                'error': f'Article not found: {article_id}'
            }), 404

        # Check if shorts video exists
        shorts_video_path = article.get('shorts_video_path')
        if not shorts_video_path:
            return jsonify({
                'status': 'error',
                'error': 'Shorts video not generated for this article'
            }), 400

        # Check if already uploaded
        if article.get('youtube_shorts_id'):
            return jsonify({
                'status': 'error',
                'error': 'This short has already been uploaded to YouTube',
                'video_url': article.get('youtube_shorts_url')
            }), 400

        # Get video file from video-generator service
        video_generator_url = os.getenv('VIDEO_GENERATOR_URL', 'http://ichat-video-generator:8095')

        # Convert relative path to download URL
        # shorts_video_path can be:
        # - /public/article_id/short.mp4
        # - article_id/article_id_short.mp4
        shorts_video_path_clean = shorts_video_path.lstrip('/')
        if shorts_video_path_clean.startswith('public/'):
            shorts_video_path_clean = shorts_video_path_clean[7:]  # Remove 'public/' prefix

        video_filename = os.path.basename(shorts_video_path_clean)
        video_dir = os.path.dirname(shorts_video_path_clean).split('/')[-1] if '/' in shorts_video_path_clean else shorts_video_path_clean.split('/')[0]
        video_url = f"{video_generator_url}/download/{video_dir}/{video_filename}"

        logger.info(f"📥 Downloading shorts video from: {video_url}")

        # Download video file
        video_response = requests.get(video_url, timeout=60)
        if video_response.status_code != 200:
            logger.error(f"❌ Failed to download video from {video_url}")
            logger.error(f"❌ HTTP Status: {video_response.status_code}")
            logger.error(f"❌ Response: {video_response.text[:500]}")
            return jsonify({
                'status': 'error',
                'error': f'Failed to download shorts video: HTTP {video_response.status_code}'
            }), 500

        # Save video temporarily
        temp_video_path = f'/tmp/short_{article_id}.mp4'
        with open(temp_video_path, 'wb') as f:
            f.write(video_response.content)

        logger.info(f"✅ Downloaded shorts video: {len(video_response.content)} bytes")

        # Generate metadata for the short
        title = article.get('title', 'News Update')
        description = article.get('short_summary', article.get('description', ''))

        # Build metadata using metadata builder
        metadata = metadata_builder.build_shorts_metadata(
            title=title,
            description=description
        )

        logger.info(f"📝 Generated metadata - Title: {metadata['title'][:50]}...")
        logger.info(f"🏷️ Generated {len(metadata.get('tags', []))} tags: {metadata.get('tags', [])}")
        logger.info(f"📄 Description length: {len(metadata.get('description', ''))} characters")

        # Upload to YouTube
        upload_result = youtube_service.upload_video(
            video_path=temp_video_path,
            title=metadata['title'],
            description=metadata['description'],
            tags=metadata['tags'],
            category_id='25',  # News & Politics
            privacy_status='public'
        )

        # Clean up temp file
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)

        if upload_result and upload_result['status'] == 'success':
            # Update database with YouTube Shorts info
            news_collection.update_one(
                {'id': article_id},
                {
                    '$set': {
                        'youtube_shorts_id': upload_result['video_id'],
                        'youtube_shorts_url': upload_result['video_url'],
                        'youtube_shorts_uploaded_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            logger.info(f"✅ Successfully uploaded short: {upload_result['video_url']}")

            return jsonify({
                'status': 'success',
                'message': 'Short uploaded successfully',
                'video_url': upload_result['video_url'],
                'video_id': upload_result['video_id']
            })
        else:
            error_msg = upload_result.get('error', 'Unknown error') if upload_result else 'Upload failed'
            logger.error(f"❌ Failed to upload short: {error_msg}")

            return jsonify({
                'status': 'error',
                'error': error_msg
            }), 500

    except Exception as e:
        logger.error(f"❌ Short upload failed: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/auth/start', methods=['POST'])
def start_auth():
    """Start OAuth authentication flow for a credential"""
    try:
        data = request.get_json()
        credential_id = data.get('credential_id')

        if not credential_id:
            return jsonify({
                'status': 'error',
                'error': 'credential_id is required'
            }), 400

        # Get credentials collection
        credentials_collection = db['youtube_credentials']

        # Get credential from database
        credential = credentials_collection.find_one({'credential_id': credential_id})
        if not credential:
            return jsonify({
                'status': 'error',
                'error': 'Credential not found'
            }), 404

        # Create client config for OAuth flow
        client_config = {
            'installed': {
                'client_id': credential['client_id'],
                'client_secret': credential['client_secret'],
                'project_id': credential['project_id'],
                'auth_uri': credential.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth'),
                'token_uri': credential.get('token_uri', 'https://oauth2.googleapis.com/token'),
                'auth_provider_x509_cert_url': credential.get('auth_provider_x509_cert_url', 'https://www.googleapis.com/oauth2/v1/certs'),
                'redirect_uris': ['urn:ietf:wg:oauth:2.0:oob']
            }
        }

        # Create OAuth flow
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_config(
            client_config,
            scopes=credential.get('scopes', ['https://www.googleapis.com/auth/youtube.upload'])
        )
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

        # Generate authorization URL
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # Save flow state for later use
        flow_state = {
            'credential_id': credential_id,
            'state': state,
            'client_config': client_config,
            'scopes': credential.get('scopes', ['https://www.googleapis.com/auth/youtube.upload']),
            'created_at': datetime.now().isoformat()
        }

        flow_state_file = os.path.join(os.path.dirname(Config.YOUTUBE_CREDENTIALS_FILE), f'oauth_flow_{credential_id}.json')
        with open(flow_state_file, 'w') as f:
            json.dump(flow_state, f)

        logger.info(f"🔐 Started OAuth flow for credential: {credential_id}")

        return jsonify({
            'status': 'success',
            'auth_url': auth_url,
            'credential_id': credential_id
        })

    except Exception as e:
        logger.error(f"❌ Failed to start OAuth flow: {str(e)}")
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
        credential_id = data.get('credential_id')

        if not auth_code:
            return jsonify({
                'status': 'error',
                'error': 'Authorization code is required'
            }), 400

        if not credential_id:
            return jsonify({
                'status': 'error',
                'error': 'credential_id is required'
            }), 400

        logger.info(f"📝 Received OAuth authorization code for credential: {credential_id}")

        # Get credentials collection
        credentials_collection = db['youtube_credentials']

        # Load flow state
        flow_state_file = os.path.join(os.path.dirname(Config.YOUTUBE_CREDENTIALS_FILE), f'oauth_flow_{credential_id}.json')
        if not os.path.exists(flow_state_file):
            return jsonify({
                'status': 'error',
                'error': 'OAuth flow not found. Please start authentication first.'
            }), 400

        with open(flow_state_file, 'r') as f:
            flow_state = json.load(f)

        # Create OAuth flow
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_config(
            flow_state['client_config'],
            scopes=flow_state['scopes']
        )
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

        # Exchange authorization code for credentials
        logger.info("Exchanging authorization code for credentials...")
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials

        # Update credential in database with tokens
        credentials_collection.update_one(
            {'credential_id': credential_id},
            {
                '$set': {
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                    'is_authenticated': True,
                    'updated_at': datetime.now()
                }
            }
        )

        # Clean up flow state file
        if os.path.exists(flow_state_file):
            os.remove(flow_state_file)

        logger.info(f"✅ YouTube authentication completed successfully for credential: {credential_id}")

        return jsonify({
            'status': 'success',
            'message': 'YouTube authentication completed successfully! You can now upload videos.'
        })

    except Exception as e:
        logger.error(f"❌ OAuth callback error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# ============================================================================
# YOUTUBE CREDENTIALS CRUD OPERATIONS
# ============================================================================

@app.route('/api/credentials', methods=['GET'])
def get_credentials():
    """Get all YouTube credentials"""
    try:
        logger.info("📋 GET /api/credentials")

        # Get credentials collection
        credentials_collection = db['youtube_credentials']

        # Fetch all credentials (excluding sensitive fields)
        credentials = list(credentials_collection.find(
            {},
            {
                '_id': 0,
                'client_secret': 0,
                'access_token': 0,
                'refresh_token': 0
            }
        ).sort('created_at', -1))

        # Convert datetime objects to ISO strings
        for cred in credentials:
            if 'created_at' in cred and cred['created_at']:
                if isinstance(cred['created_at'], datetime):
                    cred['created_at'] = cred['created_at'].isoformat()
            if 'updated_at' in cred and cred['updated_at']:
                if isinstance(cred['updated_at'], datetime):
                    cred['updated_at'] = cred['updated_at'].isoformat()
            if 'last_used_at' in cred and cred['last_used_at']:
                if isinstance(cred['last_used_at'], datetime):
                    cred['last_used_at'] = cred['last_used_at'].isoformat()
            if 'token_expiry' in cred and cred['token_expiry']:
                if isinstance(cred['token_expiry'], datetime):
                    cred['token_expiry'] = cred['token_expiry'].isoformat()

        return jsonify({
            'status': 'success',
            'data': credentials,
            'count': len(credentials)
        })

    except Exception as e:
        logger.error(f"❌ Error fetching credentials: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/credentials/<credential_id>', methods=['GET'])
def get_credential(credential_id):
    """Get a specific YouTube credential by ID"""
    try:
        logger.info(f"📋 GET /api/credentials/{credential_id}")

        credentials_collection = db['youtube_credentials']

        # Fetch credential (excluding sensitive fields)
        credential = credentials_collection.find_one(
            {'credential_id': credential_id},
            {
                '_id': 0,
                'client_secret': 0,
                'access_token': 0,
                'refresh_token': 0
            }
        )

        if not credential:
            return jsonify({
                'status': 'error',
                'error': 'Credential not found'
            }), 404

        # Convert datetime objects to ISO strings
        if 'created_at' in credential and credential['created_at']:
            if isinstance(credential['created_at'], datetime):
                credential['created_at'] = credential['created_at'].isoformat()
        if 'updated_at' in credential and credential['updated_at']:
            if isinstance(credential['updated_at'], datetime):
                credential['updated_at'] = credential['updated_at'].isoformat()
        if 'last_used_at' in credential and credential['last_used_at']:
            if isinstance(credential['last_used_at'], datetime):
                credential['last_used_at'] = credential['last_used_at'].isoformat()
        if 'token_expiry' in credential and credential['token_expiry']:
            if isinstance(credential['token_expiry'], datetime):
                credential['token_expiry'] = credential['token_expiry'].isoformat()

        return jsonify({
            'status': 'success',
            'data': credential
        })

    except Exception as e:
        logger.error(f"❌ Error fetching credential: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/credentials', methods=['POST'])
def create_credential():
    """Create a new YouTube credential"""
    try:
        logger.info("➕ POST /api/credentials")

        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'client_id', 'client_secret', 'project_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'error': f'Missing required field: {field}'
                }), 400

        credentials_collection = db['youtube_credentials']

        # Generate credential ID
        import uuid
        credential_id = str(uuid.uuid4())

        # Prepare credential document
        credential = {
            'credential_id': credential_id,
            'name': data['name'],
            'client_id': data['client_id'],
            'client_secret': data['client_secret'],
            'project_id': data['project_id'],
            'auth_uri': data.get('auth_uri', 'https://accounts.google.com/o/oauth2/auth'),
            'token_uri': data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            'auth_provider_x509_cert_url': data.get('auth_provider_x509_cert_url', 'https://www.googleapis.com/oauth2/v1/certs'),
            'redirect_uris': data.get('redirect_uris', ['http://localhost:8097/oauth2callback']),
            'access_token': None,
            'refresh_token': None,
            'token_expiry': None,
            'scopes': data.get('scopes', ['https://www.googleapis.com/auth/youtube.upload']),
            'channel_id': data.get('channel_id', ''),
            'channel_name': data.get('channel_name', ''),
            'is_active': data.get('is_active', False),
            'is_authenticated': False,
            'last_used_at': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'created_by': data.get('created_by', 'system'),
            'notes': data.get('notes', '')
        }

        # Insert credential
        credentials_collection.insert_one(credential)

        logger.info(f"✅ Created credential: {credential_id} - {data['name']}")

        # Return created credential (excluding sensitive fields)
        credential.pop('_id', None)
        credential.pop('client_secret', None)
        credential.pop('access_token', None)
        credential.pop('refresh_token', None)
        credential['created_at'] = credential['created_at'].isoformat()
        credential['updated_at'] = credential['updated_at'].isoformat()

        return jsonify({
            'status': 'success',
            'data': credential,
            'message': 'Credential created successfully'
        }), 201

    except Exception as e:
        logger.error(f"❌ Error creating credential: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/credentials/<credential_id>', methods=['PUT'])
def update_credential(credential_id):
    """Update a YouTube credential"""
    try:
        logger.info(f"✏️ PUT /api/credentials/{credential_id}")

        data = request.get_json()
        credentials_collection = db['youtube_credentials']

        # Check if credential exists
        existing = credentials_collection.find_one({'credential_id': credential_id})
        if not existing:
            return jsonify({
                'status': 'error',
                'error': 'Credential not found'
            }), 404

        # Prepare update data
        update_data = {
            'updated_at': datetime.now()
        }

        # Update allowed fields
        allowed_fields = ['name', 'client_id', 'client_secret', 'project_id', 'auth_uri',
                         'token_uri', 'redirect_uris', 'channel_id', 'channel_name',
                         'is_active', 'notes']

        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

        # If setting this credential as active, deactivate others
        if data.get('is_active') == True:
            credentials_collection.update_many(
                {'credential_id': {'$ne': credential_id}},
                {'$set': {'is_active': False}}
            )

        # Update credential
        credentials_collection.update_one(
            {'credential_id': credential_id},
            {'$set': update_data}
        )

        logger.info(f"✅ Updated credential: {credential_id}")

        # Fetch and return updated credential
        updated = credentials_collection.find_one(
            {'credential_id': credential_id},
            {
                '_id': 0,
                'client_secret': 0,
                'access_token': 0,
                'refresh_token': 0
            }
        )

        # Convert datetime objects
        if 'created_at' in updated and updated['created_at']:
            updated['created_at'] = updated['created_at'].isoformat()
        if 'updated_at' in updated and updated['updated_at']:
            updated['updated_at'] = updated['updated_at'].isoformat()
        if 'last_used_at' in updated and updated['last_used_at']:
            updated['last_used_at'] = updated['last_used_at'].isoformat()

        return jsonify({
            'status': 'success',
            'data': updated,
            'message': 'Credential updated successfully'
        })

    except Exception as e:
        logger.error(f"❌ Error updating credential: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/credentials/<credential_id>', methods=['DELETE'])
def delete_credential(credential_id):
    """Delete a YouTube credential"""
    try:
        logger.info(f"🗑️ DELETE /api/credentials/{credential_id}")

        credentials_collection = db['youtube_credentials']

        # Check if credential exists
        existing = credentials_collection.find_one({'credential_id': credential_id})
        if not existing:
            return jsonify({
                'status': 'error',
                'error': 'Credential not found'
            }), 404

        # Delete credential
        credentials_collection.delete_one({'credential_id': credential_id})

        logger.info(f"✅ Deleted credential: {credential_id}")

        return jsonify({
            'status': 'success',
            'message': 'Credential deleted successfully'
        })

    except Exception as e:
        logger.error(f"❌ Error deleting credential: {str(e)}")
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

