// Migration: Create twitter_credentials collection
// Description: Store Twitter/X OAuth credentials in MongoDB for multi-account support
// Date: 2026-01-24

print('Running migration: 058_create_twitter_credentials.js');

// Switch to news database
db = db.getSiblingDB('news');

// Create twitter_credentials collection
db.createCollection('twitter_credentials');
print('✓ Created twitter_credentials collection');

// Create indexes
db.getCollection('twitter_credentials').createIndex({ "credential_id": 1 }, { unique: true });
db.getCollection('twitter_credentials').createIndex({ "customer_id": 1 });
db.getCollection('twitter_credentials').createIndex({ "is_active": 1 });
db.getCollection('twitter_credentials').createIndex({ "created_at": -1 });
db.getCollection('twitter_credentials').createIndex({ "customer_id": 1, "is_active": 1 });
print('✓ Created indexes for twitter_credentials collection');

// Schema structure for twitter_credentials collection:
// {
//     "credential_id": "string (unique identifier, UUID)",
//     "name": "string (friendly name for this credential, e.g., 'Main Twitter', 'Brand X')",
//     "platform": "string (always 'twitter')",
//     
//     // OAuth 2.0 credentials (Twitter API v2)
//     "client_id": "string (Twitter OAuth 2.0 Client ID)",
//     "client_secret": "string (Twitter OAuth 2.0 Client Secret)",
//     "access_token": "string (OAuth 2.0 access token)",
//     "refresh_token": "string (OAuth 2.0 refresh token)",
//     "token_expiry": "Date (when the access token expires)",
//     "scopes": ["array of strings (OAuth scopes granted, e.g., 'tweet.read', 'tweet.write', 'users.read')"],
//     
//     // OAuth 1.0a credentials (legacy, if needed)
//     "api_key": "string (Twitter API Key / Consumer Key)",
//     "api_secret": "string (Twitter API Secret / Consumer Secret)",
//     "oauth_token": "string (OAuth 1.0a Access Token)",
//     "oauth_token_secret": "string (OAuth 1.0a Access Token Secret)",
//     
//     // Twitter account information
//     "user_id": "string (Twitter user ID)",
//     "username": "string (Twitter handle without @)",
//     "display_name": "string (Twitter display name)",
//     "profile_image_url": "string (Twitter profile picture URL)",
//     "verified": "boolean (whether account is verified)",
//     "follower_count": "number (number of followers)",
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

print('✓ Migration 058_create_twitter_credentials.js completed successfully');

