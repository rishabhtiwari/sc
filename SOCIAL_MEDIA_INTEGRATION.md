# Social Media Integration Architecture

## Overview

This document explains how the multi-tenant social media integration works, allowing multiple customers to connect their own social media accounts and post content.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                    Social Platform Page                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Frontend Server (Express)                      │
│                    Port 3002 - API Proxy                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Server (Flask)                            │
│              Port 8080 - API Gateway + JWT Auth                 │
│                                                                   │
│  Routes:                                                         │
│  - /api/social-media/instagram/oauth/initiate                   │
│  - /api/social-media/instagram/oauth/callback                   │
│  - /api/social-media/instagram/credentials                      │
│  - /api/social-media/<platform>/credentials                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Social Media Uploader Service (Flask)               │
│                    Port 8097 - OAuth & Upload                    │
│                                                                   │
│  Endpoints:                                                      │
│  - /api/instagram/oauth/initiate                                │
│  - /api/instagram/oauth/callback                                │
│  - /api/instagram/credentials                                   │
│  - /api/instagram/upload (coming soon)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MongoDB Database                            │
│                                                                   │
│  Collections:                                                    │
│  - instagram_credentials (customer_id, user_id, access_token)   │
│  - tiktok_credentials                                           │
│  - twitter_credentials                                          │
│  - linkedin_credentials                                         │
│  - facebook_credentials                                         │
│  - reddit_credentials                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Multi-Tenant Design

### Application-Level Credentials (One Set)

Your application needs ONE set of credentials per platform:

- **Instagram**: Facebook App ID + App Secret
- **TikTok**: TikTok App ID + App Secret
- **Twitter**: Twitter App ID + App Secret
- **LinkedIn**: LinkedIn App ID + App Secret
- **Facebook**: Facebook App ID + App Secret
- **Reddit**: Reddit App ID + App Secret

These are set as environment variables in `docker-compose.yml`.

### Customer-Level Credentials (Many Sets)

Each customer can connect multiple accounts per platform:

```javascript
// Example: Customer A connects 2 Instagram accounts
{
  customer_id: "customer_a",
  user_id: "user_1",
  instagram_username: "business_account_1",
  access_token: "token_1",
  ...
}

{
  customer_id: "customer_a",
  user_id: "user_1",
  instagram_username: "business_account_2",
  access_token: "token_2",
  ...
}

// Example: Customer B connects 1 Instagram account
{
  customer_id: "customer_b",
  user_id: "user_5",
  instagram_username: "customer_b_account",
  access_token: "token_3",
  ...
}
```

### Data Isolation

All queries automatically filter by `customer_id` and `user_id`:

```python
# In social-media-uploader/app.py
user_context = extract_user_context_from_headers(request.headers)
customer_id = user_context.get('customer_id')
user_id = user_context.get('user_id')

query = build_multi_tenant_query({}, customer_id=customer_id, user_id=user_id)
credentials = instagram_credentials_collection.find(query)
```

This ensures:
- Customer A can only see their own accounts
- Customer B can only see their own accounts
- No data leakage between customers

## OAuth Flow

### Step 1: Initiate OAuth

```
User clicks "Connect Instagram Account"
  ↓
Frontend calls: GET /api/social-media/instagram/oauth/initiate
  ↓
API Server proxies to: GET /api/instagram/oauth/initiate
  ↓
Social Media Uploader generates OAuth URL with:
  - client_id: YOUR_APP_ID
  - redirect_uri: YOUR_REDIRECT_URI
  - scope: instagram_basic,instagram_content_publish
  - state: customer_id:user_id (for tracking)
  ↓
Returns auth_url to frontend
  ↓
Frontend opens auth_url in popup window
```

### Step 2: User Authorizes

```
User sees Facebook/Instagram OAuth screen
  ↓
User logs in and clicks "Allow"
  ↓
Facebook redirects to: YOUR_REDIRECT_URI?code=...&state=customer_id:user_id
```

### Step 3: Exchange Code for Token

