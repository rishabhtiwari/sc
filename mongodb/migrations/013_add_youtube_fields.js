// Migration: 013_add_youtube_fields.js
// Description: Add YouTube upload tracking fields to news_document collection
// Created: 2025-11-24

print('Starting migration: 013_add_youtube_fields');

// Switch to news database
db = db.getSiblingDB('news');

// Add YouTube fields to existing news documents with null values
print('Adding YouTube fields to existing news documents...');

const updateResult = db.news_document.updateMany(
    { 
        youtube_video_id: { $exists: false }
    },
    { 
        $set: { 
            youtube_video_id: null,
            youtube_video_url: null,
            youtube_uploaded_at: null,
            updated_at: new Date()
        } 
    }
);

print(`✓ Updated ${updateResult.modifiedCount} existing news documents with YouTube fields`);

// Create index on youtube_video_id field for better query performance
print('Creating index on youtube_video_id field...');
db.news_document.createIndex({ "youtube_video_id": 1 });
print('✓ Created index on youtube_video_id field');

// Create compound index for finding videos ready to upload
print('Creating compound index for upload workflow...');
db.news_document.createIndex({ 
    "video_path": 1, 
    "youtube_video_id": 1
}, {
    name: "youtube_upload_workflow_index"
});
print('✓ Created YouTube upload workflow index');

print('✓ Migration 013_add_youtube_fields completed successfully');

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
//     "clean_image": "string (path to watermark-removed image file, null if not cleaned)",
//     "youtube_video_id": "string (YouTube video ID, null if not uploaded)",
//     "youtube_video_url": "string (YouTube video URL, null if not uploaded)",
//     "youtube_uploaded_at": "Date (when video was uploaded to YouTube, null if not uploaded)",
//     "created_at": "Date (when record was created)",
//     "updated_at": "Date (when record was last updated)",
//     "enriched_at": "Date (when article was enriched with summary)"
// }

