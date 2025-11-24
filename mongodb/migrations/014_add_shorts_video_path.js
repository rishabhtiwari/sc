// Migration: 014_add_shorts_video_path.js
// Description: Add shorts_video_path field to news_document collection for YouTube Shorts generation
// Created: 2025-11-24

print('Starting migration: 014_add_shorts_video_path');

// Switch to news database
db = db.getSiblingDB('news');

// Add shorts_video_path field to existing news documents with null value
print('Adding shorts_video_path field to existing news documents...');

const updateResult = db.news_document.updateMany(
    { shorts_video_path: { $exists: false } }, // Only update documents that don't have shorts_video_path field
    { 
        $set: { 
            shorts_video_path: null,
            updated_at: new Date()
        } 
    }
);

print(`✓ Updated ${updateResult.modifiedCount} documents with shorts_video_path field`);

// Create index on shorts_video_path for efficient queries
print('Creating index on shorts_video_path...');
db.news_document.createIndex({ "shorts_video_path": 1 });
print('✓ Created index on shorts_video_path');

print('Migration completed successfully: 014_add_shorts_video_path');

// Updated schema structure for news_document collection:
// {
//     "id": "string (unique identifier)",
//     "title": "string (article title)",
//     "description": "string (article description)",
//     "content": "string (full article content)",
//     "url": "string (article URL)",
//     "image": "string (article image URL)",
//     "publishedAt": "string (ISO date)",
//     "lang": "string (language code)",
//     "source": {
//         "id": "string (source identifier)",
//         "name": "string (source name)",
//         "url": "string (source URL)",
//         "country": "string (country code)"
//     },
//     "status": "string (published, draft, archived, deleted, completed)",
//     "category": "string (news category: general, business, entertainment, health, science, sports, technology)",
//     "short_summary": "string (concise article summary)",
//     "audio_paths": {
//         "title": "string (path to title audio file, null if not generated)",
//         "description": "string (path to description audio file, null if not generated)",
//         "content": "string (path to content audio file, null if not generated)",
//         "short_summary": "string (path to short_summary audio file, null if not generated)"
//     },
//     "video_path": "string (path to generated video file, null if not generated)",
//     "shorts_video_path": "string (path to generated YouTube Shorts video file, null if not generated)",
//     "clean_image": "string (path to watermark-removed image file, null if not cleaned)",
//     "youtube_video_id": "string (YouTube video ID if uploaded, null if not uploaded)",
//     "youtube_uploaded_at": "Date (when video was uploaded to YouTube, null if not uploaded)",
//     "created_at": "Date (when record was created)",
//     "updated_at": "Date (when record was last updated)",
//     "enriched_at": "Date (when article was enriched with summary)"
// }

