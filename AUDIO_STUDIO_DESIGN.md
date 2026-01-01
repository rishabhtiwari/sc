# 🎙️ Audio Studio - Complete Design & Integration Plan

## 📋 Overview

Transform your existing audio capabilities into a comprehensive **Audio Studio** similar to Canva, with 4 main features:

1. **Text-to-Speech Voiceover** ✅ (Already have Kokoro-82m)
2. **AI Voice Generation** 🆕 (Integrate ElevenLabs/PlayHT)
3. **AI Music Generator** 🆕 (Integrate MusicGen/Stable Audio)
4. **Voice Cloning** ✅ (Already have XTTS)

---

## 🏗️ Current Audio System Analysis

### ✅ What You Already Have

**1. Text-to-Speech (TTS)**
- ✅ Kokoro-82m model (high-quality, fast)
- ✅ Multiple voices (male/female)
- ✅ Multi-language support (English, Hindi)
- ✅ Voice preview functionality
- ✅ Section-based speed control
- ✅ Audio generation service (port 8095)

**2. Voice Cloning**
- ✅ XTTS API integration (port 5003)
- ✅ Upload reference audio
- ✅ Chunked processing for long texts
- ✅ Multi-language support

**3. Infrastructure**
- ✅ Voice generator service (port 8094)
- ✅ Audio generation service (port 8095)
- ✅ Voice configuration API
- ✅ Audio file serving
- ✅ MongoDB voice config storage

---

## 🎨 Audio Studio UI Design

### Main Audio Studio Page

```
┌─────────────────────────────────────────────────────────────┐
│  🎙️ Audio Studio                                    [Close] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐  │
│  │  📝 Text to  │  🎤 AI Voice │  🎵 AI Music │ 🔊 Voice │  │
│  │   Speech     │  Generation  │  Generator   │ Cloning  │  │
│  │              │              │              │          │  │
│  │  Convert     │  Generate    │  Create      │ Clone    │  │
│  │  text to     │  realistic   │  background  │ any      │  │
│  │  speech      │  AI voices   │  music       │ voice    │  │
│  │              │              │              │          │  │
│  │  [Selected]  │              │              │          │  │
│  └──────────────┴──────────────┴──────────────┴──────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  TEXT TO SPEECH VOICEOVER                             │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │                                                         │  │
│  │  📝 Enter Text                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ Type or paste your text here...                 │  │  │
│  │  │                                                   │  │  │
│  │  │                                                   │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  🎤 Voice Selection                                    │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┐       │  │
│  │  │ 👨 Adam  │ 👨 Brian │ 👩 Emma  │ 👩 Sarah │       │  │
│  │  │ [▶️ Play]│ [▶️ Play]│ [▶️ Play]│ [▶️ Play]│       │  │
│  │  └──────────┴──────────┴──────────┴──────────┘       │  │
│  │                                                         │  │
│  │  ⚙️ Voice Settings                                     │  │
│  │  Speed: [====●====] 1.0x    Pitch: [====●====] 0      │  │
│  │  Stability: [====●====] 0.5  Clarity: [====●====] 0.7 │  │
│  │                                                         │  │
│  │  [🎙️ Generate Voiceover]  [▶️ Preview]  [💾 Save]     │  │
│  │                                                         │  │
│  │  🎵 Generated Audio                                    │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ ▶️ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:45 │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  📁 My Audio Library                                         │
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │ 🎵 Audio1│ 🎵 Audio2│ 🎵 Audio3│ [+ New]  │             │
│  │ 0:45     │ 1:23     │ 2:10     │          │             │
│  └──────────┴──────────┴──────────┴──────────┘             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Feature 1: Text-to-Speech Voiceover (ENHANCE EXISTING)

### Current Implementation
- ✅ Kokoro-82m model
- ✅ Voice selection
- ✅ Preview functionality
- ✅ Section-based speed control

### Enhancements Needed

**1. Voice Gallery with Categories**
```javascript
{
  "voices": {
    "standard": [
      { id: "am_adam", name: "Adam", gender: "male", accent: "American", preview: "url" },
      { id: "am_emma", name: "Emma", gender: "female", accent: "American", preview: "url" }
    ],
    "premium": [
      { id: "elevenlabs_josh", name: "Josh (Premium)", provider: "elevenlabs", preview: "url" }
    ],
    "custom": [
      { id: "cloned_voice_1", name: "My Cloned Voice", type: "cloned", preview: "url" }
    ]
  }
}
```

**2. Advanced Voice Controls**
- Speed: 0.5x - 2.0x (already have)
- Pitch: -12 to +12 semitones (NEW)
- Stability: 0.0 - 1.0 (NEW)
- Clarity/Similarity: 0.0 - 1.0 (NEW)
- Emotion: Neutral, Happy, Sad, Angry (NEW - if using ElevenLabs)

**3. Voice Preview Gallery**
- Grid layout with voice cards
- Play button on each card
- Waveform visualization
- Voice characteristics (gender, accent, age)

---

## 📦 Feature 2: AI Voice Generation (NEW - ElevenLabs/PlayHT)

### Integration Options

**Option A: ElevenLabs API** (Recommended)
- ✅ Best quality AI voices
- ✅ Voice cloning
- ✅ Emotion control
- ✅ Multi-language
- ❌ Paid API ($1/1000 characters)

**Option B: PlayHT API**
- ✅ Good quality
- ✅ More affordable
- ✅ Voice cloning
- ⚠️ Slightly lower quality than ElevenLabs

**Option C: Coqui TTS (Open Source)**
- ✅ Free
- ✅ Self-hosted
- ⚠️ Lower quality than commercial options

### Recommended: Hybrid Approach
- **Kokoro-82m** (existing) - Free tier, fast generation
- **ElevenLabs** - Premium tier, highest quality
- **Voice Cloning (XTTS)** - Custom voices

### Implementation

**New Service:** `ai-voice-service` (Port 5014)

```python
# ai-voice-service/app.py

