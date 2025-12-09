// Migration: Create youtube_credentials collection
// Description: Store YouTube OAuth credentials in MongoDB for multi-account support
// Date: 2025-11-30

print('Running migration: 018_create_youtube_credentials.js');

// Switch to news database
db = db.getSiblingDB('news');

// Create youtube_credentials collection
db.createCollection('youtube_credentials');
print('✓ Created youtube_credentials collection');

// Create indexes
db.getCollection('youtube_credentials').createIndex({ "credential_id": 1 }, { unique: true });
db.getCollection('youtube_credentials').createIndex({ "is_active": 1 });
db.getCollection('youtube_credentials').createIndex({ "created_at": -1 });
print('✓ Created indexes for youtube_credentials collection');

// Schema structure for youtube_credentials collection:
// {
//     "credential_id": "string (unique identifier, UUID)",
//     "name": "string (friendly name for this credential, e.g., 'Main Channel', 'Backup Channel')",
//     "client_id": "string (OAuth 2.0 client ID)",
//     "client_secret": "string (OAuth 2.0 client secret)",
//     "project_id": "string (Google Cloud project ID)",
//     "auth_uri": "string (OAuth 2.0 auth URI, default: https://accounts.google.com/o/oauth2/auth)",
//     "token_uri": "string (OAuth 2.0 token URI, default: https://oauth2.googleapis.com/token)",
//     "auth_provider_x509_cert_url": "string (default: https://www.googleapis.com/oauth2/v1/certs)",
//     "redirect_uris": ["array of strings (OAuth redirect URIs)"],
//     "access_token": "string (OAuth access token, encrypted)",
//     "refresh_token": "string (OAuth refresh token, encrypted)",
//     "token_expiry": "Date (when the access token expires)",
//     "scopes": ["array of strings (OAuth scopes granted)"],
//     "channel_id": "string (YouTube channel ID associated with this credential)",
//     "channel_name": "string (YouTube channel name)",
//     "is_active": "boolean (whether this credential is currently active/default)",
//     "is_authenticated": "boolean (whether OAuth flow is complete)",
//     "last_used_at": "Date (last time this credential was used for upload)",
//     "created_at": "Date (when credential was created)",
//     "updated_at": "Date (when credential was last updated)",
//     "created_by": "string (user who created this credential)",
//     "notes": "string (optional notes about this credential)"
// }

print('✓ Migration 018_create_youtube_credentials.js completed successfully');

