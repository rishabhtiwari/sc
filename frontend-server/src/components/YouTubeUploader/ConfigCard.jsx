import React, { useState } from 'react';
import { Button } from '../common';

/**
 * Config Card Component - Display a saved video configuration
 */
const ConfigCard = ({ config, onMerge, onUpload, onDelete, onEdit, loading }) => {
  const [showPreview, setShowPreview] = useState(false);

  const getStatusBadge = (status) => {
    const badges = {
      unknown: { color: 'bg-gray-100 text-gray-800', icon: '❓', text: 'Not Generated' },
      pending: { color: 'bg-yellow-100 text-yellow-800', icon: '⏳', text: 'Pending' },
      processing: { color: 'bg-blue-100 text-blue-800', icon: '⚙️', text: 'Processing' },
      completed: { color: 'bg-green-100 text-green-800', icon: '✅', text: 'Completed' },
      failed: { color: 'bg-red-100 text-red-800', icon: '❌', text: 'Failed' }
    };

    const badge = badges[status] || badges.unknown;
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badge.color}`}>
        {badge.icon} {badge.text}
      </span>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    // Format as local time with date and time
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getVideoUrl = () => {
    if (config.videoPath) {
      // Convert /public/<config_id>/latest.mp4 to /api/news/videos/<config_id>/latest.mp4
      const url = config.videoPath.replace('/public/', '/api/news/videos/');
      console.log('Video URL:', url, 'from path:', config.videoPath);
      return url;
    }
    return null;
  };

  const getThumbnailUrl = () => {
    if (config.thumbnailPath) {
      // Convert /public/<config_id>/latest-thumbnail.jpg to /api/news/videos/<config_id>/latest-thumbnail.jpg
      const url = config.thumbnailPath.replace('/public/', '/api/news/videos/');
      console.log('Thumbnail URL:', url, 'from path:', config.thumbnailPath);
      return url;
    }
    return null;
  };

  const handleMerge = () => {
    onMerge(config._id);
  };

  const handleUpload = () => {
    onUpload(config._id);
  };

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete "${config.title}"?`)) {
      onDelete(config._id);
    }
  };

  const handleEdit = () => {
    onEdit(config);
  };

  const isCompleted = config.status === 'completed';
  const isProcessing = config.status === 'processing';
  const canUpload = isCompleted && !config.youtubeVideoId;
  const isUploaded = !!config.youtubeVideoId;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-semibold text-gray-900 flex-1">{config.title}</h3>
          {getStatusBadge(config.status)}
        </div>
        
        {/* Configuration Details */}
        <div className="grid grid-cols-2 gap-2 text-sm text-gray-600 mt-3">
          <div>
            <span className="font-medium">Videos:</span> {config.videoCount}
          </div>
          {config.categories && config.categories.length > 0 && (
            <div>
              <span className="font-medium">Categories:</span> {config.categories.join(', ')}
            </div>
          )}
          {config.country && (
            <div>
              <span className="font-medium">Country:</span> {config.country.toUpperCase()}
            </div>
          )}
          {config.language && (
            <div>
              <span className="font-medium">Language:</span> {config.language.toUpperCase()}
            </div>
          )}
          <div>
            <span className="font-medium">Frequency:</span> {config.frequency || 'none'}
          </div>
          {config.runCount !== undefined && (
            <div>
              <span className="font-medium">Run Count:</span> {config.runCount}
            </div>
          )}
          <div>
            <span className="font-medium">Created:</span> {formatDate(config.createdAt)}
          </div>
          {config.lastRunTime && (
            <div>
              <span className="font-medium">Last Run:</span> {formatDate(config.lastRunTime)}
            </div>
          )}
          {config.nextRunTime && config.frequency !== 'none' && (
            <div>
              <span className="font-medium">Next Run:</span> {formatDate(config.nextRunTime)}
            </div>
          )}
        </div>

        {/* YouTube Upload Info */}
        {isUploaded && (
          <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded">
            <div className="flex items-center gap-2 text-sm text-green-800">
              <span className="font-medium">✅ Uploaded to YouTube</span>
              {config.youtubeVideoUrl && (
                <a
                  href={config.youtubeVideoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  View Video
                </a>
              )}
            </div>
          </div>
        )}

        {/* Error Message */}
        {config.error && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
            <p className="text-sm text-red-800">
              <span className="font-medium">Error:</span> {config.error}
            </p>
          </div>
        )}
      </div>

      {/* Preview Section */}
      {isCompleted && (
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            {showPreview ? '▼' : '▶'} {showPreview ? 'Hide' : 'Show'} Preview
          </button>
          
          {showPreview && (
            <div className="mt-3 space-y-3">
              {/* Thumbnail */}
              {getThumbnailUrl() && (
                <div>
                  <p className="text-xs font-medium text-gray-700 mb-1">Thumbnail:</p>
                  <img
                    src={getThumbnailUrl()}
                    alt="Video Thumbnail"
                    className="w-full rounded border border-gray-300"
                  />
                </div>
              )}
              
              {/* Video Preview */}
              {getVideoUrl() && (
                <div>
                  <p className="text-xs font-medium text-gray-700 mb-1">Video Preview:</p>
                  <video
                    src={getVideoUrl()}
                    controls
                    className="w-full rounded border border-gray-300"
                    preload="metadata"
                  >
                    Your browser does not support the video tag.
                  </video>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="p-4 bg-gray-50 flex gap-2">
        {/* Edit Button */}
        <Button
          variant="secondary"
          icon="✏️"
          onClick={handleEdit}
          disabled={loading || isProcessing}
          size="sm"
        >
          Edit
        </Button>

        {/* Re-compute/Merge Button */}
        {!isProcessing && (
          <Button
            variant="secondary"
            icon="🔄"
            onClick={handleMerge}
            loading={loading}
            disabled={loading}
            size="sm"
          >
            {isCompleted ? 'Re-compute' : 'Merge'}
          </Button>
        )}

        {/* Upload Button */}
        {canUpload && (
          <Button
            variant="danger"
            icon="⬆️"
            onClick={handleUpload}
            loading={loading}
            disabled={loading}
            size="sm"
          >
            Upload
          </Button>
        )}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="flex items-center gap-2 text-sm text-blue-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span>Processing...</span>
          </div>
        )}

        {/* Delete Button */}
        <Button
          variant="secondary"
          icon="🗑️"
          onClick={handleDelete}
          disabled={loading || isProcessing}
          size="sm"
          className="ml-auto"
        >
          Delete
        </Button>
      </div>
    </div>
  );
};

export default ConfigCard;

