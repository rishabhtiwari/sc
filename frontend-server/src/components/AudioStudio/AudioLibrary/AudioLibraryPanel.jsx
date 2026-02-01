import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../../../hooks/useToast';
import { useAudioLibrary } from '../../../hooks/useAudioLibrary';
import AudioGrid from './AudioGrid';
import ConfirmDialog from '../../common/ConfirmDialog';

/**
 * Audio Library Panel Component
 * Sidebar panel showing saved audio files
 */
const AudioLibraryPanel = ({ refreshTrigger, onAddToCanvas }) => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { audioFiles, loading, fetchAudioFiles, deleteAudio } = useAudioLibrary();
  const [filter, setFilter] = useState('all'); // all, voiceover, music
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, audio: null });

  useEffect(() => {
    fetchAudioFiles();
  }, [refreshTrigger]);

  const handleDeleteClick = (audio) => {
    setDeleteDialog({ isOpen: true, audio });
  };

  const confirmDelete = async () => {
    if (!deleteDialog.audio) return;

    try {
      await deleteAudio(deleteDialog.audio.audio_id);
      showToast('Audio deleted successfully', 'success');
      setDeleteDialog({ isOpen: false, audio: null });
    } catch (error) {
      showToast(error.message || 'Failed to delete audio', 'error');
      setDeleteDialog({ isOpen: false, audio: null });
    }
  };

  // Filter audio files
  const filteredAudioFiles = audioFiles.filter(audio => {
    if (filter === 'all') return true;
    return audio.type === filter;
  });

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">
            📁 Audio Library
          </h3>
          <button
            onClick={() => navigate('/audio-studio/library')}
            className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            title="View full library with filters"
          >
            View All →
          </button>
        </div>

        {/* Filter Buttons */}
        <div className="flex flex-col gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`
              px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left
              ${filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            All Audio ({audioFiles.length})
          </button>
          <button
            onClick={() => setFilter('voiceover')}
            className={`
              px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left
              ${filter === 'voiceover'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            🎙️ Voiceovers ({audioFiles.filter(a => a.type === 'voiceover').length})
          </button>
          <button
            onClick={() => setFilter('music')}
            className={`
              px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left
              ${filter === 'music'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            🎵 Music ({audioFiles.filter(a => a.type === 'music').length})
          </button>
        </div>
      </div>

      {/* Recent Audios Label */}
      <div className="px-4 pb-2">
        <div className="px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs font-medium text-blue-700 flex items-center gap-1">
            <span>🕒</span>
            <span>Recents</span>
          </p>
        </div>
      </div>

      {/* Audio Grid */}
      <div className="flex-1 overflow-y-auto px-4">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin text-3xl">⏳</div>
          </div>
        ) : filteredAudioFiles.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-2">🎵</div>
            <p className="text-sm text-gray-600">
              {filter === 'all'
                ? 'No audio files yet'
                : `No ${filter} files yet`
              }
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Generate audio to see it here
            </p>
          </div>
        ) : (
          <AudioGrid
            audioFiles={filteredAudioFiles}
            onDelete={handleDeleteClick}
            onAddToCanvas={onAddToCanvas}
          />
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, audio: null })}
        onConfirm={confirmDelete}
        title="Delete Audio"
        description="This action cannot be undone"
        message={
          deleteDialog.audio
            ? `Are you sure you want to delete "${deleteDialog.audio.name}"?`
            : ''
        }
        warningMessage="This will permanently delete the audio from your library. This action cannot be undone."
        confirmText="Delete Audio"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default AudioLibraryPanel;

