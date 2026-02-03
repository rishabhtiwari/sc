# Project Export System - Implementation Plan

## 📋 Overview

This document outlines the complete implementation plan for exporting Design Editor projects to multiple formats (MP4, MP3, PDF, PNG, GIF, JSON).

---

## 🎯 Supported Export Formats

| Format | Use Case | Priority | Complexity | Estimated Time |
|--------|----------|----------|------------|----------------|
| **MP4** | Video export (primary) | 🔴 Critical | Medium | 2 weeks |
| **MP3** | Audio-only export | 🟡 High | Low | 3 days |
| **PDF** | Static presentation/slides | 🟡 Medium | Medium | 1 week |
| **PNG/JPG** | Individual slide images | 🟢 Low | Low | 3 days |
| **GIF** | Animated preview | 🟢 Low | Medium | 4 days |
| **JSON** | Project backup/transfer | 🟢 Low | Low | 1 day |

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────┐
│  Frontend UI    │
│  (React)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Server     │
│  (Flask Proxy)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Project Export Service         │
│  (New Microservice)             │
│  ┌───────────────────────────┐  │
│  │ Video Export (MoviePy)    │  │
│  │ Audio Export (pydub)      │  │
│  │ PDF Export (ReportLab)    │  │
│  │ Image Export (Pillow)     │  │
│  │ GIF Export (Pillow)       │  │
│  └───────────────────────────┘  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  MongoDB        │     │  MinIO Storage  │
│  (Export Jobs)  │     │  (Output Files) │
└─────────────────┘     └─────────────────┘
```

### Export Flow

```
User clicks Export → Select Format → Create Export Job → Queue Job
    ↓
Background Worker picks up job → Download assets from MinIO
    ↓
Render project based on format → Generate output file
    ↓
Upload to MinIO → Update job status → Notify user → Download
```

---

## 📁 Project Structure

### New Microservice: `project-export-service`

```
project-export-service/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app.py                          # Flask application
├── config.py                       # Configuration
├── services/
│   ├── __init__.py
│   ├── video_export_service.py     # MP4 export (MoviePy)
│   ├── audio_export_service.py     # MP3 export (pydub)
│   ├── pdf_export_service.py       # PDF export (ReportLab)
│   ├── image_export_service.py     # PNG/JPG export (Pillow)
│   ├── gif_export_service.py       # GIF export (Pillow)
│   ├── export_queue_service.py     # Background job queue (Celery/RQ)
│   └── storage_service.py          # MinIO integration
├── utils/
│   ├── __init__.py
│   ├── project_parser.py           # Parse project JSON
│   ├── asset_downloader.py         # Download assets from MinIO
│   ├── render_engine.py            # Render canvas elements
│   └── progress_tracker.py         # Track export progress
├── models/
│   ├── __init__.py
│   └── export_job.py               # Export job Pydantic model
├── routes/
│   ├── __init__.py
│   └── export_routes.py            # API endpoints
└── workers/
    ├── __init__.py
    └── export_worker.py            # Celery worker
