// Migration: 009_add_video_path_to_news_documents.js
// Description: Add video_path field to news_document collection for video generation
// Created: 2025-11-15

print('Starting migration: 009_add_video_path_to_news_documents');

// Switch to news database
db = db.getSiblingDB('news');

// Add video_path field to existing news documents with null value
print('Adding video_path field to existing news documents...');

const updateResult = db.news_document.updateMany(
    { video_path: { $exists: false } }, // Only update documents that don't have video_path field
    { 
        $set: { 
            video_path: null,
            updated_at: new Date()
        } 
    }
);

print(`✓ Updated ${updateResult.modifiedCount} existing news documents with video_path field`);

// Create index on video_path field for better query performance
print('Creating index on video_path field...');
db.news_document.createIndex({ "video_path": 1 });
print('✓ Created index on video_path field');

// Create compound index for status + audio_path + video_path for finding articles that need video generation
print('Creating compound index on status, audio_path and video_path...');
db.news_document.createIndex({ "status": 1, "audio_path": 1, "video_path": 1 });
print('✓ Created compound index on status, audio_path and video_path');

// Create compound index for video generation workflow
print('Creating index for video generation workflow...');
db.news_document.createIndex({ 
    "audio_path": 1, 
    "video_path": 1, 
    "image": 1 
}, {
    name: "video_generation_workflow_index"
});
print('✓ Created video generation workflow index');

print('✓ Migration 008_add_video_path_to_news_documents completed successfully');

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
//     "audio_path": "string (path to generated audio file, null if not generated)",
//     "video_path": "string (path to generated video file, null if not generated)",
//     "created_at": "Date (when record was created)",
//     "updated_at": "Date (when record was last updated)",
//     "enriched_at": "Date (when article was enriched with summary)"
// }
