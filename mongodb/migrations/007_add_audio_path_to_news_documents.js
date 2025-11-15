// Migration: 005_add_audio_path_to_news_documents.js
// Description: Add audio_path field to news_document collection for voice generation
// Created: 2025-11-09

print('Starting migration: 005_add_audio_path_to_news_documents');

// Switch to news database
db = db.getSiblingDB('news');

// Add audio_path field to existing news documents with null value
print('Adding audio_path field to existing news documents...');

const updateResult = db.news_document.updateMany(
    { audio_path: { $exists: false } }, // Only update documents that don't have audio_path field
    { 
        $set: { 
            audio_path: null,
            updated_at: new Date()
        } 
    }
);

print(`✓ Updated ${updateResult.modifiedCount} existing news documents with audio_path field`);

// Create index on audio_path field for better query performance
print('Creating index on audio_path field...');
db.news_document.createIndex({ "audio_path": 1 });
print('✓ Created index on audio_path field');

// Create compound index for status + audio_path for finding articles that need audio generation
print('Creating compound index on status and audio_path...');
db.news_document.createIndex({ "status": 1, "audio_path": 1 });
print('✓ Created compound index on status and audio_path');

print('✓ Migration 005_add_audio_path_to_news_documents completed successfully');

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
//     "created_at": "Date (when record was created)",
//     "updated_at": "Date (when record was last updated)",
//     "enriched_at": "Date (when article was enriched with summary)"
// }
