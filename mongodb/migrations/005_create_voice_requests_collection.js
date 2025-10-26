// Migration: 005_create_voice_requests_collection.js
// Description: Create voice_requests collection for voice generation job
// Date: 2025-10-21

print('Starting migration: 005_create_voice_requests_collection');

// Switch to ichat_db database
use ichat_db;

// Create voice_requests collection
db.createCollection('voice_requests');

// Create indexes for the voice_requests collection
db.getCollection('voice_requests').createIndex({ "request_id": 1 }, { unique: true }); // Unique request ID
db.getCollection('voice_requests').createIndex({ "status": 1 }); // Filter by status (pending, processing, completed, failed)
db.getCollection('voice_requests').createIndex({ "created_at": 1 }); // Sort by creation time
db.getCollection('voice_requests').createIndex({ "updated_at": 1 }); // Sort by update time
db.getCollection('voice_requests').createIndex({ "status": 1, "created_at": 1 }); // Compound index for processing queue

print('✓ Created voice_requests collection with indexes');

// Schema structure for voice_requests collection:
// {
//     "request_id": "string (unique identifier for the voice generation request)",
//     "reference_audio_path": "string (path to the reference audio file)",
//     "text_script": "string (text to be spoken in the cloned voice)",
//     "language": "string (language code, default: 'en')",
//     "generated_audio_path": "string (path to generated audio file, null until completed)",
//     "status": "string (pending, processing, completed, failed)",
//     "created_at": "Date (when request was created)",
//     "updated_at": "Date (when request was last updated)",
//     "started_at": "Date (when processing started, null if not started)",
//     "completed_at": "Date (when processing completed, null if not completed)",
//     "error_message": "string (error message if processing failed, null if successful)",
//     "metadata": "object (additional metadata like file sizes, processing time, etc.)"
// }

print('✓ Voice requests collection created for voice generation job');
print('Migration 005_create_voice_requests_collection completed successfully');
