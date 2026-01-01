# 🎨 Canva-Like Design Platform - Complete Implementation Plan

## 📋 Executive Summary

Transform the existing template system into a full-featured Canva-like design platform with:
- **Category-based template selection** (9 categories)
- **Unified canvas-based editor** (video, image, audio)
- **Timeline-based editing** for videos
- **Real-time collaboration** (future)
- **Export to multiple formats**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 FRONTEND (React + Canvas)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Category    │  │   Unified    │  │  Specialized │      │
│  │  Selection   │→ │   Editor     │→ │   Editors    │      │
│  │  Page        │  │  (Fabric.js) │  │  (Timeline)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓ REST API
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND SERVICES                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Server  │→ │  Template    │→ │  Rendering   │      │
│  │  (Auth/Proxy)│  │  Service     │  │  Service     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   MongoDB    │  │   S3/Minio   │  │   Redis      │      │
│  │  (Templates) │  │   (Assets)   │  │   (Cache)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 PHASE 1: Foundation & Data Model (Week 1-2)

### 1.1 Enhanced MongoDB Schema

**New Collections:**

```javascript
// designs collection - User's design projects
{
  design_id: "design_abc123",
  customer_id: "customer_xyz",
  user_id: "user_123",
  name: "My Instagram Post",
  category: "social_media",
  subcategory: "instagram_post",
  
  // Canvas state (Fabric.js JSON)
  canvas_state: {
    version: "5.3.0",
    objects: [...],  // All canvas objects
    background: "#ffffff"
  },
  
  // Design properties
  dimensions: {
    width: 1080,
    height: 1080,
    unit: "px"
  },
  
  // Timeline (for video/animation)
  timeline: {
    duration: 10.0,
    tracks: [
      {
        id: "track_1",
        type: "video",
        clips: [...]
      },
      {
        id: "track_2",
        type: "audio",
        clips: [...]
      }
    ]
  },
  
  // Assets used in design
  assets: [
    {
      id: "asset_1",
      type: "image",
      url: "s3://bucket/path/image.jpg",
      thumbnail: "s3://bucket/path/thumb.jpg"
    }
  ],
  
  // Metadata
  created_at: ISODate(),
  updated_at: ISODate(),
  status: "draft",  // draft, published, archived
  thumbnail: "s3://bucket/path/thumbnail.jpg",
  tags: ["marketing", "social"],
  
  // Export history
  exports: [
    {
      format: "mp4",
      url: "s3://bucket/exports/video.mp4",
      created_at: ISODate()
    }
  ]
}

// categories collection - Design categories
{
  category_id: "social_media",
  name: "Social Media",
  icon: "📱",
  description: "Create stunning social media posts",
  order: 3,
  
  subcategories: [
    {
      id: "instagram_post",
      name: "Instagram Post",
      dimensions: { width: 1080, height: 1080 },
      templates: ["template_1", "template_2"]
    },
    {
      id: "instagram_story",
      name: "Instagram Story",
      dimensions: { width: 1080, height: 1920 },
      templates: ["template_3", "template_4"]
    }
  ]
}

// assets collection - User uploaded assets
{
  asset_id: "asset_abc123",
  customer_id: "customer_xyz",
  user_id: "user_123",
  type: "image",  // image, video, audio, font
  
  // File info
  filename: "my-photo.jpg",
  url: "s3://bucket/path/my-photo.jpg",
  thumbnail: "s3://bucket/path/thumb.jpg",
  size: 1024000,  // bytes
  mime_type: "image/jpeg",
  
  // Media properties
  dimensions: { width: 1920, height: 1080 },
  duration: null,  // for video/audio
  
  // Metadata
  uploaded_at: ISODate(),
  tags: ["product", "photography"],
  folder: "My Photos"
}
```

### 1.2 Update Template Schema

Extend existing `templates` collection:

```javascript
{
  // ... existing fields ...
  
  // NEW: Category mapping
  category: "social_media",  // top-level category
  subcategory: "instagram_post",  // specific use case
  
  // NEW: Template type
  template_type: "video",  // video, image, presentation, printable
  
  // NEW: Recommended dimensions
  recommended_dimensions: [
    { width: 1080, height: 1080, label: "Square" },
    { width: 1080, height: 1920, label: "Story" }
  ],
  
  // NEW: Preview assets
  preview: {
    thumbnail: "s3://bucket/templates/thumb.jpg",
    video: "s3://bucket/templates/preview.mp4"
  },
  
  // NEW: Usage stats
  usage_count: 0,
  popularity_score: 0.0
}
```

---

## 📦 PHASE 2: Category Selection Interface (Week 3)

### 2.1 Create Category Selection Page

**File:** `frontend-server/src/pages/DesignHomePage.jsx`

**Features:**
- Grid layout with 9 main categories
- Each category shows icon, name, description
- Click → Navigate to subcategory selection
- Search bar for templates
- "Recent Designs" section
- "Blank Canvas" quick start

**Components:**
```
DesignHomePage.jsx
├── CategoryGrid.jsx
│   └── CategoryCard.jsx
├── RecentDesigns.jsx
│   └── DesignCard.jsx
├── SearchBar.jsx
└── QuickStart.jsx
```

### 2.2 Create Subcategory Selection Page

**File:** `frontend-server/src/pages/SubcategoryPage.jsx`

**Features:**
- Template gallery for selected category
- Filter by: popularity, recent, free/premium
- Template preview on hover
- Click template → Open in editor
- "Blank" option for each subcategory

---

## 📦 PHASE 3: Unified Canvas Editor (Week 4-6)

### 3.1 Choose Canvas Library

**Recommendation: Fabric.js**
- ✅ Mature, well-documented
- ✅ Rich object model (text, images, shapes, groups)
- ✅ Built-in transformations (rotate, scale, skew)
- ✅ JSON serialization (save/load canvas state)
- ✅ Event system for interactions
- ✅ Good performance for 2D canvas

**Alternative: Konva.js**
- Better for complex animations
- React integration via react-konva

### 3.2 Core Editor Architecture

**File:** `frontend-server/src/components/DesignEditor/DesignEditor.jsx`

```
DesignEditor/
├── DesignEditor.jsx (Main container)
├── EditorCanvas.jsx (Fabric.js canvas wrapper)
├── LeftSidebar/
│   ├── ElementsPanel.jsx (shapes, lines, icons)
│   ├── TextPanel.jsx (text tools)
│   ├── ImagesPanel.jsx (stock images, uploads)
│   ├── VideosPanel.jsx (stock videos, uploads)
│   ├── AudioPanel.jsx (music, sound effects)
│   ├── TemplatesPanel.jsx (pre-made layouts)
│   └── UploadsPanel.jsx (user uploads)
├── RightSidebar/
│   ├── PropertiesPanel.jsx (context-aware)
│   ├── LayersPanel.jsx (layer management)
│   └── HistoryPanel.jsx (undo/redo)
├── TopToolbar/
│   ├── FileMenu.jsx (save, export, share)
│   ├── EditMenu.jsx (undo, redo, copy, paste)
│   ├── ViewMenu.jsx (zoom, grid, rulers)
│   └── ExportButton.jsx
└── BottomTimeline/
    ├── Timeline.jsx (for video/animation)
    ├── TimelineTrack.jsx
    └── PlaybackControls.jsx
```

### 3.3 Canvas State Management

**Use Redux Toolkit for state:**

```javascript
// designSlice.js
{
  currentDesign: {
    id: "design_123",
    name: "My Design",
    category: "social_media",
    dimensions: { width: 1080, height: 1080 },
    canvasState: { /* Fabric.js JSON */ },
    timeline: { /* Timeline data */ },
    assets: [ /* Used assets */ ]
  },

  selectedObjects: [],  // Currently selected canvas objects
  clipboard: null,      // Copy/paste buffer
  history: {
    past: [],
    future: []
  },

  ui: {
    leftSidebarTab: "elements",
    rightSidebarVisible: true,
    zoom: 1.0,
    gridVisible: false,
    rulersVisible: false
  }
}
```

