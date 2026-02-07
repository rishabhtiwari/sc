import React, { useState, useEffect } from 'react';
import { Card, Button } from '../common';
import { useToast } from '../../hooks/useToast';
import api from '../../services/api';

/**
 * Instagram Credentials Manager Component
 * Manage Instagram OAuth credentials via Facebook Graph API
 */
const InstagramCredentialsManager = () => {
  const [credentials, setCredentials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    try {
      setLoading(true);
      const response = await api.get('/social-media/instagram/credentials');
      const data = response.data;

      if (data.status === 'success') {
        setCredentials(data.credentials || []);
      } else {
        showToast('Failed to load Instagram credentials', 'error');
      }
    } catch (error) {
      console.error('Error loading Instagram credentials:', error);
      showToast('Error loading Instagram credentials', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectInstagram = async () => {
    try {
      setConnecting(true);

      // Initiate Instagram OAuth flow
      const response = await api.get('/social-media/instagram/oauth/initiate');

      if (response.data && response.data.auth_url) {
        // Open OAuth URL in popup window
        const width = 600;
        const height = 700;
        const left = window.screen.width / 2 - width / 2;
        const top = window.screen.height / 2 - height / 2;

        const authWindow = window.open(
          response.data.auth_url,
          'Instagram OAuth',
          `width=${width},height=${height},left=${left},top=${top}`
        );

        // Listen for OAuth callback
        const checkWindow = setInterval(() => {
          if (authWindow.closed) {
            clearInterval(checkWindow);
            setConnecting(false);
            // Reload credentials after OAuth
            loadCredentials();
          }
        }, 1000);
      } else {
        showToast('Failed to initiate Instagram OAuth', 'error');
        setConnecting(false);
      }
    } catch (error) {
      console.error('Error connecting Instagram:', error);
      showToast(error.response?.data?.error || 'Failed to connect Instagram account', 'error');
      setConnecting(false);
    }
  };

  const handleDelete = async (credentialId) => {
    if (!window.confirm('Are you sure you want to disconnect this Instagram account?')) {
      return;
    }

    try {
      const response = await api.delete(`/social-media/instagram/credentials/${credentialId}`);
      const data = response.data;

      if (data.status === 'success') {
        showToast('Instagram account disconnected successfully', 'success');
        loadCredentials();
      } else {
        showToast(data.error || 'Failed to disconnect account', 'error');
      }
    } catch (error) {
      console.error('Error deleting Instagram credential:', error);
      showToast('Error disconnecting Instagram account', 'error');
    }
  };

  if (loading) {
    return (
      <Card>
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Instagram accounts...</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Add Button */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Instagram Accounts</h2>
          <p className="text-gray-600 mt-1">Manage your connected Instagram Business accounts</p>
        </div>
        <Button
          onClick={handleConnectInstagram}
          disabled={connecting}
          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
        >
          {connecting ? (
            <>
              <span className="animate-spin mr-2">⏳</span>
              Connecting...
            </>
          ) : (
            <>
              <span className="mr-2">➕</span>
              Connect Instagram Account
            </>
          )}
        </Button>
      </div>

      {/* Requirements Info */}
      <Card>
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 border-l-4 border-pink-500 p-4">
          <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
            <span>ℹ️</span>
            Requirements for Instagram Integration
          </h3>
          <ul className="space-y-1 text-sm text-gray-700 ml-6">
            <li className="list-disc">Instagram Business or Creator account</li>
            <li className="list-disc">Facebook Page connected to your Instagram account</li>
            <li className="list-disc">Admin access to the Facebook Page</li>
          </ul>
        </div>
      </Card>

      {/* Credentials List */}
      {credentials.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📸</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Instagram Accounts Connected</h3>
            <p className="text-gray-600 mb-6">
              Connect your Instagram Business account to start posting content
            </p>
            <Button
              onClick={handleConnectInstagram}
              disabled={connecting}
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
            >
              {connecting ? 'Connecting...' : 'Connect Your First Account'}
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {credentials.map((credential) => (
            <Card key={credential._id}>
              <div className="p-6">
                {/* Account Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white text-xl font-bold">
                      {credential.instagram_username?.charAt(0).toUpperCase() || 'I'}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        @{credential.instagram_username || 'Unknown'}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        {credential.is_authenticated ? (
                          <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full flex items-center gap-1">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                            Connected
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full flex items-center gap-1">
                            <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                            Disconnected
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Account Details */}
                <div className="space-y-2 mb-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Instagram ID:</span>
                    <span className="text-gray-900 font-mono text-xs">
                      {credential.instagram_user_id?.substring(0, 12)}...
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Connected:</span>
                    <span className="text-gray-900">
                      {new Date(credential.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleDelete(credential._id)}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white text-sm"
                  >
                    Disconnect
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default InstagramCredentialsManager;
