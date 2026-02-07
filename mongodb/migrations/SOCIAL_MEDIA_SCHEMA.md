# Social Media Credentials Database Schema

## Overview
This document describes the database schema for storing OAuth credentials for multiple social media platforms. Each platform has its own dedicated collection to accommodate platform-specific fields and requirements.

## Collections Created

### 1. `youtube_credentials` (Existing - Migration 018)
- **Purpose**: Store YouTube OAuth credentials
- **Platform**: YouTube
- **Key Fields**: channel_id, channel_name, client_id, client_secret, access_token, refresh_token

### 2. `instagram_credentials` (Migration 056)
- **Purpose**: Store Instagram OAuth credentials
- **Platform**: Instagram
- **Key Fields**: instagram_user_id, instagram_username, app_id, app_secret, facebook_page_id
- **Special Requirements**: Requires Facebook Page connection for Instagram Graph API

### 3. `tiktok_credentials` (Migration 057)
- **Purpose**: Store TikTok OAuth credentials
- **Platform**: TikTok
- **Key Fields**: open_id, username, client_key, client_secret, access_token, refresh_token

### 4. `twitter_credentials` (Migration 058)
- **Purpose**: Store Twitter/X OAuth credentials
- **Platform**: Twitter/X
- **Key Fields**: user_id, username, client_id, client_secret (OAuth 2.0), api_key, api_secret (OAuth 1.0a)
- **Special Note**: Supports both OAuth 2.0 and OAuth 1.0a for backward compatibility

### 5. `linkedin_credentials` (Migration 059)
- **Purpose**: Store LinkedIn OAuth credentials
- **Platform**: LinkedIn
- **Key Fields**: person_id, profile_id, organization_id (for company pages), client_id, client_secret

### 6. `facebook_credentials` (Migration 060)
- **Purpose**: Store Facebook OAuth credentials
- **Platform**: Facebook
- **Key Fields**: user_id, page_id, page_access_token, app_id, app_secret
- **Special Note**: Supports both personal profiles and business pages

### 7. `reddit_credentials` (Migration 061)
- **Purpose**: Store Reddit OAuth credentials
- **Platform**: Reddit
- **Key Fields**: username, user_id, client_id, client_secret, default_subreddit

## Common Fields Across All Collections

All credential collections share these common fields:

### Identity
- `credential_id`: Unique identifier (UUID)
- `name`: Friendly name for the credential
- `platform`: Platform identifier (youtube, instagram, tiktok, etc.)

### OAuth Credentials
- `access_token`: OAuth access token
- `refresh_token`: OAuth refresh token (if supported)
- `token_expiry`: Token expiration date
- `scopes`: Array of granted OAuth scopes

### Multi-Tenancy
- `customer_id`: Customer ID for multi-tenant isolation

### Status
- `is_active`: Whether credential is active/default
- `is_authenticated`: Whether OAuth flow is complete
- `last_used_at`: Last usage timestamp
- `last_token_refresh`: Last token refresh timestamp

### Audit Trail
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `created_by`: User ID who created
- `updated_by`: User ID who last updated

### Metadata
- `notes`: Optional notes
- `upload_count` / `post_count`: Total uploads/posts
- `last_upload_status` / `last_post_status`: Last operation status

## Indexes

Each collection has the following indexes:
1. `credential_id` (unique)
2. `customer_id`
3. `is_active`
4. `created_at` (descending)
5. Compound index: `customer_id` + `is_active`

## Platform-Specific Considerations

### Instagram
- Requires Facebook Page connection
- Uses Facebook Graph API
- Supports Business and Creator accounts only

### TikTok
- Refresh tokens have expiration dates
- Requires separate scopes for video upload and user info

### Twitter/X
- Supports both OAuth 2.0 (recommended) and OAuth 1.0a (legacy)
- Different scopes for reading vs writing

### LinkedIn
- Can post as individual or organization
- Requires organization admin rights for company posting

### Facebook
- Page-specific access tokens for page posting
- Long-lived tokens (60 days)

### Reddit
- Requires app registration with Reddit
- Subreddit-specific posting permissions

## Migration Execution Order

Run migrations in this order:
1. 018_create_youtube_credentials.js (already exists)
2. 056_create_instagram_credentials.js
3. 057_create_tiktok_credentials.js
4. 058_create_twitter_credentials.js
5. 059_create_linkedin_credentials.js
6. 060_create_facebook_credentials.js
7. 061_create_reddit_credentials.js

## Next Steps

1. Run all migrations to create collections
2. Rename youtube-uploader service to social-media-uploader
3. Implement OAuth flows for each platform
4. Create unified credential management UI
5. Build platform-specific upload/post services

