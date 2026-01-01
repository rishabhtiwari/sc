// Migration: 043_create_cloned_voices_collection.js
// Description: Create cloned_voices collection for Voice Cloning feature
// Created: 2025-12-31

print('Starting migration: 043_create_cloned_voices_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create cloned_voices collection with schema validation
db.createCollection('cloned_voices', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['voice_id', 'customer_id', 'user_id', 'name', 'status', 'created_at'],
            properties: {
                voice_id: {
                    bsonType: 'string',
                    description: 'Unique voice identifier - required'
                },
                customer_id: {
                    bsonType: 'string',
                    description: 'Customer ID for multi-tenant support - required'
                },
                user_id: {
                    bsonType: 'string',
                    description: 'User ID who created the voice clone - required'
                },
                name: {
                    bsonType: 'string',
                    description: 'Voice clone name - required'
                },
                description: {
                    bsonType: 'string',
                    description: 'Voice clone description'
                },
                reference_audios: {
                    bsonType: 'array',
                    description: 'Array of reference audio files',
                    items: {
                        bsonType: 'object',
                        required: ['url', 'duration', 'uploaded_at'],
                        properties: {
                            url: {
                                bsonType: 'string',
                                description: 'S3/Storage URL of reference audio'
                            },
                            duration: {
                                bsonType: 'double',
                                minimum: 0,
                                description: 'Duration in seconds'
                            },
                            uploaded_at: {
                                bsonType: 'date',
                                description: 'Upload timestamp'
                            },
                            format: {
                                bsonType: 'string',
                                description: 'Audio format'
                            },
                            size: {
                                bsonType: 'long',
                                description: 'File size in bytes'
                            }
                        }
                    }
                },
                status: {
                    bsonType: 'string',
                    enum: ['pending', 'training', 'trained', 'failed'],
                    description: 'Training status - required'
                },
                training_started_at: {
                    bsonType: 'date',
                    description: 'Training start timestamp'
                },
                training_completed_at: {
                    bsonType: 'date',
                    description: 'Training completion timestamp'
                },
                training_error: {
                    bsonType: 'string',
                    description: 'Error message if training failed'
                },
                characteristics: {
                    bsonType: 'object',
                    description: 'Auto-detected voice characteristics',
                    properties: {
                        gender: {
                            bsonType: 'string',
                            enum: ['male', 'female', 'neutral', 'unknown'],
                            description: 'Detected gender'
                        },
                        age_range: {
                            bsonType: 'string',
                            enum: ['child', 'young_adult', 'adult', 'senior', 'unknown'],
                            description: 'Detected age range'
                        },
                        accent: {
                            bsonType: 'string',
                            description: 'Detected accent'
                        },
                        quality_score: {
                            bsonType: 'double',
                            minimum: 0,
                            maximum: 1,
                            description: 'Voice quality score (0-1)'
                        },
                        clarity_score: {
                            bsonType: 'double',
                            minimum: 0,
                            maximum: 1,
                            description: 'Audio clarity score (0-1)'
                        },
                        background_noise_level: {
                            bsonType: 'double',
                            minimum: 0,
                            maximum: 1,
                            description: 'Background noise level (0-1)'
                        }
                    }
                },
                sample_text: {
                    bsonType: 'string',
                    description: 'Sample text for voice preview'
                },
                sample_audio: {
                    bsonType: 'string',
                    description: 'S3/Storage URL of sample audio'
                },
                usage_count: {
                    bsonType: 'int',
                    minimum: 0,
                    description: 'Number of times voice has been used'
                },
                last_used_at: {
                    bsonType: 'date',
                    description: 'Last usage timestamp'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Creation timestamp - required'
                },
                updated_at: {
                    bsonType: 'date',
                    description: 'Last update timestamp'
                },
                is_active: {
                    bsonType: 'bool',
                    description: 'Whether voice is active'
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
print('✓ Created cloned_voices collection with schema validation');

// Create indexes
db.cloned_voices.createIndex(
    { voice_id: 1 },
    { unique: true, name: 'idx_voice_id' }
);
print('✓ Created unique index: voice_id');

db.cloned_voices.createIndex(
    { customer_id: 1, user_id: 1, created_at: -1 },
    { name: 'idx_customer_user_created' }
);
print('✓ Created compound index: customer_id + user_id + created_at');

db.cloned_voices.createIndex(
    { customer_id: 1, status: 1 },
    { name: 'idx_customer_status' }
);
print('✓ Created compound index: customer_id + status');

db.cloned_voices.createIndex(
    { customer_id: 1, is_active: 1 },
    { name: 'idx_customer_active' }
);
print('✓ Created compound index: customer_id + is_active');

db.cloned_voices.createIndex(
    { usage_count: -1 },
    { name: 'idx_usage_count' }
);
print('✓ Created index: usage_count (descending)');

db.cloned_voices.createIndex(
    { is_deleted: 1 },
    { name: 'idx_is_deleted' }
);
print('✓ Created index: is_deleted');

print('Migration 043_create_cloned_voices_collection completed successfully');

