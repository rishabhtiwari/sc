// Migration: 042_create_audio_library_collection.js
// Description: Create audio_library collection for Audio Studio
// Created: 2025-12-31

print('Starting migration: 042_create_audio_library_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create audio_library collection with schema validation
db.createCollection('audio_library', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['audio_id', 'customer_id', 'user_id', 'name', 'type', 'source', 'url', 'created_at'],
            properties: {
                audio_id: {
                    bsonType: 'string',
                    description: 'Unique audio identifier - required'
                },
                customer_id: {
                    bsonType: 'string',
                    description: 'Customer ID for multi-tenant support - required'
                },
                user_id: {
                    bsonType: 'string',
                    description: 'User ID who created the audio - required'
                },
                name: {
                    bsonType: 'string',
                    description: 'Audio file name - required'
                },
                type: {
                    bsonType: 'string',
                    enum: ['voiceover', 'music', 'sound_effect'],
                    description: 'Type of audio - required'
                },
                source: {
                    bsonType: 'string',
                    enum: ['tts', 'ai_voice', 'ai_music', 'cloned', 'uploaded'],
                    description: 'Source of audio generation - required'
                },
                url: {
                    bsonType: 'string',
                    description: 'S3/Storage URL of the audio file - required'
                },
                duration: {
                    bsonType: 'double',
                    minimum: 0,
                    description: 'Duration in seconds'
                },
                format: {
                    bsonType: 'string',
                    description: 'Audio format (wav, mp3, etc.)'
                },
                size: {
                    bsonType: 'long',
                    minimum: 0,
                    description: 'File size in bytes'
                },
                generation_config: {
                    bsonType: 'object',
                    description: 'Configuration used for generation (for regeneration)',
                    properties: {
                        provider: {
                            bsonType: 'string',
                            enum: ['kokoro', 'elevenlabs', 'musicgen', 'xtts'],
                            description: 'AI provider used'
                        },
                        model: {
                            bsonType: 'string',
                            description: 'Model name/version'
                        },
                        voice: {
                            bsonType: 'string',
                            description: 'Voice ID used'
                        },
                        text: {
                            bsonType: 'string',
                            description: 'Original text for TTS'
                        },
                        settings: {
                            bsonType: 'object',
                            description: 'Generation settings',
                            properties: {
                                speed: {
                                    bsonType: 'double',
                                    description: 'Speech speed'
                                },
                                pitch: {
                                    bsonType: 'int',
                                    description: 'Pitch adjustment'
                                },
                                stability: {
                                    bsonType: 'double',
                                    description: 'Voice stability'
                                },
                                clarity: {
                                    bsonType: 'double',
                                    description: 'Voice clarity'
                                }
                            }
                        }
                    }
                },
                tags: {
                    bsonType: 'array',
                    items: {
                        bsonType: 'string'
                    },
                    description: 'Tags for categorization'
                },
                folder: {
                    bsonType: 'string',
                    description: 'Folder/category name'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Creation timestamp - required'
                },
                updated_at: {
                    bsonType: 'date',
                    description: 'Last update timestamp'
                },
                is_deleted: {
                    bsonType: 'bool',
                    description: 'Soft delete flag'
                },
                deleted_at: {
                    bsonType: 'date',
                    description: 'Deletion timestamp'
                }
            }
        }
    }
});
print('✓ Created audio_library collection with schema validation');

// Create indexes
db.audio_library.createIndex(
    { audio_id: 1 },
    { unique: true, name: 'idx_audio_id' }
);
print('✓ Created unique index: audio_id');

db.audio_library.createIndex(
    { customer_id: 1, user_id: 1, created_at: -1 },
    { name: 'idx_customer_user_created' }
);
print('✓ Created compound index: customer_id + user_id + created_at');

db.audio_library.createIndex(
    { customer_id: 1, type: 1 },
    { name: 'idx_customer_type' }
);
print('✓ Created compound index: customer_id + type');

db.audio_library.createIndex(
    { customer_id: 1, source: 1 },
    { name: 'idx_customer_source' }
);
print('✓ Created compound index: customer_id + source');

db.audio_library.createIndex(
    { tags: 1 },
    { name: 'idx_tags' }
);
print('✓ Created index: tags');

db.audio_library.createIndex(
    { folder: 1 },
    { name: 'idx_folder' }
);
print('✓ Created index: folder');

db.audio_library.createIndex(
    { is_deleted: 1 },
    { name: 'idx_is_deleted' }
);
print('✓ Created index: is_deleted');

print('Migration 042_create_audio_library_collection completed successfully');

