# Instagram Integration Setup Guide

## Overview

This service allows **multiple customers** to connect their own Instagram Business accounts and post content. The system uses a **multi-tenant architecture** where:

1. **Your Application** has ONE Facebook App (shared by all customers)
2. **Each Customer** connects their own Instagram Business account via OAuth
3. **Customer credentials** are stored separately in MongoDB with `customer_id` and `user_id`
4. **When posting**, customers choose which of their connected accounts to use

## Prerequisites

### For Your Application (One-Time Setup)

1. **Facebook Developer Account**
   - Go to https://developers.facebook.com/
   - Create a developer account if you don't have one

2. **Create a Facebook App**
   - Click "Create App"
   - Choose "Business" type
   - Fill in app details

3. **Add Instagram Graph API Product**
   - In your app dashboard, click "Add Product"
   - Select "Instagram Graph API"
   - Complete the setup

4. **Configure OAuth Settings**
   - Go to App Settings > Basic
   - Add OAuth Redirect URIs:
     - Development: `http://localhost:8097/api/instagram/oauth/callback`
     - Production: `https://yourdomain.com/api/instagram/oauth/callback`

5. **Get App Credentials**
   - App ID: Found in App Settings > Basic
   - App Secret: Found in App Settings > Basic (click "Show")

6. **Set Environment Variables**
   ```bash
   export INSTAGRAM_APP_ID="your_app_id_here"
   export INSTAGRAM_APP_SECRET="your_app_secret_here"
   export INSTAGRAM_REDIRECT_URI="http://localhost:8097/api/instagram/oauth/callback"
   ```

   Or add to `.env` file:
   ```
   INSTAGRAM_APP_ID=your_app_id_here
   INSTAGRAM_APP_SECRET=your_app_secret_here
   INSTAGRAM_REDIRECT_URI=http://localhost:8097/api/instagram/oauth/callback
   ```

### For Each Customer (Per-Customer Setup)

Each customer needs:

1. **Instagram Business or Creator Account**
   - Personal Instagram accounts won't work
   - Must be converted to Business or Creator account

2. **Facebook Page**
   - Must have a Facebook Page
   - Instagram account must be connected to the Facebook Page
   - Customer must be admin of the Facebook Page

3. **Steps for Customer**:
   - Go to Social Platform page in the application
   - Click "Connect Instagram Account"
   - Authorize the app to access their Instagram account
   - Their credentials are saved with their `customer_id`

## How It Works

### OAuth Flow

1. **Customer clicks "Connect Instagram Account"**
   ```
   Frontend → API Server → Social Media Uploader Service
   ```

2. **Service generates OAuth URL**
   ```
   https://www.facebook.com/v18.0/dialog/oauth?
     client_id=YOUR_APP_ID&
     redirect_uri=YOUR_REDIRECT_URI&
     scope=instagram_basic,instagram_content_publish,pages_read_engagement&
     state=customer_id:user_id
   ```

3. **Customer authorizes on Facebook**
   - Popup window opens with Facebook OAuth
   - Customer logs in and authorizes

4. **OAuth callback receives authorization code**
   ```
   GET /api/instagram/oauth/callback?code=...&state=customer_id:user_id
   ```

5. **Service exchanges code for access token**
   - Calls Facebook Graph API
   - Gets long-lived access token
   - Retrieves Instagram Business Account ID

6. **Credentials saved to MongoDB**
   ```javascript
   {
     customer_id: "customer_123",
     user_id: "user_456",
     instagram_user_id: "17841...",
     instagram_username: "customer_account",
     access_token: "EAAx...",
     facebook_page_id: "12345...",
     is_active: true,
     created_at: "2026-01-24T..."
   }
   ```

### Multi-Tenant Data Isolation

- Each customer's credentials are isolated by `customer_id`
- Queries automatically filter by `customer_id` and `user_id`
- Customers can only see and use their own connected accounts

## API Endpoints

### Initiate OAuth Flow
```
GET /api/social-media/instagram/oauth/initiate
Headers:
  Authorization: Bearer <jwt_token>
  X-Customer-ID: customer_123
  X-User-ID: user_456

Response:
{
  "status": "success",
  "auth_url": "https://www.facebook.com/v18.0/dialog/oauth?..."
}
```

### OAuth Callback (handled automatically)
```
GET /api/social-media/instagram/oauth/callback?code=...&state=...
```

### Get Customer's Credentials
```
GET /api/social-media/instagram/credentials
Headers:
  Authorization: Bearer <jwt_token>
  X-Customer-ID: customer_123
  X-User-ID: user_456

Response:
{
  "status": "success",
  "credentials": [
    {
      "_id": "...",
      "instagram_username": "customer_account",
      "instagram_user_id": "17841...",
      "is_active": true,
      "created_at": "..."
    }
  ]
}
```

## Database Schema

Collection: `instagram_credentials`

```javascript
{
  _id: ObjectId,
  customer_id: String,        // Multi-tenant isolation
  user_id: String,            // User who connected the account
  instagram_user_id: String,  // Instagram Business Account ID
  instagram_username: String, // Instagram username
  app_id: String,             // Your Facebook App ID
  app_secret: String,         // Your Facebook App Secret
  facebook_page_id: String,   // Connected Facebook Page ID
  access_token: String,       // Long-lived access token
  is_active: Boolean,
  is_authenticated: Boolean,
  created_at: Date,
  updated_at: Date,
  created_by: String,
  updated_by: String
}
```

## Testing

1. **Set up environment variables** (see above)
2. **Restart the service**:
   ```bash
   docker-compose restart social-media-uploader
   ```
3. **Go to Social Platform page** in the UI
4. **Click "Connect Instagram Account"**
5. **Authorize with your Instagram Business account**
6. **Verify credentials are saved** in MongoDB

## Troubleshooting

### "Instagram API credentials not configured"
- Make sure `INSTAGRAM_APP_ID` and `INSTAGRAM_APP_SECRET` are set
- Restart the service after setting environment variables

### "No Facebook pages found"
- Customer needs to have a Facebook Page
- Customer must be admin of the page

### "No Instagram Business Account found"
- Instagram account must be Business or Creator account
- Instagram must be connected to the Facebook Page
- Go to Facebook Page Settings > Instagram to connect

### "OAuth error: access_denied"
- Customer declined authorization
- Ask customer to try again and click "Allow"

## Next Steps

After customers connect their accounts:

1. **Implement Instagram posting functionality**
2. **Add account selection UI** when creating posts
3. **Handle token refresh** (Instagram tokens expire)
4. **Add posting history** and analytics

