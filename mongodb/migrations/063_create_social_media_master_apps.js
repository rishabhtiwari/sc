// Migration: Create social_media_master_apps collection
// Description: Store master app credentials for social media platforms (Instagram, TikTok, Twitter, etc.)
// Date: 2026-02-07

print('Running migration: 063_create_social_media_master_apps.js');

// Switch to news database
db = db.getSiblingDB('news');

// Create social_media_master_apps collection
db.createCollection('social_media_master_apps');
print('✓ Created social_media_master_apps collection');

// Create indexes
// Index for finding active app for customer+platform
db.getCollection('social_media_master_apps').createIndex(
    { "customer_id": 1, "platform": 1, "is_active": 1 },
    { name: "customer_platform_active_idx" }
);

// Index for listing customer's apps
db.getCollection('social_media_master_apps').createIndex(
    { "customer_id": 1 },
    { name: "customer_idx" }
);

// Unique index: only one active app per customer per platform
db.getCollection('social_media_master_apps').createIndex(
    { "customer_id": 1, "platform": 1, "is_active": 1 },
    { 
        unique: true, 
        partialFilterExpression: { "is_active": true },
        name: "unique_active_app_idx" 
    }
);

// Index for created_at
db.getCollection('social_media_master_apps').createIndex({ "created_at": -1 });

print('✓ Created indexes for social_media_master_apps collection');

// Schema structure for social_media_master_apps collection:
// {
//     "_id": "ObjectId",
//     "customer_id": "string (customer ID for multi-tenancy)",
//     "platform": "string (instagram, tiktok, twitter, linkedin, facebook, reddit)",
//     "app_name": "string (user-friendly name, e.g., 'Production Instagram App')",
//     "app_id": "string (platform app ID - e.g., Facebook App ID for Instagram)",
//     "app_secret": "string (ENCRYPTED - platform app secret using customer's encryption key)",
//     "redirect_uri": "string (OAuth callback URL)",
//     "scopes": ["array of strings (OAuth scopes/permissions)"],
//     "is_active": "boolean (only one active app per platform per customer)",
//     "created_by": "string (user_id who created this master app)",
//     "created_at": "Date (when master app was created)",
//     "updated_at": "Date (when master app was last updated)",
//     "metadata": {
//         "description": "string (optional description)",
//         "environment": "string (production, staging, development)",
//         "notes": "string (admin notes)"
//     }
// }

// Supported platforms:
// - instagram: Uses Facebook Graph API (requires Facebook App ID/Secret)
// - tiktok: TikTok for Developers API
// - twitter: Twitter API v2
// - linkedin: LinkedIn Marketing API
// - facebook: Facebook Graph API
// - reddit: Reddit API

print('✓ Migration 063_create_social_media_master_apps.js completed successfully');

