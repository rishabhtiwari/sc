import { useState } from 'react';
import api from '../services/api';

/**
 * Custom hook for audio library management
 * Handles CRUD operations for audio files
 */
export const useAudioLibrary = () => {
  const [audioFiles, setAudioFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all audio files from library
  const fetchAudioFiles = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/audio-studio/library');
      
      if (response.data.success) {
        setAudioFiles(response.data.audio_files || []);
      } else {
        throw new Error(response.data.error || 'Failed to fetch audio files');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to fetch audio files';
      setError(errorMessage);
      console.error('Fetch audio files error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Save audio to library
  const saveToLibrary = async (audioData) => {
    setSaving(true);
    setError(null);

    try {
      const response = await api.post('/audio-studio/library', audioData);
      
      if (response.data.success) {
        // Add new audio to the list
        setAudioFiles(prev => [response.data.audio, ...prev]);
        return response.data.audio;
      } else {
        throw new Error(response.data.error || 'Failed to save audio');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to save audio';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // Delete audio from library
  const deleteAudio = async (audioId) => {
    setError(null);

    try {
      const response = await api.delete(`/audio-studio/library/${audioId}`);
      
      if (response.data.success) {
        // Remove audio from the list
        setAudioFiles(prev => prev.filter(audio => audio.audio_id !== audioId));
      } else {
        throw new Error(response.data.error || 'Failed to delete audio');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to delete audio';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  // Update audio metadata
  const updateAudio = async (audioId, updates) => {
    setError(null);

    try {
      const response = await api.put(`/audio-studio/library/${audioId}`, updates);
      
      if (response.data.success) {
        // Update audio in the list
        setAudioFiles(prev => prev.map(audio =>
          audio.audio_id === audioId ? { ...audio, ...updates } : audio
        ));
        return response.data.audio;
      } else {
        throw new Error(response.data.error || 'Failed to update audio');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to update audio';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  return {
    audioFiles,
    loading,
    saving,
    error,
    fetchAudioFiles,
    saveToLibrary,
    deleteAudio,
    updateAudio
  };
};