from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1'

@app.route('/api/ai-voice/generate', methods=['POST'])
def generate_ai_voice():
    """
    Generate AI voice using ElevenLabs
    
    Request:
    {
        "text": "Hello world",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  // ElevenLabs voice ID
        "model": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": true
        }
    }
    """
    data = request.json
    
    # Call ElevenLabs API
    response = requests.post(
        f"{ELEVENLABS_API_URL}/text-to-speech/{data['voice_id']}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": data['text'],
            "model_id": data.get('model', 'eleven_multilingual_v2'),
            "voice_settings": data.get('voice_settings', {})
        }
    )
    
    if response.status_code == 200:
        # Save audio file
        audio_path = save_audio(response.content)
        return jsonify({
            "status": "success",
            "audio_url": audio_path
        })
    else:
        return jsonify({
            "status": "error",
            "error": response.text
        }), response.status_code

@app.route('/api/ai-voice/voices', methods=['GET'])
def get_available_voices():
    """Get list of available ElevenLabs voices"""
    response = requests.get(
        f"{ELEVENLABS_API_URL}/voices",
        headers={"xi-api-key": ELEVENLABS_API_KEY}
    )
    
    return jsonify(response.json())
```

---

## 📦 Feature 3: AI Music Generator (NEW)

### Integration Options

**Option A: Stable Audio (Stability AI)** (Recommended)
- ✅ High-quality music generation
- ✅ Text-to-music
- ✅ Customizable duration
- ✅ Commercial license
- ❌ Paid API

**Option B: MusicGen (Meta)** (Open Source)
- ✅ Free
- ✅ Self-hosted
- ✅ Text-to-music
- ⚠️ Requires GPU
- ⚠️ Lower quality than Stable Audio

**Option C: Mubert API**
- ✅ Royalty-free music
- ✅ API-based
- ✅ Mood/genre selection
- ⚠️ Limited customization

### Recommended: MusicGen (Self-hosted)

**New Service:** `music-generator-service` (Port 5015)

```python
# music-generator-service/app.py

