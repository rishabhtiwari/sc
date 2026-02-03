import React from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Asset Management Page - Central hub for all assets and projects
 * Provides navigation to Projects, Text, Image, Audio, and Video libraries
 */
const AssetLibraryPage = () => {
  const navigate = useNavigate();

  const assetTypes = [
    {
      id: 'projects',
      name: 'Projects',
      icon: '📁',
      description: 'Manage your design projects',
      route: '/asset-management/projects',
      stats: { total: 0, recent: 0 }
    },
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
      route: '/asset-management/images',
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
      route: '/asset-management/videos',
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
                  Asset Management
                </h1>
                <p className="text-gray-600 mt-1">
                  Manage your projects and assets
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Asset Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {assetTypes.map((asset) => (
            <div
              key={asset.id}
              className="group bg-white rounded-lg shadow hover:shadow-lg transition-all duration-200 border border-gray-200 p-6 cursor-pointer"
              onClick={() => handleNavigate(asset.route)}
            >
              {/* Icon and Title */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
                    <span className="text-2xl">{asset.icon}</span>
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">
                      {asset.name}
                    </h2>
                    <p className="text-gray-600 text-sm mt-1">
                      {asset.description}
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
                    <p className="text-xs text-gray-600 font-medium">Total Items</p>
                    <p className="text-2xl font-bold text-gray-900">{asset.stats.total}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-600 font-medium">Recent</p>
                    <p className="text-2xl font-bold text-gray-900">{asset.stats.recent}</p>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="mt-4">
                <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">
                  Browse {asset.name}
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

