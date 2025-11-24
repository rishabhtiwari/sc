# YouTube News Compilation Upload

## Overview
The YouTube uploader service uploads **news compilation videos** (merged videos of multiple news items) to YouTube with optimized metadata.

## Workflow

### 1. Generate Merged Video
First, create a compilation video using the video-generator service:

```bash
curl -X POST http://localhost:8095/merge-latest -H "Content-Type: application/json" -d '{}'
```

This creates a merged video file: `jobs/video-generator/public/merged_news_YYYYMMDD_HHMMSS.mp4`

### 2. Upload to YouTube
Then upload the compilation to YouTube:

```bash
curl -X POST http://localhost:8097/api/upload-latest-20 -H "Content-Type: application/json" -d '{}'
```

## Title Format

The title is automatically generated based on time of day:

**Morning (5 AM - 12 PM):**
```
📰 Top 20 News: This Morning's Top Headlines | 24 November 2024
```

**Afternoon (12 PM - 5 PM):**
```
📰 Top 20 News: This Afternoon's Top Headlines | 24 November 2024
```

**Evening (5 PM - 9 PM):**
```
📰 Top 20 News: This Evening's Top Headlines | 24 November 2024
```

**Night (9 PM - 5 AM):**
```
📰 Top 20 News: This Night's Top Headlines | 24 November 2024
```

## Description Format

The description includes:

1. **Opening**: Welcome message with time of day
2. **News Headlines List**: All 20 news titles with timestamps
3. **Call-to-Action**: Subscribe, Like, Comment, Share
4. **Hashtags**: #News #BreakingNews #LatestNews #HindiNews #India #NewsToday #TopNews #NewsCompilation
5. **Keywords**: SEO keywords for discoverability
6. **About Section**: Channel description
7. **Disclaimer**: Informational purposes

### Example Description:

```
Welcome to this Morning's top news compilation! Here are the 20 most important headlines you need to know about today.

📋 NEWS HEADLINES:
1. [0:00] Stock Market Hits All-Time High as Sensex Crosses 70,000 Mark
2. [0:30] India Wins Cricket World Cup Final Against Australia
3. [1:00] New AI Technology Revolutionizes Healthcare Diagnosis
4. [1:30] Government Announces New Tax Relief for Middle Class
5. [2:00] Bollywood Star Announces Retirement from Acting
...
20. [9:30] Weather Alert: Heavy Rainfall Expected in Northern States

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 SUBSCRIBE for Daily News Updates!
👍 LIKE if you found this informative
💬 COMMENT your thoughts below
🔗 SHARE with friends and family
━━━━━━━━━━━━━━━━━━━━━━━━━━

#News #BreakingNews #LatestNews #HindiNews #India #NewsToday #TopNews #NewsCompilation

━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 KEYWORDS:
top news, latest news, breaking news, news today, morning news, hindi news, india news, news compilation, current affairs, news update

━━━━━━━━━━━━━━━━━━━━━━━━━━
📢 About This Channel:
Stay updated with the latest news from India and around the world.
We bring you breaking news, current affairs, and in-depth analysis.

⚠️ Disclaimer:
This content is for informational purposes only.
```

## Tags

The following tags are automatically added:

1. news compilation
2. top news
3. latest news
4. breaking news
5. hindi news
6. news today
7. morning news / afternoon news / evening news / night news (based on time)
8. india news
9. current affairs
10. news update
11. daily news

## Privacy Settings

Videos are uploaded as **private** by default. You can:
- Review them in YouTube Studio
- Manually change to public/unlisted when ready
- Edit title/description if needed

## API Response

### Success Response:
```json
{
  "status": "success",
  "message": "Successfully uploaded compilation of 20 news items",
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "video_id": "VIDEO_ID",
  "title": "📰 Top 20 News: This Morning's Top Headlines | 24 November 2024",
  "news_count": 20
}
```

### Error Response:
```json
{
  "status": "error",
  "error": "No merged video found. Please generate merged video first using /merge-latest endpoint."
}
```

## Timestamps in Description

Each news item gets a timestamp based on its position:
- News 1: 0:00
- News 2: 0:30
- News 3: 1:00
- News 4: 1:30
- ...
- News 20: 9:30

This assumes each news segment is approximately 30 seconds long.

## SEO Optimization

### Title SEO:
- Front-loads "Top 20 News" keyword
- Includes time of day for freshness
- Includes date for relevance
- Uses emoji for visual appeal
- Under 100 characters

### Description SEO:
- First 2 lines are engaging hook
- Includes all news titles (keyword-rich)
- Natural keyword integration
- Hashtags for discoverability
- Keywords section for search

### Tags SEO:
- Mix of broad ("news") and specific ("news compilation")
- Time-based tags ("morning news")
- Regional tags ("india news", "hindi news")
- Trending tags ("breaking news", "latest news")

## Best Practices

1. **Generate merged video first** before uploading
2. **Review video in YouTube Studio** before making public
3. **Upload during peak hours** for better initial engagement
4. **Consistent schedule** (e.g., morning and evening compilations daily)
5. **Monitor analytics** to optimize upload times and content

## Troubleshooting

### "No merged video found"
- Run `/merge-latest` endpoint first to generate compilation video
- Check that video file exists in `jobs/video-generator/public/`

### "Upload failed"
- Check YouTube API credentials in `credentials/client_secrets.json`
- Verify OAuth authentication is complete
- Check video file is valid MP4 format
- Check file size is under YouTube's limit (256 GB)

### "LLM service timeout"
- LLM is not used for compilation uploads (only for individual news)
- Compilation uses template-based metadata generation

## Future Enhancements

1. **Custom thumbnails**: Auto-generate compilation thumbnails
2. **Chapters**: Add YouTube chapters for each news item
3. **Playlists**: Auto-organize into daily/weekly playlists
4. **Scheduling**: Schedule uploads for optimal times
5. **Analytics**: Track which news items get most engagement

