# 🎙️ Audio Studio - Quick Reference Card

## 📚 Documentation Index

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **AUDIO_STUDIO_SUMMARY.md** | Executive overview | Start here! Quick overview of everything |
| **AUDIO_STUDIO_DESIGN.md** | Complete design & architecture | Detailed technical design |
| **AUDIO_STUDIO_COMPARISON.md** | Current vs. target analysis | Understand what you have vs. need |
| **AUDIO_STUDIO_CHECKLIST.md** | Implementation checklist | Track your progress |
| **AUDIO_STUDIO_STARTER_CODE.md** | Starter code for Phase 1 | Copy-paste code to get started |

---

## 🎯 Quick Facts

### What You're Building
**Canva-like Audio Studio** with 4 features:
1. 📝 Text-to-Speech (enhance existing)
2. 🎤 AI Voice Generation (new)
3. 🎵 AI Music Generator (new)
4. 🔊 Voice Cloning (enhance existing)

### Timeline
- **MVP:** 6 weeks
- **Full:** 8 weeks

### Cost
- **Current:** $0/month
- **MVP:** $5-22/month
- **Full:** $17-322/month

### Progress
**You're 40% there!** ✅
- ✅ TTS (Kokoro-82m)
- ✅ Voice Cloning (XTTS)
- ✅ Infrastructure (MongoDB, S3)

---

## 🚀 Quick Start (5 Steps)

### Step 1: Review Documents (30 min)
```bash
# Read in this order:
1. AUDIO_STUDIO_SUMMARY.md          # 5 min - Overview
2. AUDIO_STUDIO_COMPARISON.md       # 10 min - What you have vs. need
3. AUDIO_STUDIO_DESIGN.md           # 10 min - Skim the design
4. AUDIO_STUDIO_STARTER_CODE.md     # 5 min - See the code structure
```

### Step 2: Set Up Environment (15 min)
```bash
# Sign up for ElevenLabs (for Phase 2)
# Visit: https://elevenlabs.io
# Get API key

# Add to .env
echo "ELEVENLABS_API_KEY=your_api_key_here" >> .env
```

### Step 3: Create File Structure (10 min)
```bash
cd frontend-server/src

# Create directories
mkdir -p pages
mkdir -p components/AudioStudio/TextToSpeech
mkdir -p components/AudioStudio/AudioLibrary
mkdir -p hooks
mkdir -p constants

# You'll copy code from AUDIO_STUDIO_STARTER_CODE.md
```

### Step 4: Create Components (2-3 hours)
```bash
# Copy code from AUDIO_STUDIO_STARTER_CODE.md

# Create these files:
# 1. pages/AudioStudioPage.jsx
# 2. components/AudioStudio/AudioStudioTabs.jsx
# 3. components/AudioStudio/TextToSpeech/TextToSpeechPanel.jsx
# 4. components/AudioStudio/TextToSpeech/VoiceGallery.jsx
# 5. components/AudioStudio/TextToSpeech/VoiceCard.jsx
# 6. components/AudioStudio/TextToSpeech/VoiceSettings.jsx
# 7. components/AudioStudio/TextToSpeech/AudioPreview.jsx
# 8. components/AudioStudio/AudioLibrary/AudioLibraryPanel.jsx
# 9. components/AudioStudio/AudioLibrary/AudioGrid.jsx
# 10. components/AudioStudio/AudioLibrary/AudioCard.jsx
# 11. hooks/useAudioGeneration.js
# 12. hooks/useAudioLibrary.js
# 13. constants/audioModels.js
```

### Step 5: Test (30 min)
```bash
# Start frontend
cd frontend-server
npm start

# Navigate to http://localhost:3000/audio-studio
# Test voice generation
# Test audio library
```

---

## 📋 Phase 1 Checklist (Week 1-2)

### Frontend (Day 1-3)
- [ ] Create AudioStudioPage.jsx
- [ ] Create AudioStudioTabs.jsx
- [ ] Create TextToSpeechPanel.jsx
- [ ] Create VoiceGallery.jsx
- [ ] Create VoiceCard.jsx
- [ ] Create VoiceSettings.jsx
- [ ] Create AudioPreview.jsx

### Frontend (Day 4-5)
- [ ] Create AudioLibraryPanel.jsx
- [ ] Create AudioGrid.jsx
- [ ] Create AudioCard.jsx
- [ ] Create useAudioGeneration.js hook
- [ ] Create useAudioLibrary.js hook
- [ ] Create audioModels.js constants

### Backend (Day 6-7)
- [ ] Create audio_studio.py routes
- [ ] Add GET /api/audio-studio/library
- [ ] Add POST /api/audio-studio/library
- [ ] Add DELETE /api/audio-studio/library/:id
- [ ] Add PUT /api/audio-studio/library/:id

### Database (Day 8)
- [ ] Create audio_library collection
- [ ] Create indexes
- [ ] Test CRUD operations

### Testing (Day 9-10)
- [ ] Test voice generation
- [ ] Test audio library save
- [ ] Test audio library delete
- [ ] Test audio playback
- [ ] Test voice settings

---

## 🔑 Key Components

### Frontend Components (13 files)

```
AudioStudioPage.jsx              - Main container
AudioStudioTabs.jsx              - Tab navigation
TextToSpeechPanel.jsx            - TTS main panel
VoiceGallery.jsx                 - Voice selection grid
VoiceCard.jsx                    - Individual voice card
VoiceSettings.jsx                - Speed, pitch, stability sliders
AudioPreview.jsx                 - Audio player with waveform
AudioLibraryPanel.jsx            - Library sidebar
AudioGrid.jsx                    - Audio file grid
AudioCard.jsx                    - Individual audio card
useAudioGeneration.js            - Audio generation hook
useAudioLibrary.js               - Library management hook
audioModels.js                   - Voice constants
```