### 3.4 Key Features to Implement

**Canvas Operations:**
- ✅ Add/remove objects (text, images, shapes, videos)
- ✅ Transform objects (move, resize, rotate, flip)
- ✅ Layer management (z-index, lock, hide)
- ✅ Grouping/ungrouping
- ✅ Alignment tools (left, center, right, top, middle, bottom)
- ✅ Distribution tools
- ✅ Copy/paste/duplicate
- ✅ Undo/redo (with history limit)

**Text Editing:**
- ✅ Rich text editor (font, size, color, weight, style)
- ✅ Text alignment (left, center, right, justify)
- ✅ Line height, letter spacing
- ✅ Text effects (shadow, outline, gradient)
- ✅ Google Fonts integration

**Image Editing:**
- ✅ Filters (brightness, contrast, saturation, blur)
- ✅ Crop/resize
- ✅ Background removal (integrate existing IOPaint)
- ✅ Image adjustments
- ✅ Flip/rotate

**Shapes & Elements:**
- ✅ Basic shapes (rectangle, circle, triangle, line)
- ✅ Custom shapes (stars, arrows, speech bubbles)
- ✅ Icons library (Font Awesome, custom SVGs)
- ✅ Fill (solid, gradient, pattern)
- ✅ Stroke (color, width, style)

---

## 📦 PHASE 4: Video Editor (Week 7-8)

### 4.1 Timeline Component

**File:** `frontend-server/src/components/VideoEditor/Timeline.jsx`

**Features:**
- Multi-track timeline (video, audio, text, effects)
- Drag-and-drop clips
- Trim clips (in/out points)
- Split clips
- Transitions between clips
- Keyframe animation
- Playback controls (play, pause, seek)
- Zoom timeline (fit, 1s, 5s, 10s intervals)

**Data Structure:**
```javascript
{
  duration: 30.0,  // total duration in seconds
  fps: 30,
  tracks: [
    {
      id: "track_video_1",
      type: "video",
      clips: [
        {
          id: "clip_1",
          asset_id: "asset_123",
          start: 0.0,      // timeline position
          end: 5.0,
          trim_start: 0.0, // trim from source
          trim_end: 5.0,
          effects: ["fade_in", "ken_burns"],
          transitions: {
            in: { type: "fade", duration: 0.5 },
            out: { type: "crossfade", duration: 1.0 }
          }
        }
      ]
    },
    {
      id: "track_audio_1",
      type: "audio",
      clips: [...]
    }
  ]
}
```

### 4.2 Video Rendering Pipeline

**Extend existing video-generator service:**

**New endpoint:** `POST /api/render/timeline`

```python
# jobs/video-generator/services/timeline_renderer.py

class TimelineRenderer:
    def render_timeline(self, timeline_data, output_path):
        """
        Render timeline to video file

        Args:
            timeline_data: Timeline JSON with tracks and clips
            output_path: Output video file path
        """
        # 1. Load all clips from tracks
        # 2. Apply effects to each clip
        # 3. Apply transitions
        # 4. Composite all tracks
        # 5. Add audio tracks
        # 6. Export final video
```

### 4.3 Video Effects Library

**Extend existing effects:**
- ✅ Ken Burns (already implemented)
- ✅ Fade in/out (already implemented)
- ✅ Transitions (crossfade, slide, wipe)
- 🆕 Speed control (slow motion, time lapse)
- 🆕 Reverse
- 🆕 Filters (vintage, black & white, sepia)
- 🆕 Color grading
- 🆕 Stabilization
- 🆕 Chroma key (green screen)

---

## 📦 PHASE 5: Audio Editor (Week 9)

### 5.1 Audio Waveform Visualization

**Library:** WaveSurfer.js

**File:** `frontend-server/src/components/AudioEditor/AudioWaveform.jsx`

**Features:**
- Waveform display
- Playback controls
- Trim audio
- Volume control
- Fade in/out
- Audio effects (normalize, compress, EQ)

