import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { InstagramCredentialsManager } from '../components/InstagramUploader';
import { Card, Button } from '../components/common';
import { MasterAppCard, MasterAppForm } from '../components/SocialMedia';
import { useToast } from '../hooks/useToast';
import {
  listMasterApps,
  createMasterApp,
  updateMasterApp,
  deleteMasterApp,
  activateMasterApp,
  SOCIAL_PLATFORMS
} from '../services/socialMediaService';
import { getCurrentUser } from '../services/authService';

/**
 * Instagram Platform Management Page
 * Dedicated page for managing Instagram Business accounts and credentials
 */
const InstagramPlatformPage = () => {
  const navigate = useNavigate();
  const [masterApp, setMasterApp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showMasterAppForm, setShowMasterAppForm] = useState(false);
  const currentUser = getCurrentUser();

  // Check if user is admin - check role_name or role_id or permissions
  const isAdmin = currentUser?.role_name?.toLowerCase().includes('admin') ||
                  currentUser?.role_id?.toLowerCase().includes('admin') ||
                  currentUser?.permissions?.includes('admin') ||
                  currentUser?.permissions?.includes('master_app.manage');

  const { showToast } = useToast();
  const instagramPlatform = SOCIAL_PLATFORMS.instagram;

  console.log('Current User:', currentUser);
  console.log('Is Admin:', isAdmin);

  useEffect(() => {
    loadMasterApp();
  }, []);

  const loadMasterApp = async () => {
    try {
      setLoading(true);
      const response = await listMasterApps({ platform: 'instagram', active_only: true });
      if (response.master_apps && response.master_apps.length > 0) {
        setMasterApp(response.master_apps[0]);
      } else {
        setMasterApp(null);
      }
    } catch (error) {
      console.error('Error loading master app:', error);
      setMasterApp(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveMasterApp = async (appData) => {
    try {
      if (masterApp) {
        // Update existing app
        const response = await updateMasterApp(masterApp._id, appData);
        if (response.status === 'success') {
          showToast('Instagram app updated successfully', 'success');
          loadMasterApp();
        }
      } else {
        // Create new app
        const response = await createMasterApp(appData);
        if (response.status === 'success') {
          showToast('Instagram app created successfully', 'success');
          loadMasterApp();
        }
      }
    } catch (error) {
      console.error('Error saving master app:', error);
      throw error; // Re-throw to let form handle it
    }
  };

  const handleDeleteMasterApp = async (app) => {
    if (!window.confirm(`Are you sure you want to delete "${app.app_name}"?\n\nThis will prevent users from connecting new Instagram accounts.`)) {
      return;
    }

    try {
      const response = await deleteMasterApp(app._id);
      if (response.status === 'success') {
        showToast('Instagram app deleted successfully', 'success');
        loadMasterApp();
      }
    } catch (error) {
      console.error('Error deleting master app:', error);
      showToast(error.response?.data?.error || 'Failed to delete Instagram app', 'error');
    }
  };

  const handleActivateMasterApp = async (appId) => {
    try {
      const response = await activateMasterApp(appId);
      if (response.status === 'success') {
        showToast('Instagram app activated successfully', 'success');
        loadMasterApp();
      }
    } catch (error) {
      console.error('Error activating master app:', error);
      showToast(error.response?.data?.error || 'Failed to activate Instagram app', 'error');
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

        {/* Admin: Master App Configuration Section */}
        {isAdmin && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Instagram App Configuration</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Configure the Facebook App credentials for Instagram OAuth
                </p>
              </div>
              {!masterApp && (
                <Button
                  onClick={() => setShowMasterAppForm(true)}
                  variant="primary"
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                >
                  <span className="mr-2">➕</span>
                  Configure Instagram App
                </Button>
              )}
            </div>

            {loading ? (
              <Card>
                <div className="flex items-center justify-center py-8">
                  <div className="text-center">
                    <div className="animate-spin text-3xl mb-2">⏳</div>
                    <p className="text-gray-600 text-sm">Loading configuration...</p>
                  </div>
                </div>
              </Card>
            ) : masterApp ? (
              <div className="max-w-md">
                <MasterAppCard
                  masterApp={masterApp}
                  platform={instagramPlatform}
                  onEdit={() => setShowMasterAppForm(true)}
                  onDelete={handleDeleteMasterApp}
                  onActivate={handleActivateMasterApp}
                />
              </div>
            ) : (
              <Card className="bg-yellow-50 border-yellow-200">
                <div className="flex items-start gap-4 p-6">
                  <div className="text-3xl">⚠️</div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-yellow-900 mb-2">Instagram App Not Configured</h3>
                    <p className="text-sm text-yellow-800 mb-3">
                      Configure your Facebook App credentials to enable Instagram OAuth for all users.
                      This is required before users can connect their Instagram accounts.
                    </p>
                    <Button
                      onClick={() => setShowMasterAppForm(true)}
                      className="bg-yellow-600 hover:bg-yellow-700 text-white"
                    >
                      <span className="mr-2">⚙️</span>
                      Configure Now
                    </Button>
                  </div>
                </div>
              </Card>
            )}
          </div>
        )}

        {/* Non-Admin: Warning if no master app */}
        {!isAdmin && !loading && !masterApp && (
          <Card className="bg-yellow-50 border-yellow-200 mb-6">
            <div className="flex items-start gap-4 p-6">
              <div className="text-3xl">⚠️</div>
              <div className="flex-1">
                <h3 className="font-semibold text-yellow-900 mb-2">Instagram App Not Configured</h3>
                <p className="text-sm text-yellow-800">
                  Your administrator needs to configure an Instagram master app before you can connect accounts.
                  Please contact your administrator to set up the Instagram integration.
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Divider for Admin */}
        {isAdmin && masterApp && (
          <div className="border-t border-gray-200 my-8"></div>
        )}

        {/* User Accounts Section Header */}
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900">Your Instagram Accounts</h2>
          <p className="text-sm text-gray-600 mt-1">
            Connect and manage your Instagram Business accounts
          </p>
        </div>

        {/* Setup Instructions */}
        {!loading && masterApp && (
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

        {/* Master App Form Modal */}
        {showMasterAppForm && (
          <MasterAppForm
            isOpen={showMasterAppForm}
            onClose={() => setShowMasterAppForm(false)}
            onSave={handleSaveMasterApp}
            masterApp={masterApp}
            platformId="instagram"
          />
        )}
      </div>
    </div>
  );
};

export default InstagramPlatformPage;

