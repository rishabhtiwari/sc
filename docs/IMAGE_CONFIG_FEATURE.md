# Image Cleaning Configuration Feature

## Overview

This feature allows customers to configure whether images require manual watermark removal or should be automatically marked as cleaned. This provides flexibility for customers who:
- Already have clean images and don't need watermark removal
- Want to skip the manual cleaning process
- Need to process images quickly without AI intervention

## Features

### 1. Configurable Cleaning Mode

**Manual Cleaning Mode** (Default):
- Images require manual watermark removal
- Users paint over watermarks and use AI to remove them
- Full editing tools available

**Auto-Mark Mode**:
- Images are automatically marked as cleaned
- No watermark removal processing
- Original images are used as "cleaned" images
- Faster processing for bulk operations

### 2. Multi-Tenancy Support

- Each customer has their own configuration
- Settings are isolated by `customer_id`
- Automatic context extraction from JWT headers
- No cross-customer data leakage

### 3. User Interface

- Toggle switch on Image Cleaning page
- Visual indicators for current mode
- Contextual instructions based on mode
- Simplified controls in auto-mark mode

## Architecture

### Database Schema

**Collection**: `image_config`

```javascript
{
  _id: ObjectId,
  customer_id: String,        // Unique per customer
  auto_mark_cleaned: Boolean, // true = auto-mark, false = manual
  created_at: Date,
  updated_at: Date
}
```

**Indexes**:
- `customer_id`: Unique index for fast lookups

### API Endpoints

#### Get Configuration
```
GET /api/image/config
Authorization: Bearer <jwt_token>

Response:
{
  "customer_id": "customer_123",
  "auto_mark_cleaned": false,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

#### Update Configuration
```
PUT /api/image/config
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "auto_mark_cleaned": true
}

Response:
{
  "customer_id": "customer_123",
  "auto_mark_cleaned": true,
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T12:00:00Z"
}
```

### Backend Implementation

**Files Modified**:
1. `jobs/watermark-remover/iopaint_ui_service.py`
   - Added `get_or_create_image_config()` function
   - Added `/api/image-config` GET/PUT endpoints
   - Modified `/api/save` to check config and auto-mark if enabled

2. `api-server/routes/image_routes.py`
   - Added proxy routes for `/image/config` GET/PUT

### Frontend Implementation

**Files Modified**:
1. `frontend-server/src/services/imageService.js`
   - Added `getImageConfig()` method
   - Added `updateImageConfig()` method

2. `frontend-server/src/pages/ImageCleaningPage.jsx`
   - Added config state management
   - Added toggle switch UI
   - Added auto-mark mode notice
   - Modified save logic to handle both modes
   - Conditional rendering based on mode

3. `frontend-server/src/components/ImageCleaning/ControlPanel.jsx`
   - Added `autoMarkMode` prop
   - Conditional rendering of editing tools
   - Updated button labels for auto-mark mode

## Usage

### For Administrators

1. **Run Migration**:
```bash
cd jobs/watermark-remover/migrations
export MONGODB_URL="mongodb://ichat_app:ichat_app_password_2024@ichat-mongodb:27017/news?authSource=admin"
python3 001_create_image_config.py
```

2. **Verify Migration**:
```javascript
// In MongoDB shell
db.image_config.find().pretty()
db.image_config.getIndexes()
```

### For End Users

1. **Navigate to Image Cleaning Page**
2. **Toggle Auto-Mark Setting**:
   - ON: Images will be marked as cleaned automatically
   - OFF: Manual watermark removal required

3. **Process Images**:
   - **Auto-Mark Mode**: Click "Load Next Image" → "Save & Next"
   - **Manual Mode**: Click "Load Next Image" → Paint watermark → "Remove Watermark" → "Save & Mark Done"

## Data Flow

### Manual Cleaning Mode
```
User loads image
  ↓
GET /api/image/next-image
  ↓
Backend returns: { doc_id, image_url, original_image_url }
  ↓
Frontend displays image from URL (no base64 conversion)
  ↓
User paints watermark mask
  ↓
User clicks "Remove Watermark"
  ↓
POST /api/image/process (with image_url + mask_data)
  ↓
Backend fetches image from URL
  ↓
AI removes watermark
  ↓
Backend returns processed image as base64
  ↓
Frontend displays processed image
  ↓
User clicks "Save & Mark Done"
  ↓
POST /api/image/save (with processed image as base64)
  ↓
Cleaned image saved to disk
  ↓
MongoDB updated with clean_image path
```

### Auto-Mark Mode
```
User loads image
  ↓
GET /api/image/next-image
  ↓
Backend returns: { doc_id, image_url, original_image_url }
  ↓
Frontend displays image from URL
  ↓
User clicks "Save & Next"
  ↓
POST /api/image/save (doc_id only, no image data)
  ↓
Backend checks config: auto_mark_cleaned = true
  ↓
MongoDB updated with clean_image = original image URL
  ↓
auto_marked_cleaned flag set to true
  ↓
Next image loaded
```

## Performance Optimizations

### Network Optimization
The system is optimized to minimize network data transfer:

1. **Image Loading**: Images are loaded directly from URLs, not converted to base64
2. **Processing**: Only the image URL and mask data are sent to backend
3. **Backend Fetching**: Backend fetches the original image from URL when needed
4. **Auto-Mark Mode**: No image data is transferred at all

### Benefits
- **Reduced Bandwidth**: Image URLs (~100 bytes) instead of base64 data (~1-5 MB)
- **Faster Loading**: Direct image display without base64 conversion
- **Lower Memory**: No need to store large base64 strings in frontend state
- **Better Performance**: Especially beneficial for high-resolution images

## Benefits

1. **Flexibility**: Customers choose their workflow
2. **Performance**: Skip AI processing when not needed
3. **Cost Savings**: Reduce GPU usage for customers with clean images
4. **User Experience**: Simplified UI for auto-mark mode
5. **Multi-Tenancy**: Isolated configurations per customer

## Migration Path

Existing customers are automatically migrated with `auto_mark_cleaned=false` (manual mode), ensuring no change in behavior until they explicitly enable auto-mark mode.

## Testing Checklist

- [ ] Migration creates image_config collection
- [ ] Default configs created for all customers
- [ ] GET /api/image/config returns correct data
- [ ] PUT /api/image/config updates configuration
- [ ] Toggle switch works in UI
- [ ] Auto-mark mode marks images correctly
- [ ] Manual mode still works as before
- [ ] Multi-tenancy isolation verified
- [ ] Original images used in auto-mark mode
- [ ] Cleaned images saved in manual mode

