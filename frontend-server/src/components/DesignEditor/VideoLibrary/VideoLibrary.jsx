import React, { useState, useEffect } from 'react';
import { useToast } from '../../../hooks/useToast';
import { videoLibrary } from '../../../services/assetLibraryService';
import ConfirmDialog from '../../common/ConfirmDialog';
import AuthenticatedVideo from '../../common/AuthenticatedVideo';

/**
 * Video Library Modal - Full-screen modal for browsing video library
 */
const VideoLibrary = ({ isOpen, onClose, onAddToCanvas }) => {
  const { showToast } = useToast();
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, video: null });

  useEffect(() => {
    if (isOpen) {
      fetchVideos();
    }
  }, [isOpen]);

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

  const handleAddToCanvas = (video) => {
    if (onAddToCanvas) {
      onAddToCanvas({
        type: 'video',
        url: video.url,
        title: video.name,
        duration: video.duration,
        libraryId: video.video_id
      });
      showToast('Video added to canvas', 'success');
      onClose();
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-2xl w-[95%] h-[95%] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🎬</span>
              <h1 className="text-2xl font-bold text-gray-900">Video Library</h1>
            </div>
            <button
              onClick={onClose}
              className="text-gray-600 hover:text-gray-900 text-2xl font-bold transition-colors"
            >
              ✕
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Browse and add videos from your library to the canvas
          </p>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading videos...</p>
              </div>
            </div>
          ) : videos.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <span className="text-6xl">🎬</span>
                <p className="mt-4 text-gray-600">No videos in library</p>
                <p className="text-sm text-gray-500 mt-2">Upload videos from the Video panel to see them here</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {videos.map((video) => (
                <div
                  key={video.video_id}
                  className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden group"
                >
                  <div className="aspect-video bg-gray-100 relative overflow-hidden">
                    <AuthenticatedVideo
                      src={video.url}
                      className="w-full h-full object-cover"
                      preload="metadata"
                    />
                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all flex items-center justify-center gap-2">
                      <button
                        onClick={() => handleAddToCanvas(video)}
                        className="px-3 py-1.5 bg-blue-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity text-sm font-medium"
                      >
                        Add to Canvas
                      </button>
                      <button
                        onClick={() => handleDeleteClick(video)}
                        className="px-3 py-1.5 bg-red-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <div className="p-3">
                    <p className="text-sm font-medium text-gray-900 truncate">{video.name}</p>
                    <div className="flex items-center justify-between mt-1">
                      <p className="text-xs text-gray-500">
                        {video.duration ? `${video.duration.toFixed(1)}s` : 'N/A'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(video.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, video: null })}
        onConfirm={confirmDelete}
        title="Delete Video"
        description="This action cannot be undone"
        message={
          deleteDialog.video
            ? `Are you sure you want to delete "${deleteDialog.video.name}"?`
            : ''
        }
        warningMessage="This will permanently delete the video from your library. This action cannot be undone."
        confirmText="Delete Video"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default VideoLibrary;

