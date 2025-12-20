// Migration: 039_add_template_preferences_to_customers.js
// Description: Add template preferences to customer video_config
// Created: 2025-12-20

print('Starting migration: 039_add_template_preferences_to_customers');

// Switch to news database
db = db.getSiblingDB('news');

// Add template preferences to all existing customers
const updateResult = db.customers.updateMany(
    {},
    {
        $set: {
            'video_config.long_video_template': 'modern_news_v1',
            'video_config.shorts_template': 'vertical_overlay_v1',
            'video_config.template_overrides': {}
        }
    }
);
print('✓ Added template preferences to ' + updateResult.modifiedCount + ' customers');

// Update the default system customer with template preferences
db.customers.updateOne(
    { customer_id: 'customer_system' },
    {
        $set: {
            'video_config.long_video_template': 'modern_news_v1',
            'video_config.shorts_template': 'vertical_overlay_v1',
            'video_config.template_overrides': {
                'modern_news_v1': {
                    'layers.bottom_banner.fill': '#2980b9',
                    'layers.bottom_ticker.fill': '#34495e',
                    'variables.brand_font.default': 'Arial-Bold'
                }
            }
        }
    }
);
print('✓ Updated system customer with default template preferences');

// Create index for template queries
db.customers.createIndex(
    { 'video_config.long_video_template': 1 },
    { name: 'idx_long_video_template', sparse: true }
);
print('✓ Created index on video_config.long_video_template');

db.customers.createIndex(
    { 'video_config.shorts_template': 1 },
    { name: 'idx_shorts_template', sparse: true }
);
print('✓ Created index on video_config.shorts_template');

print('✓ Migration 039_add_template_preferences_to_customers completed successfully');

