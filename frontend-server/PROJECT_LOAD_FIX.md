# 🔧 Project Load Fixes

## Issues Fixed

### 1. ✅ Videos Not Visible After Loading Project

**Problem:**
- Videos were uploaded successfully to MinIO during project save
- After loading project, videos had MinIO URLs but weren't visible on canvas
- Root cause: MinIO URLs were internal Docker URLs (e.g., `minio:9000/video-assets/...`) that:
  - Can't be accessed from browser (internal Docker hostname)
  - Require authentication to access

**Solution:**
Modified `asset-service/routes/asset_routes.py` upload endpoint to return **presigned URLs** instead of regular MinIO URLs:

```python
# Generate presigned URL for browser access (valid for 24 hours)
presigned_url = storage_service.get_presigned_url(
    bucket=bucket,
    object_name=storage_key,
    expires=timedelta(hours=24)
)

# Return response with presigned URL
return {
    "success": True,
    "asset_id": asset_id,
    "url": presigned_url,  # Presigned URL for browser access
    "asset": {
        "asset_id": asset_id,
        "storage": {
            "url": presigned_url  # Also in asset object
        }
    }
}
```

**Benefits:**
- Presigned URLs work from browser (no authentication needed)
- URLs are publicly accessible for 24 hours
- Videos load correctly after project load

---

### 2. ✅ Media Not Appearing in Left Sidebar After Loading Project

**Problem:**
- When loading a project, audio/video tracks appeared on timeline
- But they didn't appear in the left sidebar media lists
- Root cause: `uploadedAudio` and `uploadedVideo` state variables weren't being populated from loaded project data

**Solution:**
Added `extractMediaFromProject()` function in `DesignEditor.jsx` that:

1. **Extracts audio from audio tracks:**
```javascript
const audioItems = (project.audioTracks || []).map(track => ({
  id: track.id,
  type: 'audio',
  url: track.url,
  title: track.name || 'Audio',
  duration: track.duration
}));
```

2. **Extracts videos from video tracks:**
```javascript
const videoFromTracks = (project.videoTracks || []).map(track => ({
  id: track.id,
  type: 'video',
  url: track.url || track.src,
  title: track.name || 'Video',
  duration: track.duration || track.originalDuration
}));
```

3. **Extracts videos from page elements:**
```javascript
const videoFromElements = [];
(project.pages || []).forEach(page => {
  (page.elements || []).forEach(el => {
    if (el.type === 'video' && el.src) {
      videoFromElements.push({
        id: el.id,
        type: 'video',
        url: el.src,
        title: 'Video Element',
        duration: el.duration
      });
    }
  });
});
```

4. **Populates sidebar media lists:**
```javascript
const media = extractMediaFromProject(project);
setUploadedAudio(media.audio);
setUploadedVideo(media.video);
```

**Benefits:**
- All media from loaded project appears in left sidebar
- Users can see and reuse media from loaded projects
- Consistent experience between save and load

---

## Files Modified

### Backend:
1. **asset-service/routes/asset_routes.py** (Lines 186-217)
   - Changed upload response to return presigned URLs
   - Added full asset object to response
   - URLs valid for 24 hours

### Frontend:
2. **frontend-server/src/components/DesignEditor/DesignEditor.jsx** (Lines 884-982)
   - Added `extractMediaFromProject()` function
   - Updated `handleLoadProject()` to populate media lists
   - Added detailed logging for debugging

---

## Testing Checklist

### Test Video Visibility:
- [ ] Upload a video to a slide
- [ ] Save the project
- [ ] Reload the page
- [ ] Load the project
- [ ] ✅ Video should be visible on canvas
- [ ] ✅ Video should play when timeline plays

### Test Media Sidebar:
- [ ] Create a new project
- [ ] Upload 2 audio files
- [ ] Upload 3 videos
- [ ] Add 1 video to canvas
- [ ] Save the project
- [ ] Reload the page
- [ ] Load the project
- [ ] ✅ Left sidebar should show 2 audio items
- [ ] ✅ Left sidebar should show 3 video items
- [ ] ✅ Canvas should show 1 video element

### Test Presigned URL Expiration:
- [ ] Save a project with video
- [ ] Wait 24+ hours
- [ ] Load the project
- [ ] ⚠️ Video may not load (URL expired)
- [ ] **Future enhancement:** Refresh presigned URLs on load

---

## Console Logs to Watch

### During Project Save:
```
📤 Asset upload request received
✅ Asset uploaded successfully: {asset_id}
💾 Saving project...
✅ Project saved successfully
```

### During Project Load:
```
📂 Loaded project: {project_id}
📦 Extracting media from project: {...}
📦 Extracted media: { audio: 2, video: 3 }
✅ Media lists populated: { uploadedAudio: 2, uploadedVideo: 3 }
✅ Project loaded successfully
```

### During Video Rendering:
```
🎬 Rendering video element: {element_id} src: https://minio:9000/...
🎬 Video onLoadedMetadata: {element_id} duration: 15.5
🎬 Video onCanPlay: {element_id}
```

---

## Known Limitations

### 1. Presigned URL Expiration
- **Issue:** Presigned URLs expire after 24 hours
- **Impact:** Projects older than 24 hours may have broken video/audio links
- **Future Fix:** Refresh presigned URLs when loading old projects

### 2. Images Not Handled
- **Issue:** Images are stored as base64 data URLs, not uploaded to MinIO
- **Impact:** Large images increase project size
- **Future Fix:** Upload images to MinIO like videos/audio

---

## Next Steps

1. **Restart Asset Service** to load the new upload endpoint code:
   ```bash
   docker-compose restart ichat-asset-service
   ```

2. **Test the fixes:**
   - Create a project with videos and audio
   - Save the project
   - Reload the page
   - Load the project
   - Verify videos are visible and media appears in sidebar

3. **Monitor logs:**
   ```bash
   docker-compose logs -f ichat-asset-service
   docker-compose logs -f ichat-api
   ```

---

**Last Updated:** 2026-02-01  
**Version:** 1.0.0

