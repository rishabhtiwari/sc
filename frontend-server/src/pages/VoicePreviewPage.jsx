import React, { useState } from 'react';
import { Card } from '../components/common';
import { AUDIO_MODELS, LANGUAGES } from '../constants/audioModels';
import VoicePreviewCard from '../components/AudioStudio/TextToSpeech/VoicePreviewCard';

/**
 * Voice Preview Page
 * Dedicated page for browsing and previewing all available voices
 */
const VoicePreviewPage = () => {
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [filter, setFilter] = useState('all'); // all, male, female

  // Get model for selected language
  const modelId = selectedLanguage === 'en' ? 'kokoro-82m' : 'mms-tts-hin';
  const modelData = AUDIO_MODELS[modelId];

  // Get all voices for the model
  const allVoices = Object.entries(modelData.voices).flatMap(([category, voices]) =>
    voices.map(v => ({ ...v, category }))
  );

  // Filter voices
  const getFilteredVoices = () => {
    switch (filter) {
      case 'male':
        return allVoices.filter(v => v.category === 'male');
      case 'female':
        return allVoices.filter(v => v.category === 'female');
      default:
        return allVoices;
    }
  };

  const filteredVoices = getFilteredVoices();
  const maleCount = allVoices.filter(v => v.category === 'male').length;
  const femaleCount = allVoices.filter(v => v.category === 'female').length;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">🎭 Voice Gallery</h1>
              <p className="text-gray-600 mt-2">
                Browse and preview all available voices for text-to-speech
              </p>
            </div>
            <button
              onClick={() => window.close()}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              ✕ Close
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            {/* Language Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Language:</label>
              <div className="flex gap-2">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.id}
                    onClick={() => {
                      setSelectedLanguage(lang.id);
                      setFilter('all');
                    }}
                    className={`
                      px-4 py-2 rounded-lg font-medium transition-colors text-sm
                      ${selectedLanguage === lang.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }
                    `}
                  >
                    {lang.flag} {lang.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Gender Filter */}
            <div className="flex items-center gap-2 ml-auto">
              <label className="text-sm font-medium text-gray-700">Filter:</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setFilter('all')}
                  className={`
                    px-4 py-2 rounded-lg font-medium transition-colors text-sm
                    ${filter === 'all'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                  `}
                >
                  All Voices ({allVoices.length})
                </button>
                <button
                  onClick={() => setFilter('male')}
                  className={`
                    px-4 py-2 rounded-lg font-medium transition-colors text-sm
                    ${filter === 'male'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                  `}
                >
                  👨 Male ({maleCount})
                </button>
                <button
                  onClick={() => setFilter('female')}
                  className={`
                    px-4 py-2 rounded-lg font-medium transition-colors text-sm
                    ${filter === 'female'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }
                  `}
                >
                  👩 Female ({femaleCount})
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Voice Grid */}
      <div className="px-6 py-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredVoices.map((voice) => (
              <VoicePreviewCard
                key={voice.id}
                voice={voice}
                modelId={modelId}
                language={selectedLanguage}
              />
            ))}
          </div>

          {/* Empty State */}
          {filteredVoices.length === 0 && (
            <div className="text-center py-16">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No voices found
              </h3>
              <p className="text-gray-600">
                Try selecting a different filter or language
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoicePreviewPage;