```

---

## 🗄️ Database Schema

### Export Jobs Collection

```javascript
// MongoDB: export_jobs collection
{
  export_job_id: "export_abc123",
  customer_id: "customer_xyz",
  user_id: "user_123",
  project_id: "proj_abc123",
  project_name: "My Video Project",
  
  // Export configuration
  format: "mp4",  // mp4, mp3, pdf, png, jpg, gif, json
  settings: {
    // Video settings
    quality: "1080p",        // 1080p, 720p, 480p, 360p
    fps: 30,                 // 24, 30, 60
    codec: "libx264",        // libx264, libx265
    bitrate: "5000k",        // Video bitrate
    
    // Audio settings
    includeAudio: true,
    audioBitrate: "192k",    // 128k, 192k, 320k
    audioCodec: "aac",       // aac, mp3
    
    // Image settings
    imageFormat: "png",      // png, jpg
    imageQuality: 95,        // 1-100 for JPG
    
    // PDF settings
    pdfPageSize: "A4",       // A4, Letter, Custom
    pdfOrientation: "landscape",  // portrait, landscape
    
    // GIF settings
    gifFps: 10,              // 5, 10, 15
    gifLoop: true,
    
    // General
    watermark: false,
    watermarkText: "",
    watermarkPosition: "bottom-right"
  },

  // Job status
  status: "processing",  // queued, processing, completed, failed, cancelled
  progress: 45,          // 0-100
  current_step: "Rendering slide 3/10",

  // Output
  output_url: "https://minio.example.com/exports/video_abc123.mp4",
  output_filename: "My_Video_Project.mp4",
  file_size: 15728640,   // bytes (15 MB)
  duration: 30.5,        // seconds (for video/audio)

  // Timestamps
  created_at: ISODate("2024-01-15T10:30:00Z"),
  started_at: ISODate("2024-01-15T10:30:05Z"),
  completed_at: ISODate("2024-01-15T10:32:15Z"),
  expires_at: ISODate("2024-01-22T10:32:15Z"),  // Auto-delete after 7 days

  // Error handling
  error: null,
  error_details: null,
  retry_count: 0,
  max_retries: 3,

  // Download tracking
  download_count: 0,
  max_downloads: 5,
  last_downloaded_at: null
}
```

### Indexes

```javascript
// Indexes for export_jobs collection
db.export_jobs.createIndex({ "export_job_id": 1 }, { unique: true });
db.export_jobs.createIndex({ "customer_id": 1, "user_id": 1 });
db.export_jobs.createIndex({ "project_id": 1 });
db.export_jobs.createIndex({ "status": 1 });
db.export_jobs.createIndex({ "created_at": 1 });
db.export_jobs.createIndex({ "expires_at": 1 });  // For cleanup job
```

---

## 🔧 Implementation Details

### Phase 1: Video Export (MP4) - Priority 1

**File**: `services/video_export_service.py`

**Key Features**:
- Render each page/slide as video clip
- Support text, image, video, shape elements
- Apply element properties (opacity, rotation, position)
- Composite audio tracks with volume, fade in/out
- Support transitions between slides
- Apply watermark if enabled
- Export with H.264 codec for maximum compatibility

**Technology Stack**:
- **MoviePy** - Video composition and editing
- **Pillow (PIL)** - Image rendering and manipulation
- **FFmpeg** - Video encoding (via MoviePy)
- **NumPy** - Array operations for video frames

**Rendering Pipeline**:
```
1. Parse project JSON
2. Download all assets (images, videos, audio) from MinIO
3. For each page:
   a. Create base image (1920x1080) with background color/image
   b. Render text elements (font, size, color, position)
   c. Render image elements (resize, position, opacity, rotation)
   d. Render shape elements (rectangles, circles, etc.)
   e. Convert to ImageClip with page duration
4. Process video elements:
   a. Download video files
   b. Apply trim (trimStart, trimEnd)
   c. Apply playback speed
   d. Position as overlay on slide
5. Concatenate all slide clips
6. Process audio tracks:
   a. Download audio files
   b. Apply volume adjustments
   c. Apply fade in/out
   d. Composite at correct timeline positions
7. Combine video and audio
8. Apply logo watermark if enabled
9. Export to MP4 with optimized settings
```

**Code Structure**:
```python
class VideoExportService:
    def export_to_video(self, project_data, settings, output_path):
        """Main export function"""

    def _render_slide(self, page, settings):
        """Render single slide with all elements"""

    def _render_text_element(self, draw, element):
        """Render text on image"""

    def _render_image_element(self, base_img, element):
        """Render image element with transformations"""

    def _render_shape_element(self, draw, element):
        """Render shapes (rectangle, circle, line)"""

    def _process_video_elements(self, elements, slide_duration):
        """Process video overlays"""

    def _process_audio_tracks(self, audio_tracks, total_duration):
        """Composite all audio tracks"""

    def _apply_watermark(self, video_clip, settings):
        """Apply logo watermark"""

    def _update_progress(self, job_id, progress, step):
        """Update job progress in database"""
