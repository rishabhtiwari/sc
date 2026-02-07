import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CredentialsManager } from '../components/YouTubeUploader';

/**
 * YouTube Platform Management Page
 * Dedicated page for managing YouTube accounts and credentials
 */
const YouTubePlatformPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header with Back Button */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/social-platform')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back to Social Platforms</span>
          </button>

          <div className="flex items-center gap-4 mb-4">
            <div className="text-5xl">📺</div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">YouTube Platform</h1>
              <p className="text-gray-600 mt-1">
                Manage your YouTube channel credentials and authentication
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => navigate('/youtube')}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Go to Video Processing
            </button>
          </div>
        </div>

        {/* Platform Info Banner */}
        <div className="bg-gradient-to-r from-red-50 to-yellow-50 border-l-4 border-red-500 p-6 rounded-lg mb-6">
          <div className="flex items-start gap-4">
            <div className="text-3xl">🔑</div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">YouTube Account Management</h3>
              <p className="text-sm text-gray-700 mb-3">
                Add and manage multiple YouTube channel credentials. Each credential allows you to upload videos to a specific YouTube channel.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div className="bg-white/50 rounded-lg p-3">
                  <div className="text-2xl mb-1">📝</div>
                  <div className="font-semibold text-gray-900 text-sm">Add Credentials</div>
                  <div className="text-xs text-gray-600 mt-1">Configure OAuth credentials from Google Cloud Console</div>
                </div>
                <div className="bg-white/50 rounded-lg p-3">
                  <div className="text-2xl mb-1">🔐</div>
                  <div className="font-semibold text-gray-900 text-sm">Authenticate</div>
                  <div className="text-xs text-gray-600 mt-1">Complete OAuth flow to authorize channel access</div>
                </div>
                <div className="bg-white/50 rounded-lg p-3">
                  <div className="text-2xl mb-1">🚀</div>
                  <div className="font-semibold text-gray-900 text-sm">Upload Videos</div>
                  <div className="text-xs text-gray-600 mt-1">Use authenticated channels in Video Processing</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Credentials Manager */}
        <CredentialsManager />
      </div>
    </div>
  );
};

export default YouTubePlatformPage;

