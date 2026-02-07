import React, { useState, useEffect } from 'react';
import api, { appendAuthToken } from '../../../services/api';
import { useToast } from '../../../hooks/useToast';

/**
 * Export Dialog Component
 * Allows users to export their Design Editor project to various formats
 */
const ExportDialog = ({ isOpen, onClose, project }) => {
  const { showToast } = useToast();

  // Export settings
  const [format, setFormat] = useState('mp4');
  const [quality, setQuality] = useState('1080p');
  const [fps, setFps] = useState(30);
  const [includeAudio, setIncludeAudio] = useState(true);

  // Export state
  const [exporting, setExporting] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);

  // Quality options for different formats
  const qualityOptions = {
    mp4: [
      { value: '720p', label: '720p (HD)', bitrate: '2500k' },
      { value: '1080p', label: '1080p (Full HD)', bitrate: '5000k' },
      { value: '1440p', label: '1440p (2K)', bitrate: '8000k' },
      { value: '2160p', label: '2160p (4K)', bitrate: '15000k' }
    ],
    mp3: [
      { value: '128k', label: '128 kbps (Standard)' },
      { value: '192k', label: '192 kbps (High)' },
      { value: '320k', label: '320 kbps (Premium)' }
    ]
  };

  const fpsOptions = [24, 30, 60];

  // Reset state when dialog opens
  useEffect(() => {
    console.log('ExportDialog isOpen changed:', isOpen, 'project:', project);
    if (isOpen) {
      setExporting(false);
      setJobId(null);
      setProgress(0);
      setCurrentStep('');
      setError(null);
      setDownloadUrl(null);
    }
  }, [isOpen, project]);

  // Poll for export status
  const pollExportStatus = async (exportJobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/projects/export/${exportJobId}/status`);
        const { status, progress: jobProgress, current_step, output_url, error: jobError } = response.data;

        setProgress(jobProgress || 0);
        setCurrentStep(current_step || '');

        if (status === 'completed') {
          clearInterval(pollInterval);
          setExporting(false);
          setDownloadUrl(output_url);
          showToast('Export completed successfully!', 'success');
        } else if (status === 'failed') {
          clearInterval(pollInterval);
          setExporting(false);
          setError(jobError || 'Export failed');
          showToast('Export failed', 'error');
        }
      } catch (err) {
        console.error('Error polling export status:', err);
        clearInterval(pollInterval);
        setExporting(false);
        setError('Failed to check export status');
      }
    }, 2000); // Poll every 2 seconds

    // Cleanup on unmount
    return () => clearInterval(pollInterval);
  };

  const handleExport = async () => {
    // Validate project exists
    if (!project) {
      showToast('No project loaded. Please create or load a project first.', 'error');
      return;
    }

    // Validate project has been saved
    if (!project.project_id) {
      showToast('Please save your project before exporting.', 'error');
      return;
    }

    setExporting(true);
    setError(null);
    setProgress(0);

    try {
      console.log('Starting export for project:', project.project_id);

      const response = await api.post('/projects/export', {
        project_id: project.project_id,
        format: format,
        settings: {
          quality: quality,
          fps: fps,
          includeAudio: includeAudio,
          codec: 'libx264',
          bitrate: qualityOptions.mp4.find(q => q.value === quality)?.bitrate || '5000k'
        }
      });

      console.log('Export response:', response.data);

      const newJobId = response.data.export_job_id;
      setJobId(newJobId);
      setCurrentStep('Initializing export...');
      showToast('Export started successfully!', 'success');

      // Start polling for progress
      pollExportStatus(newJobId);

    } catch (err) {
      console.error('Export error:', err);
      const errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Failed to start export';
      setError(errorMessage);
      setExporting(false);
      showToast(errorMessage, 'error');
    }
  };

  const handleDownload = async () => {
    if (!downloadUrl) return;

    try {
      showToast('Starting download...', 'info');

      // Fetch the file as a blob with authentication
      const token = localStorage.getItem('auth_token');
      const response = await fetch(downloadUrl, {
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
      link.download = `${project.name}_${format}_${quality}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up blob URL
      URL.revokeObjectURL(blobUrl);

      showToast('Download started', 'success');
    } catch (error) {
      console.error('Download error:', error);
      showToast(`Download failed: ${error.message}`, 'error');
    }
  };

  const handleClose = () => {
    if (!exporting) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Export Project</h2>
          <button
            onClick={handleClose}
            disabled={exporting}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Format
            </label>
            <div className="grid grid-cols-3 gap-3">
              <button
                onClick={() => setFormat('mp4')}
                disabled={exporting}
                className={`p-4 border-2 rounded-lg transition-all ${
                  format === 'mp4'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                } disabled:opacity-50`}
              >
                <div className="text-2xl mb-1">🎬</div>
                <div className="font-medium">MP4 Video</div>
              </button>
              <button
                onClick={() => setFormat('mp3')}
                disabled={exporting}
                className={`p-4 border-2 rounded-lg transition-all ${
                  format === 'mp3'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                } disabled:opacity-50`}
              >
                <div className="text-2xl mb-1">🎵</div>
                <div className="font-medium">MP3 Audio</div>
              </button>
              <button
                onClick={() => setFormat('json')}
                disabled={exporting}
                className={`p-4 border-2 rounded-lg transition-all ${
                  format === 'json'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                } disabled:opacity-50`}
              >
                <div className="text-2xl mb-1">📄</div>
                <div className="font-medium">JSON Data</div>
              </button>
            </div>
          </div>

          {/* MP4 Settings */}
          {format === 'mp4' && (
            <>
              {/* Quality */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Video Quality
                </label>
                <select
                  value={quality}
                  onChange={(e) => setQuality(e.target.value)}
                  disabled={exporting}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
                >
                  {qualityOptions.mp4.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* FPS */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Frame Rate (FPS)
                </label>
                <div className="flex gap-3">
                  {fpsOptions.map(fpsOption => (
                    <button
                      key={fpsOption}
                      onClick={() => setFps(fpsOption)}
                      disabled={exporting}
                      className={`flex-1 px-4 py-2 border-2 rounded-lg transition-all ${
                        fps === fpsOption
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 hover:border-gray-300'
                      } disabled:opacity-50`}
                    >
                      {fpsOption} FPS
                    </button>
                  ))}
                </div>
              </div>

              {/* Include Audio */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="includeAudio"
                  checked={includeAudio}
                  onChange={(e) => setIncludeAudio(e.target.checked)}
                  disabled={exporting}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50"
                />
                <label htmlFor="includeAudio" className="ml-2 text-sm text-gray-700">
                  Include audio tracks in export
                </label>
              </div>
            </>
          )}

          {/* Progress Bar */}
          {exporting && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-700 font-medium">{currentStep || 'Processing...'}</span>
                <span className="text-gray-500">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-red-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-red-800">Export Failed</h4>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Success Message with Download */}
          {downloadUrl && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-green-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-green-800">Export Complete!</h4>
                  <p className="text-sm text-green-700 mt-1">Your file is ready to download.</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={handleClose}
            disabled={exporting}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            {downloadUrl ? 'Close' : 'Cancel'}
          </button>

          {downloadUrl ? (
            <button
              onClick={handleDownload}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
          ) : (
            <button
              onClick={handleExport}
              disabled={exporting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {exporting ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Exporting...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Export
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExportDialog;