```
Social Media Uploader receives callback
  ↓
Extracts customer_id and user_id from state
  ↓
Exchanges authorization code for access token
  ↓
Gets Instagram Business Account ID
  ↓
Saves to MongoDB:
  {
    customer_id: "...",
    user_id: "...",
    instagram_user_id: "...",
    access_token: "...",
    ...
  }
  ↓
Shows success page, user closes popup
```

## Supported Platforms

| Platform  | Status        | OAuth Provider | Required Account Type        |
|-----------|---------------|----------------|------------------------------|
| YouTube   | ✅ Active     | Google         | Any YouTube account          |
| Instagram | ✅ Active     | Facebook       | Business/Creator account     |
| TikTok    | 🚧 Coming Soon | TikTok         | TikTok account               |
| Twitter   | 🚧 Coming Soon | Twitter/X      | Twitter account              |
| LinkedIn  | 🚧 Coming Soon | LinkedIn       | LinkedIn account             |
| Facebook  | 🚧 Coming Soon | Facebook       | Facebook Page                |
| Reddit    | 🚧 Coming Soon | Reddit         | Reddit account               |

## Setup Instructions

### 1. Create Facebook App (for Instagram)

See `social-media-uploader/INSTAGRAM_SETUP.md` for detailed instructions.

### 2. Set Environment Variables

Add to `.env` file or export:

```bash
# Instagram (Facebook Graph API)
INSTAGRAM_APP_ID=your_facebook_app_id
INSTAGRAM_APP_SECRET=your_facebook_app_secret
INSTAGRAM_REDIRECT_URI=http://localhost:8097/api/instagram/oauth/callback

# TikTok (coming soon)
# TIKTOK_CLIENT_KEY=...
# TIKTOK_CLIENT_SECRET=...

# Twitter (coming soon)
# TWITTER_CLIENT_ID=...
# TWITTER_CLIENT_SECRET=...
```

### 3. Update docker-compose.yml

Environment variables are already configured in `docker-compose.yml` to read from `.env` file.

### 4. Restart Services

```bash
docker-compose restart social-media-uploader
docker-compose restart ichat-api-server
docker-compose restart news-automation-frontend
```

### 5. Test OAuth Flow

1. Go to http://localhost:3002/social-platform
2. Click on Instagram
3. Click "Connect Instagram Account"
4. Authorize with your Instagram Business account
5. Verify credentials are saved in MongoDB

## Next Steps

1. ✅ Instagram OAuth integration (DONE)
2. 🚧 Instagram posting functionality
3. 🚧 TikTok OAuth integration
4. 🚧 Twitter OAuth integration
5. 🚧 LinkedIn OAuth integration
6. 🚧 Facebook OAuth integration
7. 🚧 Reddit OAuth integration
8. 🚧 Unified posting UI (select platform + account)
9. 🚧 Posting history and analytics
10. 🚧 Token refresh handling

## Files Modified/Created

### Created:
- `mongodb/migrations/056_create_instagram_credentials.js`
- `mongodb/migrations/057_create_tiktok_credentials.js`
- `mongodb/migrations/058_create_twitter_credentials.js`
- `mongodb/migrations/059_create_linkedin_credentials.js`
- `mongodb/migrations/060_create_facebook_credentials.js`
- `mongodb/migrations/061_create_reddit_credentials.js`
- `api-server/routes/social_media_routes.py`
- `frontend-server/src/pages/SocialPlatformPage.jsx`
- `social-media-uploader/INSTAGRAM_SETUP.md`
- `.env.instagram.example`
- `SOCIAL_MEDIA_INTEGRATION.md` (this file)

### Modified:
- `docker-compose.yml` (renamed service, added Instagram env vars)
- `deploy-news-services.sh` (updated service name)
- `social-media-uploader/Dockerfile` (updated paths)
- `social-media-uploader/README.md` (updated description)
- `social-media-uploader/config/settings.py` (added Instagram config)
- `social-media-uploader/app.py` (added Instagram OAuth endpoints)
- `api-server/app.py` (registered social_media_bp blueprint)
- `frontend-server/src/App.jsx` (added SocialPlatformPage route)