### Backend API (4 endpoints)

```
GET    /api/audio-studio/library           - Get all audio files
POST   /api/audio-studio/library           - Save audio file
DELETE /api/audio-studio/library/:id       - Delete audio file
PUT    /api/audio-studio/library/:id       - Update audio metadata
```

### Database (1 collection)

```
audio_library                              - Audio files collection
  - audio_id (unique)
  - customer_id, user_id
  - name, type, source
  - url, duration, format, size
  - generation_config
  - created_at, updated_at
  - tags, folder
```

---

## 💡 Common Commands

### Development
```bash
# Start frontend
cd frontend-server && npm start

# Start backend (if separate)
cd backend && python app.py

# View MongoDB
mongosh
use your_database
db.audio_library.find()
```

### Testing
```bash
# Test API endpoints
curl http://localhost:3000/api/audio-studio/library

# Test voice generation
curl -X POST http://localhost:8095/api/audio/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice":"am_adam"}'
```

### Debugging
```bash
# Check logs
tail -f frontend-server/logs/app.log
tail -f backend/logs/app.log

# Check MongoDB
mongosh
db.audio_library.find().pretty()

# Check S3/Storage
aws s3 ls s3://your-bucket/audio/
```

---

## 🎨 UI Components Hierarchy

```
AudioStudioPage
├── Header
│   ├── Title
│   └── Close Button
├── AudioStudioTabs
│   ├── Text-to-Speech Tab
│   ├── AI Voice Tab (disabled)
│   ├── AI Music Tab (disabled)
│   └── Voice Cloning Tab (disabled)
├── Main Content (2/3 width)
│   └── TextToSpeechPanel
│       ├── Text Input
│       ├── VoiceGallery
│       │   └── VoiceCard (multiple)
│       ├── VoiceSettings
│       │   ├── Speed Slider
│       │   ├── Pitch Slider
│       │   ├── Stability Slider
│       │   └── Clarity Slider
│       ├── Generate Button
│       └── AudioPreview
│           ├── Play/Pause Button
│           ├── Progress Bar
│           └── Download Button
└── Sidebar (1/3 width)
    └── AudioLibraryPanel
        ├── Filter Buttons
        └── AudioGrid
            └── AudioCard (multiple)
                ├── Play Button
                ├── Audio Info
                └── Menu (Rename, Download, Delete)
```

---

## 📊 API Response Formats

### Generate Audio
```json
POST /api/audio/generate
Request:
{
  "text": "Hello world",
  "voice": "am_adam",
  "speed": 1.0,
  "pitch": 0,
  "stability": 0.5,
  "clarity": 0.75
}

Response:
{
  "success": true,
  "audio_url": "https://s3.../audio.wav",
  "duration": 2.5
}
```

### Get Audio Library
```json
GET /api/audio-studio/library?customer_id=xxx&user_id=yyy

Response:
{
  "success": true,
  "audio_files": [
    {
      "audio_id": "abc123",
      "name": "Voiceover 1",
      "type": "voiceover",
      "url": "https://s3.../audio.wav",
      "duration": 45.5,
      "created_at": "2025-12-31T10:00:00Z"
    }
  ]
}
```

---

## 🐛 Troubleshooting

### Issue: Audio not generating
**Solution:**
1. Check if audio-generation-service is running (port 8095)
2. Check logs: `tail -f audio-generation-service/logs/app.log`
3. Test API directly: `curl http://localhost:8095/health`

### Issue: Audio library not loading
**Solution:**
1. Check MongoDB connection
2. Check if audio_library collection exists
3. Check API endpoint: `curl http://localhost:3000/api/audio-studio/library`

### Issue: Voice preview not working
**Solution:**
1. Check if preview audio files exist
2. Check browser console for errors
3. Check CORS settings

---

## 📞 Need Help?

### Quick Links
- **Design:** See `AUDIO_STUDIO_DESIGN.md`
- **Code:** See `AUDIO_STUDIO_STARTER_CODE.md`
- **Progress:** See `AUDIO_STUDIO_CHECKLIST.md`
- **Comparison:** See `AUDIO_STUDIO_COMPARISON.md`

### Common Questions

**Q: Should I build MVP or Full version?**
A: Start with MVP (6 weeks). Skip AI Music for now.

**Q: Which AI voice API should I use?**
A: ElevenLabs ($5-22/month). Best quality.

**Q: Do I need a GPU for MusicGen?**
A: For MVP, use Stable Audio API ($12/month). No GPU needed.

**Q: When should I integrate with Design Editor?**
A: Phase 5 (Week 6). Build Audio Studio first.

---

## ✅ Success Criteria

### Phase 1 Complete When:
- ✅ Audio Studio UI is live
- ✅ Can generate voiceovers
- ✅ Can save to library
- ✅ Can delete from library
- ✅ Can play audio
- ✅ Voice settings work

### MVP Complete When:
- ✅ All Phase 1 features
- ✅ ElevenLabs integration works
- ✅ Voice cloning management works
- ✅ Can add audio to timeline
- ✅ Can export video with audio

---

**Ready to build! 🚀**

Start with Phase 1 and you'll have a working Audio Studio in 2 weeks! 🎙️