from flask import Flask, request, jsonify, send_file
from audiocraft.models import MusicGen
import torch
import torchaudio
import os

app = Flask(__name__)

# Load MusicGen model
model = MusicGen.get_pretrained('facebook/musicgen-medium')

@app.route('/api/music/generate', methods=['POST'])
def generate_music():
    """
    Generate AI music from text description
    
    Request:
    {
        "prompt": "upbeat electronic music with drums",
        "duration": 30,  // seconds
        "temperature": 1.0,
        "top_k": 250,
        "top_p": 0.0
    }
    """
    data = request.json
    
    prompt = data.get('prompt')
    duration = data.get('duration', 30)
    
    # Set generation parameters
    model.set_generation_params(
        duration=duration,
        temperature=data.get('temperature', 1.0),
        top_k=data.get('top_k', 250),
        top_p=data.get('top_p', 0.0)
    )
    
    # Generate music
    wav = model.generate([prompt])
    
    # Save audio file
    output_path = f"output/music_{int(time.time())}.wav"
    torchaudio.save(output_path, wav[0].cpu(), model.sample_rate)
    
    return jsonify({
        "status": "success",
        "audio_url": f"/api/music/serve/{os.path.basename(output_path)}",
        "duration": duration
    })

@app.route('/api/music/presets', methods=['GET'])
def get_music_presets():
    """Get predefined music style presets"""
    return jsonify({
        "presets": [
            {
                "id": "upbeat_electronic",
                "name": "Upbeat Electronic",
                "prompt": "upbeat electronic music with drums and synthesizers",
                "icon": "🎹"
            },
            {
                "id": "calm_ambient",
                "name": "Calm Ambient",
                "prompt": "calm ambient music with soft pads and gentle melodies",
                "icon": "🌊"
            },
            {
                "id": "energetic_rock",
                "name": "Energetic Rock",
                "prompt": "energetic rock music with electric guitars and drums",
                "icon": "🎸"
            },
            {
                "id": "corporate_background",
                "name": "Corporate Background",
                "prompt": "corporate background music with piano and strings",
                "icon": "💼"
            }
        ]
    })
