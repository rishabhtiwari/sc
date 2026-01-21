import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AudioStudioTabs from '../../AudioStudio/AudioStudioTabs';
import TextToSpeechPanel from '../../AudioStudio/TextToSpeech/TextToSpeechPanel';
import AudioLibraryPanel from '../../AudioStudio/AudioLibrary/AudioLibraryPanel';
import { Card } from '../../common';

/**
 * Audio Studio Modal - Full-screen modal for AI audio generation
 * Reuses the existing Audio Studio components from AudioStudioPage
 * Similar to TextStudio but for audio content
 */
const AudioStudio = ({ isOpen, onClose, onAddToCanvas }) => {
  const [activeTab, setActiveTab] = useState('tts');
  const [refreshLibrary, setRefreshLibrary] = useState(0);

  // Trigger library refresh when new audio is generated
  const handleAudioGenerated = () => {
    setRefreshLibrary(prev => prev + 1);
  };

  // Handle adding audio to canvas
  const handleAddAudioToCanvas = (audioData) => {
    if (onAddToCanvas) {
      onAddToCanvas({
        type: 'audio',
        src: audioData.url || audioData.audio_url,
        title: audioData.title || 'Generated Audio',
        duration: audioData.duration || 0
      });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-2xl w-[95%] h-[95%] flex flex-col overflow-hidden">
        {/* Header - Similar to Text Studio */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🎙️</span>
              <h1 className="text-2xl font-bold text-gray-900">Audio Studio</h1>
            </div>
            <button
              onClick={onClose}
              className="text-gray-600 hover:text-gray-900 text-2xl font-bold transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white border-b border-gray-200 flex-shrink-0">
          <AudioStudioTabs activeTab={activeTab} onTabChange={setActiveTab} />
        </div>

        {/* Main Content */}
        <div className="flex flex-1 min-h-0 bg-gray-50">
          {/* Left Panel - Main Content (2/3 width) */}
          <div className={`flex-1 ${activeTab === 'tts' ? '' : 'overflow-y-auto p-6'}`}>
            {activeTab === 'tts' && (
              <TextToSpeechPanel 
                onAudioGenerated={handleAudioGenerated}
                onAddToCanvas={handleAddAudioToCanvas}
              />
            )}

            {activeTab === 'ai-voice' && (
              <Card title="">
                <div className="text-center py-16">
                  <div className="text-6xl mb-4">🎤</div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    AI Voice Generation
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Premium AI voices with emotions and accents
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
            <AudioLibraryPanel 
              refreshTrigger={refreshLibrary}
              onAddToCanvas={handleAddAudioToCanvas}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AudioStudio;

