// Migration: 006_add_progress_fields_to_voice_requests.js
// Description: Add progress tracking fields to voice_requests collection
// Date: 2025-10-22

print('Starting migration: 006_add_progress_fields_to_voice_requests');

// Switch to ichat_db database
use ichat_db;

// Add progress fields to existing voice_requests documents
// Set default values for existing records
db.getCollection('voice_requests').updateMany(
    { 
        progress_percentage: { $exists: false } 
    },
    { 
        $set: { 
            progress_percentage: 0,
            progress_message: "Pending"
        } 
    }
);

print('✓ Added progress fields to existing voice_requests documents');

// Create index for progress_percentage for efficient filtering
db.getCollection('voice_requests').createIndex({ "progress_percentage": 1 });

print('✓ Created index for progress_percentage field');

// Updated schema structure for voice_requests collection:
// {
//     "request_id": "string (unique identifier for the voice generation request)",
//     "reference_audio_path": "string (path to the reference audio file)",
//     "text_script": "string (text to be spoken in the cloned voice)",
//     "language": "string (language code, default: 'en')",
//     "generated_audio_path": "string (path to generated audio file, null until completed)",
//     "status": "string (pending, processing, completed, failed)",
//     "progress_percentage": "number (0-100, progress percentage for processing status)",
//     "progress_message": "string (current progress message, e.g., 'Analyzing reference voice...')",
//     "created_at": "Date (when request was created)",
//     "updated_at": "Date (when request was last updated)",
//     "started_at": "Date (when processing started, null if not started)",
//     "completed_at": "Date (when processing completed, null if not completed)",
//     "error_message": "string (error message if processing failed, null if successful)",
//     "metadata": "object (additional metadata like file sizes, processing time, etc.)"
// }

print('✓ Progress tracking fields added to voice_requests collection');
print('Migration 006_add_progress_fields_to_voice_requests completed successfully');