```

---

### Phase 2: Audio Export (MP3)

**File**: `services/audio_export_service.py`

**Key Features**:
- Extract all audio tracks from project
- Merge audio tracks at correct timeline positions
- Apply volume adjustments
- Apply fade in/out effects
- Apply playback speed changes
- Export to MP3 with configurable bitrate

**Technology Stack**:
- **pydub** - Audio manipulation
- **FFmpeg** - Audio encoding

**Code Structure**:
```python
class AudioExportService:
    def export_to_audio(self, project_data, settings, output_path):
        """Export project audio to MP3"""

    def _merge_audio_tracks(self, audio_tracks, total_duration):
        """Merge all audio tracks"""

    def _apply_audio_effects(self, audio, track_settings):
        """Apply volume, fade, speed effects"""
```

---

### Phase 3: PDF Export

**File**: `services/pdf_export_service.py`

**Key Features**:
- Render each slide as PDF page
- Support custom page sizes (A4, Letter, Custom)
- Support portrait/landscape orientation
- Embed images and text
- Maintain aspect ratio

**Technology Stack**:
- **ReportLab** - PDF generation
- **Pillow** - Image rendering

**Code Structure**:
```python
class PDFExportService:
    def export_to_pdf(self, project_data, settings, output_path):
        """Export slides to PDF"""

    def _render_slide_to_image(self, page):
        """Render slide as image for PDF"""

    def _add_page_to_pdf(self, canvas, image, page_size):
        """Add rendered slide to PDF"""
```

---

### Phase 4: Image Export (PNG/JPG)

**File**: `services/image_export_service.py`

**Key Features**:
- Export each slide as individual image
- Support PNG (lossless) and JPG (compressed)
- Configurable quality for JPG
- Create ZIP archive of all images

**Technology Stack**:
- **Pillow** - Image rendering
- **zipfile** - Archive creation

**Code Structure**:
```python
class ImageExportService:
    def export_to_images(self, project_data, settings, output_dir):
        """Export slides as PNG/JPG images"""

    def _render_slide_to_image(self, page, format, quality):
        """Render single slide as image"""

    def _create_zip_archive(self, image_files, output_path):
        """Create ZIP of all images"""
```

---

### Phase 5: GIF Export

**File**: `services/gif_export_service.py`

**Key Features**:
- Create animated GIF from slides
- Configurable FPS (5, 10, 15)
- Loop or play once
- Optimize file size

**Technology Stack**:
- **Pillow** - GIF creation

**Code Structure**:
```python
class GIFExportService:
    def export_to_gif(self, project_data, settings, output_path):
        """Export slides as animated GIF"""

    def _optimize_gif(self, frames):
        """Optimize GIF file size"""
```

---

### Phase 6: Background Job Queue

**File**: `services/export_queue_service.py`

**Key Features**:
- Queue export jobs for background processing
- Support job prioritization
- Handle job retries on failure
- Track job progress
- Send notifications on completion

**Technology Stack**:
- **Redis** - Job queue backend
- **Celery** or **RQ (Redis Queue)** - Task queue

**Code Structure**:
```python
# Using Celery
from celery import Celery

celery_app = Celery('export_service', broker='redis://redis:6379/0')

@celery_app.task(bind=True)
def process_export_job(self, job_id):
    """Background task to process export"""
    job = get_export_job(job_id)

    try:
        # Update status
        update_job_status(job_id, 'processing')

        # Get project data
        project = get_project(job.project_id)

        # Route to appropriate export service
        if job.format == 'mp4':
            service = VideoExportService()
        elif job.format == 'mp3':
            service = AudioExportService()
        # ... etc

        # Execute export
        output_path = service.export(project, job.settings)

        # Upload to MinIO
        output_url = upload_to_storage(output_path, job.export_job_id)

        # Update job with result
        update_job_complete(job_id, output_url, file_size)

        # Send notification
        notify_user(job.user_id, job_id, 'completed')

    except Exception as e:
        # Handle error
        update_job_failed(job_id, str(e))
        notify_user(job.user_id, job_id, 'failed')
