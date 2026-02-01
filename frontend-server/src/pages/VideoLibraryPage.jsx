import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../components/common';
import { useToast } from '../hooks/useToast';
import { videoLibrary } from '../services/assetLibraryService';
import AuthenticatedVideo from '../components/common/AuthenticatedVideo';
import ConfirmDialog from '../components/common/ConfirmDialog';

/**
 * Video Library Page - Full page view of all videos with modern, appealing design
 */
const VideoLibraryPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, video: null });
  const [playingVideo, setPlayingVideo] = useState(null);

  // Check if opened from Design Editor
  const fromEditor = location.state?.fromEditor || false;
  const returnPath = location.state?.returnPath || '/design-editor';

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

  const handlePlayVideo = (videoId) => {
    setPlayingVideo(playingVideo === videoId ? null : videoId);
  };

  const handleAddToCanvas = (video) => {
    if (fromEditor) {
      // Navigate back to editor with selected video, preserving the return path
      navigate(returnPath, {
        state: {
          addAsset: {
            type: 'video',
            src: video.url,
            name: video.name,
            duration: video.duration,
            libraryId: video.video_id
          }
        }
      });
      showToast('Video added to media library', 'success');
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
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="w-16 h-16 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">🎬</span>
            </div>
          </div>
          <p className="text-gray-700">Loading your video library...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Content */}
      <div className="space-y-6 p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🎬</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Video Library
                </h1>
                <p className="text-gray-600 text-sm mt-1">
                  Browse and manage your video collection
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-gray-50 px-4 py-2 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-700">
                  <span className="font-semibold text-gray-900">{filteredVideos.length}</span>
                  <span className="text-gray-500 mx-1">/</span>
                  <span className="font-semibold text-gray-900">{videos.length}</span>
                  <span className="text-gray-600 ml-1">videos</span>
                </p>
              </div>
              {fromEditor ? (
                <Button
                  onClick={() => navigate(returnPath)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Editor
                </Button>
              ) : (
                <Button
                  onClick={() => navigate('/design-editor')}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  🎨 Design Editor
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <div className="relative">
            <input
              type="text"
              placeholder="🔍 Search videos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>
        </div>

        {/* Videos Grid */}
        {filteredVideos.length === 0 ? (
          <div className="bg-white rounded-lg shadow border border-gray-200 p-16">
            <div className="text-center">
              <div className="text-6xl mb-4 opacity-40">🎬</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {videos.length === 0 ? 'No Videos Yet' : 'No Matching Videos'}
              </h3>
              <p className="text-gray-600 mb-4">
                {videos.length === 0
                  ? 'Upload videos from the Design Editor to see them here'
                  : 'Try adjusting your search query'}
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredVideos.map((video, index) => (
              <div
                key={video.video_id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-all overflow-hidden group border border-gray-200"
              >
                {/* Video Preview */}
                <div className="aspect-video bg-gray-100 relative overflow-hidden">
                  <AuthenticatedVideo
                    src={video.url}
                    className="w-full h-full object-cover"
                    preload="metadata"
                    autoPlay={playingVideo === video.video_id}
                    controls={playingVideo === video.video_id}
                  />
                  {/* Play Button Overlay */}
                  {playingVideo !== video.video_id && !fromEditor && (
                    <button
                      onClick={() => handlePlayVideo(video.video_id)}
                      className="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/30 transition-all group/play"
                      title="Play video"
                    >
                      <div className="w-16 h-16 bg-blue-600 hover:bg-blue-700 rounded-full flex items-center justify-center shadow-lg transform group-hover/play:scale-110 transition-transform">
                        <svg className="w-8 h-8 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </div>
                    </button>
                  )}
                  {/* Add to Canvas Button Overlay (when fromEditor) */}
                  {fromEditor && playingVideo !== video.video_id && (
                    <button
                      onClick={() => handleAddToCanvas(video)}
                      className="absolute inset-0 flex items-center justify-center bg-black/0 hover:bg-black/40 transition-all group/add"
                      title="Add to canvas"
                    >
                      <div className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg opacity-0 group-hover/add:opacity-100 transition-opacity text-sm font-medium">
                        Add to Canvas
                      </div>
                    </button>
                  )}
                  {/* Delete Button Overlay */}
                  {!fromEditor && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteClick(video);
                      }}
                      className="absolute top-2 right-2 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-all shadow flex items-center justify-center z-10"
                      title="Delete video"
                    >
                      ✕
                    </button>
                  )}
                  {/* Duration Badge */}
                  <div className="absolute bottom-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-xs font-medium">
                    {formatDuration(video.duration)}
                  </div>
                </div>

                {/* Video Info */}
                <div className="p-3">
                  <h3 className="font-medium text-gray-900 truncate mb-1">
                    {video.name || 'Untitled Video'}
                  </h3>
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span className="flex items-center gap-1">
                      🎬 {formatDuration(video.duration)}
                    </span>
                    <span className="text-gray-500">
                      {new Date(video.created_at).toLocaleDateString()}
                    </span>
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
    </div>
  );
};

export default VideoLibraryPage;

