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

# Initialize YouTube service
youtube_service = YouTubeService(Config)

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


@app.route('/api/shorts/pending', methods=['GET'])
def get_pending_shorts():
    """Get list of shorts ready to upload (not yet uploaded)"""
    try:
        # Query for news with shorts_video_path but no youtube_shorts_id
        # Sort by publishedAt in descending order (most recent first)
        shorts = list(news_collection.find(
            {
                'shorts_video_path': {'$ne': None},
                '$or': [
                    {'youtube_shorts_id': {'$exists': False}},
                    {'youtube_shorts_id': None}
                ]
            },
            {
                'id': 1,
                'title': 1,
                'short_summary': 1,
                'shorts_video_path': 1,
                'publishedAt': 1,
                'image': 1,
                '_id': 0
            }
        ).sort('publishedAt', -1))  # -1 for descending order (most recent first)

        logger.info(f"📋 Found {len(shorts)} shorts ready to upload")

        return jsonify({
            'status': 'success',
            'count': len(shorts),
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