```

---

## 🌐 API Endpoints

### Export Routes

**File**: `routes/export_routes.py`

```python
from flask import Blueprint, request, jsonify, send_file

export_bp = Blueprint('export', __name__)

@export_bp.route('/export', methods=['POST'])
def create_export_job():
    """
    Create a new export job

    Request Body:
    {
      "project_id": "proj_abc123",
      "format": "mp4",
      "settings": {
        "quality": "1080p",
        "fps": 30,
        "includeAudio": true
      }
    }

    Response:
    {
      "export_job_id": "export_xyz789",
      "status": "queued",
      "message": "Export job created successfully"
    }
    """
    pass

@export_bp.route('/export/<job_id>', methods=['GET'])
def get_export_job(job_id):
    """
    Get export job details and status

    Response:
    {
      "export_job_id": "export_xyz789",
      "status": "processing",
      "progress": 45,
      "current_step": "Rendering slide 3/10",
      "output_url": null,
      "created_at": "2024-01-15T10:30:00Z"
    }
    """
    pass

@export_bp.route('/export/<job_id>/download', methods=['GET'])
def download_export(job_id):
    """
    Download exported file

    Response: File stream (MP4, MP3, PDF, ZIP, GIF)
    """
    pass

@export_bp.route('/export/<job_id>/cancel', methods=['POST'])
def cancel_export(job_id):
    """
    Cancel an in-progress export job

    Response:
    {
      "message": "Export job cancelled",
      "status": "cancelled"
    }
    """
    pass

@export_bp.route('/export/history', methods=['GET'])
def get_export_history():
    """
    Get user's export history

    Query Params:
    - skip: int (default: 0)
    - limit: int (default: 20)
    - format: str (optional filter)
    - status: str (optional filter)

    Response:
    {
      "exports": [...],
      "total": 45,
      "skip": 0,
      "limit": 20
    }
    """
    pass

@export_bp.route('/export/<job_id>', methods=['DELETE'])
def delete_export(job_id):
    """
    Delete an export job and its output file

    Response:
    {
      "message": "Export deleted successfully"
    }
    """
    pass
```

---

## 🎨 Frontend Implementation

### Export Dialog Component

**File**: `frontend-server/src/components/DesignEditor/ExportDialog.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import api from '../../services/api';

