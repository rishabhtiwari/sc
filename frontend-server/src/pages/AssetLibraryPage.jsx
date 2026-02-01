import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Asset Library Page - Central hub for all asset types
 * Provides tabs to navigate to Text, Image, Audio, and Video libraries
 */
const AssetLibraryPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  const libraryTypes = [
    {
      id: 'text',
      name: 'Text Library',
      icon: '📝',
      description: 'Manage your text content and scripts',
      route: '/text-studio',
      stats: { total: 0, recent: 0 }
    },
    {
      id: 'image',
      name: 'Image Library',
      icon: '🖼️',
      description: 'Browse and manage your image assets',
      route: '/asset-library/images',
      stats: { total: 0, recent: 0 }
    },
    {
      id: 'audio',
      name: 'Audio Library',
      icon: '🎵',
      description: 'Access your audio files and voiceovers',
      route: '/audio-studio/library',
      stats: { total: 0, recent: 0 }
    },
    {
      id: 'video',
      name: 'Video Library',
      icon: '🎬',
      description: 'Manage your video content',
      route: '/asset-library/videos',
      stats: { total: 0, recent: 0 }
    }
  ];

  const handleNavigate = (route) => {
    navigate(route);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 bg-blue-600 rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-3xl">📚</span>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Asset Library
                </h1>
                <p className="text-gray-600 mt-1">
                  Manage your news automation workflow
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Library Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {libraryTypes.map((library, index) => (
            <div
              key={library.id}
              className="group bg-white rounded-lg shadow hover:shadow-lg transition-all duration-200 border border-gray-200 p-6 cursor-pointer"
              onClick={() => handleNavigate(library.route)}
            >
              {/* Icon and Title */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">{library.icon}</span>
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">
                      {library.name}
                    </h2>
                    <p className="text-gray-600 text-sm mt-1">
                      {library.description}
                    </p>
                  </div>
                </div>
                <div className="text-gray-400 group-hover:text-blue-600 transition-colors">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>

              {/* Stats */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-600 font-medium">Total Assets</p>
                    <p className="text-2xl font-bold text-gray-900">{library.stats.total}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-600 font-medium">Recent</p>
                    <p className="text-2xl font-bold text-gray-900">{library.stats.recent}</p>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="mt-4">
                <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">
                  Browse {library.name}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};

export default AssetLibraryPage;

