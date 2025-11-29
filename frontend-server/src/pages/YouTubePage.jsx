import React, { useState, useEffect } from 'react';
import { Card, Button } from '../components/common';
import { useToast } from '../hooks/useToast';
import { youtubeService } from '../services';
import { StatsCards, UploadProgress, ShortsGrid } from '../components/YouTubeUploader';

/**
 * YouTube Page - Upload news videos to YouTube
 */
const YouTubePage = () => {
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
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadLogs, setUploadLogs] = useState([]);
  const [showProgress, setShowProgress] = useState(false);

  const { showToast } = useToast();

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

  // Load pending shorts
  const loadPendingShorts = async () => {
    setShortsLoading(true);
    try {
      const response = await youtubeService.getPendingShorts();
      const data = response.data;
      
      if (data.status === 'success') {
        setShorts(data.shorts || []);
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
        
        // Reload data
        await loadStats();
        await loadPendingShorts();
      } else {
        showToast(data.error || 'Upload failed', 'error');
      }
    } catch (error) {
      console.error('Upload error:', error);
      showToast(error.response?.data?.error || 'Upload failed', 'error');
    }
  };

  // Load initial data
  useEffect(() => {
    loadStats();
    loadPendingShorts();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <span>📺</span>
          YouTube Uploader
        </h1>
        <p className="text-gray-600">Upload news videos to YouTube channel</p>
      </div>

      {/* Statistics */}
      <StatsCards stats={stats} loading={statsLoading} />

      {/* Upload Latest 20 Section */}
      <Card title="Upload Actions">
        <div className="space-y-4">
          <Button
            variant="danger"
            icon="⬆️"
            onClick={handleUploadLatest20}
            loading={uploading}
            size="lg"
          >
            Upload Latest 20 News to YouTube
          </Button>

          {/* Upload Progress */}
          <UploadProgress
            progress={uploadProgress}
            logs={uploadLogs}
            visible={showProgress}
          />
        </div>
      </Card>

      {/* YouTube Shorts Section */}
      <Card title="📱 YouTube Shorts - Ready to Upload">
        <ShortsGrid
          shorts={shorts}
          onUpload={handleUploadShort}
          loading={shortsLoading}
        />
      </Card>
    </div>
  );
};

export default YouTubePage;

