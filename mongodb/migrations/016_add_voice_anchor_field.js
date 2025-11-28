// Migration: 016_add_voice_anchor_field.js
// Description: Add voice/anchor field to news_document collection to track which voice (male/female) was used for audio generation
// Created: 2025-11-28

print('Starting migration: 016_add_voice_anchor_field');

// Switch to news database
db = db.getSiblingDB('news');

// Add voice field to existing news documents with null value
print('Adding voice field to existing news documents...');

const updateResult = db.news_document.updateMany(
    { 
        voice: { $exists: false }
    },
    { 
        $set: { 
            voice: null,  // Will be 'male' or 'female' or specific voice name like 'am_adam', 'af_bella'
            voice_updated_at: null,
            updated_at: new Date()
        } 
    }
);

print(`✓ Updated ${updateResult.modifiedCount} existing news documents with voice field`);

// Create index on voice field for better query performance
print('Creating index on voice field...');
db.news_document.createIndex({ "voice": 1 });
print('✓ Created index on voice field');

// Create compound index for finding news by voice and creation date
print('Creating compound index for voice and created_at...');
db.news_document.createIndex({ 
    "voice": 1, 
    "created_at": -1
}, {
    name: "voice_created_at_index"
});
print('✓ Created voice and created_at compound index');

print('✓ Migration 016_add_voice_anchor_field completed successfully');

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
//     "voice": "string (voice used for audio generation: 'male', 'female', or specific voice name like 'am_adam', 'af_bella', null if not generated)",
//     "voice_updated_at": "Date (when voice was last updated, null if not set)",
//     "youtube_video_id": "string (YouTube video ID, null if not uploaded)",
//     "youtube_video_url": "string (YouTube video URL, null if not uploaded)",
//     "youtube_uploaded_at": "Date (when video was uploaded to YouTube, null if not uploaded)",
//     "youtube_shorts_id": "string (YouTube Shorts video ID, null if not uploaded)",
//     "youtube_shorts_url": "string (YouTube Shorts video URL, null if not uploaded)",
//     "youtube_shorts_uploaded_at": "Date (when shorts was uploaded to YouTube, null if not uploaded)",
//     "created_at": "Date (when record was created)",
//     "updated_at": "Date (when record was last updated)",
//     "deleted_at": "Date (when record was soft deleted, null if not deleted)"
// }

