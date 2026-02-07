# Instagram Integration Verification Guide

## Current Status

✅ **Backend Implementation**: Complete
✅ **Frontend UI**: Complete
✅ **API Routes**: Registered
❌ **Environment Variables**: Not configured (causing 500 errors)

## Step 1: Configure Instagram App Credentials

### 1.1 Create Facebook App (if not already done)

1. Go to https://developers.facebook.com/
2. Click "My Apps" → "Create App"
3. Choose "Business" as app type
4. Fill in app details:
   - App Name: "Your News Automation Platform" (or any name)
   - App Contact Email: your email
5. Click "Create App"

### 1.2 Add Instagram Product

1. In your Facebook App dashboard, go to "Add Products"
2. Find "Instagram" and click "Set Up"
3. Choose "Instagram Graph API" (for Business/Creator accounts)

### 1.3 Configure OAuth Settings

1. Go to "App Settings" → "Basic"
2. Copy your **App ID** and **App Secret**
3. Go to "Settings" → "Basic"
4. Scroll down and click "Add Platform" → "Website"
5. Add OAuth Redirect URI in "Valid OAuth Redirect URIs":
   - For local: `http://localhost:8080/api/social-media/instagram/oauth/callback`
   - For production: `https://yourdomain.com/api/social-media/instagram/oauth/callback`
6. Save changes

### 1.4 Add Required Permissions

Make sure your app has these permissions:
- `instagram_basic` - Read basic Instagram account info
- `instagram_content_publish` - Publish content to Instagram
- `pages_read_engagement` - Read Facebook Page data
- `pages_show_list` - List Facebook Pages

## Step 2: Update Environment Variables

Add these lines to your `.env` file:

```bash
# Instagram API Configuration
INSTAGRAM_APP_ID=876162771907731
INSTAGRAM_APP_SECRET=your_app_secret_here
# OAuth callback goes through API server (port 8080)
INSTAGRAM_REDIRECT_URI=http://localhost:8080/api/social-media/instagram/oauth/callback
```

**Replace** `your_app_secret_here` with the actual App Secret from Facebook App Settings → Basic (click "Show" button).

## Step 3: Restart Services

After updating `.env`, restart the services:

```bash
./deploy-news-services.sh --build --service social-media-uploader ichat-api
```

Or using docker-compose:

```bash
docker-compose restart social-media-uploader ichat-api
```

## Step 4: Verify Backend is Running

Check if the social-media-uploader service is running:

```bash
docker-compose ps social-media-uploader
```

Check logs:

```bash
docker-compose logs -f social-media-uploader
```

Test health endpoint:

```bash
curl http://localhost:8097/health
```

## Step 5: Manual Verification Steps

### 5.1 Access Instagram Platform Page

1. Open browser: http://localhost:3002
2. Login to your account
3. Navigate to: **Social Platform** (from sidebar)
4. Click on **Instagram** card
5. You should see the Instagram Platform Management page

### 5.2 Connect Instagram Account

**Prerequisites:**
- You need an Instagram Business or Creator account
- Instagram account must be connected to a Facebook Page
- You must have admin access to that Facebook Page

**Steps:**
1. Click "Connect Instagram Account" button
2. A popup window should open with Facebook OAuth
3. Login to Facebook (if not already logged in)
4. Select the Facebook Page connected to your Instagram
5. Click "Allow" to authorize the app
6. Popup should close automatically
7. Your Instagram account should appear in the list

### 5.3 Verify Account is Connected

After connecting, you should see:
- Instagram username (e.g., @yourusername)
- Green "Connected" badge
- Instagram ID
- Connection date
- "Disconnect" button

### 5.4 Check Database

Verify credentials are saved in MongoDB:

```bash
docker exec -it ichat-mongodb mongosh -u ichat_app -p ichat_app_password_2024 --authenticationDatabase admin
```

Then run:

```javascript
use news
db.instagram_credentials.find().pretty()
```

You should see your Instagram credentials with:
- `customer_id`
- `user_id`
- `instagram_user_id`
- `instagram_username`
- `access_token` (encrypted)
- `is_authenticated: true`

## Step 6: Test API Endpoints

### 6.1 Test OAuth Initiate

```bash
curl -X GET "http://localhost:8080/api/social-media/instagram/oauth/initiate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Customer-ID: your_customer_id" \
  -H "X-User-ID: your_user_id"
```

Expected response:
```json
{
  "status": "success",
  "auth_url": "https://www.facebook.com/v18.0/dialog/oauth?client_id=..."
}
```

### 6.2 Test Get Credentials

```bash
curl -X GET "http://localhost:8080/api/social-media/instagram/credentials" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Customer-ID: your_customer_id" \
  -H "X-User-ID: your_user_id"
```

Expected response:
```json
{
  "status": "success",
  "credentials": [
    {
      "_id": "...",
      "instagram_username": "yourusername",
      "instagram_user_id": "...",
      "is_authenticated": true,
      "created_at": "..."
    }
  ]
}
```

## Troubleshooting

### Error: "Instagram API credentials not configured"

**Cause**: Environment variables not set
**Solution**: 
1. Add credentials to `.env` file (see Step 2)
2. Restart services (see Step 3)

### Error: "No Facebook pages found"

**Cause**: Your Facebook account doesn't have any pages
**Solution**: Create a Facebook Page and connect it to your Instagram Business account

### Error: "No Instagram Business Account found"

**Cause**: Instagram account is not converted to Business/Creator
**Solution**: 
1. Open Instagram app
2. Go to Settings → Account
3. Switch to Professional Account
4. Choose Business or Creator
5. Connect to your Facebook Page

### OAuth popup doesn't close

**Cause**: CORS or redirect URI mismatch
**Solution**:
1. Check redirect URI in Facebook App settings matches `.env`
2. Check browser console for errors
3. Manually close popup and refresh the page

## Next Steps After Verification

Once Instagram OAuth is working:

1. ✅ Test connecting multiple Instagram accounts
2. ✅ Test disconnecting accounts
3. 🚧 Implement Instagram posting functionality
4. 🚧 Add support for Instagram Stories
5. 🚧 Add support for Instagram Reels
6. 🚧 Implement other platforms (TikTok, Twitter, etc.)

## Files Modified/Created

### Created:
- `frontend-server/src/components/InstagramUploader/InstagramCredentialsManager.jsx`
- `frontend-server/src/components/InstagramUploader/index.js`
- `frontend-server/src/pages/InstagramPlatformPage.jsx`
- `INSTAGRAM_VERIFICATION_GUIDE.md` (this file)

### Modified:
- `docker-compose.yml` - Replaced youtube-uploader with social-media-uploader
- `deploy-news-services.sh` - Updated service name and directories
- `api-server/app.py` - Registered social_media_bp blueprint
- `frontend-server/src/App.jsx` - Added Instagram route
- `frontend-server/src/pages/SocialPlatformPage.jsx` - Updated to navigate to dedicated pages

