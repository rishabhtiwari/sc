import React, { useState, useEffect } from 'react';
import { Card } from '../common';
import { useToast } from '../../hooks/useToast';
import MasterAppCard from './MasterAppCard';
import MasterAppForm from './MasterAppForm';
import { 
  listMasterApps, 
  createMasterApp, 
  updateMasterApp, 
  deleteMasterApp,
  activateMasterApp,
  SOCIAL_PLATFORMS 
} from '../../services/socialMediaService';

/**
 * Master App Manager Component
 * Manage social media master apps (admin only)
 */
const MasterAppManager = () => {
  const [masterApps, setMasterApps] = useState({});
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedApp, setSelectedApp] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const { showToast } = useToast();

  useEffect(() => {
    loadMasterApps();
  }, []);

  const loadMasterApps = async () => {
    try {
      setLoading(true);
      const response = await listMasterApps();
      
      if (response.status === 'success') {
        // Group apps by platform
        const appsByPlatform = {};
        response.master_apps.forEach(app => {
          appsByPlatform[app.platform] = app;
        });
        setMasterApps(appsByPlatform);
      } else {
        showToast('Failed to load master apps', 'error');
      }
    } catch (error) {
      console.error('Error loading master apps:', error);
      
      // Handle "no master app" error gracefully
      if (error.response?.data?.code === 'NO_MASTER_APP') {
        setMasterApps({});
      } else {
        showToast('Error loading master apps', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = (platformId) => {
    setSelectedApp(null);
    setSelectedPlatform(platformId);
    setShowForm(true);
  };

  const handleEdit = (app, platformId = null) => {
    setSelectedApp(app);
    setSelectedPlatform(platformId || app?.platform);
    setShowForm(true);
  };

  const handleSave = async (appData) => {
    try {
      if (selectedApp) {
        // Update existing app
        const response = await updateMasterApp(selectedApp._id, appData);
        if (response.status === 'success') {
          showToast('Master app updated successfully', 'success');
          loadMasterApps();
        }
      } else {
        // Create new app
        const response = await createMasterApp(appData);
        if (response.status === 'success') {
          showToast('Master app created successfully', 'success');
          loadMasterApps();
        }
      }
    } catch (error) {
      console.error('Error saving master app:', error);
      throw error; // Re-throw to let form handle it
    }
  };

  const handleDelete = async (app) => {
    if (!window.confirm(`Are you sure you want to delete "${app.app_name}"?\n\nThis will affect all users using this app.`)) {
      return;
    }

    try {
      const response = await deleteMasterApp(app._id);
      if (response.status === 'success') {
        showToast('Master app deleted successfully', 'success');
        loadMasterApps();
      }
    } catch (error) {
      console.error('Error deleting master app:', error);
      showToast(error.response?.data?.error || 'Failed to delete master app', 'error');
    }
  };

  const handleActivate = async (appId) => {
    try {
      const response = await activateMasterApp(appId);
      if (response.status === 'success') {
        showToast('Master app activated successfully', 'success');
        loadMasterApps();
      }
    } catch (error) {
      console.error('Error activating master app:', error);
      showToast(error.response?.data?.error || 'Failed to activate master app', 'error');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-600">Loading master apps...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Social Media Master Apps</h2>
        <p className="text-gray-600 mt-1">
          Configure OAuth apps for social media platforms. Users will connect their accounts using these apps.
        </p>
      </div>

      {/* Info Banner */}
      <Card className="bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3 p-4">
          <span className="text-2xl">ℹ️</span>
          <div className="flex-1">
            <h3 className="font-semibold text-blue-900 mb-2">About Master Apps</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Master apps store OAuth credentials (App ID & Secret) for each platform</li>
              <li>• All users in your organization share the same master app per platform</li>
              <li>• Only one app can be active per platform at a time</li>
              <li>• App secrets are encrypted automatically with your customer-specific encryption key</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Platform Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.values(SOCIAL_PLATFORMS).map((platform) => (
          <MasterAppCard
            key={platform.id}
            masterApp={masterApps[platform.id]}
            platform={platform}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onActivate={handleActivate}
          />
        ))}
      </div>

      {/* Master App Form Modal */}
      {showForm && (
        <MasterAppForm
          isOpen={showForm}
          onClose={() => {
            setShowForm(false);
            setSelectedApp(null);
            setSelectedPlatform(null);
          }}
          onSave={handleSave}
          masterApp={selectedApp}
          platformId={selectedPlatform}
        />
      )}
    </div>
  );
};

export default MasterAppManager;

