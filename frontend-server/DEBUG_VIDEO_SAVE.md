# 🔍 Debug: Video Not Being Saved in Project

## Problem
When adding a video to a slide, the video is not appearing in the saved project data. The page elements array only contains text and image elements, but no video elements.

## Investigation Steps

### 1. Added Comprehensive Logging

**In `handleAddElement()` (Lines 80-152):**
- Logs when element is added
- Shows element type, src, file, duration
- Shows which page it's being added to
- Shows element count before/after

**In `handleSaveProject()` (Lines 927-979):**
- Logs current state before save
- Shows all pages and their elements
- Shows video tracks and audio tracks count

**In `prepareProjectData()` (Lines 812-867):**
- Logs each page being processed
- Logs each element in each page
- Shows if video is being uploaded
- Shows upload success/failure

### 2. Expected Console Output

When you **add a video to a slide**, you should see:

```
🎨 handleAddElement called with: {
  type: 'video',
  hasSrc: true,
  hasFile: true,
  duration: 15.5,
  width: 640,
  height: 360
}
✅ Created new element: {
  id: 'element-1234567890',
  type: 'video',
  hasSrc: true,
  hasFile: true
}
📄 Adding element to page 0: {
  pageId: 'page-1',
  pageName: 'Slide 1',
  oldElementCount: 2,
  newElementCount: 3,
  newElementId: 'element-1234567890',
  newElementType: 'video'
}
✅ Pages updated. Total pages: 1
✅ Current page elements: 3
🎬 Video added with duration: 15.5
📊 Slide duration updated to: 16
🎬 Adding video to timeline: {...}
```

When you **save the project**, you should see:

```
💾 Current state before save:
  📄 Pages: 1
    Page 0 (Slide 1): {
      id: 'page-1',
      elementCount: 3,
      elements: [
        { id: '...', type: 'text', hasSrc: false, hasFile: false },
        { id: '...', type: 'image', hasSrc: true, hasFile: false },
        { id: 'element-1234567890', type: 'video', hasSrc: true, hasFile: true }
      ]
    }
  🎬 Video tracks: 1
  🎵 Audio tracks: 0

💾 Preparing project data...
📄 Pages to process: 1
📄 Processing page 0: { id: 'page-1', name: 'Slide 1', elementCount: 3 }
  🔍 Element 0: { type: 'text', ... }
  🔍 Element 1: { type: 'image', ... }
  🔍 Element 2: { type: 'video', id: 'element-1234567890', hasSrc: true, hasFile: true, srcType: 'blob:http:' }
  📤 Uploading video: video.mp4
  ✅ Uploaded successfully: { asset_id: '...', url: 'https://...' }
  ✅ Page 0 processed: 3 elements
✅ All pages processed: 1
```

### 3. What to Check

**If video is NOT in the console logs when adding:**
- `handleAddElement` is not being called
- Check if MediaPanel is calling `onAddElement` correctly
- Check if there's an error preventing the function from running

**If video IS in logs when adding, but NOT when saving:**
- The `pages` state is being reset somewhere
- Check if there's a state update that's removing the video element
- Check if the page is being replaced instead of updated

**If video IS in logs when saving, but NOT uploaded:**
- The `element.file` property is missing
- Check if the file reference is being lost
- Check if there's an error during upload

## Next Steps

1. **Add a video to a slide**
2. **Open browser console** (F12)
3. **Look for the logs** starting with 🎨, 📄, ✅
4. **Click "Save Project"**
5. **Look for the logs** starting with 💾, 📄, 🔍, 📤
6. **Copy all the logs** and share them

The logs will tell us exactly where the video element is being lost!

## Possible Issues

### Issue A: Video element not being added to page
- `handleAddElement` not called
- Element added to wrong page
- State update not working

### Issue B: Video element added but lost before save
- State being reset
- Page being replaced
- Element being filtered out

### Issue C: Video element present but file missing
- File reference lost
- Blob URL revoked
- File not passed correctly

---

**Created:** 2026-02-01  
**Status:** Investigating

