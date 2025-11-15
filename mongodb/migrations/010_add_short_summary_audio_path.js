// Migration: 010_add_short_summary_audio_path.js
// Description: Add short_summary audio path to existing audio_paths structure in news_document collection
// Created: 2025-11-15

print('Starting migration: 010_add_short_summary_audio_path');

// Switch to news database
db = db.getSiblingDB('news');

// Update existing documents that have audio_paths but missing short_summary
print('Adding short_summary to existing audio_paths...');

const updateResult = db.news_document.updateMany(
    { 
        'audio_paths': { $exists: true, $ne: null },
        'audio_paths.short_summary': { $exists: false }
    },
    { 
        $set: { 
            'audio_paths.short_summary': null,
            'updated_at': new Date()
        } 
    }
);

print(`✓ Updated ${updateResult.modifiedCount} existing documents with short_summary audio path`);

// Also update documents that have null audio_paths to include the short_summary field structure
print('Initializing audio_paths structure for documents with null audio_paths...');

const initResult = db.news_document.updateMany(
    { 
        $or: [
            { 'audio_paths': null },
            { 'audio_paths': { $exists: false } }
        ]
    },
    { 
        $set: { 
            'audio_paths': {
                'title': null,
                'description': null,
                'content': null,
                'short_summary': null
            },
            'updated_at': new Date()
        } 
    }
);

print(`✓ Initialized audio_paths structure for ${initResult.modifiedCount} documents`);

// Create index for short_summary audio path queries
print('Creating index for short_summary audio path...');
db.news_document.createIndex({ "audio_paths.short_summary": 1 });
print('✓ Created index on audio_paths.short_summary field');

// Create compound index for audio generation workflow including short_summary
print('Creating compound index for audio generation workflow...');
db.news_document.createIndex({ 
    "audio_paths.title": 1,
    "audio_paths.description": 1, 
    "audio_paths.content": 1,
    "audio_paths.short_summary": 1,
    "status": 1
}, {
    name: "audio_generation_workflow_index"
});
print('✓ Created audio generation workflow index');

print('✓ Migration 010_add_short_summary_audio_path completed successfully');

// Updated schema structure for news_document collection audio_paths:
// {
//     "audio_paths": {
//         "title": "string (path to title audio file, null if not generated)",
//         "description": "string (path to description audio file, null if not generated)",
//         "content": "string (path to content audio file, null if not generated)",
//         "short_summary": "string (path to short_summary audio file, null if not generated)"
//     }
// }
