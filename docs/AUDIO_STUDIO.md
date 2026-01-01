# Audio Studio Feature

## Overview

Audio Studio is a Canva-like audio generation interface that provides professional text-to-speech capabilities using the Kokoro-82m model. It features a modern, intuitive UI with real-time audio generation, voice preview, and a comprehensive audio library management system.

## Features

### 1. Text-to-Speech (TTS)
- **Model**: Kokoro-82m (82M parameter TTS model)
- **Voices**: 
  - American English: Adam, Michael, Emma, Bella, Nicole
  - British English: Alfie, Amy
  - Spanish: Geraint
  - French: Celine
  - German: Seraphina
  - Japanese: Hina, Takumi
  - Korean: Jiwoo
  - Chinese: Xiaomo, Yunxi
- **Features**:
  - Real-time voice preview
  - Adjustable speech speed (0.5x - 2.0x)
  - Character count with limit (5000 chars)
  - Live audio playback
  - Save to library

### 2. Audio Library
- **Features**:
  - View all generated audio files
  - Play/pause audio inline
  - Download audio files
  - Delete audio files
  - Filter by type (voiceover, music, sound effects)
  - Metadata display (duration, voice, creation date)

### 3. Future Enhancements (Planned)
- AI Voice Generation (ElevenLabs integration)
- AI Music Generator (MusicGen)
- Voice Cloning (XTTS)
- Audio editing capabilities
- Batch generation
- Audio mixing

## Architecture

### Frontend Components

```
frontend-server/src/
├── pages/
│   └── AudioStudioPage.jsx              # Main page component
├── components/AudioStudio/
│   ├── AudioStudioTabs.jsx              # Tab navigation
│   ├── TextToSpeech/
│   │   ├── TextToSpeechPanel.jsx        # TTS main panel
│   │   ├── VoiceSelector.jsx            # Voice selection with preview
│   │   ├── TextInput.jsx                # Text input with char count
│   │   └── AudioPlayer.jsx              # Audio playback controls
│   └── AudioLibrary/
│       ├── AudioLibraryPanel.jsx        # Library main panel
│       ├── AudioGrid.jsx                # Grid layout for audio files
│       └── AudioCard.jsx                # Individual audio file card
├── hooks/
│   ├── useAudioGeneration.js            # Audio generation hook
│   └── useAudioLibrary.js               # Library management hook
└── constants/
    └── audioModels.js                   # Voice configurations
```

### Backend API Routes

```
api-server/routes/
└── audio_studio_routes.py               # Audio Studio API endpoints
```

#### API Endpoints

1. **GET /api/audio-studio/library**
   - Get all audio files for current user
   - Returns: Array of audio file objects

2. **POST /api/audio-studio/library**
   - Save audio file to library
   - Body: Audio metadata (name, type, url, duration, etc.)
   - Returns: Created audio object

3. **PUT /api/audio-studio/library/:audio_id**
   - Update audio file metadata
   - Body: Updated fields (name, tags, folder)
   - Returns: Success message

4. **DELETE /api/audio-studio/library/:audio_id**
   - Delete audio file (soft delete)
   - Returns: Success message

5. **POST /api/audio/generate**
   - Generate audio using TTS
   - Body: { text, model, voice, speed, format }
   - Returns: { success, audio_url, audio_info }

6. **POST /api/audio/preview**
   - Generate preview audio for voice selection
   - Body: { text, model, voice, language }
   - Returns: { success, audio_url }

7. **GET /api/audio/proxy/:filename**
   - Proxy audio files from audio generation service
   - Returns: Audio file stream

### Database Schema

**Collection**: `audio_library`

```javascript
{
  audio_id: String,           // Unique audio ID
  customer_id: String,        // Customer ID
  user_id: String,            // User ID
  name: String,               // Audio file name
  type: String,               // 'voiceover', 'music', 'sound_effect'
  source: String,             // 'tts', 'ai_voice', 'music_gen', 'upload'
  url: String,                // Audio file URL
  duration: Number,           // Duration in seconds
  format: String,             // 'wav', 'mp3'
  size: Number,               // File size in bytes
  generation_config: {        // Generation configuration
    model: String,
    voice: String,
    speed: Number,
    text: String
  },
  tags: [String],             // Tags for organization
  folder: String,             // Folder path
  created_at: Date,           // Creation timestamp
  updated_at: Date,           // Last update timestamp
  is_deleted: Boolean,        // Soft delete flag
  deleted_at: Date            // Deletion timestamp
}
```

## Usage

### Accessing Audio Studio

1. Navigate to `/audio-studio` in the application
2. The page is accessible from the main navigation menu (🎙️ Audio Studio)

### Generating Audio

1. Select the "Text-to-Speech" tab
2. Enter your text (up to 5000 characters)
3. Select a voice from the dropdown
4. Click the preview button (▶️) to hear the voice
5. Adjust speed if needed (0.5x - 2.0x)
6. Click "Generate Audio"
7. Listen to the generated audio
8. Click "Save to Library" to save

### Managing Audio Library

1. Select the "Audio Library" tab
2. View all your generated audio files
3. Click play (▶️) to listen to any audio
4. Click the menu (⋮) for options:
   - Download: Save audio file locally
   - Delete: Remove from library

## Integration with Audio Generation Service

The Audio Studio integrates with the `audio-generation-factory` service:

- **Service URL**: `http://audio-generation-factory:3000`
- **TTS Endpoint**: `/tts`
- **Model**: Kokoro-82m (82M parameter model)
- **Initialization**: First request may take ~10 minutes for model loading
- **Subsequent Requests**: Fast (<5 seconds)

## Development

### Adding New Voices

1. Update `frontend-server/src/constants/audioModels.js`
2. Add voice configuration to the appropriate language group
3. Voice will automatically appear in the voice selector

### Adding New Features

1. Create new tab in `AudioStudioTabs.jsx`
2. Create new panel component in `components/AudioStudio/`
3. Add tab content to `AudioStudioPage.jsx`
4. Update backend routes if needed

## Testing

### Manual Testing

1. Start the application
2. Navigate to Audio Studio
3. Test TTS generation with different voices
4. Test voice preview functionality
5. Test saving to library
6. Test library management (play, download, delete)

### API Testing

```bash
# Generate audio
curl -X POST http://localhost:8080/api/audio/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test",
    "model": "kokoro-82m",
    "voice": "am_adam",
    "speed": 1.0
  }'

# Get library
curl -X GET http://localhost:8080/api/audio-studio/library \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Audio Generation Fails

1. Check if audio-generation-factory service is running
2. Check service logs: `docker logs audio-generation-factory`
3. First request may timeout - retry after model initialization

### Voice Preview Not Working

1. Check browser console for errors
2. Verify audio proxy endpoint is accessible
3. Check CORS configuration

### Library Not Loading

1. Check MongoDB connection
2. Verify user authentication
3. Check browser network tab for API errors

## Future Roadmap

1. **Phase 2**: AI Voice Generation (ElevenLabs)
2. **Phase 3**: AI Music Generator (MusicGen)
3. **Phase 4**: Voice Cloning (XTTS)
4. **Phase 5**: Audio Editing & Mixing
5. **Phase 6**: Batch Generation & Templates

