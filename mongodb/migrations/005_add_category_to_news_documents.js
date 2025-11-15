// Migration: 004_add_category_to_news_documents.js
// Description: Add category field to news_document collection and update existing records
// Created: 2025-10-20

print('Starting migration: 004_add_category_to_news_documents');

// Switch to news database
use news;

// Add category field to existing news documents with default value 'general'
print('Adding category field to existing news documents...');

const updateResult = db.news_document.updateMany(
    { category: { $exists: false } }, // Only update documents that don't have category field
    { 
        $set: { 
            category: 'general',
            updated_at: new Date()
        } 
    }
);

print(`✓ Updated ${updateResult.modifiedCount} existing news documents with default category 'general'`);

// Create index on category field for better query performance
print('Creating index on category field...');
db.news_document.createIndex({ "category": 1 });
print('✓ Created index on category field');

// Create compound index for category + created_at for efficient sorting
print('Creating compound index on category and created_at...');
db.news_document.createIndex({ "category": 1, "created_at": -1 });
print('✓ Created compound index on category and created_at');

// Create compound index for status + category + created_at for filtering completed articles by category
print('Creating compound index on status, category and created_at...');
db.news_document.createIndex({ "status": 1, "category": 1, "created_at": -1 });
print('✓ Created compound index on status, category and created_at');

print('✓ Migration 004_add_category_to_news_documents completed successfully');

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
//     "created_at": "Date (when record was created)",
//     "updated_at": "Date (when record was last updated)",
//     "enriched_at": "Date (when article was enriched with summary)"
// }