```

---

## 📦 Feature 4: Voice Cloning (ENHANCE EXISTING)

### Current Implementation
- ✅ XTTS API integration
- ✅ Upload reference audio
- ✅ Chunked processing

### Enhancements Needed

**1. Voice Library Management**
```javascript
{
  "cloned_voices": [
    {
      "id": "cloned_voice_1",
      "name": "My Voice",
      "reference_audio": "s3://bucket/voices/my_voice.wav",
      "created_at": "2025-12-31T10:00:00Z",
      "sample_text": "This is how my cloned voice sounds",
      "sample_audio": "s3://bucket/voices/my_voice_sample.wav"
    }
  ]
}
```

**2. Voice Training UI**
- Upload multiple audio samples (3-5 recommended)
- Audio quality validation
- Background noise detection
- Voice preview after training

**3. Voice Management**
- List all cloned voices
- Delete cloned voices
- Rename cloned voices
- Share cloned voices (team feature)

---

## 🗄️ Database Schema Extensions

### New Collections

**1. `audio_library` Collection**
```javascript
{
  audio_id: "audio_abc123",
  customer_id: "customer_xyz",
  user_id: "user_123",

  // Audio metadata
  name: "Product Voiceover 1",
  type: "voiceover",  // voiceover, music, sound_effect
  source: "tts",  // tts, ai_voice, ai_music, cloned, uploaded

  // File info
  url: "s3://bucket/audio/voiceover_1.wav",
  duration: 45.5,  // seconds
  format: "wav",
  size: 1024000,  // bytes

  // Generation config (for regeneration)
  generation_config: {
    provider: "kokoro",  // kokoro, elevenlabs, musicgen, xtts
    model: "kokoro-82m",
    voice: "am_adam",
    text: "Original text used for generation",
    settings: {
      speed: 1.0,
      pitch: 0,
      stability: 0.5
    }
  },

  // Metadata
  created_at: ISODate(),
  updated_at: ISODate(),
  tags: ["product", "voiceover"],
  folder: "Product Videos"
}
```

**2. `cloned_voices` Collection**
```javascript
{
  voice_id: "voice_abc123",
  customer_id: "customer_xyz",
  user_id: "user_123",

  // Voice info
  name: "My Voice",
  description: "My personal voice clone",

  // Reference audio
  reference_audios: [
    {
      url: "s3://bucket/voices/sample1.wav",
      duration: 10.5,
      uploaded_at: ISODate()
    }
  ],

  // Training status
  status: "trained",  // pending, training, trained, failed
  training_started_at: ISODate(),
  training_completed_at: ISODate(),

  // Voice characteristics (auto-detected)
  characteristics: {
    gender: "male",
    age_range: "adult",
    accent: "american",
    quality_score: 0.85
  },

  // Sample audio
  sample_text: "This is how my cloned voice sounds",
  sample_audio: "s3://bucket/voices/sample.wav",

  // Usage stats
  usage_count: 42,
  last_used_at: ISODate(),

  // Metadata
  created_at: ISODate(),
  is_active: true
}
```

**3. `music_library` Collection**
```javascript
{
  music_id: "music_abc123",
  customer_id: "customer_xyz",
  user_id: "user_123",

  // Music metadata
  name: "Upbeat Background Music",
  genre: "electronic",
  mood: "upbeat",

  // File info
  url: "s3://bucket/music/track_1.wav",
  duration: 120.0,
  bpm: 128,
  key: "C major",

  // Generation config
  generation_config: {
    provider: "musicgen",
    prompt: "upbeat electronic music with drums",
    duration: 120,
    temperature: 1.0
  },

  // Metadata
  created_at: ISODate(),
  tags: ["background", "upbeat"],
  is_royalty_free: true
}
```

---

## 🎨 Frontend Components

### Component Structure

```
AudioStudio/
├── AudioStudioPage.jsx (Main container)
├── AudioStudioTabs.jsx (4 tabs)
├── TextToSpeech/
│   ├── TextToSpeechPanel.jsx
│   ├── VoiceGallery.jsx
│   ├── VoiceCard.jsx
│   ├── VoiceSettings.jsx
│   └── AudioPreview.jsx
├── AIVoiceGeneration/
│   ├── AIVoicePanel.jsx
│   ├── ElevenLabsVoices.jsx
│   ├── VoiceCustomization.jsx
│   └── EmotionControl.jsx
├── AIMusicGenerator/
│   ├── MusicGeneratorPanel.jsx
│   ├── MusicPresets.jsx
│   ├── MusicPromptInput.jsx
│   └── MusicPreview.jsx
├── VoiceCloning/
│   ├── VoiceCloningPanel.jsx
│   ├── VoiceUploader.jsx
│   ├── VoiceTraining.jsx
│   ├── ClonedVoicesList.jsx
│   └── VoiceQualityCheck.jsx
└── AudioLibrary/
    ├── AudioLibraryPanel.jsx
    ├── AudioGrid.jsx
    ├── AudioCard.jsx
    └── AudioPlayer.jsx
```

### Main Audio Studio Page

**File:** `frontend-server/src/pages/AudioStudioPage.jsx`

```jsx
import React, { useState } from 'react';
import AudioStudioTabs from '../components/AudioStudio/AudioStudioTabs';
import TextToSpeechPanel from '../components/AudioStudio/TextToSpeech/TextToSpeechPanel';
import AIVoicePanel from '../components/AudioStudio/AIVoiceGeneration/AIVoicePanel';
import MusicGeneratorPanel from '../components/AudioStudio/AIMusicGenerator/MusicGeneratorPanel';
import VoiceCloningPanel from '../components/AudioStudio/VoiceCloning/VoiceCloningPanel';
import AudioLibraryPanel from '../components/AudioStudio/AudioLibrary/AudioLibraryPanel';

