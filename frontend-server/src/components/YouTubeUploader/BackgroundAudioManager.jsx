import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, ConfirmDialog } from '../common';
import { useToast } from '../../hooks/useToast';
import { backgroundAudioService } from '../../services';

/**
 * Background Audio Manager Component - Manage background audio library
 */
const BackgroundAudioManager = () => {
  const [audioFiles, setAudioFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [playingAudio, setPlayingAudio] = useState(null);
  const [shortsDefaultAudio, setShortsDefaultAudio] = useState('background_music.wav');
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, audioId: null });
  const { showToast } = useToast();
  const fileInputRef = useRef(null);
  const audioPlayerRef = useRef(null);

  useEffect(() => {
    loadAudioFiles();
  }, []);

  const loadAudioFiles = async () => {
    try {
      setLoading(true);
      const response = await backgroundAudioService.getBackgroundAudioList();
      
      if (response.data.status === 'success') {
        setAudioFiles(response.data.audio_files || []);
      } else {
        showToast('Failed to load audio files', 'error');
      }
    } catch (error) {
      console.error('Error loading audio files:', error);
      showToast('Error loading audio files', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleUpload(file);
    }
  };

  const handleUpload = async (file) => {
    // Validate file type
    const allowedExtensions = ['.wav', '.mp3', '.m4a', '.aac', '.ogg'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
      showToast(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`, 'error');
      return;
    }

    // Validate file size (max 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      showToast('File size must be less than 50MB', 'error');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);

      await backgroundAudioService.uploadBackgroundAudio(file, (progress) => {
        setUploadProgress(progress);
      });

      showToast('Audio file uploaded successfully', 'success');
      loadAudioFiles();
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error uploading audio:', error);
      const errorMsg = error.response?.data?.error || 'Error uploading audio file';
      showToast(errorMsg, 'error');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDelete = (audioId) => {
    setDeleteDialog({ isOpen: true, audioId });
  };

  const confirmDelete = async () => {
    const audioId = deleteDialog.audioId;
    setDeleteDialog({ isOpen: false, audioId: null });

    try {
      await backgroundAudioService.deleteBackgroundAudio(audioId);
      showToast('Audio file deleted successfully', 'success');

      // Stop playing if this audio is currently playing
      if (playingAudio === audioId) {
        stopAudio();
      }

      loadAudioFiles();
    } catch (error) {
      console.error('Error deleting audio:', error);
      const errorMsg = error.response?.data?.error || 'Error deleting audio file';
      showToast(errorMsg, 'error');
    }
  };

  const handlePlayPause = (audioId) => {
    if (playingAudio === audioId) {
      stopAudio();
    } else {
      playAudio(audioId);
    }
  };

  const playAudio = (audioId) => {
    const audioUrl = backgroundAudioService.getBackgroundAudioDownloadUrl(audioId);
    
    if (audioPlayerRef.current) {
      audioPlayerRef.current.src = audioUrl;
      audioPlayerRef.current.play();
      setPlayingAudio(audioId);
    }
  };

  const stopAudio = () => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current.currentTime = 0;
      setPlayingAudio(null);
    }
  };

  const handleAudioEnded = () => {
    setPlayingAudio(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Background Audio Library</h2>
          <p className="text-gray-600 mt-1">
            Upload and manage background audio files for your videos
          </p>
        </div>
        <Button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          {uploading ? '⏳ Uploading...' : '➕ Upload Audio'}
        </Button>
      </div>

      {/* Shorts Default Audio Settings */}
      <Card className="p-6 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                📱 Shorts Default Background Music
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                This audio will be automatically applied to all generated shorts
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selected Audio File
              </label>
              <select
                value={shortsDefaultAudio}
                onChange={(e) => setShortsDefaultAudio(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white"
              >
                {audioFiles.map((audio) => (
                  <option key={audio.id} value={audio.id}>
                    {audio.name} ({formatFileSize(audio.size)})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2 pt-6">
              {playingAudio === shortsDefaultAudio ? (
                <button
                  onClick={() => stopAudio()}
                  className="px-4 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  ⏸️ Stop
                </button>
              ) : (
                <button
                  onClick={() => handlePlayPause(shortsDefaultAudio)}
                  className="px-4 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  ▶️ Preview
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 p-3 bg-blue-100 rounded-lg">
            <span className="text-blue-800 text-sm">
              ℹ️ <strong>Note:</strong> This setting applies globally to all shorts. Long videos can have custom background music configured individually.
            </span>
          </div>
        </div>
      </Card>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".wav,.mp3,.m4a,.aac,.ogg"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Hidden audio player */}
      <audio
        ref={audioPlayerRef}
        onEnded={handleAudioEnded}
        className="hidden"
      />

      {/* Upload Progress */}
      {uploading && (
        <Card className="p-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-700">Uploading...</span>
              <span className="text-gray-700">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        </Card>
      )}

      {/* Audio Files List */}
      {loading ? (
        <Card className="p-8 text-center">
          <div className="text-gray-500">Loading audio files...</div>
        </Card>
      ) : audioFiles.length === 0 ? (
        <Card className="p-8 text-center">
          <div className="text-gray-500">
            <p className="text-lg mb-2">No audio files uploaded yet</p>
            <p className="text-sm">Click "Upload Audio" to add your first background audio file</p>
          </div>
        </Card>
      ) : (
        <div className="grid gap-4">
          {audioFiles.map((audio) => (
            <Card key={audio.id} className="p-4 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 flex-1">
                  {/* Play/Pause Button */}
                  <button
                    onClick={() => handlePlayPause(audio.id)}
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
                      playingAudio === audio.id
                        ? 'bg-red-100 text-red-600 hover:bg-red-200'
                        : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                    }`}
                  >
                    {playingAudio === audio.id ? '⏸️' : '▶️'}
                  </button>

                  {/* Audio Info */}
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{audio.name}</h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                      <span>📦 {formatFileSize(audio.size)}</span>
                      <span>📅 {formatDate(audio.created_at)}</span>
                      <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                        {audio.extension.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2">
                  <a
                    href={backgroundAudioService.getBackgroundAudioDownloadUrl(audio.id)}
                    download
                    className="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors"
                  >
                    ⬇️ Download
                  </a>
                  <button
                    onClick={() => handleDelete(audio.id)}
                    className="px-3 py-2 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded transition-colors"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Info Card */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">ℹ️ Audio File Guidelines</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Supported formats: WAV, MP3, M4A, AAC, OGG</li>
          <li>• Maximum file size: 50MB</li>
          <li>• Audio files can be selected when creating or editing video configurations</li>
          <li>• The same audio file can be used across multiple video configurations</li>
        </ul>
      </Card>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, audioId: null })}
        onConfirm={confirmDelete}
        title="Delete Audio File"
        description="This action cannot be undone"
        message={
          deleteDialog.audioId
            ? `Are you sure you want to delete "${deleteDialog.audioId}"?`
            : ''
        }
        warningMessage="This will permanently delete the audio file. Any video configurations using this audio will need to be updated."
        confirmText="Delete Audio"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default BackgroundAudioManager;

