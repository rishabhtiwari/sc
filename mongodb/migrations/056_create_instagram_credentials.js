// Migration: Create instagram_credentials collection
// Description: Store Instagram OAuth credentials in MongoDB for multi-account support
// Date: 2026-01-24

print('Running migration: 056_create_instagram_credentials.js');

// Switch to news database
db = db.getSiblingDB('news');

// Create instagram_credentials collection
db.createCollection('instagram_credentials');
print('✓ Created instagram_credentials collection');

// Create indexes
db.getCollection('instagram_credentials').createIndex({ "credential_id": 1 }, { unique: true });
db.getCollection('instagram_credentials').createIndex({ "customer_id": 1 });
db.getCollection('instagram_credentials').createIndex({ "is_active": 1 });
db.getCollection('instagram_credentials').createIndex({ "created_at": -1 });
db.getCollection('instagram_credentials').createIndex({ "customer_id": 1, "is_active": 1 });
print('✓ Created indexes for instagram_credentials collection');

// Schema structure for instagram_credentials collection:
// {
//     "credential_id": "string (unique identifier, UUID)",
//     "name": "string (friendly name for this credential, e.g., 'Main Account', 'Brand Account')",
//     "platform": "string (always 'instagram')",
//     
//     // OAuth 2.0 credentials
//     "app_id": "string (Instagram/Facebook App ID)",
//     "app_secret": "string (Instagram/Facebook App Secret)",
//     "access_token": "string (OAuth access token, long-lived)",
//     "refresh_token": "string (OAuth refresh token, if available)",
//     "token_expiry": "Date (when the access token expires)",
//     "scopes": ["array of strings (OAuth scopes granted, e.g., 'instagram_basic', 'instagram_content_publish')"],
//     
//     // Instagram account information
//     "instagram_user_id": "string (Instagram Business/Creator Account ID)",
//     "instagram_username": "string (Instagram username)",
//     "instagram_account_type": "string (BUSINESS or CREATOR)",
//     "profile_picture_url": "string (Instagram profile picture URL)",
//     
//     // Facebook Page connection (required for Instagram Graph API)
//     "facebook_page_id": "string (Connected Facebook Page ID)",
//     "facebook_page_name": "string (Connected Facebook Page name)",
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

print('✓ Migration 056_create_instagram_credentials.js completed successfully');