### 5.2 Audio Mixing

**Multiple audio tracks:**
- Background music
- Voiceover
- Sound effects
- Volume envelopes
- Ducking (auto-lower music when voice plays)

---

## 📦 PHASE 6: Asset Management (Week 10)

### 6.1 Upload System

**File:** `frontend-server/src/components/AssetManager/AssetUploader.jsx`

**Features:**
- Drag-and-drop upload
- Multiple file upload
- Progress indicators
- File type validation
- Size limits
- Thumbnail generation
- Organize in folders

### 6.2 Stock Assets Integration

**Options:**
1. **Unsplash API** (free stock photos)
2. **Pexels API** (free stock photos & videos)
3. **Pixabay API** (free stock media)
4. **Google Fonts API** (fonts)

**Implementation:**
```javascript
// services/stockAssetService.js

class StockAssetService {
  async searchImages(query, page = 1) {
    // Search Unsplash/Pexels
  }

  async searchVideos(query, page = 1) {
    // Search Pexels videos
  }

  async getFonts() {
    // Get Google Fonts list
  }
}
```

---

## 📦 PHASE 7: Export & Rendering (Week 11)

### 7.1 Export Formats

**Image Designs:**
- PNG (transparent background support)
- JPG (smaller file size)
- SVG (vector, if applicable)
- PDF (for printables)

**Video Designs:**
- MP4 (H.264, most compatible)
- WebM (web optimized)
- GIF (animated, short clips)

**Quality Options:**
- Low (720p, smaller file)
- Medium (1080p, balanced)
- High (4K, best quality)

### 7.2 Rendering Service

**File:** `jobs/video-generator/services/design_renderer.py`

```python
class DesignRenderer:
    def render_image(self, design_data, format="png", quality="high"):
        """Render image design to file"""
        # Use Pillow or Cairo for image rendering

    def render_video(self, design_data, format="mp4", quality="high"):
        """Render video design to file"""
        # Use existing MoviePy pipeline
        # Add timeline rendering

    def render_pdf(self, design_data):
        """Render printable design to PDF"""
        # Use ReportLab or WeasyPrint
```

### 7.3 Background Job Queue

**Use existing RabbitMQ/Celery setup:**

```python
# New task
@celery_app.task
def render_design_task(design_id, format, quality):
    """Background task for rendering designs"""
    # 1. Load design from MongoDB
    # 2. Render to file
    # 3. Upload to S3
    # 4. Update design with export URL
    # 5. Notify user (WebSocket/email)
```

---

## 📦 PHASE 8: Collaboration Features (Week 12+)

### 8.1 Real-time Collaboration (Optional)

**Technology:** Socket.io or WebSockets

**Features:**
- Multiple users editing same design
- Live cursors
- Presence indicators
- Conflict resolution
- Comments/annotations

### 8.2 Sharing & Permissions

**Share design:**
- View-only link
- Edit link
- Public/private toggle
- Team workspaces

---

## 🛠️ Technology Stack Summary

### Frontend
- **React** - UI framework
- **Fabric.js** - Canvas manipulation
- **Redux Toolkit** - State management
- **React Router** - Navigation
- **WaveSurfer.js** - Audio waveforms
- **Tailwind CSS** - Styling

### Backend
- **Flask** - API server (existing)
- **MongoDB** - Database (existing)
- **S3/Minio** - Asset storage
- **Redis** - Caching
- **RabbitMQ** - Job queue (existing)

### Rendering
- **MoviePy** - Video rendering (existing)
- **Pillow** - Image processing
- **FFmpeg** - Media encoding
- **Cairo/Playwright** - Canvas to image

---

## 📊 Database Migrations Needed

### New Collections
1. `designs` - User design projects
2. `categories` - Design categories & subcategories
3. `assets` - User uploaded assets
4. `stock_assets` - Cached stock assets
5. `exports` - Export history

### Updated Collections
1. `templates` - Add category mapping, preview assets
2. `customers` - Add storage quota, usage stats

---

