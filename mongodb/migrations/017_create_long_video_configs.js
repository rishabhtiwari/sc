// Migration: 017_create_long_video_configs.js
// Description: Create long_video_configs collection for storing video configuration and scheduling
// Created: 2025-11-30

print('Starting migration: 017_create_long_video_configs');

// Switch to news database
use news;

// Create long_video_configs collection
db.createCollection('long_video_configs');

// Create indexes for efficient queries
db.getCollection('long_video_configs').createIndex({ "status": 1 }, { name: "idx_status" });
print('✓ Created index on status');

db.getCollection('long_video_configs').createIndex({ "createdAt": -1 }, { name: "idx_createdAt" });
print('✓ Created index on createdAt (descending)');

db.getCollection('long_video_configs').createIndex({ "nextRunTime": 1 }, { name: "idx_nextRunTime" });
print('✓ Created index on nextRunTime');

db.getCollection('long_video_configs').createIndex({ "status": 1, "nextRunTime": 1 }, { name: "idx_status_nextRunTime" });
print('✓ Created compound index on status and nextRunTime');

db.getCollection('long_video_configs').createIndex({ "frequency": 1 }, { name: "idx_frequency" });
print('✓ Created index on frequency');

// Add schema validation
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
                    enum: ['pending', 'processing', 'completed', 'failed'],
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
print('✓ Added schema validation rules');

// Schema structure for long_video_configs collection:
// {
//     "title": "string (video title) - REQUIRED",
//     "categories": ["string"] (array of category filters),
//     "country": "string (country code like 'us', 'in')",
//     "language": "string (language code like 'en', 'hi')",
//     "videoCount": "int (number of videos to merge, 1-100) - REQUIRED",
//     "frequency": "string (none|hourly|daily|weekly|monthly) - REQUIRED",
//     "status": "string (pending|processing|completed|failed) - REQUIRED",
//     "videoPath": "string|null (path to merged video)",
//     "thumbnailPath": "string|null (path to thumbnail)",
//     "youtubeVideoId": "string|null (YouTube video ID)",
//     "youtubeVideoUrl": "string|null (YouTube video URL)",
//     "createdAt": "Date (creation timestamp) - REQUIRED",
//     "updatedAt": "Date (last update timestamp)",
//     "lastRunTime": "Date|null (last computation time)",
//     "nextRunTime": "Date|null (next scheduled run)",
//     "mergeStartedAt": "Date|null (merge start time)",
//     "mergeCompletedAt": "Date|null (merge completion time)",
//     "uploadedAt": "Date|null (YouTube upload time)",
//     "error": "string|null (error message)",
//     "runCount": "int (number of times run, default 0)"
// }

print('✓ Long video configs collection created with indexes and validation');
print('Migration 017_create_long_video_configs completed successfully');

