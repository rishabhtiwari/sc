# Media Library Upload Fix (Audio, Image, Video)

## Problem
Media files (audio, images, videos) from their respective libraries were being re-uploaded to the asset service every time a project was saved, even though they were already stored in the library.

### Root Cause
When audio from the library was added to the timeline:
1. The audio had an `audio_id` in the library
2. When added to timeline via `handleAddAudioTrack`, the `audio_id` was not preserved
3. When saving the project, the code checked if the URL was a blob or audio service URL
4. Since audio library URLs are audio service URLs (e.g., `/api/audio-studio/preview/{audio_id}`), they were treated as temporary and re-uploaded

## Solution

### Changes Made

#### 1. **DesignEditor.jsx** - Preserve audio_id when adding to timeline
- Updated `handleAddAudioTrack` to accept audio metadata object (not just File)
- Added `assetId` and `libraryId` to the track when audio has an `audio_id`

```javascript
const newTrack = {
  // ... other fields
  assetId: audioFile.audio_id || audioFile.libraryId || audioFile.assetId,
  libraryId: audioFile.audio_id || audioFile.libraryId
};
```

#### 2. **MediaPanel.jsx** - Pass audio metadata when adding from library
- Changed to pass audio metadata object instead of just file name
- Includes `audio_id`, `libraryId`, and `assetId`

```javascript
const audioMetadata = {
  name: media.title || media.name,
  audio_id: media.audio_id || media.libraryId,
  libraryId: media.libraryId || media.audio_id,
  assetId: media.assetId
};
onAddAudioTrack(audioMetadata, media.url);
```

#### 3. **projectDataHelpers.js** - Check for assetId before uploading
- Added check for `track.assetId` or `track.libraryId` before uploading
- If audio has an assetId, skip upload and use existing library reference

```javascript
// Check if audio already has an assetId or libraryId (from audio library)
if (track.assetId || track.libraryId) {
  console.log(`✅ Audio already in library, skipping upload`);
  // Keep existing assetId and URL
}
```

#### 4. **AudioLibraryPage.jsx** - Include audio_id when navigating back
- Added `audio_id`, `libraryId`, and `assetId` to the addAsset state

#### 5. **DesignEditor.jsx** - Preserve audio_id when adding from library
- Updated to include `audio_id`, `libraryId`, and `assetId` when adding audio to media list

## How It Works Now

### Adding Audio from Library to Timeline
1. User selects audio from library (has `audio_id`)
2. Audio is added to media list with `audio_id`, `libraryId`, `assetId`
3. When added to timeline, these IDs are preserved in the track
4. Track now has: `{ assetId: "audio_id", url: "/api/audio-studio/preview/audio_id" }`

### Saving Project
1. When preparing project data, check each audio track
2. If track has `assetId` or `libraryId`, skip upload
3. Save track with existing `assetId` and URL
4. Backend stores: `{ assetId: "audio_id", url: "/api/audio-studio/preview/audio_id" }`

### Loading Project
1. Load project from backend
2. Audio tracks have `assetId` and stable proxy URL
3. Proxy URL (`/api/audio-studio/preview/{audio_id}`) fetches fresh presigned URL from MinIO
4. Audio plays correctly without re-upload

## Benefits
- ✅ No duplicate uploads of library audio
- ✅ Faster project saves
- ✅ Reduced storage usage
- ✅ Consistent audio references
- ✅ Proper library tracking

## Extended Fix for Images and Videos

### Additional Changes Made

#### 1. **projectDataHelpers.js** - Check for assetId/libraryId before uploading images/videos
- Added check for `element.assetId` or `element.libraryId` before uploading
- If image/video has an assetId, skip upload and use existing library reference

```javascript
// Check if element already has an assetId or libraryId (from library)
if (element.assetId || element.libraryId) {
  console.log(`✅ ${element.type} already in library, skipping upload`);
  // Keep existing assetId and URL
}
```

#### 2. **MediaPanel.jsx** - Preserve libraryId/assetId when adding videos
- Updated video addition to include `libraryId` and `assetId`

```javascript
onAddElement({
  // ... other fields
  libraryId: media.libraryId || media.video_id,
  assetId: media.assetId || media.libraryId || media.video_id
});
```

#### 3. **ImagesPanel.jsx** - Preserve assetId when adding images
- Updated image addition to include `assetId` in addition to existing `libraryId`

## Testing
To verify the fix:

### Audio
1. Generate audio in Audio Studio and save to library
2. Add audio from library to timeline in Design Editor
3. Save the project
4. Check network tab - should NOT see upload to `/api/assets/upload`
5. Load the project - audio should play correctly

### Images
1. Upload image to image library
2. Add image from library to canvas in Design Editor
3. Save the project
4. Check network tab - should NOT see upload to `/api/assets/upload`
5. Load the project - image should display correctly

### Videos
1. Upload video to video library
2. Add video from library to canvas in Design Editor
3. Save the project
4. Check network tab - should NOT see upload to `/api/assets/upload`
5. Load the project - video should play correctly

## Known Separate Issue
There is a separate issue where newly uploaded audio files (not from library) are trying to be saved to the audio library with incorrect field names (`audio_url` instead of `audioUrl`). This is unrelated to the library re-upload fix and needs to be addressed separately.

