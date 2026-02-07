// Migration: Create facebook_credentials collection
// Description: Store Facebook OAuth credentials in MongoDB for multi-account support
// Date: 2026-01-24

print('Running migration: 060_create_facebook_credentials.js');

// Switch to news database
db = db.getSiblingDB('news');

// Create facebook_credentials collection
db.createCollection('facebook_credentials');
print('✓ Created facebook_credentials collection');

// Create indexes
db.getCollection('facebook_credentials').createIndex({ "credential_id": 1 }, { unique: true });
db.getCollection('facebook_credentials').createIndex({ "customer_id": 1 });
db.getCollection('facebook_credentials').createIndex({ "is_active": 1 });
db.getCollection('facebook_credentials').createIndex({ "created_at": -1 });
db.getCollection('facebook_credentials').createIndex({ "customer_id": 1, "is_active": 1 });
print('✓ Created indexes for facebook_credentials collection');

// Schema structure for facebook_credentials collection:
// {
//     "credential_id": "string (unique identifier, UUID)",
//     "name": "string (friendly name for this credential, e.g., 'Personal FB', 'Business Page')",
//     "platform": "string (always 'facebook')",
//     
//     // OAuth 2.0 credentials
//     "app_id": "string (Facebook App ID)",
//     "app_secret": "string (Facebook App Secret)",
//     "access_token": "string (OAuth access token, long-lived)",
//     "token_expiry": "Date (when the access token expires)",
//     "scopes": ["array of strings (OAuth scopes granted, e.g., 'pages_manage_posts', 'pages_read_engagement')"],
//     
//     // Facebook user information
//     "user_id": "string (Facebook user ID)",
//     "user_name": "string (Facebook user name)",
//     "user_email": "string (Facebook user email)",
//     "profile_picture_url": "string (Facebook profile picture URL)",
//     
//     // Facebook Page information (if posting to page)
//     "page_id": "string (Facebook Page ID)",
//     "page_name": "string (Facebook Page name)",
//     "page_access_token": "string (Page-specific access token)",
//     "page_category": "string (Facebook Page category)",
//     "page_follower_count": "number (number of page followers)",
//     
//     // Multi-tenancy fields
//     "customer_id": "string (customer ID for multi-tenancy)",
//     
//     // Status and metadata
//     "is_active": "boolean (whether this credential is currently active/default)",
//     "is_authenticated": "boolean (whether OAuth flow is complete)",
//     "last_used_at": "Date (last time this credential was used for posting)",
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
//     "post_count": "number (total number of posts using this credential)",
//     "last_post_status": "string (status of last post: success, failed, pending)"
// }

print('✓ Migration 060_create_facebook_credentials.js completed successfully');

