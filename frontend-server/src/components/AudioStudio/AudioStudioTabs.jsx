import React from 'react';

/**
 * Audio Studio Tabs Component
 * Navigation tabs for different audio generation features
 */
const AudioStudioTabs = ({ activeTab, onTabChange }) => {
  const tabs = [
    {
      id: 'tts',
      label: 'Text-to-Speech',
      icon: '📝',
      description: 'Generate voiceovers from text',
      enabled: true
    },
    {
      id: 'ai-voice',
      label: 'AI Voice',
      icon: '🎤',
      description: 'Premium AI voices with emotions',
      enabled: false,
      badge: 'Soon'
    },
    {
      id: 'ai-music',
      label: 'AI Music',
      icon: '🎵',
      description: 'Generate background music',
      enabled: false,
      badge: 'Soon'
    },
    {
      id: 'voice-clone',
      label: 'Voice Cloning',
      icon: '🔊',
      description: 'Clone any voice',
      enabled: false,
      badge: 'Soon'
    }
  ];

  return (
    <div className="flex border-b border-gray-200">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => tab.enabled && onTabChange(tab.id)}
          disabled={!tab.enabled}
          className={`
            relative flex-1 px-6 py-4 text-left transition-all
            ${activeTab === tab.id
              ? 'bg-white border-b-2 border-blue-600'
              : 'bg-gray-50 hover:bg-gray-100'
            }
            ${!tab.enabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">{tab.icon}</span>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className={`
                  font-semibold
                  ${activeTab === tab.id ? 'text-blue-600' : 'text-gray-900'}
                `}>
                  {tab.label}
                </span>
                {tab.badge && (
                  <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                    {tab.badge}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-600 mt-0.5">
                {tab.description}
              </p>
            </div>
          </div>
          
          {/* Active indicator */}
          {activeTab === tab.id && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
          )}
        </button>
      ))}
    </div>
  );
};

export default AudioStudioTabs;

