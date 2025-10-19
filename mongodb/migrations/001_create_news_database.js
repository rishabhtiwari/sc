// Migration: 001_create_news_database.js
// Description: Create news database with news_document collection
// Created: 2025-10-18

print('Starting migration: 001_create_news_database');

// Switch to news database (will create it if it doesn't exist)
use news;

// Create news_document collection
db.createCollection('news_document');

// Create only essential indexes for common queries
db.getCollection('news_document').createIndex({ "id": 1 }, { unique: true }); // Primary key
db.getCollection('news_document').createIndex({ "publishedAt": -1 }); // Most recent articles first
db.getCollection('news_document').createIndex({ "status": 1 }); // Filter by status (published/draft/etc)
// Create text search index for title and description
try {
    db.getCollection('news_document').createIndex({
        "title": "text",
        "description": "text"
    }, {
        name: "text_search_index",
        default_language: "english"
    });
    print('✓ Created text search index');
} catch (e) {
    print('⚠ Text search index creation failed: ' + e.message);
}
print('✓ Created news_document collection with essential indexes');

// Schema structure for news_document collection:
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
//     "status": "string (published, draft, archived, deleted)",
//     "short_summary": "string (concise article summary)",
//     "created_at": "Date (record creation timestamp)",
//     "updated_at": "Date (record update timestamp)"
// }

print('✓ News document collection created');
print('Migration 001_create_news_database completed successfully');
