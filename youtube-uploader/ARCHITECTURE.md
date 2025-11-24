# YouTube Uploader Service - Architecture

## Overview
The YouTube Uploader service automates uploading news videos to YouTube with AI-generated, SEO-optimized metadata.

## Components

### 1. **Metadata Builder Factory** (`services/metadata_builder.py`)
Factory pattern for building optimized YouTube metadata.

**Features:**
- **Title Builder**: Optimizes titles with category prefixes and emojis
- **Description Builder**: Orchestrates LLM-based description generation
- **Tags Builder**: Creates SEO-optimized tags (5-15 tags, max 500 chars)
- **Hashtags Builder**: Category-specific hashtags (first 3 appear above title)

**Methods:**
- `build_title(news_doc)` → Optimized title (max 100 chars)
- `build_description(news_doc)` → Complete description with LLM content
- `build_tags(news_doc)` → List of SEO tags
- `build_metadata(news_doc)` → Complete metadata package

### 2. **LLM Description Generator** (`services/description_generator.py`)
Uses LLM to create engaging 200-word descriptions.

**Features:**
- Calls LLM service to generate natural, engaging descriptions
- Validates word count (180-220 words)
- Fallback to template-based description if LLM fails
- SEO-optimized with natural keyword integration

**Prompt Engineering:**
- Compelling hook in first 2 sentences
- Key facts: who, what, when, where, why, how
- Professional yet conversational tone
- Natural keyword integration for YouTube SEO
- No hashtags/emojis (added separately)

### 3. **YouTube Service** (`services/youtube_service.py`)
Handles YouTube API authentication and video uploads.

**Features:**
- OAuth 2.0 authentication with credential persistence
- Resumable uploads with 1MB chunks
- Retry logic with exponential backoff
- Progress tracking and logging

### 4. **Flask Application** (`app.py`)
Web UI and REST API for upload management.

**Endpoints:**
- `GET /` - Web UI dashboard
- `GET /api/stats` - Upload statistics
- `POST /api/upload-latest-20` - Upload latest 20 videos
- `GET /health` - Health check

## Data Flow

```
1. User clicks "Upload Latest 20" button
   ↓
2. Fetch 20 videos from MongoDB (has video_path, no youtube_video_id)
   ↓
3. For each video:
   a. Metadata Builder creates metadata package
      ├─ Title Builder: Optimizes title
      ├─ Description Generator: Calls LLM for 200-word description
      ├─ Tags Builder: Creates SEO tags
      └─ Hashtags Builder: Adds category hashtags
   ↓
   b. YouTube Service uploads video with metadata
      ├─ Authenticate with OAuth 2.0
      ├─ Upload video file (resumable, chunked)
      └─ Return video ID and URL
   ↓
   c. Update MongoDB with YouTube metadata
      ├─ youtube_video_id
      ├─ youtube_video_url
      └─ youtube_uploaded_at
   ↓
4. Return results to UI
```

## YouTube Description Structure

```
[LLM-Generated 200-word description]
- Engaging hook (first 2 sentences)
- Key facts and context
- Impact and significance
- Natural SEO keywords

━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 Source: [Source Name]
📅 Published: [Date]

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 SUBSCRIBE for Daily News Updates!
👍 LIKE if you found this informative
💬 COMMENT your thoughts below
🔗 SHARE with friends and family
━━━━━━━━━━━━━━━━━━━━━━━━━━

#News #BreakingNews #LatestNews #HindiNews #India [+ category hashtags]

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 KEYWORDS:
breaking news, latest news, hindi news, news today, india news, current affairs

━━━━━━━━━━━━━━━━━━━━━━━━━━
📢 About This Channel:
Stay updated with the latest news from India and around the world.
We bring you breaking news, current affairs, and in-depth analysis.

⚠️ Disclaimer:
This content is for informational purposes only.
Original source: [Source Name]
```

## SEO Optimization

### Title Optimization
- Max 100 characters (60-70 optimal for mobile)
- Front-load important keywords
- Category prefix with emoji (📰, 💼, ⚽, etc.)
- Truncate gracefully if too long

### Description Optimization
- **First 2-3 lines critical** (appear in search results)
- LLM generates engaging 200-word content
- Natural keyword integration
- Call-to-action for engagement
- Hashtags (first 3 appear above title)
- SEO keywords section

### Tags Optimization
- 5-15 tags (optimal range)
- Mix of broad and specific tags
- Category-specific tags
- Hindi/Hinglish variations
- Time-based tags (year, "today", "latest")
- Max 500 characters total

### Hashtags Strategy
- **First 3 hashtags** appear above video title
- Generic high-traffic: #News, #BreakingNews, #LatestNews
- Category-specific: #Business, #Sports, #Technology, etc.
- Regional: #HindiNews, #India, #IndianNews
- Max 15 hashtags total

## Category-Specific Metadata

### Business News
- Prefix: 💼 Business:
- Hashtags: #Business, #Economy, #Finance, #StockMarket
- Tags: business news, economy, finance, stock market

### Sports News
- Prefix: ⚽ Sports:
- Hashtags: #Sports, #Cricket, #Football, #IPL
- Tags: sports news, cricket, football, ipl, sports

### Technology News
- Prefix: 💻 Tech:
- Hashtags: #Technology, #Tech, #Innovation, #Gadgets
- Tags: tech news, technology, gadgets, innovation

### Entertainment News
- Prefix: 🎬 Entertainment:
- Hashtags: #Entertainment, #Bollywood, #Celebrity, #Movies
- Tags: entertainment news, bollywood, celebrity, movies

## Configuration

### Environment Variables
- `LLM_SERVICE_URL` - LLM service endpoint (default: http://ichat-llm-service:8083)
- `DEFAULT_PRIVACY_STATUS` - Video privacy (private/public/unlisted)
- `DEFAULT_CATEGORY_ID` - YouTube category (25 = News & Politics)
- `DEFAULT_TAGS` - Fallback tags if builder fails

### YouTube API Limits
- Title: 100 characters max
- Description: 5000 characters max
- Tags: 500 characters total, 15 tags recommended
- Hashtags: 15 max (first 3 appear above title)

## Error Handling

### LLM Service Failure
- Fallback to template-based description
- Log warning but continue upload
- Ensures uploads don't fail due to LLM issues

### YouTube API Failure
- Retry with exponential backoff (max 3 retries)
- Log detailed error information
- Mark video as failed in results
- Continue with remaining videos

### MongoDB Failure
- Log error and skip video
- Continue with remaining videos
- Return partial results to user

## Testing

Run test script to see example metadata:
```bash
cd jobs/youtube-uploader
python test_metadata_builder.py
```

This shows:
- Original vs optimized titles
- LLM-generated descriptions
- SEO tags and hashtags
- Character counts and validation

## Future Enhancements

1. **Thumbnail Generation**: Auto-generate custom thumbnails
2. **Playlist Management**: Auto-organize videos into playlists
3. **Scheduling**: Schedule uploads for optimal times
4. **Analytics**: Track video performance metrics
5. **A/B Testing**: Test different titles/descriptions
6. **Multi-language**: Support for multiple languages
7. **Shorts Support**: Optimize for YouTube Shorts format