const AudioStudioPage = () => {
  const [activeTab, setActiveTab] = useState('tts');

  const tabs = [
    { id: 'tts', name: 'Text to Speech', icon: '📝' },
    { id: 'ai_voice', name: 'AI Voice Generation', icon: '🎤' },
    { id: 'ai_music', name: 'AI Music Generator', icon: '🎵' },
    { id: 'voice_cloning', name: 'Voice Cloning', icon: '🔊' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🎙️</span>
              <h1 className="text-2xl font-bold text-gray-900">Audio Studio</h1>
            </div>
            <button className="text-gray-600 hover:text-gray-900">
              ✕ Close
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <AudioStudioTabs
            tabs={tabs}
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Panel (2/3 width) */}
          <div className="lg:col-span-2">
            {activeTab === 'tts' && <TextToSpeechPanel />}
            {activeTab === 'ai_voice' && <AIVoicePanel />}
            {activeTab === 'ai_music' && <MusicGeneratorPanel />}
            {activeTab === 'voice_cloning' && <VoiceCloningPanel />}
          </div>

          {/* Audio Library Sidebar (1/3 width) */}
          <div className="lg:col-span-1">
            <AudioLibraryPanel />
          </div>
        </div>
      </main>
    </div>
  );
};

export default AudioStudioPage;
```

### Text-to-Speech Panel (Enhanced)

**File:** `frontend-server/src/components/AudioStudio/TextToSpeech/TextToSpeechPanel.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import VoiceGallery from './VoiceGallery';
import VoiceSettings from './VoiceSettings';
import AudioPreview from './AudioPreview';
import { useAudioGeneration } from '../../../hooks/useAudioGeneration';
import { AUDIO_MODELS } from '../../../constants/audioModels';

