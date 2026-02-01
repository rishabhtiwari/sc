import React, { useState, useEffect } from 'react';
import { Button } from '../components/common';
import { useToast } from '../hooks/useToast';
import { videoLibrary } from '../services/assetLibraryService';
import AuthenticatedVideo from '../components/common/AuthenticatedVideo';
import ConfirmDialog from '../components/common/ConfirmDialog';

/**
 * Video Library Page - Full page view of all videos with modern, appealing design
 */
const VideoLibraryPage = () => {
  const { showToast } = useToast();
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, video: null });

  // Load videos on mount
  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    setLoading(true);
    try {
      const response = await videoLibrary.list();
      if (response.success) {
        setVideos(response.videos || []);
      }
    } catch (error) {
      console.error('Failed to fetch videos:', error);
      showToast('Failed to load video library', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (video) => {
    setDeleteDialog({ isOpen: true, video });
  };

  const confirmDelete = async () => {
    if (!deleteDialog.video) return;

    try {
      await videoLibrary.delete(deleteDialog.video.video_id);
      showToast('Video deleted successfully', 'success');
      setDeleteDialog({ isOpen: false, video: null });
      fetchVideos(); // Refresh list
    } catch (error) {
      console.error('Failed to delete video:', error);
      showToast('Failed to delete video', 'error');
      setDeleteDialog({ isOpen: false, video: null });
    }
  };

  // Filter videos based on search query
  const filteredVideos = videos.filter(video =>
    video.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 via-red-50 to-pink-50">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="w-20 h-20 border-4 border-orange-200 border-t-orange-600 rounded-full animate-spin mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-3xl">🎬</span>
            </div>
          </div>
          <p className="text-lg font-semibold text-gray-700">Loading your video library...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50">
      {/* Content */}
      <div className="relative space-y-6 p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/50 p-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform">
                <span className="text-4xl">🎬</span>
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-600 via-red-600 to-pink-600 bg-clip-text text-transparent">
                  Video Library
                </h1>
                <p className="text-gray-600 mt-1 font-medium">
                  Browse and manage your video collection
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-gradient-to-r from-orange-100 to-red-100 px-6 py-3 rounded-xl border border-orange-200">
                <p className="text-sm font-semibold text-gray-700">
                  <span className="text-orange-600 text-xl">{filteredVideos.length}</span>
                  <span className="text-gray-500 mx-1">/</span>
                  <span className="text-red-600 text-xl">{videos.length}</span>
                  <span className="text-gray-600 ml-2">videos</span>
                </p>
              </div>
              <Button
                onClick={() => window.location.href = '/design-editor'}
                className="bg-gradient-to-r from-orange-600 to-red-600 text-white px-6 py-3 rounded-xl hover:shadow-xl transition-all transform hover:scale-105 font-semibold"
              >
                🎨 Design Editor
              </Button>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-lg border border-white/50 p-6">
          <div className="relative">
            <input
              type="text"
              placeholder="🔍 Search videos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-6 py-4 bg-white border-2 border-orange-200 rounded-xl focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all text-lg"
            />
          </div>
        </div>

        {/* Videos Grid */}
        {filteredVideos.length === 0 ? (
          <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/50 p-16">
            <div className="text-center">
              <div className="text-8xl mb-6 opacity-50">🎬</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                {videos.length === 0 ? 'No Videos Yet' : 'No Matching Videos'}
              </h3>
              <p className="text-gray-600 text-lg mb-6">
                {videos.length === 0
                  ? 'Upload videos from the Design Editor to see them here'
                  : 'Try adjusting your search query'}
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredVideos.map((video, index) => (
              <div
                key={video.video_id}
                className="transform transition-all duration-300 hover:scale-105"
                style={{
                  animation: `fadeInUp 0.5s ease-out ${index * 0.05}s both`
                }}
              >
                <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl transition-all overflow-hidden group border border-orange-100">
                  {/* Video Preview */}
                  <div className="aspect-video bg-gradient-to-br from-orange-100 to-red-100 relative overflow-hidden">
                    <AuthenticatedVideo
                      src={video.url}
                      className="w-full h-full object-cover"
                      preload="metadata"
                    />
                    {/* Delete Button Overlay */}
                    <button
                      onClick={() => handleDeleteClick(video)}
                      className="absolute top-3 right-3 w-10 h-10 bg-red-500 hover:bg-red-600 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all shadow-lg flex items-center justify-center transform hover:scale-110"
                      title="Delete video"
                    >
                      ✕
                    </button>
                    {/* Duration Badge */}
                    <div className="absolute bottom-3 right-3 bg-black/70 text-white px-3 py-1 rounded-lg text-sm font-semibold">
                      {formatDuration(video.duration)}
                    </div>
                  </div>

                  {/* Video Info */}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 truncate text-lg mb-2">
                      {video.name || 'Untitled Video'}
                    </h3>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        🎬 {formatDuration(video.duration)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(video.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, video: null })}
        onConfirm={confirmDelete}
        title="Delete Video"
        description="This action cannot be undone"
        message={`Are you sure you want to delete "${deleteDialog.video?.name || 'this video'}"?`}
        confirmText="Delete Video"
        cancelText="Cancel"
        variant="danger"
      />

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

export default VideoLibraryPage;

