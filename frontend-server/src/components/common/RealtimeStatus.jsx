import React, { useState, useEffect } from 'react';
import ProgressBar from './ProgressBar';
import Card from './Card';

/**
 * RealtimeStatus Component
 * Displays real-time status updates with progress bar
 * 
 * @param {string} title - Panel title
 * @param {Object} statusData - Status data from WebSocket
 * @param {boolean} isConnected - WebSocket connection status
 * @param {string} icon - Icon emoji
 */
const RealtimeStatus = ({ 
  title = 'Status',
  statusData = null,
  isConnected = false,
  icon = '📊'
}) => {
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('');
  const [details, setDetails] = useState({});

  // Update state when statusData changes
  useEffect(() => {
    if (statusData) {
      setStatus(statusData.status || 'idle');
      setProgress(statusData.progress || 0);
      setMessage(statusData.message || '');
      setDetails(statusData);
    }
  }, [statusData]);

  // Status badge
  const getStatusBadge = () => {
    const badges = {
      idle: { text: 'Idle', color: 'bg-gray-100 text-gray-800' },
      running: { text: 'Running', color: 'bg-blue-100 text-blue-800' },
      completed: { text: 'Completed', color: 'bg-green-100 text-green-800' },
      error: { text: 'Error', color: 'bg-red-100 text-red-800' }
    };

    const badge = badges[status] || badges.idle;

    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${badge.color}`}>
        {badge.text}
      </span>
    );
  };

  // Connection indicator
  const getConnectionIndicator = () => {
    return (
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
        <span className="text-xs text-gray-600">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
    );
  };

  return (
    <Card>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{icon}</span>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <div className="flex items-center gap-3">
          {getConnectionIndicator()}
          {getStatusBadge()}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <ProgressBar
          progress={progress}
          status={status}
          message={message}
          showPercentage={true}
          size="md"
        />
      </div>

      {/* Details */}
      {status !== 'idle' && Object.keys(details).length > 0 && (
        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-200">
          {details.current_source && (
            <div>
              <p className="text-xs text-gray-500">Current Source</p>
              <p className="text-sm font-medium text-gray-900">{details.current_source}</p>
            </div>
          )}
          {details.current_article && (
            <div>
              <p className="text-xs text-gray-500">Current Article</p>
              <p className="text-sm font-medium text-gray-900 truncate">{details.current_article}</p>
            </div>
          )}
          {details.current_video && (
            <div>
              <p className="text-xs text-gray-500">Current Video</p>
              <p className="text-sm font-medium text-gray-900 truncate">{details.current_video}</p>
            </div>
          )}
          {details.articles_fetched !== undefined && (
            <div>
              <p className="text-xs text-gray-500">Articles Fetched</p>
              <p className="text-sm font-medium text-gray-900">
                {details.articles_fetched} / {details.total_sources || '?'}
              </p>
            </div>
          )}
          {details.articles_processed !== undefined && (
            <div>
              <p className="text-xs text-gray-500">Articles Processed</p>
              <p className="text-sm font-medium text-gray-900">
                {details.articles_processed} / {details.total_articles || '?'}
              </p>
            </div>
          )}
          {details.videos_uploaded !== undefined && (
            <div>
              <p className="text-xs text-gray-500">Videos Uploaded</p>
              <p className="text-sm font-medium text-gray-900">
                {details.videos_uploaded} / {details.total_videos || '?'}
              </p>
            </div>
          )}
          {details.images_processed !== undefined && (
            <div>
              <p className="text-xs text-gray-500">Images Processed</p>
              <p className="text-sm font-medium text-gray-900">
                {details.images_processed} / {details.total_images || '?'}
              </p>
            </div>
          )}
          {details.video_url && (
            <div className="col-span-2">
              <p className="text-xs text-gray-500">Video URL</p>
              <a 
                href={details.video_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-sm font-medium text-blue-600 hover:text-blue-800 truncate block"
              >
                {details.video_url}
              </a>
            </div>
          )}
        </div>
      )}

      {/* Idle state */}
      {status === 'idle' && (
        <div className="text-center py-4 text-gray-500 text-sm">
          No active jobs
        </div>
      )}
    </Card>
  );
};

export default RealtimeStatus;

