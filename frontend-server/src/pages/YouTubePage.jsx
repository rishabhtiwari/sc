import React, { useState, useEffect } from 'react';
import { Card, Button } from '../components/common';
import { useToast } from '../hooks/useToast';
import { youtubeService, videoService, videoConfigService } from '../services';
import { StatsCards, UploadProgress, ShortsGrid, LongVideoConfig, ConfigCard, CredentialsManager } from '../components/YouTubeUploader';
import PlusCard from '../components/YouTubeUploader/PlusCard';

/**
 * YouTube Page - Upload news videos to YouTube
 */
const YouTubePage = () => {
  const [activeTab, setActiveTab] = useState('overview'); // overview, shorts, long, credentials
  const [stats, setStats] = useState({
    ready_to_upload: 0,
    already_uploaded: 0,
    total_videos: 0,
    shorts_ready_to_upload: 0,
    shorts_already_uploaded: 0,
    total_shorts: 0,
  });
  const [statsLoading, setStatsLoading] = useState(false);
  const [shorts, setShorts] = useState([]);
  const [shortsLoading, setShortsLoading] = useState(false);
  const [shortsPagination, setShortsPagination] = useState({
    page: 1,
    limit: 5,
    total: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false,
  });
  const [uploading, setUploading] = useState(false);
  const [merging, setMerging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadLogs, setUploadLogs] = useState([]);
  const [showProgress, setShowProgress] = useState(false);

  // Video configurations state
  const [videoConfigs, setVideoConfigs] = useState([]);
  const [configsLoading, setConfigsLoading] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);

  const { showToast } = useToast();

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'shorts', label: 'Shorts', icon: '📱' },
    { id: 'long', label: 'Long Videos', icon: '🎬' },
    { id: 'credentials', label: 'Credentials', icon: '🔑' },
  ];

  // Load statistics
  const loadStats = async () => {
    setStatsLoading(true);
    try {
      const response = await youtubeService.getStats();
      const data = response.data;
      setStats({
        ready_to_upload: data.ready_to_upload || 0,
        already_uploaded: data.already_uploaded || 0,
        total_videos: data.total_videos || 0,
        shorts_ready_to_upload: data.shorts_ready_to_upload || 0,
        shorts_already_uploaded: data.shorts_already_uploaded || 0,
        total_shorts: data.total_shorts || 0,
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
      showToast('Failed to load statistics', 'error');
    } finally {
      setStatsLoading(false);
    }
  };

  // Load pending shorts with pagination
  const loadPendingShorts = async (page = 1, limit = 5) => {
    setShortsLoading(true);
    try {
      const response = await youtubeService.getPendingShorts(page, limit);
      const data = response.data;

      if (data.status === 'success') {
        setShorts(data.shorts || []);
        setShortsPagination({
          page: data.page,
          limit: data.limit,
          total: data.total,
          total_pages: data.total_pages,
          has_next: data.has_next,
          has_prev: data.has_prev,
        });
      } else {
        setShorts([]);
      }
    } catch (error) {
      console.error('Failed to load pending shorts:', error);
      showToast('Failed to load pending shorts', 'error');
      setShorts([]);
    } finally {
      setShortsLoading(false);
    }
  };

  // Handle page change for shorts
  const handleShortsPageChange = (newPage) => {
    loadPendingShorts(newPage, shortsPagination.limit);
  };

  // Poll for config status updates using the merge-status endpoint
  const pollConfigStatus = async (configId, maxAttempts = 60, interval = 2000) => {
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await videoConfigService.getMergeStatus(configId);
        const statusData = response.data;

        if (statusData.status === 'completed' || statusData.status === 'failed') {
          // Status changed, reload all configs
          await loadVideoConfigs();
          setMerging(false);

          if (statusData.status === 'completed') {
            showToast('Video merge completed successfully!', 'success');
          } else {
            showToast(statusData.error || 'Video merge failed', 'error');
          }
          return true; // Stop polling
        }

        attempts++;
        if (attempts >= maxAttempts) {
          // Timeout - reload configs anyway
          await loadVideoConfigs();
          setMerging(false);
          showToast('Merge is taking longer than expected. Please check back later.', 'warning');
          return true; // Stop polling
        }

        // Continue polling
        setTimeout(poll, interval);
        return false;
      } catch (error) {
        console.error('Error polling config status:', error);
        attempts++;
        if (attempts >= maxAttempts) {
          await loadVideoConfigs();
          setMerging(false);
          return true;
        }
        setTimeout(poll, interval);
        return false;
      }
    };

    // Start polling
    poll();
  };

  // Merge videos with configuration
  const handleMergeVideos = async (config) => {
    setMerging(true);
    try {
      // First, create the configuration in database
      const createResponse = await videoConfigService.createConfig(config);
      const createData = createResponse.data;

      if (createData.status !== 'success') {
        showToast(createData.error || 'Failed to create configuration', 'error');
        setMerging(false);
        return { status: 'error' };
      }

      const configId = createData._id;
      showToast('Configuration created successfully', 'success');

      // Then trigger the merge for this configuration
      const mergeResponse = await videoConfigService.mergeConfig(configId);
      const mergeData = mergeResponse.data;

      if (mergeData.status === 'success' || mergeData.status === 'processing') {
        showToast(mergeData.message || 'Video merging started successfully', 'success');

        // Reload configurations to show the new one
        await loadVideoConfigs();

        // Start polling for status updates
        pollConfigStatus(configId);

        return {
          status: 'created',
          config_id: configId,
          video_count: mergeData.video_count,
          estimated_time: mergeData.estimated_time,
          preview_url: '/api/news/videos/latest-20-news.mp4',
          message: mergeData.message
        };
      } else {
        showToast(mergeData.error || 'Failed to merge videos', 'error');
        setMerging(false);
        return { status: 'error' };
      }
    } catch (error) {
      console.error('Merge error:', error);
      showToast(error.response?.data?.error || 'Failed to merge videos', 'error');
      setMerging(false);
      return { status: 'error' };
    }
  };

  // Upload long video with configuration
  const handleUploadLongVideo = async (configId) => {
    if (!window.confirm('Upload this video to YouTube?')) {
      return;
    }

    setUploading(true);
    setShowProgress(true);
    setUploadProgress(0);
    setUploadLogs([]);

    try {
      setUploadLogs(prev => [...prev, `📤 Uploading config video: ${configId}`]);

      // Call the config-specific upload endpoint
      const response = await fetch(`/api/youtube/upload-config/${configId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (data.status === 'success') {
        setUploadProgress(100);
        setUploadLogs(prev => [...prev, `✅ ${data.message}`]);
        setUploadLogs(prev => [...prev, `🔗 Video URL: ${data.video_url}`]);
        showToast('Video uploaded successfully to YouTube!', 'success');

        // Reload stats and configs (config is already updated by backend)
        await loadStats();
        await loadVideoConfigs();
      } else {
        setUploadLogs(prev => [...prev, `❌ ${data.error || 'Upload failed'}`]);
        showToast(data.error || 'Upload failed', 'error');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadLogs(prev => [...prev, `❌ ${error.message || 'Upload failed'}`]);
      showToast(error.message || 'Upload failed', 'error');
    } finally {
      setUploading(false);
      setShowProgress(false);
    }
  };

  // Handle re-compute for a saved configuration
  const handleRecomputeConfig = async (configId, articleIds = null) => {
    setMerging(true);
    try {
      const response = await videoConfigService.mergeConfig(configId, articleIds);
      const data = response.data;

      if (data.status === 'success' || data.status === 'processing') {
        showToast(data.message || 'Video merging started successfully', 'success');
        await loadVideoConfigs();

        // Start polling for status updates
        pollConfigStatus(configId);
      } else {
        showToast(data.error || 'Failed to merge videos', 'error');
        setMerging(false);
      }
    } catch (error) {
      console.error('Recompute error:', error);
      showToast(error.response?.data?.error || 'Failed to merge videos', 'error');
      setMerging(false);
    }
  };

  // Handle delete configuration
  const handleDeleteConfig = async (configId) => {
    try {
      const response = await videoConfigService.deleteConfig(configId);
      const data = response.data;

      if (data.status === 'success') {
        showToast('Configuration deleted successfully', 'success');
        await loadVideoConfigs();
      } else {
        showToast(data.error || 'Failed to delete configuration', 'error');
      }
    } catch (error) {
      console.error('Delete error:', error);
      showToast(error.response?.data?.error || 'Failed to delete configuration', 'error');
    }
  };

  // Handle create new configuration
  const handleCreateConfig = () => {
    setEditingConfig(null);
    setShowConfigModal(true);
  };

  // Handle edit configuration
  const handleEditConfig = (config) => {
    setEditingConfig(config);
    setShowConfigModal(true);
  };

  // Handle close modal
  const handleCloseModal = () => {
    setShowConfigModal(false);
    setEditingConfig(null);
  };

  // Handle save configuration (from modal)
  const handleSaveConfig = async (configData) => {
    try {
      let response;
      if (editingConfig) {
        // Update existing config
        response = await videoConfigService.updateConfig(editingConfig._id, configData);
      } else {
        // Create new config
        response = await videoConfigService.createConfig(configData);
      }

      const data = response.data;
      if (data.status === 'success') {
        showToast(
          editingConfig ? 'Configuration updated successfully' : 'Configuration created successfully',
          'success'
        );
        await loadVideoConfigs();
        handleCloseModal();
      } else {
        showToast(data.error || 'Failed to save configuration', 'error');
      }
    } catch (error) {
      console.error('Save config error:', error);
      showToast(error.response?.data?.error || 'Failed to save configuration', 'error');
    }
  };

  // Upload latest 20 compilation video
  const handleUploadLatest20 = async () => {
    if (!window.confirm('Upload latest 20 news compilation video to YouTube?')) {
      return;
    }

    setUploading(true);
    setShowProgress(true);
    setUploadProgress(0);
    setUploadLogs([]);

    try {
      // Add initial log
      setUploadLogs([{ type: 'info', message: '🚀 Starting upload process...' }]);

      const response = await youtubeService.uploadLatest20();
      const data = response.data;

      if (data.status === 'success') {
        setUploadProgress(100);
        setUploadLogs((prev) => [
          ...prev,
          { type: 'success', message: `✅ ${data.message}` },
          { type: 'info', message: `📺 Video URL: ${data.video_url}` },
        ]);
        showToast('Video uploaded successfully!', 'success');
        
        // Reload stats
        await loadStats();
      } else {
        setUploadLogs((prev) => [
          ...prev,
          { type: 'error', message: `❌ Upload failed: ${data.error}` },
        ]);
        showToast(data.error || 'Upload failed', 'error');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadLogs((prev) => [
        ...prev,
        { type: 'error', message: `❌ Error: ${error.response?.data?.error || error.message}` },
      ]);
      showToast(error.response?.data?.error || 'Upload failed', 'error');
    } finally {
      setUploading(false);
    }
  };

  // Upload single short
  const handleUploadShort = async (articleId) => {
    if (!window.confirm('Upload this short to YouTube?')) {
      return;
    }

    try {
      const response = await youtubeService.uploadShort(articleId);
      const data = response.data;

      if (data.status === 'success') {
        showToast(`Short uploaded successfully! ${data.video_url}`, 'success');

        // Reload data - preserve current page
        await loadStats();
        await loadPendingShorts(shortsPagination.page, shortsPagination.limit);
      } else {
        showToast(data.error || 'Upload failed', 'error');
      }
    } catch (error) {
      console.error('Upload error:', error);
      showToast(error.response?.data?.error || 'Upload failed', 'error');
    }
  };

  // Load video configurations
  const loadVideoConfigs = async () => {
    setConfigsLoading(true);
    try {
      const response = await videoConfigService.getConfigs();
      const data = response.data;

      if (data.status === 'success') {
        setVideoConfigs(data.configs || []);
      } else {
        setVideoConfigs([]);
      }
    } catch (error) {
      console.error('Failed to load video configs:', error);
      showToast('Failed to load video configurations', 'error');
      setVideoConfigs([]);
    } finally {
      setConfigsLoading(false);
    }
  };

  // Load initial data
  useEffect(() => {
    loadStats();
    loadPendingShorts();
    loadVideoConfigs();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <span>📺</span>
            YouTube Uploader
          </h1>
          <p className="text-gray-600">Upload news videos to YouTube channel</p>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                    ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span>{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Statistics */}
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Statistics</h2>
                <StatsCards stats={stats} loading={statsLoading} />
              </div>

              {/* Quick Actions */}
              <Card title="Quick Actions">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <h3 className="text-lg font-semibold text-blue-900 mb-2">📱 Shorts</h3>
                    <p className="text-sm text-blue-700 mb-3">
                      {stats.shorts_ready_to_upload} shorts ready to upload
                    </p>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setActiveTab('shorts')}
                    >
                      View Shorts
                    </Button>
                  </div>
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <h3 className="text-lg font-semibold text-purple-900 mb-2">🎬 Long Videos</h3>
                    <p className="text-sm text-purple-700 mb-3">
                      {stats.ready_to_upload} videos ready to upload
                    </p>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setActiveTab('long')}
                    >
                      View Long Videos
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Shorts Tab */}
          {activeTab === 'shorts' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-1">YouTube Shorts</h2>
                <p className="text-sm text-gray-600 mb-4">
                  Upload short-form vertical videos to YouTube
                </p>
              </div>

              <Card title="📱 Shorts Ready to Upload">
                <ShortsGrid
                  shorts={shorts}
                  onUpload={handleUploadShort}
                  loading={shortsLoading}
                  pagination={shortsPagination}
                  onPageChange={handleShortsPageChange}
                />
              </Card>
            </div>
          )}

          {/* Long Videos Tab */}
          {activeTab === 'long' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-1">Long Videos</h2>
                <p className="text-sm text-gray-600 mb-4">
                  Create and upload compilation videos to YouTube with custom configuration
                </p>
              </div>

              {/* Video Configurations Grid */}
              <div>
                {configsLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {/* Existing Configuration Cards */}
                    {videoConfigs.map((config) => (
                      <ConfigCard
                        key={config._id}
                        config={config}
                        onEdit={handleEditConfig}
                        onMerge={handleRecomputeConfig}
                        onUpload={handleUploadLongVideo}
                        onDelete={handleDeleteConfig}
                        loading={merging || uploading}
                      />
                    ))}

                    {/* Plus Card - Always last */}
                    <PlusCard onClick={handleCreateConfig} />
                  </div>
                )}
              </div>

              {/* Configuration Modal */}
              {showConfigModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                  <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                    <div className="p-6">
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-xl font-semibold text-gray-900">
                          {editingConfig ? 'Edit Configuration' : 'Create New Configuration'}
                        </h3>
                        <button
                          onClick={handleCloseModal}
                          className="text-gray-400 hover:text-gray-600 text-2xl"
                        >
                          ×
                        </button>
                      </div>
                      <LongVideoConfig
                        initialConfig={editingConfig}
                        onSave={handleSaveConfig}
                        onCancel={handleCloseModal}
                        loading={uploading}
                        merging={merging}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Upload Progress */}
              {showProgress && (
                <Card title="Upload Progress">
                  <UploadProgress
                    progress={uploadProgress}
                    logs={uploadLogs}
                    visible={showProgress}
                  />
                </Card>
              )}
            </div>
          )}

          {/* Credentials Tab */}
          {activeTab === 'credentials' && (
            <div className="space-y-6">
              <CredentialsManager />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default YouTubePage;

