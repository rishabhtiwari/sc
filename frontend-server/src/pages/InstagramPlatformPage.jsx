import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { InstagramCredentialsManager } from '../components/InstagramUploader';
import { Card } from '../components/common';
import { listMasterApps } from '../services/socialMediaService';
import { getCurrentUser } from '../services/authService';

/**
 * Instagram Platform Management Page
 * Dedicated page for managing Instagram Business accounts and credentials
 */
const InstagramPlatformPage = () => {
  const navigate = useNavigate();
  const [hasMasterApp, setHasMasterApp] = useState(true);
  const [loading, setLoading] = useState(true);
  const currentUser = getCurrentUser();
  const isAdmin = currentUser?.role === 'admin' || currentUser?.permissions?.includes('admin');

  useEffect(() => {
    checkMasterApp();
  }, []);

  const checkMasterApp = async () => {
    try {
      setLoading(true);
      const response = await listMasterApps({ platform: 'instagram', active_only: true });
      setHasMasterApp(response.master_apps && response.master_apps.length > 0);
    } catch (error) {
      console.error('Error checking master app:', error);
      setHasMasterApp(false);
    } finally {
      setLoading(false);
    }
  };

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
            <div className="text-5xl">📸</div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Instagram Platform</h1>
              <p className="text-gray-600 mt-1">
                Manage your Instagram Business account credentials and authentication
              </p>
            </div>
          </div>
        </div>

        {/* Platform Info Banner */}
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-l-4 border-pink-500 p-6 rounded-lg mb-6">
          <div className="flex items-start gap-4">
            <div className="text-3xl">🔑</div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Instagram Account Management</h3>
              <p className="text-sm text-gray-700 mb-3">
                Connect your Instagram Business or Creator accounts via Facebook OAuth. Each account allows you to post content to Instagram.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div className="bg-white/50 rounded-lg p-3">
                  <div className="text-2xl mb-1">🔗</div>
                  <div className="font-semibold text-gray-900 text-sm">Connect Account</div>
                  <div className="text-xs text-gray-600 mt-1">Link your Instagram Business account via Facebook</div>
                </div>
                <div className="bg-white/50 rounded-lg p-3">
                  <div className="text-2xl mb-1">🔐</div>
                  <div className="font-semibold text-gray-900 text-sm">OAuth Authentication</div>
                  <div className="text-xs text-gray-600 mt-1">Secure authentication through Facebook Graph API</div>
                </div>
                <div className="bg-white/50 rounded-lg p-3">
                  <div className="text-2xl mb-1">📤</div>
                  <div className="font-semibold text-gray-900 text-sm">Post Content</div>
                  <div className="text-xs text-gray-600 mt-1">Share photos, videos, and reels to Instagram</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Master App Warning Banner */}
        {!loading && !hasMasterApp && (
          <Card className="bg-yellow-50 border-yellow-200 mb-6">
            <div className="flex items-start gap-4 p-6">
              <div className="text-3xl">⚠️</div>
              <div className="flex-1">
                <h3 className="font-semibold text-yellow-900 mb-2">Instagram App Not Configured</h3>
                <p className="text-sm text-yellow-800 mb-3">
                  Your administrator needs to configure an Instagram master app before you can connect accounts.
                  The master app stores the OAuth credentials required for Instagram authentication.
                </p>
                {isAdmin && (
                  <Link
                    to="/settings?tab=social-apps"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors text-sm font-medium"
                  >
                    <span>⚙️</span>
                    Configure Instagram App Now
                  </Link>
                )}
                {!isAdmin && (
                  <p className="text-xs text-yellow-700 mt-2">
                    Please contact your administrator to set up the Instagram integration.
                  </p>
                )}
              </div>
            </div>
          </Card>
        )}

        {/* Setup Instructions */}
        {!loading && hasMasterApp && (
          <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded-lg mb-6">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span>📋</span>
              Before You Connect
            </h3>
            <div className="text-sm text-gray-700 space-y-2">
              <p className="font-medium">Make sure you have:</p>
              <ul className="ml-6 space-y-1">
                <li className="list-disc">An Instagram Business or Creator account</li>
                <li className="list-disc">A Facebook Page connected to your Instagram account</li>
                <li className="list-disc">Admin access to the Facebook Page</li>
              </ul>
              <p className="mt-3 text-xs text-gray-600">
                💡 <strong>Tip:</strong> To convert your Instagram account to Business, go to Instagram Settings → Account → Switch to Professional Account
              </p>
            </div>
          </div>
        )}

        {/* Credentials Manager */}
        <InstagramCredentialsManager />
      </div>
    </div>
  );
};

export default InstagramPlatformPage;

