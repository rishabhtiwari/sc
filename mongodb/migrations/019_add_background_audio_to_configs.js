// Migration: 019_add_background_audio_to_configs.js
// Description: Add backgroundAudioId field to long_video_configs collection for custom background audio selection
// Created: 2025-12-15

print('Starting migration: 019_add_background_audio_to_configs');

// Switch to news database
db = db.getSiblingDB('news');

// Update existing documents to add backgroundAudioId field (set to null by default)
const result = db.getCollection('long_video_configs').updateMany(
    { backgroundAudioId: { $exists: false } },
    { $set: { backgroundAudioId: null } }
);

print('✓ Updated ' + result.modifiedCount + ' existing documents with backgroundAudioId field');

// Update schema validation to include backgroundAudioId
db.runCommand({
    collMod: 'long_video_configs',
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['title', 'videoCount', 'status', 'createdAt', 'frequency'],
            properties: {
                title: {
                    bsonType: 'string',
                    description: 'Video title - required'
                },
                categories: {
                    bsonType: 'array',
                    description: 'List of categories to filter',
                    items: {
                        bsonType: 'string'
                    }
                },
                country: {
                    bsonType: 'string',
                    description: 'Country code filter (e.g., us, in, uk)'
                },
                language: {
                    bsonType: 'string',
                    description: 'Language code filter (e.g., en, hi, es)'
                },
                videoCount: {
                    bsonType: 'int',
                    minimum: 1,
                    maximum: 100,
                    description: 'Number of videos to merge - required'
                },
                frequency: {
                    enum: ['none', 'hourly', 'daily', 'weekly', 'monthly'],
                    description: 'Frequency for automatic re-computation - required'
                },
                status: {
                    enum: ['pending', 'processing', 'completed', 'failed', 'unknown'],
                    description: 'Current status - required'
                },
                videoPath: {
                    bsonType: ['string', 'null'],
                    description: 'Path to merged video file'
                },
                thumbnailPath: {
                    bsonType: ['string', 'null'],
                    description: 'Path to video thumbnail'
                },
                youtubeVideoId: {
                    bsonType: ['string', 'null'],
                    description: 'YouTube video ID after upload'
                },
                youtubeVideoUrl: {
                    bsonType: ['string', 'null'],
                    description: 'YouTube video URL after upload'
                },
                backgroundAudioId: {
                    bsonType: ['string', 'null'],
                    description: 'Filename of custom background audio from assets directory (e.g., "my_music.wav")'
                },
                createdAt: {
                    bsonType: 'date',
                    description: 'Creation timestamp - required'
                },
                updatedAt: {
                    bsonType: 'date',
                    description: 'Last update timestamp'
                },
                lastRunTime: {
                    bsonType: ['date', 'null'],
                    description: 'Last time video was computed'
                },
                nextRunTime: {
                    bsonType: ['date', 'null'],
                    description: 'Next scheduled run time'
                },
                mergeStartedAt: {
                    bsonType: ['date', 'null'],
                    description: 'When merge process started'
                },
                mergeCompletedAt: {
                    bsonType: ['date', 'null'],
                    description: 'When merge process completed'
                },
                uploadedAt: {
                    bsonType: ['date', 'null'],
                    description: 'When video was uploaded to YouTube'
                },
                error: {
                    bsonType: ['string', 'null'],
                    description: 'Error message if failed'
                },
                runCount: {
                    bsonType: 'int',
                    minimum: 0,
                    description: 'Number of times this config has been run'
                }
            }
        }
    },
    validationLevel: 'moderate',
    validationAction: 'warn'
});
print('✓ Updated schema validation rules with backgroundAudioId field');

print('✓ Migration 019_add_background_audio_to_configs completed successfully');

