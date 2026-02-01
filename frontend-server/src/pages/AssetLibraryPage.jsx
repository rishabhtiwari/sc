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
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'from-blue-50 to-cyan-50',
      route: '/text-studio',
      stats: { total: 0, recent: 0 }
    },
    {
      id: 'image',
      name: 'Image Library',
      icon: '🖼️',
      description: 'Browse and manage your image assets',
      color: 'from-purple-500 to-pink-500',
      bgColor: 'from-purple-50 to-pink-50',
      route: '/asset-library/images',
      stats: { total: 0, recent: 0 }
    },
    {
      id: 'audio',
      name: 'Audio Library',
      icon: '🎵',
      description: 'Access your audio files and voiceovers',
      color: 'from-green-500 to-teal-500',
      bgColor: 'from-green-50 to-teal-50',
      route: '/audio-studio/library',
      stats: { total: 0, recent: 0 }
    },
    {
      id: 'video',
      name: 'Video Library',
      icon: '🎬',
      description: 'Manage your video content',
      color: 'from-orange-500 to-red-500',
      bgColor: 'from-orange-50 to-red-50',
      route: '/asset-library/videos',
      stats: { total: 0, recent: 0 }
    }
  ];

  const handleNavigate = (route) => {
    navigate(route);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-lg border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform">
                <span className="text-4xl">📚</span>
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Asset Library
                </h1>
                <p className="text-gray-600 mt-1 font-medium">
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
              className="group bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/50 p-8 hover:shadow-2xl transition-all duration-300 transform hover:scale-105 cursor-pointer"
              onClick={() => handleNavigate(library.route)}
              style={{
                animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both`
              }}
            >
              {/* Icon and Title */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center space-x-4">
                  <div className={`w-16 h-16 bg-gradient-to-br ${library.color} rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                    <span className="text-4xl">{library.icon}</span>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:bg-clip-text group-hover:from-blue-600 group-hover:to-purple-600 transition-all">
                      {library.name}
                    </h2>
                    <p className="text-gray-600 mt-1">
                      {library.description}
                    </p>
                  </div>
                </div>
                <div className="text-gray-400 group-hover:text-blue-600 transition-colors">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>

              {/* Stats */}
              <div className={`bg-gradient-to-r ${library.bgColor} rounded-xl p-4 border border-gray-200`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 font-medium">Total Assets</p>
                    <p className="text-3xl font-bold text-gray-900">{library.stats.total}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600 font-medium">Recent</p>
                    <p className="text-3xl font-bold text-gray-900">{library.stats.recent}</p>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="mt-6">
                <button className={`w-full px-6 py-3 bg-gradient-to-r ${library.color} text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all transform group-hover:scale-105`}>
                  Browse {library.name}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Animations */}
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default AssetLibraryPage;

