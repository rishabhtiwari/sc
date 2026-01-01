# 🎙️ Audio Studio - Starter Code & File Structure

## 📁 Complete File Structure

```
sc/
├── frontend-server/
│   └── src/
│       ├── pages/
│       │   └── AudioStudioPage.jsx                    🆕 NEW
│       ├── components/
│       │   └── AudioStudio/                           🆕 NEW FOLDER
│       │       ├── AudioStudioTabs.jsx
│       │       ├── TextToSpeech/
│       │       │   ├── TextToSpeechPanel.jsx
│       │       │   ├── VoiceGallery.jsx
│       │       │   ├── VoiceCard.jsx
│       │       │   ├── VoiceSettings.jsx
│       │       │   └── AudioPreview.jsx
│       │       ├── AIVoiceGeneration/
│       │       │   ├── AIVoicePanel.jsx
│       │       │   ├── ElevenLabsVoices.jsx
│       │       │   ├── VoiceCustomization.jsx
│       │       │   └── EmotionControl.jsx
│       │       ├── AIMusicGenerator/
│       │       │   ├── MusicGeneratorPanel.jsx
│       │       │   ├── MusicPresets.jsx
│       │       │   ├── MusicPromptInput.jsx
│       │       │   └── MusicPreview.jsx
│       │       ├── VoiceCloning/
│       │       │   ├── VoiceCloningPanel.jsx
│       │       │   ├── VoiceUploader.jsx
│       │       │   ├── VoiceTraining.jsx
│       │       │   ├── ClonedVoicesList.jsx
│       │       │   └── VoiceQualityCheck.jsx
│       │       └── AudioLibrary/
│       │           ├── AudioLibraryPanel.jsx
│       │           ├── AudioGrid.jsx
│       │           ├── AudioCard.jsx
│       │           └── AudioPlayer.jsx
│       ├── hooks/
│       │   ├── useAudioGeneration.js                  🆕 NEW
│       │   ├── useAudioLibrary.js                     🆕 NEW
│       │   └── useVoiceCloning.js                     🆕 NEW
│       └── constants/
│           └── audioModels.js                         🆕 NEW
│
├── ai-voice-service/                                  🆕 NEW SERVICE
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── music-generator-service/                           🆕 NEW SERVICE
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── models/
│       └── download_models.py
│
├── voice-generator-service/                           ✅ EXISTING
│   └── app.py
│
├── audio-generation-service/                          ✅ EXISTING
│   └── app.py
│
└── docker-compose.yml                                 🔄 UPDATE
```

---

## 🚀 Phase 1 Starter Code

### 1. Audio Studio Page

**File:** `frontend-server/src/pages/AudioStudioPage.jsx`

```jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AudioStudioTabs from '../components/AudioStudio/AudioStudioTabs';
import TextToSpeechPanel from '../components/AudioStudio/TextToSpeech/TextToSpeechPanel';
import AudioLibraryPanel from '../components/AudioStudio/AudioLibrary/AudioLibraryPanel';

const AudioStudioPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('tts');

  const tabs = [
    { id: 'tts', name: 'Text to Speech', icon: '📝', description: 'Convert text to speech' },
    { id: 'ai_voice', name: 'AI Voice', icon: '🎤', description: 'Generate AI voices', disabled: true },
    { id: 'ai_music', name: 'AI Music', icon: '🎵', description: 'Create background music', disabled: true },
    { id: 'voice_cloning', name: 'Voice Cloning', icon: '🔊', description: 'Clone any voice', disabled: true }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🎙️</span>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Audio Studio</h1>
                <p className="text-sm text-gray-500">Create professional voiceovers and music</p>
              </div>
            </div>
            <button 
              onClick={() => navigate(-1)}
              className="text-gray-600 hover:text-gray-900 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              ✕ Close
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <AudioStudioTabs 
            tabs={tabs} 
            activeTab={activeTab} 
            onTabChange={setActiveTab} 
          />
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Panel (2/3 width) */}
          <div className="lg:col-span-2">
            {activeTab === 'tts' && <TextToSpeechPanel />}
            {activeTab === 'ai_voice' && (
              <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
                <span className="text-6xl mb-4 block">🎤</span>
                <h3 className="text-xl font-semibold mb-2">AI Voice Generation</h3>
                <p className="text-gray-600">Coming soon...</p>
              </div>
            )}
            {activeTab === 'ai_music' && (
              <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
                <span className="text-6xl mb-4 block">🎵</span>
                <h3 className="text-xl font-semibold mb-2">AI Music Generator</h3>
                <p className="text-gray-600">Coming soon...</p>
              </div>
            )}
            {activeTab === 'voice_cloning' && (
              <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
                <span className="text-6xl mb-4 block">🔊</span>
                <h3 className="text-xl font-semibold mb-2">Voice Cloning</h3>
                <p className="text-gray-600">Coming soon...</p>
              </div>
            )}
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

---

### 2. Audio Studio Tabs

**File:** `frontend-server/src/components/AudioStudio/AudioStudioTabs.jsx`

```jsx
import React from 'react';

