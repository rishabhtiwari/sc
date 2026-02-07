// Migration: Create tiktok_credentials collection
// Description: Store TikTok OAuth credentials in MongoDB for multi-account support
// Date: 2026-01-24

print('Running migration: 057_create_tiktok_credentials.js');

// Switch to news database
db = db.getSiblingDB('news');

// Create tiktok_credentials collection
db.createCollection('tiktok_credentials');
print('✓ Created tiktok_credentials collection');

// Create indexes
db.getCollection('tiktok_credentials').createIndex({ "credential_id": 1 }, { unique: true });
db.getCollection('tiktok_credentials').createIndex({ "customer_id": 1 });
db.getCollection('tiktok_credentials').createIndex({ "is_active": 1 });
db.getCollection('tiktok_credentials').createIndex({ "created_at": -1 });
db.getCollection('tiktok_credentials').createIndex({ "customer_id": 1, "is_active": 1 });
print('✓ Created indexes for tiktok_credentials collection');

// Schema structure for tiktok_credentials collection:
// {
//     "credential_id": "string (unique identifier, UUID)",
//     "name": "string (friendly name for this credential, e.g., 'Main TikTok', 'Brand TikTok')",
//     "platform": "string (always 'tiktok')",
//     
//     // OAuth 2.0 credentials
//     "client_key": "string (TikTok Client Key)",
//     "client_secret": "string (TikTok Client Secret)",
//     "access_token": "string (OAuth access token)",
//     "refresh_token": "string (OAuth refresh token)",
//     "token_expiry": "Date (when the access token expires)",
//     "refresh_token_expiry": "Date (when the refresh token expires)",
//     "scopes": ["array of strings (OAuth scopes granted, e.g., 'video.upload', 'user.info.basic')"],
//     
//     // TikTok account information
//     "open_id": "string (TikTok user's unique identifier)",
//     "username": "string (TikTok username/handle)",
//     "display_name": "string (TikTok display name)",
//     "avatar_url": "string (TikTok profile picture URL)",
//     "follower_count": "number (number of followers)",
//     
//     // Multi-tenancy fields
//     "customer_id": "string (customer ID for multi-tenancy)",
//     
//     // Status and metadata
//     "is_active": "boolean (whether this credential is currently active/default)",
//     "is_authenticated": "boolean (whether OAuth flow is complete)",
//     "last_used_at": "Date (last time this credential was used for upload)",
//     "last_token_refresh": "Date (last time token was refreshed)",
//     
//     // Audit fields
//     "created_at": "Date (when credential was created)",
//     "updated_at": "Date (when credential was last updated)",
//     "created_by": "string (user ID who created this credential)",
//     "updated_by": "string (user ID who last updated this credential)",
//     
//     // Additional metadata
//     "notes": "string (optional notes about this credential)",
//     "upload_count": "number (total number of uploads using this credential)",
//     "last_upload_status": "string (status of last upload: success, failed, pending)"
// }

print('✓ Migration 057_create_tiktok_credentials.js completed successfully');

