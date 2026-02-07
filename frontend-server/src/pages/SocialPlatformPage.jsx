import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CredentialsManager } from '../components/YouTubeUploader';

/**
 * YouTube Accounts Component - Shows all YouTube accounts
 */
const YouTubeAccounts = () => {
  return (
    <div className="space-y-6">
      {/* Platform Info */}
      <div className="bg-gradient-to-r from-red-50 to-yellow-50 border-l-4 border-red-500 p-4 rounded-lg">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📺</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">YouTube Accounts</h3>
            <p className="text-sm text-gray-600 mt-1">
              Manage your YouTube channel credentials and authentication
            </p>
          </div>
        </div>
      </div>

      {/* Credentials Manager */}
      <CredentialsManager />
    </div>
  );
};

/**
 * Social Platform Page
 * Manage credentials and upload content to multiple social media platforms
 */
const SocialPlatformPage = () => {
  const navigate = useNavigate();

  const platforms = [
    {
      id: 'youtube',
      name: 'YouTube',
      icon: '📺',
      color: 'red',
      description: 'Upload videos to YouTube',
      status: 'active',
      features: ['Video Upload', 'Shorts', 'Live Streaming']
    },
    {
      id: 'instagram',
      name: 'Instagram',
      icon: '📸',
      color: 'pink',
      description: 'Share photos and videos on Instagram',
      status: 'active',
      features: ['Posts', 'Stories', 'Reels']
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      icon: '🎵',
      color: 'black',
      description: 'Create and share short videos on TikTok',
      status: 'coming-soon',
      features: ['Short Videos', 'Duets', 'Stitches']
    },
    {
      id: 'twitter',
      name: 'Twitter / X',
      icon: '🐦',
      color: 'blue',
      description: 'Post tweets and media on Twitter/X',
      status: 'coming-soon',
      features: ['Tweets', 'Threads', 'Media']
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: '💼',
      color: 'blue',
      description: 'Share professional content on LinkedIn',
      status: 'coming-soon',
      features: ['Posts', 'Articles', 'Videos']
    },
    {
      id: 'facebook',
      name: 'Facebook',
      icon: '👥',
      color: 'blue',
      description: 'Post content to Facebook pages',
      status: 'coming-soon',
      features: ['Posts', 'Stories', 'Videos']
    },
    {
      id: 'reddit',
      name: 'Reddit',
      icon: '🤖',
      color: 'orange',
      description: 'Submit posts to Reddit communities',
      status: 'coming-soon',
      features: ['Text Posts', 'Link Posts', 'Media']
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <span>🌐</span>
            Social Media Platform
          </h1>
          <p className="text-gray-600">
            Connect your social media accounts and manage content across multiple platforms
          </p>
        </div>

        {/* Platform Selection Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {platforms.map((platform) => (
            <button
              key={platform.id}
              onClick={() => {
                if (platform.status === 'active') {
                  navigate(`/social-platform/${platform.id}`);
                }
              }}
              disabled={platform.status === 'coming-soon'}
              className={`relative p-6 rounded-xl border-2 transition-all text-left hover:shadow-lg ${
                platform.status === 'coming-soon'
                  ? 'opacity-50 cursor-not-allowed border-gray-200'
                  : 'cursor-pointer border-gray-300 hover:border-blue-500'
              }`}
            >
              {/* Coming Soon Badge */}
              {platform.status === 'coming-soon' && (
                <div className="absolute top-2 right-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full">
                  Coming Soon
                </div>
              )}

              {/* Platform Icon */}
              <div className="text-4xl mb-3">{platform.icon}</div>

              {/* Platform Name */}
              <h3 className="text-lg font-bold text-gray-900 mb-1">{platform.name}</h3>

              {/* Description */}
              <p className="text-sm text-gray-600 mb-3">{platform.description}</p>

              {/* Features */}
              <div className="flex flex-wrap gap-1">
                {platform.features.map((feature, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-white text-xs text-gray-700 rounded-full border border-gray-200"
                  >
                    {feature}
                  </span>
                ))}
              </div>

              {/* Arrow Icon for Active Platforms */}
              {platform.status === 'active' && (
                <div className="absolute bottom-4 right-4 text-gray-400">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SocialPlatformPage;

