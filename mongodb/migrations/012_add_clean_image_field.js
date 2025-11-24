// Migration: 012_add_clean_image_field.js
// Description: Add clean_image field to news_document collection for watermark-removed images
// Created: 2025-11-23

print('Starting migration: 012_add_clean_image_field');

// Switch to news database
use news;

// Add clean_image field to all existing documents (set to null initially)
db.getCollection('news_document').updateMany(
    { clean_image: { $exists: false } },
    { 
        $set: { 
            clean_image: null,
            clean_image_updated_at: null
        } 
    }
);

print('✓ Added clean_image field to existing documents');

// Create index for querying documents without clean images
db.getCollection('news_document').createIndex(
    { "clean_image": 1 },
    { name: "clean_image_index" }
);

print('✓ Created index on clean_image field');

print('✓ Migration 012_add_clean_image_field completed successfully');

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
//     "clean_image_updated_at": "Date (when clean_image was last updated)",
//     "created_at": "Date (when record was created)",
//     "updated_at": "Date (when record was last updated)",
//     "enriched_at": "Date (when article was enriched with summary)"
// }

