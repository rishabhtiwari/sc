import React, { useState } from 'react';
import { useAuthenticatedVideo } from '../../../hooks/useAuthenticatedVideo';
import { appendAuthToken } from '../../../services/api';

/**
 * VideoPreviewDialog Component
 * Shows a video player for previewing exported videos
 */
const VideoPreviewDialog = ({ export: exportItem, projectName, onClose }) => {
  const { videoUrl, loading, error } = useAuthenticatedVideo(exportItem.output_url);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[60]">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-gray-900">Video Preview</h3>
            <p className="text-sm text-gray-500 mt-1">
              {projectName} - {exportItem.quality} {exportItem.format.toUpperCase()}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Video Player */}
        <div className="flex-1 overflow-hidden p-6 bg-gray-900">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-white text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                <p>Loading video...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-red-400 text-center">
                <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p>Error loading video: {error}</p>
              </div>
            </div>
          )}
          {videoUrl && !loading && !error && (
            <video
              src={videoUrl}
              controls
              autoPlay
              className="w-full h-full max-h-[70vh] object-contain rounded-lg"
            >
              Your browser does not support the video tag.
            </video>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * ExportsListDialog Component
 * Displays all exported videos from the current project with preview functionality
 */
const ExportsListDialog = ({ isOpen, onClose, project }) => {
  const [selectedExport, setSelectedExport] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  if (!isOpen) return null;

  const exports = project?.exports || [];

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const handlePreview = (exportItem) => {
    setSelectedExport(exportItem);
    setShowPreview(true);
  };

  const handleDownload = async (exportItem) => {
    try {
      // Fetch the file as a blob with authentication
      const token = localStorage.getItem('auth_token');
      const response = await fetch(exportItem.output_url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status} ${response.statusText}`);
      }

      // Create blob from response
      const blob = await response.blob();

      // Create blob URL and trigger download
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${project.name}_${exportItem.format}_${exportItem.quality}.${exportItem.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up blob URL
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('Download error:', error);
      alert(`Failed to download: ${error.message}`);
    }
  };

  return (
    <>
      {/* Main Dialog */}
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Project Exports</h2>
              <p className="text-sm text-gray-500 mt-1">
                {exports.length} export{exports.length !== 1 ? 's' : ''} available
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {exports.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                </svg>
                <p className="text-gray-500 text-lg">No exports yet</p>
                <p className="text-gray-400 text-sm mt-2">Click the Export button to create your first export</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {exports.map((exportItem, index) => (
                  <div
                    key={exportItem.export_id || index}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start justify-between gap-4">
                      {/* Export Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold uppercase">
                            {exportItem.format}
                          </span>
                          <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-semibold">
                            {exportItem.quality}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                          <div>
                            <span className="text-gray-500">Duration:</span>
                            <span className="ml-2 text-gray-900 font-medium">{formatDuration(exportItem.duration)}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">File Size:</span>
                            <span className="ml-2 text-gray-900 font-medium">{formatFileSize(exportItem.file_size)}</span>
                          </div>
                          <div className="col-span-2">
                            <span className="text-gray-500">Exported:</span>
                            <span className="ml-2 text-gray-900 font-medium">{formatDate(exportItem.exported_at)}</span>
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-col gap-2">
                        {exportItem.format === 'mp4' && (
                          <button
                            onClick={() => handlePreview(exportItem)}
                            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium flex items-center gap-2"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Preview
                          </button>
                        )}
                        <button
                          onClick={() => handleDownload(exportItem)}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          Download
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Preview Dialog */}
      {showPreview && selectedExport && (
        <VideoPreviewDialog
          export={selectedExport}
          projectName={project?.name}
          onClose={() => {
            setShowPreview(false);
            setSelectedExport(null);
          }}
        />
      )}
    </>
  );
};

export default ExportsListDialog;

