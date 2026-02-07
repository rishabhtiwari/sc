// Migration: Create reddit_credentials collection
// Description: Store Reddit OAuth credentials in MongoDB for multi-account support
// Date: 2026-01-24

print('Running migration: 061_create_reddit_credentials.js');

// Switch to news database
db = db.getSiblingDB('news');

// Create reddit_credentials collection
db.createCollection('reddit_credentials');
print('✓ Created reddit_credentials collection');

// Create indexes
db.getCollection('reddit_credentials').createIndex({ "credential_id": 1 }, { unique: true });
db.getCollection('reddit_credentials').createIndex({ "customer_id": 1 });
db.getCollection('reddit_credentials').createIndex({ "is_active": 1 });
db.getCollection('reddit_credentials').createIndex({ "created_at": -1 });
db.getCollection('reddit_credentials').createIndex({ "customer_id": 1, "is_active": 1 });
print('✓ Created indexes for reddit_credentials collection');

// Schema structure for reddit_credentials collection:
// {
//     "credential_id": "string (unique identifier, UUID)",
//     "name": "string (friendly name for this credential, e.g., 'Main Reddit', 'Bot Account')",
//     "platform": "string (always 'reddit')",
//     
//     // OAuth 2.0 credentials
//     "client_id": "string (Reddit App Client ID)",
//     "client_secret": "string (Reddit App Client Secret)",
//     "access_token": "string (OAuth access token)",
//     "refresh_token": "string (OAuth refresh token)",
//     "token_expiry": "Date (when the access token expires)",
//     "scopes": ["array of strings (OAuth scopes granted, e.g., 'submit', 'identity', 'read')"],
//     
//     // Reddit account information
//     "username": "string (Reddit username)",
//     "user_id": "string (Reddit user ID)",
//     "icon_img": "string (Reddit profile icon URL)",
//     "link_karma": "number (user's link karma)",
//     "comment_karma": "number (user's comment karma)",
//     "is_gold": "boolean (whether user has Reddit Premium)",
//     "is_mod": "boolean (whether user is a moderator of any subreddit)",
//     
//     // Subreddit preferences (for posting)
//     "default_subreddit": "string (default subreddit for posting)",
//     "allowed_subreddits": ["array of strings (subreddits user can post to)"],
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

print('✓ Migration 061_create_reddit_credentials.js completed successfully');

