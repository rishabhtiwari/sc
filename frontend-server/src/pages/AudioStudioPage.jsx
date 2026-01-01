import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/common';
import AudioStudioTabs from '../components/AudioStudio/AudioStudioTabs';
import TextToSpeechPanel from '../components/AudioStudio/TextToSpeech/TextToSpeechPanel';
import AudioLibraryPanel from '../components/AudioStudio/AudioLibrary/AudioLibraryPanel';

/**
 * Audio Studio Page - Canva-like audio generation interface
 * Features:
 * 1. Text-to-Speech (Enhanced with Kokoro-82m)
 * 2. AI Voice Generation (Future - ElevenLabs)
 * 3. AI Music Generator (Future - MusicGen)
 * 4. Voice Cloning (Future - XTTS)
 */
const AudioStudioPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('tts');
  const [refreshLibrary, setRefreshLibrary] = useState(0);

  // Trigger library refresh when new audio is generated
  const handleAudioGenerated = () => {
    setRefreshLibrary(prev => prev + 1);
  };

  return (
    <div className="-m-6 flex flex-col" style={{ height: 'calc(100vh - 80px)' }}>
      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 flex-shrink-0">
        <AudioStudioTabs activeTab={activeTab} onTabChange={setActiveTab} />
      </div>

      {/* Main Content */}
      <div className="flex flex-1 min-h-0 bg-gray-50">
        {/* Left Panel - Main Content (2/3 width) */}
        <div className={`flex-1 ${activeTab === 'tts' ? '' : 'overflow-y-auto p-6'}`}>
          {activeTab === 'tts' && (
            <TextToSpeechPanel onAudioGenerated={handleAudioGenerated} />
          )}

          {activeTab === 'ai-voice' && (
            <Card title=""  className="p-6">
              <div className="text-center py-16">
                <div className="text-6xl mb-4">🎤</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  AI Voice Generation
                </h3>
                <p className="text-gray-600 mb-4">
                  Premium AI voices with emotion control
                </p>
                <div className="inline-block bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2">
                  <p className="text-sm text-yellow-800">
                    🚧 Coming Soon - ElevenLabs Integration
                  </p>
                </div>
              </div>
            </Card>
          )}

          {activeTab === 'ai-music' && (
            <Card title="">
              <div className="text-center py-16">
                <div className="text-6xl mb-4">🎵</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  AI Music Generator
                </h3>
                <p className="text-gray-600 mb-4">
                  Generate royalty-free background music
                </p>
                <div className="inline-block bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2">
                  <p className="text-sm text-yellow-800">
                    🚧 Coming Soon - MusicGen Integration
                  </p>
                </div>
              </div>
            </Card>
          )}

          {activeTab === 'voice-clone' && (
            <Card title="">
              <div className="text-center py-16">
                <div className="text-6xl mb-4">🔊</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Voice Cloning
                </h3>
                <p className="text-gray-600 mb-4">
                  Clone any voice with just 10 seconds of audio
                </p>
                <div className="inline-block bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2">
                  <p className="text-sm text-yellow-800">
                    🚧 Coming Soon - Enhanced XTTS UI
                  </p>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Right Panel - Audio Library (1/3 width) */}
        <div className="w-96 border-l border-gray-200 bg-white overflow-y-auto">
          <AudioLibraryPanel refreshTrigger={refreshLibrary} />
        </div>
      </div>
    </div>
  );
};

export default AudioStudioPage;

