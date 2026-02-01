# Text-to-Video Workflow Implementation Plan
## Canva/Veed.io Style Approach

## Overview
Enable users to go from **AI-generated text → Formatted slides → Voiceover → Video export** in a seamless workflow.

---

## Current Implementation Status

### ✅ Already Implemented
1. **Text Studio** - AI text generation with templates
2. **Design Editor** - Canvas-based slide designer
3. **Audio Studio** - TTS voice generation
4. **Basic Export** - Image/PDF export

### 🚧 What We're Adding Now
1. **"Create Slides" button** in Text Studio (✅ Just added)
2. **Workflow guide** showing next steps (✅ Just added)
3. **Auto-split text into slides** (⏳ Next step)
4. **Audio-per-slide** functionality (⏳ Next step)
5. **Video export with audio sync** (⏳ Next step)

---

## Detailed Workflow

### Step 1: Generate Text (Text Studio)
**User Action:**
- Opens Text Studio from main menu
- Generates text using AI templates or custom prompt
- Sees generated text in rich text editor

**New Features Added:**
- ✅ "Create Slides" button (navigates to Design Editor)
- ✅ Workflow guide showing 4-step process
- ✅ Text passed via URL parameter

**Code Location:**
- `frontend-server/src/components/DesignEditor/TextStudio/TextStudio.jsx` (lines 682-738)

---

### Step 2: Create Slides (Design Editor)

**User Action:**
- Clicks "Create Slides" button
- Redirected to Design Editor with text content
- Text is automatically split into slides

**Implementation Needed:**

#### 2.1 Auto-Split Text into Slides
**Algorithm:**
```javascript
function splitTextIntoSlides(text) {
  // Split by paragraphs or sentences
  const paragraphs = text.split('\n\n');
  
  // Create one slide per paragraph (or combine short ones)
  const slides = [];
  let currentSlide = '';
  
  paragraphs.forEach(para => {
    if (para.length < 100 && currentSlide.length < 200) {
      currentSlide += para + '\n';
    } else {
      if (currentSlide) slides.push(currentSlide.trim());
      currentSlide = para;
    }
  });
  
  if (currentSlide) slides.push(currentSlide.trim());
  return slides;
}
```

**File to Create:**
- `frontend-server/src/utils/slideGenerator.js`

#### 2.2 Design Editor URL Parameter Handling
**Update:** `frontend-server/src/pages/DesignEditorPage.jsx`

```javascript
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const action = params.get('action');
  const text = params.get('text');
  
  if (action === 'create-slides' && text) {
    const slides = splitTextIntoSlides(decodeURIComponent(text));
    createSlidesFromText(slides);
  }
}, []);
```

#### 2.3 Slide Templates
**Pre-designed templates:**
- Title Slide (large centered text)
- Content Slide (bullet points)
- Quote Slide (centered quote with attribution)
- Image + Text Slide (50/50 split)

**File to Create:**
- `frontend-server/src/constants/slideTemplates.js`

---

### Step 3: Add Audio (Audio Studio Integration)

**User Action:**
- In Design Editor, clicks "Add Audio" for each slide
- Opens Audio Studio modal
- Generates TTS for slide text
- Audio automatically attached to that slide

**Implementation Needed:**

#### 3.1 Per-Slide Audio
**Data Structure:**
```javascript
{
  slides: [
    {
      id: 'slide-1',
      elements: [...],
      audio: {
        url: 'http://minio:9000/audio/slide1.wav',
        duration: 5.2,
        text: 'Welcome to our presentation...'
      }
    }
  ]
}
```

#### 3.2 Audio Studio Integration
**Update:** `frontend-server/src/components/DesignEditor/DesignEditor.jsx`

Add "Add Audio" button to each slide in timeline:
```javascript
<button onClick={() => openAudioStudioForSlide(slideId)}>
  🎙️ Add Voiceover
</button>
```

---

### Step 4: Export Video

**User Action:**
- Clicks "Export as Video" button
- System generates MP4 with:
  - Each slide shown for duration of its audio
  - Smooth transitions between slides
  - Synchronized audio track

**Implementation Needed:**

#### 4.1 Video Export Service
**New Backend Service:** `video-export-service`

**Technology:** FFmpeg

**Endpoint:**
```
POST /api/video/export
{
  "slides": [
    {
      "image_url": "slide1.png",
      "audio_url": "slide1.wav",
      "duration": 5.2
    }
  ],
  "transitions": "fade",
  "resolution": "1920x1080"
}
```

**Response:**
```json
{
  "video_url": "http://minio:9000/videos/presentation_123.mp4",
  "duration": 45.6
}
```

---

## Implementation Priority

### Phase 1: Basic Slide Creation (Week 1)
- [x] Add "Create Slides" button in Text Studio
- [x] Add workflow guide
- [ ] Implement `splitTextIntoSlides()` utility
- [ ] Handle URL parameters in Design Editor
- [ ] Auto-create slides from text

### Phase 2: Slide Templates (Week 2)
- [ ] Create 4 basic slide templates
- [ ] Template selector UI
- [ ] Apply template to slide

### Phase 3: Per-Slide Audio (Week 3)
- [ ] Add audio property to slide data model
- [ ] "Add Audio" button in timeline
- [ ] Audio Studio integration for slides
- [ ] Audio preview in timeline

### Phase 4: Video Export (Week 4)
- [ ] Create video-export-service
- [ ] FFmpeg integration
- [ ] Export UI with progress bar
- [ ] Download/share video

---

## Next Immediate Steps

1. **Create `slideGenerator.js` utility** to split text into slides
2. **Update DesignEditorPage** to handle `?action=create-slides&text=...` URL params
3. **Test the flow:** Text Studio → Create Slides → Design Editor

Would you like me to implement these next steps now?

