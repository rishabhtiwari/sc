import React, { useState } from 'react';
import { Card } from '../../common';
import VoiceCard from './VoiceCard';

/**
 * Voice Gallery Component
 * Displays available voices in a grid layout with categories
 */
const VoiceGallery = ({ voices, selectedVoice, onVoiceSelect }) => {
  const [filter, setFilter] = useState('all'); // all, male, female

  // Group voices by category
  const maleVoices = voices.filter(v => v.category === 'male');
  const femaleVoices = voices.filter(v => v.category === 'female');

  // Filter voices based on selected filter
  const getFilteredVoices = () => {
    switch (filter) {
      case 'male':
        return maleVoices;
      case 'female':
        return femaleVoices;
      default:
        return voices;
    }
  };

  const filteredVoices = getFilteredVoices();

  return (
    <Card title="🎭 Select Voice">
      {/* Filter Buttons */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setFilter('all')}
          className={`
            px-4 py-2 rounded-lg font-medium transition-colors
            ${filter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }
          `}
        >
          All Voices ({voices.length})
        </button>
        <button
          onClick={() => setFilter('male')}
          className={`
            px-4 py-2 rounded-lg font-medium transition-colors
            ${filter === 'male'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }
          `}
        >
          👨 Male ({maleVoices.length})
        </button>
        <button
          onClick={() => setFilter('female')}
          className={`
            px-4 py-2 rounded-lg font-medium transition-colors
            ${filter === 'female'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }
          `}
        >
          👩 Female ({femaleVoices.length})
        </button>
      </div>

      {/* Voice Grid */}
      <div className="grid grid-cols-2 gap-4">
        {filteredVoices.map((voice) => (
          <VoiceCard
            key={voice.id}
            voice={voice}
            isSelected={selectedVoice === voice.id}
            onSelect={() => onVoiceSelect(voice.id)}
          />
        ))}
      </div>

      {/* Empty State */}
      {filteredVoices.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>No voices found for this filter</p>
        </div>
      )}
    </Card>
  );
};

export default VoiceGallery;

