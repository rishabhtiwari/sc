// Migration: 044_create_music_library_collection.js
// Description: Create music_library collection for AI Music Generator feature
// Created: 2025-12-31

print('Starting migration: 044_create_music_library_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create music_library collection with schema validation
db.createCollection('music_library', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['music_id', 'customer_id', 'user_id', 'name', 'url', 'created_at'],
            properties: {
                music_id: {
                    bsonType: 'string',
                    description: 'Unique music identifier - required'
                },
                customer_id: {
                    bsonType: 'string',
                    description: 'Customer ID for multi-tenant support - required'
                },
                user_id: {
                    bsonType: 'string',
                    description: 'User ID who created the music - required'
                },
                name: {
                    bsonType: 'string',
                    description: 'Music track name - required'
                },
                description: {
                    bsonType: 'string',
                    description: 'Music description'
                },
                genre: {
                    bsonType: 'string',
                    description: 'Music genre (electronic, rock, ambient, etc.)'
                },
                mood: {
                    bsonType: 'string',
                    description: 'Music mood (upbeat, calm, energetic, etc.)'
                },
                url: {
                    bsonType: 'string',
                    description: 'S3/Storage URL of the music file - required'
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
                bpm: {
                    bsonType: 'int',
                    minimum: 0,
                    description: 'Beats per minute'
                },
                key: {
                    bsonType: 'string',
                    description: 'Musical key (C major, A minor, etc.)'
                },
                generation_config: {
                    bsonType: 'object',
                    description: 'Configuration used for generation',
                    properties: {
                        provider: {
                            bsonType: 'string',
                            enum: ['musicgen', 'stable_audio', 'mubert'],
                            description: 'AI provider used'
                        },
                        model: {
                            bsonType: 'string',
                            description: 'Model name/version'
                        },
                        prompt: {
                            bsonType: 'string',
                            description: 'Text prompt used for generation'
                        },
                        duration: {
                            bsonType: 'int',
                            description: 'Requested duration in seconds'
                        },
                        temperature: {
                            bsonType: 'double',
                            description: 'Generation temperature'
                        },
                        top_k: {
                            bsonType: 'int',
                            description: 'Top-k sampling parameter'
                        },
                        top_p: {
                            bsonType: 'double',
                            description: 'Top-p sampling parameter'
                        },
                        preset: {
                            bsonType: 'string',
                            description: 'Preset name if used'
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
                is_royalty_free: {
                    bsonType: 'bool',
                    description: 'Whether music is royalty-free'
                },
                license_type: {
                    bsonType: 'string',
                    description: 'License type (personal, commercial, etc.)'
                },
                usage_count: {
                    bsonType: 'int',
                    minimum: 0,
                    description: 'Number of times music has been used'
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
print('✓ Created music_library collection with schema validation');

// Create indexes
db.music_library.createIndex(
    { music_id: 1 },
    { unique: true, name: 'idx_music_id' }
);
print('✓ Created unique index: music_id');

db.music_library.createIndex(
    { customer_id: 1, user_id: 1, created_at: -1 },
    { name: 'idx_customer_user_created' }
);
print('✓ Created compound index: customer_id + user_id + created_at');

db.music_library.createIndex(
    { customer_id: 1, genre: 1 },
    { name: 'idx_customer_genre' }
);
print('✓ Created compound index: customer_id + genre');

db.music_library.createIndex(
    { customer_id: 1, mood: 1 },
    { name: 'idx_customer_mood' }
);
print('✓ Created compound index: customer_id + mood');

db.music_library.createIndex(
    { tags: 1 },
    { name: 'idx_tags' }
);
print('✓ Created index: tags');

db.music_library.createIndex(
    { duration: 1 },
    { name: 'idx_duration' }
);
print('✓ Created index: duration');

db.music_library.createIndex(
    { bpm: 1 },
    { name: 'idx_bpm' }
);
print('✓ Created index: bpm');

db.music_library.createIndex(
    { is_deleted: 1 },
    { name: 'idx_is_deleted' }
);
print('✓ Created index: is_deleted');

print('Migration 044_create_music_library_collection completed successfully');

