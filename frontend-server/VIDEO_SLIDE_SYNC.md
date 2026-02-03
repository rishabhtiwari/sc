# 🎬 Video-Slide Synchronization System

## Overview

Videos added to slides are automatically synchronized with slide timing. Videos start when their slide starts and end when the slide ends (before the next slide begins).

## ✨ Features

### 1. **Automatic Slide Duration Adjustment**
When a video is added to a slide:
- Slide duration automatically adjusts to match video duration
- Example: 15.5 second video → slide becomes 16 seconds (rounded up)

### 2. **Video Timeline Constraint**
Videos on the timeline are constrained to their slide's duration:
- If video is **longer** than slide → video is trimmed from the end
- If video is **shorter** than slide → video plays fully, then shows last frame
- Video track duration = `Math.min(videoDuration, slideDuration)`

### 3. **Slide Duration Changes**
When slide duration is manually changed:
- All videos on that slide are automatically updated
- Video track durations are recalculated
- Trimming is adjusted accordingly

### 4. **Video Playback Control**
Videos only play during their slide's time range:
- Video starts at: `slideStartTime`
- Video ends at: `slideStartTime + slideDuration`
- Video pauses when slide ends
- Video resets when navigating away from slide

## 🔧 Technical Implementation

### Adding Video to Slide

**File:** `DesignEditor.jsx` - `handleAddElement()`

```javascript
// 1. Auto-adjust slide duration to match video
if (element.type === 'video' && element.duration > 0) {
  updatedPage.duration = Math.ceil(element.duration);
}

// 2. Create video track constrained to slide duration
const slideDuration = currentSlide.duration || 5;
const videoTrackDuration = Math.min(element.duration, slideDuration);
const trimEnd = element.duration > slideDuration ? element.duration - slideDuration : 0;

const videoTrack = {
  startTime: slideStartTime,
  duration: videoTrackDuration,  // Constrained
  originalDuration: element.duration,
  trimEnd: trimEnd,
  slideIndex: currentPageIndex
};
```

### Updating Slide Duration

**File:** `DesignEditor.jsx` - `handleSlideUpdate()`

```javascript
// When slide duration changes, update all videos on that slide
if (updates.duration !== undefined) {
  setVideoTracks(prevTracks => prevTracks.map(track => {
    if (track.slideIndex === slideIndex) {
      const constrainedDuration = Math.min(track.originalDuration, newDuration);
      const trimEnd = track.originalDuration > newDuration 
        ? track.originalDuration - newDuration 
        : 0;
      
      return {
        ...track,
        duration: constrainedDuration,
        trimEnd: trimEnd
      };
    }
    return track;
  }));
}
```

### Video Playback Control

**File:** `DesignEditor.jsx` - `useEffect()` for video playback

```javascript
// Calculate time within current slide
const timeInSlide = currentTime - slideStartTime;

// Only play if within slide duration
if (isPlaying && timeInSlide >= 0 && timeInSlide < slideDuration) {
  // Sync video time with timeline
  videoEl.currentTime = timeInSlide;
  videoEl.play();
} else {
  // Pause when outside slide range
  videoEl.pause();
}
```

## 📊 Data Flow

```
User Uploads Video
  ↓
MediaPanel extracts duration (e.g., 15.5s)
  ↓
User adds video to slide
  ↓
DesignEditor.handleAddElement()
  ├─ Updates slide duration: 16s (rounded up)
  ├─ Creates video track:
  │   - startTime: slideStartTime
  │   - duration: min(15.5, 16) = 15.5s
  │   - trimEnd: 0
  └─ Adds to videoTracks array
  ↓
Timeline renders video block (15.5s long)
  ↓
Playback starts
  ↓
Video plays from 0s to 15.5s
  ↓
Slide ends at 16s
  ↓
Next slide begins
```

## 🎯 Example Scenarios

### Scenario 1: Video Shorter Than Slide
- Video: 10 seconds
- Slide: 15 seconds (manually set)
- Result: Video plays 0-10s, then shows last frame until 15s

### Scenario 2: Video Longer Than Slide
- Video: 20 seconds
- Slide: 15 seconds (manually set)
- Result: Video plays 0-15s, then is trimmed (last 5s not shown)

### Scenario 3: Auto-Adjust
- Video: 12.7 seconds
- Slide: Initially 5 seconds
- Result: Slide auto-adjusts to 13 seconds, video plays fully

### Scenario 4: Multiple Videos on One Slide
- Video 1: 10 seconds
- Video 2: 15 seconds (added later)
- Result: Slide adjusts to 15s, Video 1 plays 0-10s, Video 2 plays 0-15s

## 🔍 Console Logs

### When Adding Video:
```
🎬 Adding video to canvas. Duration: 15.5
🎨 handleAddElement called with: {type: 'video', duration: 15.5, ...}
🎬 Video added with duration: 15.5
📊 Slide duration updated to: 16
🎬 Adding video to timeline: {
  slideDuration: 16,
  videoOriginalDuration: 15.5,
  trimmed: false
}
```

### When Changing Slide Duration:
```
📊 Slide duration updated to: 20 for slide: 0
🎬 Updating video track duration: {
  trackId: "element-123",
  oldDuration: 15.5,
  newDuration: 15.5,
  slideDuration: 20,
  originalDuration: 15.5,
  trimEnd: 0
}
```

### During Playback:
```
🎬 Video playback control: {
  currentPageIndex: 0,
  videoCount: 1,
  isPlaying: true,
  currentTime: 5.2,
  slideStartTime: 0,
  timeInSlide: 5.2,
  slideDuration: 16
}
🎬 Should play video: element-123
```

## 🚀 Future Enhancements

- [ ] Support for video start offset (trim from beginning)
- [ ] Video speed adjustment to fit slide duration
- [ ] Multiple video layers on same slide
- [ ] Video transitions between slides
- [ ] Picture-in-picture video support
- [ ] Video effects and filters

---

**Last Updated:** 2026-02-01  
**Version:** 1.0.0

