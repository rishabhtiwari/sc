// Migration: 038_create_templates_collection.js
// Description: Create templates collection to store video template definitions
// Created: 2025-12-20

print('Starting migration: 038_create_templates_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create templates collection
db.createCollection('templates', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['template_id', 'name', 'category', 'version', 'layers', 'variables', 'customer_id'],
            properties: {
                customer_id: {
                    bsonType: 'string',
                    description: 'Customer ID for multi-tenancy (use "customer_system" for system templates)'
                },
                template_id: {
                    bsonType: 'string',
                    description: 'Unique template identifier'
                },
                name: {
                    bsonType: 'string',
                    description: 'Template display name'
                },
                category: {
                    bsonType: 'string',
                    enum: ['news', 'shorts', 'ecommerce'],
                    description: 'Template category'
                },
                version: {
                    bsonType: 'string',
                    description: 'Template version (semver)'
                },
                description: {
                    bsonType: 'string',
                    description: 'Template description'
                },
                aspect_ratio: {
                    bsonType: 'string',
                    description: 'Video aspect ratio (e.g., 16:9, 9:16, 1:1)'
                },
                resolution: {
                    bsonType: 'object',
                    properties: {
                        width: { bsonType: 'int' },
                        height: { bsonType: 'int' }
                    }
                },
                layers: {
                    bsonType: 'array',
                    description: 'Template layers (background, text, shapes, etc.)'
                },
                effects: {
                    bsonType: 'array',
                    description: 'Video effects to apply (ken_burns, fade_text, transition, etc.)'
                },
                background_music: {
                    bsonType: 'object',
                    description: 'Background music configuration',
                    properties: {
                        enabled: { bsonType: 'bool' },
                        source: { bsonType: ['string', 'null'] },
                        volume: { bsonType: ['int', 'double'] },
                        fade_in: { bsonType: ['int', 'double'] },
                        fade_out: { bsonType: ['int', 'double'] }
                    }
                },
                logo: {
                    bsonType: 'object',
                    description: 'Logo watermark configuration',
                    properties: {
                        enabled: { bsonType: 'bool' },
                        source: { bsonType: ['string', 'null'] },
                        position: { bsonType: 'string' },
                        scale: { bsonType: ['int', 'double'] },
                        opacity: { bsonType: ['int', 'double'] },
                        margin: { bsonType: ['int', 'object'] }
                    }
                },
                thumbnail: {
                    bsonType: 'object',
                    description: 'Thumbnail configuration for video preview',
                    properties: {
                        source: { bsonType: 'string' },
                        auto_generate: { bsonType: 'bool' },
                        timestamp: { bsonType: ['int', 'double'] }
                    }
                },
                audio: {
                    bsonType: 'object',
                    description: 'Audio configuration'
                },
                variables: {
                    bsonType: 'object',
                    description: 'Template variable definitions'
                },
                metadata: {
                    bsonType: 'object',
                    description: 'Template metadata (author, tags, thumbnail, etc.)'
                },
                is_active: {
                    bsonType: 'bool',
                    description: 'Whether template is active'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Creation timestamp'
                },
                updated_at: {
                    bsonType: 'date',
                    description: 'Last update timestamp'
                },
                created_by: {
                    bsonType: 'string',
                    description: 'User who created the template'
                }
            }
        }
    }
});
print('✓ Created templates collection with schema validation');

// Create indexes
db.templates.createIndex(
    { template_id: 1, customer_id: 1 },
    { unique: true, name: 'idx_template_id_customer' }
);
print('✓ Created unique index on template_id + customer_id');

db.templates.createIndex(
    { customer_id: 1, category: 1, is_active: 1 },
    { name: 'idx_customer_category_active' }
);
print('✓ Created index on customer_id + category + is_active');

db.templates.createIndex(
    { customer_id: 1, 'metadata.tags': 1 },
    { name: 'idx_customer_tags' }
);
print('✓ Created index on customer_id + metadata.tags');

// Insert default templates
const now = new Date();