const TextToSpeechPanel = () => {
  const [text, setText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('am_adam');
  const [selectedModel, setSelectedModel] = useState('kokoro-82m');
  const [voiceSettings, setVoiceSettings] = useState({
    speed: 1.0,
    pitch: 0,
    stability: 0.5,
    clarity: 0.75
  });
  const [audioUrl, setAudioUrl] = useState(null);
  const { generate, generating } = useAudioGeneration();

  const handleGenerate = async () => {
    const result = await generate({
      endpoint: '/audio/generate',
      text,
      model: selectedModel,
      voice: selectedVoice,
      settings: voiceSettings,
      onSuccess: (url) => {
        setAudioUrl(url);
      }
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 space-y-6">
      {/* Text Input */}
      <div>
        <label className="block text-sm font-semibold text-gray-900 mb-2">
          📝 Enter Text
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type or paste your text here..."
          className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
        <div className="mt-1 text-xs text-gray-500">
          {text.length} characters
        </div>
      </div>

      {/* Voice Gallery */}
      <VoiceGallery
        selectedVoice={selectedVoice}
        onVoiceSelect={setSelectedVoice}
        model={selectedModel}
      />

      {/* Voice Settings */}
      <VoiceSettings
        settings={voiceSettings}
        onChange={setVoiceSettings}
      />

      {/* Generate Button */}
      <div className="flex gap-3">
        <button
          onClick={handleGenerate}
          disabled={!text || generating}
          className="flex-1 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {generating ? '⏳ Generating...' : '🎙️ Generate Voiceover'}
        </button>
        {audioUrl && (
          <button className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium">
            💾 Save to Library
          </button>
        )}
      </div>

      {/* Audio Preview */}
      {audioUrl && (
        <AudioPreview audioUrl={audioUrl} />
      )}
    </div>
  );
};

export default TextToSpeechPanel;
```

### Voice Gallery Component

**File:** `frontend-server/src/components/AudioStudio/TextToSpeech/VoiceGallery.jsx`

```jsx
import React, { useState } from 'react';
import VoiceCard from './VoiceCard';
import { getAvailableVoices } from '../../../constants/audioModels';

const VoiceGallery = ({ selectedVoice, onVoiceSelect, model }) => {
  const [previewingVoice, setPreviewingVoice] = useState(null);
  const voices = getAvailableVoices(model);

  const handlePreview = async (voiceId) => {
    setPreviewingVoice(voiceId);
    // Preview logic (already implemented in your system)
    // ...
    setPreviewingVoice(null);
  };

  // Group voices by category
  const groupedVoices = voices.reduce((acc, voice) => {
    const category = voice.gender || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(voice);
    return acc;
  }, {});

  return (
    <div>
      <label className="block text-sm font-semibold text-gray-900 mb-3">
        🎤 Voice Selection
      </label>

      {Object.entries(groupedVoices).map(([category, voiceList]) => (
        <div key={category} className="mb-4">
          <h6 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            {category === 'male' ? '👨 Male Voices' : '👩 Female Voices'}
          </h6>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {voiceList.map((voice) => (
              <VoiceCard
                key={voice.id}
                voice={voice}
                isSelected={selectedVoice === voice.id}
                isPreviewing={previewingVoice === voice.id}
                onSelect={() => onVoiceSelect(voice.id)}
                onPreview={() => handlePreview(voice.id)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default VoiceGallery;
```

---

## 🔌 Backend API Endpoints

### New Endpoints

**1. Audio Library API**

```
GET    /api/audio-studio/library
POST   /api/audio-studio/library
DELETE /api/audio-studio/library/:audioId
PUT    /api/audio-studio/library/:audioId
```

**2. AI Voice Generation API**

```
POST   /api/audio-studio/ai-voice/generate
GET    /api/audio-studio/ai-voice/voices
POST   /api/audio-studio/ai-voice/preview
```

**3. AI Music Generation API**

```
POST   /api/audio-studio/music/generate
GET    /api/audio-studio/music/presets
POST   /api/audio-studio/music/preview
```

**4. Voice Cloning API (Enhanced)**

```
POST   /api/audio-studio/voice-cloning/upload
POST   /api/audio-studio/voice-cloning/train
GET    /api/audio-studio/voice-cloning/voices
DELETE /api/audio-studio/voice-cloning/voices/:voiceId
POST   /api/audio-studio/voice-cloning/generate
```

---

## 📊 Integration with Design Editor

### How Audio Studio Integrates with Canvas Editor

**1. Audio Panel in Design Editor**

```jsx
// In DesignEditor.jsx
<LeftSidebar>
  <AudioPanel />  {/* NEW */}
</LeftSidebar>
```

**2. Audio Panel Component**

```jsx
const AudioPanel = () => {
  const [showAudioStudio, setShowAudioStudio] = useState(false);

  return (
    <div className="p-4">
      <h3 className="font-semibold mb-3">🎵 Audio</h3>

      {/* Quick Actions */}
      <div className="space-y-2">
        <button
          onClick={() => setShowAudioStudio(true)}
          className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          🎙️ Open Audio Studio
        </button>

        <button className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
          📁 Browse Audio Library
        </button>
      </div>

      {/* Recent Audio */}
      <div className="mt-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Audio</h4>
        {/* Audio list */}
      </div>

      {/* Audio Studio Modal */}
      {showAudioStudio && (
        <AudioStudioModal onClose={() => setShowAudioStudio(false)} />
      )}
    </div>
  );
};
```

**3. Add Audio to Timeline**

```jsx
// When user selects audio from library
const handleAddAudioToTimeline = (audioId) => {
  const audio = audioLibrary.find(a => a.id === audioId);

  // Add to timeline
  dispatch(addAudioTrack({
    id: generateId(),
    type: 'audio',
    asset_id: audioId,
    url: audio.url,
    start: 0,
    duration: audio.duration,
    volume: 1.0
  }));
};
```

---

## 🚀 Implementation Roadmap

### Phase 1: Enhance Existing TTS (Week 1-2)

**Tasks:**
- [ ] Create AudioStudioPage.jsx
- [ ] Build VoiceGallery component
- [ ] Add VoiceSettings component (pitch, stability, clarity)
- [ ] Create AudioLibrary component
- [ ] Add audio_library MongoDB collection
- [ ] Implement save to library functionality

### Phase 2: AI Voice Generation (Week 3-4)

**Tasks:**
- [ ] Create ai-voice-service (Port 5014)
- [ ] Integrate ElevenLabs API
- [ ] Build AIVoicePanel component
- [ ] Add emotion control UI
- [ ] Implement voice preview
- [ ] Add premium voice gallery

### Phase 3: AI Music Generator (Week 5-6)

**Tasks:**
- [ ] Create music-generator-service (Port 5015)
- [ ] Integrate MusicGen model
- [ ] Build MusicGeneratorPanel component
- [ ] Create music presets
- [ ] Add music_library MongoDB collection
- [ ] Implement music preview

### Phase 4: Voice Cloning Enhancement (Week 7)

**Tasks:**
- [ ] Enhance VoiceCloningPanel UI
- [ ] Add voice quality validation
- [ ] Create cloned_voices MongoDB collection
- [ ] Build voice management UI
- [ ] Add voice sharing (team feature)

### Phase 5: Integration with Design Editor (Week 8)

**Tasks:**
- [ ] Add AudioPanel to DesignEditor
- [ ] Integrate with timeline
- [ ] Add audio waveform visualization
- [ ] Implement audio mixing
- [ ] Add audio effects (fade, volume)

---

## 💰 Cost Estimation

### API Costs (Monthly)

**ElevenLabs API:**
- Free tier: 10,000 characters/month
- Creator tier: $5/month (30,000 characters)
- Pro tier: $22/month (100,000 characters)

**Stable Audio API:**
- Free tier: 20 generations/month
- Basic tier: $12/month (500 generations)

**Self-Hosted (MusicGen):**
- GPU instance: ~$100-300/month (AWS/GCP)
- Storage: ~$10/month

**Recommended for MVP:**
- Use existing Kokoro-82m (free)
- Add ElevenLabs Creator tier ($5/month)
- Use MusicGen self-hosted (one-time GPU cost)
- Total: ~$5-15/month

---

## 📈 Success Metrics

**User Engagement:**
- Audio generations per user
- Voice cloning usage
- Music generation usage
- Audio library size

**Quality Metrics:**
- Audio generation success rate
- Voice cloning quality score
- User satisfaction rating

**Performance:**
- Audio generation time < 10s
- Voice cloning time < 2 minutes
- Music generation time < 30s

---

## ✅ Summary

### What You're Building

**4 Main Features:**
1. ✅ **Text-to-Speech** (Enhance existing Kokoro-82m)
2. 🆕 **AI Voice Generation** (Add ElevenLabs)
3. 🆕 **AI Music Generator** (Add MusicGen)
4. ✅ **Voice Cloning** (Enhance existing XTTS)

### Timeline: 8 Weeks

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | Week 1-2 | Enhanced TTS + Audio Library |
| Phase 2 | Week 3-4 | AI Voice Generation |
| Phase 3 | Week 5-6 | AI Music Generator |
| Phase 4 | Week 7 | Voice Cloning Enhancement |
| Phase 5 | Week 8 | Design Editor Integration |

### Key Advantages

1. ✅ **Already have TTS** (Kokoro-82m)
2. ✅ **Already have Voice Cloning** (XTTS)
3. ✅ **Strong infrastructure** (microservices, MongoDB)
4. 🆕 **Add premium AI voices** (ElevenLabs)
5. 🆕 **Add AI music** (MusicGen)

---

**Ready to build your Audio Studio! 🎙️**

