# Social Media Master App Architecture

## Overview

Multi-tenant architecture where customers can manage their own Facebook/Instagram app credentials, and multiple users within each customer can connect their social media accounts.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  - Master App Management UI (Admin only)                     │
│  - Instagram Connection UI (All users)                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  API Server (Port 8080)                      │
│  - /api/social-media/master-apps/* (CRUD)                   │
│  - /api/social-media/instagram/oauth/* (OAuth flow)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            Social Media Uploader (Port 8097)                 │
│  - Master app CRUD operations                                │
│  - OAuth flow using master app from DB                       │
│  - Credential management                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    MongoDB Collections                       │
│  - social_media_master_apps                                  │
│  - instagram_credentials                                     │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### Collection: `social_media_master_apps`

Stores Facebook/Instagram app credentials for each customer.

```javascript
{
  _id: ObjectId("..."),
  customer_id: "customer_123",
  platform: "instagram",              // "instagram", "tiktok", "twitter", etc.
  app_name: "My News App",            // User-friendly name
  app_id: "876162771907731",          // Facebook App ID
  app_secret: "encrypted_secret",     // Encrypted Facebook App Secret
  redirect_uri: "http://localhost:8080/api/social-media/instagram/oauth/callback",
  scopes: [
    "instagram_basic",
    "instagram_content_publish",
    "pages_read_engagement"
  ],
  is_active: true,                    // Only one active app per platform per customer
  created_by: "user_456",             // Admin who created it
  created_at: ISODate("2024-02-07T..."),
  updated_at: ISODate("2024-02-07T..."),
  metadata: {
    app_type: "business",             // "business" or "consumer"
    environment: "production",        // "development" or "production"
    description: "Main Instagram app for news posting"
  }
}
```

**Indexes:**
- `{ customer_id: 1, platform: 1, is_active: 1 }` - Find active app for customer
- `{ customer_id: 1 }` - List all apps for customer

### Collection: `instagram_credentials` (Updated)

Stores individual user's Instagram account connections.

```javascript
{
  _id: ObjectId("..."),
  customer_id: "customer_123",
  user_id: "user_456",
  master_app_id: ObjectId("..."),     // Reference to social_media_master_apps
  instagram_user_id: "17841405309213154",
  instagram_username: "mynewschannel",
  facebook_page_id: "123456789",
  facebook_page_name: "My News Channel",
  access_token: "encrypted_token",    // Encrypted access token
  token_type: "bearer",
  token_expires_at: ISODate("2024-05-07T..."),  // 90 days from creation
  is_authenticated: true,
  created_at: ISODate("2024-02-07T..."),
  updated_at: ISODate("2024-02-07T..."),
  last_used_at: ISODate("2024-02-07T...")
}
```

**Indexes:**
- `{ customer_id: 1, user_id: 1 }` - List user's accounts
- `{ master_app_id: 1 }` - Find all accounts using a master app
- `{ instagram_user_id: 1 }` - Unique Instagram account

## API Endpoints

### Master App Management

#### 1. Create Master App
```
POST /api/social-media/master-apps
Headers:
  Authorization: Bearer <jwt_token>
  X-Customer-ID: customer_123
  X-User-ID: user_456
Body:
{
  "platform": "instagram",
  "app_name": "My News App",
  "app_id": "876162771907731",
  "app_secret": "your_app_secret",
  "redirect_uri": "http://localhost:8080/api/social-media/instagram/oauth/callback",
  "metadata": {
    "app_type": "business",
    "environment": "production",
    "description": "Main Instagram app"
  }
}
Response:
{
  "status": "success",
  "master_app": { ... },
  "message": "Master app created successfully"
}
```

#### 2. List Master Apps
```
GET /api/social-media/master-apps?platform=instagram
Headers:
  Authorization: Bearer <jwt_token>
  X-Customer-ID: customer_123
Response:
{
  "status": "success",
  "master_apps": [
    {
      "_id": "...",
      "platform": "instagram",
      "app_name": "My News App",
      "app_id": "876162771907731",
      "is_active": true,
      "created_at": "...",
      // app_secret is NOT returned for security


## Security Considerations

### 1. Encryption
- **App Secret**: Encrypted using Fernet (symmetric encryption) before storing in MongoDB
- **Access Tokens**: Encrypted using same method
- **Encryption Key**: Stored in environment variable `ENCRYPTION_KEY`

### 2. Access Control
- **Master App Management**: Only admins can create/update/delete master apps
- **OAuth Flow**: All users can connect their Instagram accounts
- **Credential Access**: Users can only see/delete their own credentials

### 3. Multi-Tenancy
- All queries filtered by `customer_id` from JWT token
- No cross-customer data leakage
- Master app shared within customer, not across customers

## User Roles & Permissions

### Admin Role
- Create/update/delete master apps
- View all Instagram credentials for customer
- Manage platform settings

### Regular User Role
- View available master apps (read-only)
- Connect their own Instagram accounts
- View/delete their own Instagram credentials
- Post content using their credentials

## Implementation Plan

### Phase 1: Backend API (Current)
1. ✅ Create database collections
2. ✅ Implement master app CRUD endpoints
3. ✅ Update OAuth flow to use master app from DB
4. ✅ Add encryption for secrets and tokens

### Phase 2: Frontend UI
1. Create "Social Media Settings" page (admin only)
2. Build master app management interface
3. Update Instagram connection flow to use master app
4. Add master app selector (if multiple apps)

### Phase 3: Testing & Deployment
1. Test multi-user Instagram connections
2. Test master app CRUD operations
3. Verify encryption/decryption
4. Deploy to production

## Migration Strategy

### For Existing Deployments

If you already have Instagram credentials in `.env`:

1. **Create migration script** to move env vars to database:
   ```python
   # Create master app from environment variables
   master_app = {
       "customer_id": "default",
       "platform": "instagram",
       "app_name": "Default Instagram App",
       "app_id": os.getenv("INSTAGRAM_APP_ID"),
       "app_secret": encrypt(os.getenv("INSTAGRAM_APP_SECRET")),
       "is_active": True
   }
   db.social_media_master_apps.insert_one(master_app)
   ```

2. **Update existing credentials** to reference master app:
   ```python
   master_app_id = db.social_media_master_apps.find_one(...)["_id"]
   db.instagram_credentials.update_many(
       {},
       {"$set": {"master_app_id": master_app_id}}
   )
   ```

3. **Remove from .env** after migration

### For New Deployments

1. No environment variables needed for Instagram
2. Admin creates master app via UI
3. Users connect Instagram accounts

## Example Workflows

### Workflow 1: Admin Sets Up Instagram

1. Admin logs in
2. Navigates to "Settings" → "Social Media Apps"
3. Clicks "Add App" → "Instagram"
4. Fills form:
   - App Name: "My News Instagram App"
   - Facebook App ID: 876162771907731
   - Facebook App Secret: (from Facebook developers)
   - Environment: Production
5. Clicks "Save"
6. System encrypts secret and saves to database
7. App is now available for all users in this customer

### Workflow 2: User Connects Instagram

1. User logs in
2. Navigates to "Social Platform" → "Instagram"
3. System checks if customer has active master app
4. If yes, shows "Connect Instagram Account" button
5. If no, shows "Contact admin to set up Instagram app"
6. User clicks "Connect"
7. OAuth popup opens using master app credentials
8. User authorizes
9. Credential saved with reference to master app

### Workflow 3: Admin Updates Master App

1. Admin navigates to "Social Media Apps"
2. Clicks "Edit" on Instagram app
3. Updates app secret (e.g., rotated for security)
4. Clicks "Save"
5. System re-encrypts new secret
6. Existing user credentials continue to work
7. New OAuth flows use updated credentials

## Error Handling

### No Master App Found
```json
{
  "status": "error",
  "error": "No active Instagram app configured for your organization. Please contact your administrator.",
  "code": "NO_MASTER_APP"
}
```

### Master App Inactive
```json
{
  "status": "error",
  "error": "Instagram app is currently inactive. Please contact your administrator.",
  "code": "MASTER_APP_INACTIVE"
}
```

### Invalid Credentials
```json
{
  "status": "error",
  "error": "Invalid Facebook App credentials. Please check your App ID and Secret.",
  "code": "INVALID_CREDENTIALS"
}
```

## Monitoring & Analytics

Track these metrics:
- Number of master apps per customer
- Number of Instagram accounts connected per user
- OAuth success/failure rates
- Token expiration and refresh rates
- API usage per master app

## Future Enhancements

1. **Token Refresh**: Auto-refresh Instagram tokens before expiry
2. **Multi-App Support**: Allow users to choose which master app to use
3. **App Analytics**: Show usage stats for each master app
4. **Webhook Management**: Configure webhooks per master app
5. **Platform Expansion**: Extend to TikTok, Twitter, LinkedIn, etc.
6. **Audit Logs**: Track all master app changes
7. **App Health Monitoring**: Check if master app credentials are still valid

    }
  ]
}
```

#### 3. Get Master App
```
GET /api/social-media/master-apps/:id
Headers:
  Authorization: Bearer <jwt_token>
  X-Customer-ID: customer_123
Response:
{
  "status": "success",
  "master_app": { ... }
}
```

#### 4. Update Master App
```
PUT /api/social-media/master-apps/:id
Body:
{
  "app_name": "Updated Name",
  "app_secret": "new_secret"  // Optional
}
```

#### 5. Delete Master App
```
DELETE /api/social-media/master-apps/:id
Response:
{
  "status": "success",
  "message": "Master app deleted",
  "affected_credentials": 5  // Number of user credentials that will be invalidated
}
```

#### 6. Activate/Deactivate Master App
```
POST /api/social-media/master-apps/:id/activate
Body:
{
  "is_active": true
}
```

### Instagram OAuth (Updated)

#### 1. Initiate OAuth
```
GET /api/social-media/instagram/oauth/initiate?master_app_id=xxx
Headers:
  Authorization: Bearer <jwt_token>
  X-Customer-ID: customer_123
  X-User-ID: user_456

Flow:
1. If master_app_id provided, use that app
2. Otherwise, find active master app for customer's platform
3. Generate OAuth URL using master app credentials
4. Return auth_url to frontend

Response:
{
  "status": "success",
  "auth_url": "https://www.facebook.com/v18.0/dialog/oauth?...",
  "master_app_id": "..."
}
```