const AudioStudioTabs = ({ tabs, activeTab, onTabChange }) => {
  return (
    <div className="flex gap-1 overflow-x-auto">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => !tab.disabled && onTabChange(tab.id)}
          disabled={tab.disabled}
          className={`
            flex items-center gap-2 px-6 py-4 border-b-2 transition-all whitespace-nowrap
            ${activeTab === tab.id 
              ? 'border-indigo-600 text-indigo-600 bg-indigo-50' 
              : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }
            ${tab.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          <span className="text-xl">{tab.icon}</span>
          <div className="text-left">
            <div className="font-semibold">{tab.name}</div>
            <div className="text-xs text-gray-500">{tab.description}</div>
          </div>
          {tab.disabled && (
            <span className="ml-2 px-2 py-0.5 bg-gray-200 text-gray-600 text-xs rounded-full">
              Soon
            </span>
          )}
        </button>
      ))}
    </div>
  );
};

export default AudioStudioTabs;
```

---

### 3. Text-to-Speech Panel

**File:** `frontend-server/src/components/AudioStudio/TextToSpeech/TextToSpeechPanel.jsx`

```jsx
import React, { useState } from 'react';
import VoiceGallery from './VoiceGallery';
import VoiceSettings from './VoiceSettings';
import AudioPreview from './AudioPreview';
import { useAudioGeneration } from '../../../hooks/useAudioGeneration';

const TextToSpeechPanel = () => {
  const [text, setText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('am_adam');
  const [voiceSettings, setVoiceSettings] = useState({
    speed: 1.0,
    pitch: 0,
    stability: 0.5,
    clarity: 0.75
  });
  const [audioUrl, setAudioUrl] = useState(null);
  const { generate, generating, error } = useAudioGeneration();

  const handleGenerate = async () => {
    const result = await generate({
      text,
      voice: selectedVoice,
      settings: voiceSettings
    });
    
    if (result.success) {
      setAudioUrl(result.audioUrl);
    }
  };

  const handleSaveToLibrary = async () => {
    // TODO: Implement save to library
    console.log('Save to library:', { text, voice: selectedVoice, audioUrl });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-gray-900">📝 Text to Speech Voiceover</h2>
        <p className="text-sm text-gray-600 mt-1">
          Convert your text into natural-sounding speech with our AI voices
        </p>
      </div>

      {/* Text Input */}
      <div>
        <label className="block text-sm font-semibold text-gray-900 mb-2">
          Enter Text
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type or paste your text here..."
          className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
        <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
          <span>{text.length} characters</span>
          <span>~{Math.ceil(text.length / 5)} words</span>
        </div>
      </div>

      {/* Voice Gallery */}
      <VoiceGallery
        selectedVoice={selectedVoice}
        onVoiceSelect={setSelectedVoice}
      />

      {/* Voice Settings */}
      <VoiceSettings
        settings={voiceSettings}
        onChange={setVoiceSettings}
      />

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">❌ {error}</p>
        </div>
      )}

      {/* Generate Button */}
      <div className="flex gap-3">
        <button
          onClick={handleGenerate}
          disabled={!text || generating}
          className="flex-1 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {generating ? (
            <>
              <span className="inline-block animate-spin mr-2">⏳</span>
              Generating...
            </>
          ) : (
            <>🎙️ Generate Voiceover</>
          )}
        </button>
        {audioUrl && (
          <button 
            onClick={handleSaveToLibrary}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium transition-colors"
          >
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

---

### 4. Voice Gallery Component

**File:** `frontend-server/src/components/AudioStudio/TextToSpeech/VoiceGallery.jsx`

```jsx
import React, { useState } from 'react';
import VoiceCard from './VoiceCard';
import { KOKORO_VOICES } from '../../../constants/audioModels';

const VoiceGallery = ({ selectedVoice, onVoiceSelect }) => {
  const [previewingVoice, setPreviewingVoice] = useState(null);

  const handlePreview = async (voiceId) => {
    setPreviewingVoice(voiceId);

    // Play preview audio
    const voice = KOKORO_VOICES.find(v => v.id === voiceId);
    if (voice.previewUrl) {
      const audio = new Audio(voice.previewUrl);
      audio.play();
      audio.onended = () => setPreviewingVoice(null);
    } else {
      // Generate preview on the fly
      setTimeout(() => setPreviewingVoice(null), 2000);
    }
  };

  // Group voices by gender
  const maleVoices = KOKORO_VOICES.filter(v => v.gender === 'male');
  const femaleVoices = KOKORO_VOICES.filter(v => v.gender === 'female');

  return (
    <div>
      <label className="block text-sm font-semibold text-gray-900 mb-3">
        🎤 Voice Selection
      </label>

      {/* Male Voices */}
      {maleVoices.length > 0 && (
        <div className="mb-4">
          <h6 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            👨 Male Voices
          </h6>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {maleVoices.map((voice) => (
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
      )}

      {/* Female Voices */}
      {femaleVoices.length > 0 && (
        <div>
          <h6 className="text-xs font-semibold text-gray-500 uppercase mb-2">
            👩 Female Voices
          </h6>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {femaleVoices.map((voice) => (
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
      )}
    </div>
  );
};

export default VoiceGallery;
```

---

### 5. Voice Card Component

**File:** `frontend-server/src/components/AudioStudio/TextToSpeech/VoiceCard.jsx`

```jsx
import React from 'react';

const VoiceCard = ({ voice, isSelected, isPreviewing, onSelect, onPreview }) => {
  return (
    <div
      onClick={onSelect}
      className={`
        relative p-4 border-2 rounded-lg cursor-pointer transition-all
        ${isSelected
          ? 'border-indigo-600 bg-indigo-50 shadow-md'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
        }
      `}
    >
      {/* Selected Badge */}
      {isSelected && (
        <div className="absolute top-2 right-2 w-5 h-5 bg-indigo-600 rounded-full flex items-center justify-center">
          <span className="text-white text-xs">✓</span>
        </div>
      )}

      {/* Voice Icon */}
      <div className="text-center mb-2">
        <span className="text-3xl">{voice.gender === 'male' ? '👨' : '👩'}</span>
      </div>

      {/* Voice Name */}
      <div className="text-center mb-2">
        <h4 className="font-semibold text-gray-900 text-sm">{voice.name}</h4>
        {voice.accent && (
          <p className="text-xs text-gray-500">{voice.accent}</p>
        )}
      </div>

      {/* Preview Button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onPreview();
        }}
        disabled={isPreviewing}
        className={`
          w-full px-3 py-1.5 text-xs font-medium rounded transition-colors
          ${isPreviewing
            ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }
        `}
      >
        {isPreviewing ? '⏸️ Playing...' : '▶️ Preview'}
      </button>
    </div>
  );
};

export default VoiceCard;
```

---

### 6. Voice Settings Component

**File:** `frontend-server/src/components/AudioStudio/TextToSpeech/VoiceSettings.jsx`

```jsx
import React from 'react';

const VoiceSettings = ({ settings, onChange }) => {
  const handleChange = (key, value) => {
    onChange({ ...settings, [key]: value });
  };

  return (
    <div>
      <label className="block text-sm font-semibold text-gray-900 mb-3">
        ⚙️ Voice Settings
      </label>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Speed */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-700">Speed</label>
            <span className="text-sm font-medium text-gray-900">{settings.speed.toFixed(1)}x</span>
          </div>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={settings.speed}
            onChange={(e) => handleChange('speed', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0.5x</span>
            <span>2.0x</span>
          </div>
        </div>

        {/* Pitch */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-700">Pitch</label>
            <span className="text-sm font-medium text-gray-900">{settings.pitch > 0 ? '+' : ''}{settings.pitch}</span>
          </div>
          <input
            type="range"
            min="-12"
            max="12"
            step="1"
            value={settings.pitch}
            onChange={(e) => handleChange('pitch', parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>-12</span>
            <span>+12</span>
          </div>
        </div>

        {/* Stability */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-700">Stability</label>
            <span className="text-sm font-medium text-gray-900">{settings.stability.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={settings.stability}
            onChange={(e) => handleChange('stability', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Variable</span>
            <span>Stable</span>
          </div>
        </div>

        {/* Clarity */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm text-gray-700">Clarity</label>
            <span className="text-sm font-medium text-gray-900">{settings.clarity.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={settings.clarity}
            onChange={(e) => handleChange('clarity', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Soft</span>
            <span>Clear</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceSettings;
```

---

### 7. Audio Preview Component

**File:** `frontend-server/src/components/AudioStudio/TextToSpeech/AudioPreview.jsx`

```jsx
import React, { useRef, useState, useEffect } from 'react';

const AudioPreview = ({ audioUrl }) => {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [audioUrl]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e) => {
    const audio = audioRef.current;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    audio.currentTime = percentage * duration;
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-6">
      <label className="block text-sm font-semibold text-gray-900 mb-3">
        🎵 Generated Audio
      </label>

      <audio ref={audioRef} src={audioUrl} />

      <div className="bg-white rounded-lg p-4 shadow-sm">
        {/* Play/Pause Button */}
        <div className="flex items-center gap-4">
          <button
            onClick={togglePlay}
            className="w-12 h-12 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full flex items-center justify-center transition-colors"
          >
            {isPlaying ? '⏸️' : '▶️'}
          </button>

          <div className="flex-1">
            {/* Progress Bar */}
            <div
              onClick={handleSeek}
              className="h-2 bg-gray-200 rounded-full cursor-pointer relative"
            >
              <div
                className="h-full bg-indigo-600 rounded-full transition-all"
                style={{ width: `${(currentTime / duration) * 100}%` }}
              />
            </div>

            {/* Time */}
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* Download Button */}
          <a
            href={audioUrl}
            download="voiceover.wav"
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
          >
            ⬇️ Download
          </a>
        </div>
      </div>
    </div>
  );
};

export default AudioPreview;
```

---

### 8. Audio Library Panel

**File:** `frontend-server/src/components/AudioStudio/AudioLibrary/AudioLibraryPanel.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import AudioGrid from './AudioGrid';
import { useAudioLibrary } from '../../../hooks/useAudioLibrary';

const AudioLibraryPanel = () => {
  const { audioFiles, loading, fetchAudioLibrary, deleteAudio } = useAudioLibrary();
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchAudioLibrary();
  }, []);

  const filteredAudio = audioFiles.filter(audio => {
    if (filter === 'all') return true;
    return audio.type === filter;
  });

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 sticky top-24">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">📁 Audio Library</h3>
        <span className="text-sm text-gray-500">{audioFiles.length} files</span>
      </div>

      {/* Filter */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 text-xs rounded-full transition-colors ${
            filter === 'all'
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('voiceover')}
          className={`px-3 py-1 text-xs rounded-full transition-colors ${
            filter === 'voiceover'
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Voiceovers
        </button>
        <button
          onClick={() => setFilter('music')}
          className={`px-3 py-1 text-xs rounded-full transition-colors ${
            filter === 'music'
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Music
        </button>
      </div>

      {/* Audio Grid */}
      {loading ? (
        <div className="text-center py-8">
          <div className="inline-block animate-spin text-3xl">⏳</div>
          <p className="text-sm text-gray-500 mt-2">Loading...</p>
        </div>
      ) : filteredAudio.length === 0 ? (
        <div className="text-center py-8">
          <span className="text-5xl mb-2 block">🎵</span>
          <p className="text-sm text-gray-500">No audio files yet</p>
          <p className="text-xs text-gray-400 mt-1">Generate your first voiceover!</p>
        </div>
      ) : (
        <AudioGrid audioFiles={filteredAudio} onDelete={deleteAudio} />
      )}
    </div>
  );
};

export default AudioLibraryPanel;
```

---

### 9. Audio Grid Component

**File:** `frontend-server/src/components/AudioStudio/AudioLibrary/AudioGrid.jsx`

```jsx
import React from 'react';
import AudioCard from './AudioCard';

const AudioGrid = ({ audioFiles, onDelete }) => {
  return (
    <div className="space-y-2 max-h-[600px] overflow-y-auto">
      {audioFiles.map((audio) => (
        <AudioCard
          key={audio.id}
          audio={audio}
          onDelete={() => onDelete(audio.id)}
        />
      ))}
    </div>
  );
};

export default AudioGrid;
```

---

### 10. Audio Card Component

**File:** `frontend-server/src/components/AudioStudio/AudioLibrary/AudioCard.jsx`

```jsx
import React, { useState } from 'react';

const AudioCard = ({ audio, onDelete }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const handlePlay = () => {
    const audioElement = new Audio(audio.url);
    audioElement.play();
    setIsPlaying(true);
    audioElement.onended = () => setIsPlaying(false);
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="group relative p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all">
      <div className="flex items-center gap-3">
        {/* Play Button */}
        <button
          onClick={handlePlay}
          disabled={isPlaying}
          className={`
            w-10 h-10 rounded-full flex items-center justify-center transition-colors
            ${isPlaying
              ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
              : 'bg-indigo-100 text-indigo-600 hover:bg-indigo-200'
            }
          `}
        >
          {isPlaying ? '⏸️' : '▶️'}
        </button>

        {/* Audio Info */}
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-gray-900 truncate">
            {audio.name || 'Untitled'}
          </h4>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>{formatDuration(audio.duration)}</span>
            <span>•</span>
            <span>{audio.type}</span>
          </div>
        </div>

        {/* Menu Button */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
          >
            ⋮
          </button>

          {/* Dropdown Menu */}
          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 top-8 z-20 w-40 bg-white border border-gray-200 rounded-lg shadow-lg py-1">
                <button
                  onClick={() => {
                    // TODO: Implement rename
                    setShowMenu(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                >
                  ✏️ Rename
                </button>
                <button
                  onClick={() => {
                    // TODO: Implement download
                    window.open(audio.url, '_blank');
                    setShowMenu(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                >
                  ⬇️ Download
                </button>
                <button
                  onClick={() => {
                    if (confirm('Delete this audio file?')) {
                      onDelete();
                    }
                    setShowMenu(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                >
                  🗑️ Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AudioCard;
```

---

### 11. useAudioGeneration Hook

**File:** `frontend-server/src/hooks/useAudioGeneration.js`

```javascript
import { useState } from 'react';
import axios from 'axios';

export const useAudioGeneration = () => {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const generate = async ({ text, voice, settings }) => {
    setGenerating(true);
    setError(null);

    try {
      // Call your existing audio generation API
      const response = await axios.post('/api/audio/generate', {
        text,
        voice,
        speed: settings.speed,
        pitch: settings.pitch,
        stability: settings.stability,
        clarity: settings.clarity
      });

      setGenerating(false);

      if (response.data.success) {
        return {
          success: true,
          audioUrl: response.data.audio_url
        };
      } else {
        setError(response.data.error || 'Generation failed');
        return { success: false };
      }
    } catch (err) {
      setGenerating(false);
      setError(err.response?.data?.error || err.message || 'Generation failed');
      return { success: false };
    }
  };

  return { generate, generating, error };
};
```

---

### 12. useAudioLibrary Hook

**File:** `frontend-server/src/hooks/useAudioLibrary.js`

```javascript
import { useState } from 'react';
import axios from 'axios';

export const useAudioLibrary = () => {
  const [audioFiles, setAudioFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAudioLibrary = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get('/api/audio-studio/library');
      setAudioFiles(response.data.audio_files || []);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const saveAudio = async (audioData) => {
    try {
      const response = await axios.post('/api/audio-studio/library', audioData);
      if (response.data.success) {
        setAudioFiles([response.data.audio, ...audioFiles]);
        return { success: true };
      }
      return { success: false };
    } catch (err) {
      setError(err.message);
      return { success: false };
    }
  };

  const deleteAudio = async (audioId) => {
    try {
      const response = await axios.delete(`/api/audio-studio/library/${audioId}`);
      if (response.data.success) {
        setAudioFiles(audioFiles.filter(a => a.id !== audioId));
        return { success: true };
      }
      return { success: false };
    } catch (err) {
      setError(err.message);
      return { success: false };
    }
  };

  const updateAudio = async (audioId, updates) => {
    try {
      const response = await axios.put(`/api/audio-studio/library/${audioId}`, updates);
      if (response.data.success) {
        setAudioFiles(audioFiles.map(a =>
          a.id === audioId ? { ...a, ...updates } : a
        ));
        return { success: true };
      }
      return { success: false };
    } catch (err) {
      setError(err.message);
      return { success: false };
    }
  };

  return {
    audioFiles,
    loading,
    error,
    fetchAudioLibrary,
    saveAudio,
    deleteAudio,
    updateAudio
  };
};
```

---

### 13. Audio Models Constants

**File:** `frontend-server/src/constants/audioModels.js`

```javascript
export const KOKORO_VOICES = [
  {
    id: 'am_adam',
    name: 'Adam',
    gender: 'male',
    accent: 'American',
    description: 'Professional male voice',
    previewUrl: null // Will be generated on demand
  },
  {
    id: 'am_michael',
    name: 'Michael',
    gender: 'male',
    accent: 'American',
    description: 'Warm male voice',
    previewUrl: null
  },
  {
    id: 'bf_emma',
    name: 'Emma',
    gender: 'female',
    accent: 'British',
    description: 'Professional female voice',
    previewUrl: null
  },
  {
    id: 'bf_isabella',
    name: 'Isabella',
    gender: 'female',
    accent: 'British',
    description: 'Elegant female voice',
    previewUrl: null
  },
  {
    id: 'am_sarah',
    name: 'Sarah',
    gender: 'female',
    accent: 'American',
    description: 'Friendly female voice',
    previewUrl: null
  }
];

export const AUDIO_MODELS = {
  KOKORO: {
    id: 'kokoro-82m',
    name: 'Kokoro TTS',
    provider: 'local',
    voices: KOKORO_VOICES,
    features: ['multi-language', 'fast', 'free']
  },
  ELEVENLABS: {
    id: 'elevenlabs',
    name: 'ElevenLabs',
    provider: 'api',
    voices: [], // Will be fetched from API
    features: ['premium', 'emotion-control', 'high-quality']
  }
};

export const getAvailableVoices = (modelId = 'kokoro-82m') => {
  if (modelId === 'kokoro-82m') {
    return KOKORO_VOICES;
  }
  return [];
};
```

---

## 🔧 Backend API Endpoints (Phase 1)

### Audio Library API

**File:** `backend/routes/audio_studio.py` (or add to existing routes)

```python
from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid

audio_studio_bp = Blueprint('audio_studio', __name__)

# MongoDB collection
# audio_library = db['audio_library']

@audio_studio_bp.route('/api/audio-studio/library', methods=['GET'])
def get_audio_library():
    """Get all audio files for the current user"""
    try:
        customer_id = request.args.get('customer_id')
        user_id = request.args.get('user_id')

        # Query MongoDB
        audio_files = list(audio_library.find({
            'customer_id': customer_id,
            'user_id': user_id
        }).sort('created_at', -1))

        # Convert ObjectId to string
        for audio in audio_files:
            audio['_id'] = str(audio['_id'])

        return jsonify({
            'success': True,
            'audio_files': audio_files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@audio_studio_bp.route('/api/audio-studio/library', methods=['POST'])
def save_audio():
    """Save audio to library"""
    try:
        data = request.json

        audio_doc = {
            'audio_id': str(uuid.uuid4()),
            'customer_id': data['customer_id'],
            'user_id': data['user_id'],
            'name': data.get('name', 'Untitled'),
            'type': data.get('type', 'voiceover'),
            'source': data.get('source', 'tts'),
            'url': data['url'],
            'duration': data.get('duration', 0),
            'format': data.get('format', 'wav'),
            'size': data.get('size', 0),
            'generation_config': data.get('generation_config', {}),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'tags': data.get('tags', []),
            'folder': data.get('folder', '')
        }

        result = audio_library.insert_one(audio_doc)
        audio_doc['_id'] = str(result.inserted_id)

        return jsonify({
            'success': True,
            'audio': audio_doc
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@audio_studio_bp.route('/api/audio-studio/library/<audio_id>', methods=['DELETE'])
def delete_audio(audio_id):
    """Delete audio from library"""
    try:
        result = audio_library.delete_one({'audio_id': audio_id})

        if result.deleted_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({
                'success': False,
                'error': 'Audio not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@audio_studio_bp.route('/api/audio-studio/library/<audio_id>', methods=['PUT'])
def update_audio(audio_id):
    """Update audio metadata"""
    try:
        data = request.json

        update_fields = {}
        if 'name' in data:
            update_fields['name'] = data['name']
        if 'tags' in data:
            update_fields['tags'] = data['tags']
        if 'folder' in data:
            update_fields['folder'] = data['folder']

        update_fields['updated_at'] = datetime.utcnow()

        result = audio_library.update_one(
            {'audio_id': audio_id},
            {'$set': update_fields}
        )

        if result.modified_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({
                'success': False,
                'error': 'Audio not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## 🗄️ MongoDB Schema

### Create Audio Library Collection

```javascript
// MongoDB shell or Compass

db.createCollection("audio_library");

// Create indexes
db.audio_library.createIndex({ "customer_id": 1, "user_id": 1 });
db.audio_library.createIndex({ "created_at": -1 });
db.audio_library.createIndex({ "audio_id": 1 }, { unique: true });

// Sample document
db.audio_library.insertOne({
  audio_id: "audio_abc123",
  customer_id: "customer_xyz",
  user_id: "user_123",
  name: "Product Voiceover 1",
  type: "voiceover",
  source: "tts",
  url: "https://s3.amazonaws.com/bucket/audio/voiceover_1.wav",
  duration: 45.5,
  format: "wav",
  size: 1024000,
  generation_config: {
    provider: "kokoro",
    model: "kokoro-82m",
    voice: "am_adam",
    text: "Welcome to our product demo",
    settings: {
      speed: 1.0,
      pitch: 0,
      stability: 0.5,
      clarity: 0.75
    }
  },
  created_at: new Date(),
  updated_at: new Date(),
  tags: ["product", "demo"],
  folder: "Product Videos"
});
```

---

## 🚀 Next Steps

### 1. Create Frontend Components
```bash
cd frontend-server/src

# Create directories
mkdir -p components/AudioStudio/TextToSpeech
mkdir -p components/AudioStudio/AudioLibrary
mkdir -p hooks
mkdir -p constants

# Create files (copy code from above)
# ... create all the component files
```

### 2. Add Route
```jsx
// In your App.jsx or routes file
import AudioStudioPage from './pages/AudioStudioPage';

// Add route
<Route path="/audio-studio" element={<AudioStudioPage />} />
```

### 3. Create Backend API
```bash
# Add audio_studio.py to your backend routes
# Register the blueprint in your main app
```

### 4. Test
```bash
# Start frontend
cd frontend-server
npm start

# Navigate to http://localhost:3000/audio-studio
```

---

## ✅ Phase 1 Checklist

- [ ] Create all frontend components
- [ ] Create hooks (useAudioGeneration, useAudioLibrary)
- [ ] Create constants (audioModels.js)
- [ ] Add route to Audio Studio page
- [ ] Create backend API endpoints
- [ ] Create MongoDB collection
- [ ] Test voice generation
- [ ] Test audio library save/delete
- [ ] Test audio playback

---

**Ready to start building! 🎙️**

Once Phase 1 is complete, you'll have:
- ✅ Beautiful Audio Studio UI
- ✅ Enhanced TTS with voice gallery
- ✅ Audio library with save/delete
- ✅ Voice settings (speed, pitch, stability, clarity)
- ✅ Audio preview with waveform

Then you can move to Phase 2 (AI Voice Generation) and beyond! 🚀