// Modern News Template
db.templates.insertOne({
    customer_id: 'customer_system',
    template_id: 'modern_news_v1',
    name: 'Modern News',
    category: 'news',
    version: '1.0.0',
    description: 'Professional news video with banner, ticker, and effects',
    aspect_ratio: '16:9',
    resolution: { width: 1920, height: 1080 },
    layers: [
        {
            id: 'background',
            type: 'image',
            source: '{{background_image}}',
            duration: 'auto',
            effects: [],
            z_index: 0
        },
        {
            id: 'bottom_banner',
            type: 'rectangle',
            position: { x: 0, y: 960 },
            size: { width: 1920, height: 120 },
            fill: '{{brand_color}}',
            z_index: 10
        },
        {
            id: 'bottom_ticker',
            type: 'rectangle',
            position: { x: 0, y: 1020 },
            size: { width: 1920, height: 60 },
            fill: '{{ticker_color}}',
            z_index: 11
        },
        {
            id: 'title_text',
            type: 'text',
            content: '{{title}}',
            position: { x: 60, y: 980 },
            font: { family: '{{brand_font}}', size: 48, color: '#FFFFFF', weight: 'bold' },
            z_index: 12
        },
        {
            id: 'ticker_text',
            type: 'text',
            content: '{{summary}}',
            position: { x: 60, y: 1030 },
            font: { family: '{{brand_font}}', size: 24, color: '#FFFFFF' },
            effects: [{ type: 'scroll', params: { direction: 'left', speed: 100 } }],
            z_index: 13
        }
    ],
    effects: [
        {
            type: 'ken_burns',
            target: 'background',
            params: { zoom_start: 1.0, zoom_end: 1.2, easing: 'ease_in_out' }
        },
        {
            type: 'fade_text',
            target: 'title_text',
            params: { fade_in_duration: 0.5, fade_out_duration: 0.5, fade_type: 'both' }
        }
    ],
    background_music: {
        enabled: true,
        source: '{{music_file}}',
        volume: 0.15,
        fade_in: 3.0,
        fade_out: 2.0
    },
    logo: {
        enabled: true,
        source: '{{logo_path}}',
        position: 'top-right',
        scale: 0.12,
        opacity: 0.9,
        margin: 30
    },
    thumbnail: {
        source: '{{thumbnail_image}}',
        auto_generate: true,
        timestamp: 2.0
    },
    audio: {
        tracks: [
            { id: 'voice', source: '{{audio_file}}', volume: 1.0 }
        ]
    },
    variables: {
        background_image: { type: 'image', required: true, description: 'Main background image' },
        title: { type: 'text', required: true, max_length: 100, description: 'News headline' },
        summary: { type: 'text', required: true, max_length: 200, description: 'Scrolling ticker text' },
        audio_file: { type: 'audio', required: true, description: 'Voice narration' },
        brand_color: { type: 'color', default: '#2980b9', description: 'Banner background color' },
        ticker_color: { type: 'color', default: '#34495e', description: 'Ticker background color' },
        brand_font: { type: 'font', default: 'Arial-Bold', description: 'Font family' },
        logo_path: { type: 'image', required: false, description: 'Company logo' },
        music_file: { type: 'audio', required: false, default: 'background_music.wav', description: 'Background music' },
        thumbnail_image: { type: 'image', required: false, description: 'Custom thumbnail (auto-generated if not provided)' }
    },
    metadata: {
        author: 'System',
        tags: ['news', 'professional', 'banner', 'ticker'],
        thumbnail: '/thumbnails/modern_news.jpg'
    },
    is_active: true,
    created_at: now,
    updated_at: now,
    created_by: 'system'
});
print('✓ Inserted template: modern_news_v1');

