#!/usr/bin/env python3
"""
Test script to preview YouTube metadata without uploading
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pymongo import MongoClient
from config import Config
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import requests
import logging
import spacy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("✅ spaCy model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load spaCy model: {e}")
    nlp = None

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
        "aaj ki khabar",
        "ताज़ा खबर",
        "समाचार",
        "daily news",
        "news headlines",
        "top stories",
        "indian news",
        "global news"
    ]
    
    # Extract content-specific keywords from news titles (2 per article)
    content_keywords = _extract_keywords_from_titles(news_items, keywords_per_article=2)

    # Combine base keywords with content-specific keywords
    all_keywords = base_keywords + content_keywords
    
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


def test_compilation_metadata():
    """Test compilation video metadata generation"""
    print("=" * 80)
    print("TESTING COMPILATION VIDEO METADATA")
    print("=" * 80)
    
    # Connect to MongoDB
    mongo_client = MongoClient(Config.MONGODB_URL)
    db = mongo_client[Config.MONGODB_DATABASE]
    news_collection = db[Config.MONGODB_COLLECTION]
    
    # Fetch latest 20 news items
    news_items = list(news_collection.find(
        {'video_path': {'$exists': True, '$ne': None}},
        {'title': 1, 'category': 1}
    ).sort('created_at', -1).limit(20))
    
    if not news_items:
        print("❌ No news items found!")
        return
    
    print(f"\n✅ Found {len(news_items)} news items\n")
    
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
    
    print(f"📅 India Time: {india_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"🕐 Time of Day: {time_of_day}")
    print()
    
    # Build title
    title = f"📰 Top {len(news_items)} News: This {time_of_day}'s Top Headlines | {india_time.strftime('%d %B %Y')}"
    
    # Build description
    description = _build_compilation_description(news_items, time_of_day)
    
    # Build tags
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
        'aaj ki khabar',
        'taza khabar',
        'samachar',
        'news headlines',
        'top stories',
        'indian news',
        'global news',
        f'news {india_time.year}',
        'today news',
        'latest update'
    ]
    
    # Extract content-specific keywords and add to tags (2 per article)
    content_keywords = _extract_keywords_from_titles(news_items, keywords_per_article=2)
    tags = base_tags + content_keywords
    
    # Display results
    print("=" * 80)
    print("TITLE:")
    print("=" * 80)
    print(title)
    print()
    
    print("=" * 80)
    print("DESCRIPTION:")
    print("=" * 80)
    print(description)
    print()
    
    print("=" * 80)
    print("TAGS (sent to YouTube API):")
    print("=" * 80)
    print(f"Total tags: {len(tags)}")
    for i, tag in enumerate(tags, 1):
        print(f"{i}. {tag}")
    print()
    
    print("=" * 80)
    print("CONTENT-SPECIFIC KEYWORDS EXTRACTED:")
    print("=" * 80)
    print(f"Total: {len(content_keywords)}")
    print(", ".join(content_keywords))
    print()


if __name__ == '__main__':
    test_compilation_metadata()