const ExportDialog = ({ isOpen, onClose, project }) => {
  const [format, setFormat] = useState('mp4');
  const [quality, setQuality] = useState('1080p');
  const [fps, setFps] = useState(30);
  const [includeAudio, setIncludeAudio] = useState(true);
  const [watermark, setWatermark] = useState(false);

  const [exporting, setExporting] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState(null);

  const formatOptions = [
    { value: 'mp4', label: 'Video (MP4)', icon: '🎬', description: 'Full video with audio' },
    { value: 'mp3', label: 'Audio (MP3)', icon: '🎵', description: 'Audio tracks only' },
    { value: 'pdf', label: 'PDF Document', icon: '📄', description: 'Slides as PDF pages' },
    { value: 'png', label: 'Images (PNG)', icon: '🖼️', description: 'Individual slide images' },
    { value: 'gif', label: 'Animated GIF', icon: '🎞️', description: 'Animated preview' },
    { value: 'json', label: 'Project Backup', icon: '💾', description: 'Raw project data' }
  ];

  const qualityOptions = {
    mp4: [
      { value: '1080p', label: '1080p (Full HD)', bitrate: '5000k' },
      { value: '720p', label: '720p (HD)', bitrate: '2500k' },
      { value: '480p', label: '480p (SD)', bitrate: '1000k' }
    ]
  };

  const handleExport = async () => {
    setExporting(true);
    setError(null);

    try {
      // Create export job
      const response = await api.post('/projects/export', {
        project_id: project.project_id,
        format: format,
        settings: {
          quality: quality,
          fps: fps,
          includeAudio: includeAudio,
          watermark: watermark,
          codec: 'libx264',
          bitrate: qualityOptions.mp4.find(q => q.value === quality)?.bitrate
        }
      });

      const newJobId = response.data.export_job_id;
      setJobId(newJobId);

      // Poll for progress
      pollExportStatus(newJobId);

    } catch (error) {
      console.error('Export error:', error);
      setError(error.response?.data?.error || 'Failed to start export');
      setExporting(false);
    }
  };

  const pollExportStatus = async (jobId) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/projects/export/${jobId}`);
        const job = response.data;

        setProgress(job.progress);
        setCurrentStep(job.current_step);

        if (job.status === 'completed') {
          clearInterval(interval);
          setExporting(false);

          // Auto-download
          window.open(`/api/projects/export/${jobId}/download`, '_blank');

          // Show success message
          showToast('Export completed successfully!', 'success');

          // Close dialog after 2 seconds
          setTimeout(() => {
            onClose();
            resetState();
          }, 2000);

        } else if (job.status === 'failed') {
          clearInterval(interval);
          setExporting(false);
          setError(job.error || 'Export failed');
        }
      } catch (error) {
        clearInterval(interval);
        setExporting(false);
        setError('Failed to check export status');
      }
    }, 2000); // Poll every 2 seconds
  };

  const handleCancel = async () => {
    if (jobId && exporting) {
      try {
        await api.post(`/projects/export/${jobId}/cancel`);
        setExporting(false);
        resetState();
      } catch (error) {
        console.error('Cancel error:', error);
      }
    }
    onClose();
  };

  const resetState = () => {
    setJobId(null);
    setProgress(0);
    setCurrentStep('');
    setError(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800">Export Project</h2>
          <p className="text-gray-600 mt-1">Choose format and settings for your export</p>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Export Format
            </label>
            <div className="grid grid-cols-2 gap-3">
              {formatOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setFormat(option.value)}
                  disabled={exporting}
                  className={`p-4 border-2 rounded-lg text-left transition-all ${
                    format === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  } ${exporting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{option.icon}</span>
                    <div>
                      <div className="font-semibold text-gray-800">{option.label}</div>
                      <div className="text-xs text-gray-500">{option.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Video Settings */}
          {format === 'mp4' && (
            <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold text-gray-800">Video Settings</h3>

              {/* Quality */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quality
                </label>
                <select
                  value={quality}
                  onChange={(e) => setQuality(e.target.value)}
                  disabled={exporting}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {qualityOptions.mp4.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* FPS */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Frame Rate (FPS)
                </label>
                <select
                  value={fps}
                  onChange={(e) => setFps(Number(e.target.value))}
                  disabled={exporting}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={24}>24 FPS (Cinematic)</option>
                  <option value={30}>30 FPS (Standard)</option>
                  <option value={60}>60 FPS (Smooth)</option>
                </select>
              </div>

              {/* Include Audio */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="includeAudio"
                  checked={includeAudio}
                  onChange={(e) => setIncludeAudio(e.target.checked)}
                  disabled={exporting}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="includeAudio" className="ml-2 text-sm text-gray-700">
                  Include audio tracks
                </label>
              </div>

              {/* Watermark */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="watermark"
                  checked={watermark}
                  onChange={(e) => setWatermark(e.target.checked)}
                  disabled={exporting}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor="watermark" className="ml-2 text-sm text-gray-700">
                  Add logo watermark
                </label>
              </div>
            </div>
          )}

          {/* Progress Bar */}
          {exporting && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-600">
                <span>{currentStep || 'Preparing export...'}</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-blue-600 h-full transition-all duration-300 rounded-full"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center gap-2 text-red-800">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span className="font-semibold">Export Failed</span>
              </div>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={handleCancel}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium"
          >
            {exporting ? 'Cancel' : 'Close'}
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
          >
            {exporting ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Exporting...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Export
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportDialog;
```

### Add Export Button to Design Editor

**File**: `frontend-server/src/components/DesignEditor/DesignEditor.jsx`

```jsx
// Add state
const [showExportDialog, setShowExportDialog] = useState(false);

// Add to toolbar (after Load button)
<button
  onClick={() => setShowExportDialog(true)}
  disabled={!currentProject}
  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center gap-2 shadow-sm"
  title="Export project to video, audio, PDF, or images"
>
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
  </svg>
  Export
</button>

// Add dialog component (before closing div)
<ExportDialog
  isOpen={showExportDialog}
  onClose={() => setShowExportDialog(false)}
  project={currentProject}
/>
```

---

## 📦 Dependencies

### Backend (project-export-service)

```txt
# requirements.txt
flask==3.0.0
flask-cors==4.0.0
pymongo==4.6.0
redis==5.0.1
celery==5.3.4
moviepy==1.0.3
pillow==10.1.0
pydub==0.25.1
reportlab==4.0.7
requests==2.31.0
python-dotenv==1.0.0
boto3==1.34.0  # For MinIO (S3-compatible)
```

### Frontend

```json
// No new dependencies needed - using existing React and api service
```

---

## 🚀 Implementation Timeline

| Week | Phase | Tasks | Deliverables |
|------|-------|-------|--------------|
| **Week 1** | Infrastructure Setup | • Create project-export-service directory<br>• Setup Docker container<br>• Configure MongoDB schema<br>• Setup Redis for job queue<br>• Create basic Flask app | Working microservice skeleton |
| **Week 2** | Video Export (Part 1) | • Implement project parser<br>• Implement asset downloader<br>• Implement slide renderer (text, images)<br>• Basic video composition | Can render simple slides to video |
| **Week 3** | Video Export (Part 2) | • Add video element support<br>• Add audio track compositing<br>• Add watermark support<br>• Optimize rendering performance | Full MP4 export working |
| **Week 4** | Audio & Image Export | • Implement MP3 export<br>• Implement PNG/JPG export<br>• Create ZIP archive for images | MP3 and PNG exports working |
| **Week 5** | PDF & GIF Export | • Implement PDF export<br>• Implement GIF export<br>• Add JSON backup export | All export formats working |
| **Week 6** | Frontend Integration | • Create ExportDialog component<br>• Add export button to editor<br>• Implement progress tracking<br>• Add export history page | Complete UI integration |
| **Week 7** | Background Jobs | • Setup Celery workers<br>• Implement job queue<br>• Add retry logic<br>• Add WebSocket notifications | Background processing working |
| **Week 8** | Testing & Polish | • End-to-end testing<br>• Performance optimization<br>• Error handling<br>• Documentation | Production-ready system |

---

## ⚙️ Configuration

### Environment Variables

```bash
# project-export-service/.env

# Service Configuration
FLASK_ENV=production
FLASK_PORT=5010
LOG_LEVEL=INFO

# MongoDB
MONGODB_URI=mongodb://mongodb:27017/
MONGODB_DB=news_automation

# Redis (Job Queue)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# MinIO (Storage)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_EXPORTS=exports
MINIO_SECURE=false

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Export Settings
EXPORT_TEMP_DIR=/tmp/exports
EXPORT_MAX_CONCURRENT_JOBS=3
EXPORT_FILE_RETENTION_DAYS=7
EXPORT_MAX_DOWNLOADS=5

# Video Settings
VIDEO_DEFAULT_FPS=30
VIDEO_DEFAULT_CODEC=libx264
VIDEO_DEFAULT_QUALITY=1080p

# Watermark
WATERMARK_LOGO_PATH=/app/assets/logo.png
WATERMARK_POSITION=bottom-right
WATERMARK_OPACITY=0.7
```

---

## 🔒 Security Considerations

1. **Authentication & Authorization**
   - Verify user owns the project before allowing export
   - Rate limit export requests (e.g., 10 exports per hour per user)
   - Validate export settings to prevent abuse

2. **Resource Limits**
   - Limit maximum project size (e.g., 100 MB of assets)
   - Limit maximum video duration (e.g., 10 minutes)
   - Limit concurrent exports per user (e.g., 2 at a time)

3. **File Security**
   - Generate unique, non-guessable URLs for downloads
   - Auto-delete exported files after expiration
   - Scan uploaded assets for malware

4. **Cost Management**
   - Track export costs (compute time, storage)
   - Implement usage quotas per customer tier
   - Alert on excessive resource usage

---

## 📊 Monitoring & Analytics

### Metrics to Track

1. **Export Performance**
   - Average export time by format
   - Export success/failure rate
   - Queue wait time
   - Resource utilization (CPU, memory, disk)

2. **Usage Analytics**
   - Most popular export formats
   - Export volume by customer
   - Peak usage times
   - File size distribution

3. **Error Tracking**
   - Common failure reasons
   - Retry success rate
   - Asset download failures

### Logging

```python
# Structured logging for exports
logger.info("Export started", extra={
    "export_job_id": job_id,
    "customer_id": customer_id,
    "format": format,
    "project_id": project_id,
    "settings": settings
})

logger.info("Export progress", extra={
    "export_job_id": job_id,
    "progress": 45,
    "step": "Rendering slide 3/10"
})

logger.info("Export completed", extra={
    "export_job_id": job_id,
    "duration_seconds": 125,
    "file_size_bytes": 15728640,
    "output_url": output_url
})
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_video_export_service.py
def test_render_text_element():
    """Test text rendering with various fonts and sizes"""

def test_render_image_element():
    """Test image positioning and transformations"""

def test_audio_track_compositing():
    """Test audio merging with volume and fade"""
```

### Integration Tests

```python
# tests/test_export_integration.py
def test_full_video_export():
    """Test complete video export pipeline"""

def test_export_job_queue():
    """Test job queuing and processing"""
```

### End-to-End Tests

```javascript
// frontend-server/src/tests/export.test.js
describe('Export Flow', () => {
  it('should export project to MP4', async () => {
    // Create project
    // Click export button
    // Select MP4 format
    // Wait for completion
    // Verify download
  });
});
```

---

## 🎯 Success Criteria

### Phase 1 (MVP) - Video Export
- ✅ Can export simple project (text + images) to MP4
- ✅ Audio tracks are included and synced
- ✅ Export completes in < 2 minutes for 30-second video
- ✅ Output video plays on all major platforms (web, mobile, desktop)

### Phase 2 (Full Feature Set)
- ✅ All 6 export formats working (MP4, MP3, PDF, PNG, GIF, JSON)
- ✅ Background job queue handles concurrent exports
- ✅ Progress tracking shows real-time updates
- ✅ Export history page shows past exports
- ✅ Auto-cleanup of expired files

### Phase 3 (Production Ready)
- ✅ 99% export success rate
- ✅ Average export time < 3 minutes
- ✅ Handles 100+ concurrent exports
- ✅ Comprehensive error handling and retry logic
- ✅ Full monitoring and alerting

---

## 🔄 Future Enhancements

### Phase 4 (Advanced Features)

1. **Custom Branding**
   - Custom watermarks per customer
   - Branded intro/outro clips
   - Custom fonts and color schemes

2. **Advanced Video Effects**
   - Transitions between slides (fade, slide, zoom)
   - Animations for elements (entrance, exit)
   - Background music library
   - Voice-over recording

3. **Collaboration**
   - Share export links with team
   - Embed exports on websites
   - Social media direct publishing

4. **Templates**
   - Export presets (YouTube, Instagram, TikTok)
   - Batch export multiple projects
   - Scheduled exports

5. **AI Enhancements**
   - Auto-generate captions
   - Auto-select background music
   - Smart cropping for different aspect ratios

---

## 📝 Notes

### Known Limitations

1. **Video Elements**
   - Maximum 10 video elements per project
   - Video files must be < 100 MB each
   - Supported formats: MP4, MOV, AVI

2. **Performance**
   - Large projects (> 50 slides) may take 5-10 minutes
   - 4K export not supported in MVP (max 1080p)
   - GIF exports limited to 30 seconds

3. **Browser Compatibility**
   - Export dialog requires modern browser (Chrome 90+, Firefox 88+, Safari 14+)
   - WebSocket notifications require browser support

### Troubleshooting

**Export fails with "Out of memory" error**
- Solution: Reduce video quality or split project into smaller parts

**Audio not syncing with video**
- Solution: Ensure all audio files are valid and not corrupted

**Export stuck at 0% progress**
- Solution: Check Celery worker logs, restart worker if needed

---

## 📚 References

- [MoviePy Documentation](https://zulko.github.io/moviepy/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Celery Documentation](https://docs.celeryproject.org/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

---

## ✅ Checklist for Implementation

### Backend Setup
- [ ] Create `project-export-service` directory structure
- [ ] Setup Dockerfile and docker-compose.yml
- [ ] Configure MongoDB schema (export_jobs collection)
- [ ] Setup Redis for job queue
- [ ] Create Flask app with basic routes
- [ ] Implement project parser utility
- [ ] Implement asset downloader utility

### Video Export Service
- [ ] Implement slide renderer (base image, background)
- [ ] Implement text element rendering
- [ ] Implement image element rendering
- [ ] Implement shape element rendering
- [ ] Implement video element overlays
- [ ] Implement audio track compositing
- [ ] Implement watermark overlay
- [ ] Implement video export with FFmpeg
- [ ] Add progress tracking

### Other Export Services
- [ ] Implement MP3 audio export
- [ ] Implement PNG/JPG image export
- [ ] Implement PDF export
- [ ] Implement GIF export
- [ ] Implement JSON backup export

### Background Jobs
- [ ] Setup Celery worker
- [ ] Implement export job queue
- [ ] Implement job retry logic
- [ ] Implement job status updates
- [ ] Implement file cleanup cron job

### API Endpoints
- [ ] POST /export - Create export job
- [ ] GET /export/:id - Get job status
- [ ] GET /export/:id/download - Download file
- [ ] POST /export/:id/cancel - Cancel job
- [ ] GET /export/history - Get export history
- [ ] DELETE /export/:id - Delete export

### Frontend
- [ ] Create ExportDialog component
- [ ] Add export button to DesignEditor
- [ ] Implement format selection UI
- [ ] Implement settings UI (quality, FPS, etc.)
- [ ] Implement progress bar
- [ ] Implement error handling
- [ ] Add export history page
- [ ] Add download functionality

### Testing
- [ ] Unit tests for video export service
- [ ] Unit tests for audio export service
- [ ] Unit tests for image/PDF/GIF export
- [ ] Integration tests for job queue
- [ ] End-to-end tests for export flow
- [ ] Performance tests for large projects

### Documentation
- [ ] API documentation
- [ ] User guide for export feature
- [ ] Developer setup guide
- [ ] Troubleshooting guide

### Deployment
- [ ] Add to docker-compose.yml
- [ ] Configure environment variables
- [ ] Setup monitoring and logging
- [ ] Setup alerts for failures
- [ ] Deploy to staging
- [ ] Deploy to production

---

**Last Updated**: 2024-01-15
**Version**: 1.0
**Status**: Ready for Implementation 🚀