// Minimal News Template
db.templates.insertOne({
    customer_id: 'customer_system',
    template_id: 'minimal_news_v1',
    name: 'Minimal News',
    category: 'news',
    version: '1.0.0',
    description: 'Clean, simple news video with minimal effects',
    aspect_ratio: '16:9',
    resolution: { width: 1920, height: 1080 },
    layers: [
        {
            id: 'background',
            type: 'image',
            source: '{{background_image}}',
            duration: 'auto',
            effects: [],
            z_index: 0
        },
        {
            id: 'title_text',
            type: 'text',
            content: '{{title}}',
            position: 'center',
            font: { family: '{{brand_font}}', size: 60, color: '#FFFFFF', weight: 'bold' },
            effects: [],
            z_index: 10
        }
    ],
    effects: [
        {
            type: 'fade_text',
            target: 'title_text',
            params: { fade_in_duration: 0.5, fade_out_duration: 0.5, fade_type: 'in' }
        }
    ],
    background_music: {
        enabled: false,
        source: null,
        volume: 0.0,
        fade_in: 0.0,
        fade_out: 0.0
    },
    logo: {
        enabled: true,
        source: '{{logo_path}}',
        position: 'bottom-right',
        scale: 0.08,
        opacity: 0.5,
        margin: 30
    },
    thumbnail: {
        source: '{{thumbnail_image}}',
        auto_generate: true,
        timestamp: 2.0
    },
    audio: {
        tracks: [
            { id: 'voice', source: '{{audio_file}}', volume: 1.0 }
        ]
    },
    variables: {
        background_image: { type: 'image', required: true, description: 'Main background image' },
        title: { type: 'text', required: true, max_length: 100, description: 'News headline' },
        audio_file: { type: 'audio', required: true, description: 'Voice narration' },
        brand_font: { type: 'font', default: 'Arial-Bold', description: 'Font family' },
        logo_path: { type: 'image', required: false, description: 'Company logo' },
        thumbnail_image: { type: 'image', required: false, description: 'Custom thumbnail (auto-generated if not provided)' }
    },
    metadata: {
        author: 'System',
        tags: ['news', 'minimal', 'clean', 'simple'],
        thumbnail: '/thumbnails/minimal_news.jpg'
    },
    is_active: true,
    created_at: now,
    updated_at: now,
    created_by: 'system'
});
print('✓ Inserted template: minimal_news_v1');

// Vertical Overlay Shorts Template
db.templates.insertOne({
    customer_id: 'customer_system',
    template_id: 'vertical_overlay_v1',
    name: 'Vertical Overlay',
    category: 'shorts',
    version: '1.0.0',
    description: 'YouTube Shorts with thumbnail overlay at top',
    aspect_ratio: '9:16',
    resolution: { width: 1080, height: 1920 },
    layers: [
        {
            id: 'background',
            type: 'video',
            source: '{{news_video}}',
            duration: 'auto',
            resize: { width: 1080, height: 1620, position: 'center' },
            z_index: 0
        },
        {
            id: 'thumbnail_overlay',
            type: 'image',
            source: '{{thumbnail}}',
            position: { x: 0, y: 0 },
            size: { width: 1080, height: 300 },
            effects: [
                { type: 'blur', amount: 10 },
                { type: 'darken', amount: 0.3 }
            ],
            z_index: 10
        },
        {
            id: 'title_text',
            type: 'text',
            content: '{{title}}',
            position: { x: 60, y: 100 },
            font: { family: 'Arial-Bold', size: 40, color: '#FFFFFF', weight: 'bold' },
            max_width: 960,
            z_index: 11
        },
        {
            id: 'subscribe_video',
            type: 'video',
            source: '{{subscribe_video}}',
            append: true,
            z_index: 0
        }
    ],
    effects: [],
    background_music: {
        enabled: true,
        source: '{{music_file}}',
        volume: 0.15,
        fade_in: 2.0,
        fade_out: 2.0
    },
    logo: {
        enabled: false,
        source: null,
        position: 'top-right',
        scale: 0.08,
        opacity: 0.8,
        margin: 20
    },
    thumbnail: {
        source: '{{thumbnail}}',
        auto_generate: false,
        timestamp: 0.0
    },
    audio: {
        tracks: [
            { id: 'news_audio', source: 'from_video', volume: 1.0 }
        ]
    },
    variables: {
        news_video: { type: 'video', required: true, description: 'News video file' },
        thumbnail: { type: 'image', required: true, description: 'Thumbnail image' },
        title: { type: 'text', required: true, max_length: 80, description: 'Video title' },
        subscribe_video: { type: 'video', required: false, description: 'Subscribe call-to-action video' },
        music_file: { type: 'audio', required: false, default: 'background_music.wav', description: 'Background music' }
    },
    metadata: {
        author: 'System',
        tags: ['shorts', 'vertical', 'youtube', 'overlay'],
        thumbnail: '/thumbnails/vertical_overlay.jpg'
    },
    is_active: true,
    created_at: now,
    updated_at: now,
    created_by: 'system'
});
print('✓ Inserted template: vertical_overlay_v1');

print('✓ Migration 038_create_templates_collection completed successfully');