## 🚀 Deployment Considerations

### Infrastructure
- **CDN** for asset delivery (CloudFront, Cloudflare)
- **Load balancer** for API servers
- **Auto-scaling** for rendering workers
- **Monitoring** (Prometheus, Grafana)

### Performance
- **Lazy loading** for templates/assets
- **Image optimization** (WebP, responsive images)
- **Canvas virtualization** for large designs
- **Debounced auto-save** (every 5 seconds)

### Security
- **File upload validation** (type, size, malware scan)
- **Rate limiting** on API endpoints
- **CORS** configuration
- **Asset access control** (signed URLs)

---

## 📈 Success Metrics

### User Engagement
- Designs created per user
- Time spent in editor
- Template usage rate
- Export completion rate

### Performance
- Editor load time < 2s
- Canvas interaction latency < 100ms
- Export time < 30s for 1080p video
- Asset upload success rate > 99%

---

## 🎯 MVP Feature Prioritization

### Must-Have (MVP)
1. ✅ Category selection page
2. ✅ Basic canvas editor (text, images, shapes)
3. ✅ Template selection
4. ✅ Image export (PNG, JPG)
5. ✅ Asset upload
6. ✅ Save/load designs

### Should-Have (V1.1)
1. ✅ Video timeline editor
2. ✅ Video export (MP4)
3. ✅ Audio tracks
4. ✅ Stock asset integration
5. ✅ Advanced text editing

### Nice-to-Have (V2.0)
1. ⭐ Real-time collaboration
2. ⭐ Animation keyframes
3. ⭐ AI-powered features (background removal, auto-layout)
4. ⭐ Mobile app
5. ⭐ Team workspaces

---

## 📅 Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | Week 1-2 | Enhanced data model, migrations |
| Phase 2 | Week 3 | Category selection UI |
| Phase 3 | Week 4-6 | Unified canvas editor |
| Phase 4 | Week 7-8 | Video timeline editor |
| Phase 5 | Week 9 | Audio editor |
| Phase 6 | Week 10 | Asset management |
| Phase 7 | Week 11 | Export & rendering |
| Phase 8 | Week 12+ | Collaboration (optional) |

**Total MVP Timeline:** ~11 weeks (3 months)

---

## 🔧 Migration from Current System

### Leverage Existing Components
1. ✅ **TemplateEditor.jsx** → Reuse for template creation in admin panel
2. ✅ **ImageCanvas.jsx** → Integrate into image editing tools
3. ✅ **Video generation pipeline** → Extend for timeline rendering
4. ✅ **Template system** → Use as starting point for designs
5. ✅ **Asset management** → Extend for user uploads

### Backward Compatibility
- Keep existing template API for news automation
- Add new `/api/designs` endpoints for Canva-like features
- Gradual migration of UI components

---

## 💡 Key Differentiators from Canva

### Your Unique Features
1. **AI-powered news automation** (existing strength)
2. **Integrated watermark removal** (existing IOPaint)
3. **Multi-tenant B2B focus** (existing architecture)
4. **Custom video effects** (Ken Burns, etc.)
5. **Template marketplace** (monetization opportunity)

---

## 📚 Resources & References

### Libraries to Install
```bash
# Frontend
npm install fabric
npm install wavesurfer.js
npm install @reduxjs/toolkit
npm install react-color
npm install react-dropzone

# Backend
pip install Pillow
pip install reportlab
pip install cairosvg
```

### Documentation
- Fabric.js: http://fabricjs.com/docs/
- WaveSurfer.js: https://wavesurfer-js.org/
- MoviePy: https://zulko.github.io/moviepy/
- Unsplash API: https://unsplash.com/developers

---

## ✅ Next Steps

1. **Review this plan** with your team
2. **Prioritize features** based on business needs
3. **Set up development environment** (install libraries)
4. **Create database migrations** (Phase 1)
5. **Build category selection page** (Phase 2)
6. **Prototype canvas editor** (Phase 3)

---

**Questions? Let's discuss specific phases or technical details!** 🚀

