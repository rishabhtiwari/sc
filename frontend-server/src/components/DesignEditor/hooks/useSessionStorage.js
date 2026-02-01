import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Custom hook to auto-save and restore in-memory state from sessionStorage
 * This preserves unsaved work when navigating to libraries and back
 */
export const useSessionStorage = ({
  pages,
  uploadedAudio,
  uploadedImage,
  uploadedVideo,
  audioTracks,
  currentProject,
  setPages,
  setUploadedAudio,
  setUploadedImage,
  setUploadedVideo,
  setAudioTracks,
  setCurrentProject
}) => {
  const location = useLocation();

  /**
   * Restore in-memory state from sessionStorage on mount
   * SessionStorage is ALWAYS the source of truth (most recent in-memory changes)
   * Only load from backend if sessionStorage is empty
   */
  useEffect(() => {
    const savedState = sessionStorage.getItem('designEditor_inMemoryState');
    if (!savedState) {
      console.log('📭 No sessionStorage found - will load from backend if project ID in URL');
      return;
    }

    try {
      const parsed = JSON.parse(savedState);
      const age = Date.now() - (parsed.timestamp || 0);

      // Always restore sessionStorage if less than 1 hour old (it's the most recent state)
      if (age < 60 * 60 * 1000) {
        console.log('🔄 Restoring in-memory state from sessionStorage (source of truth):', {
          pages: parsed.pages?.length || 0,
          uploadedAudio: parsed.uploadedAudio?.length || 0,
          uploadedImage: parsed.uploadedImage?.length || 0,
          uploadedVideo: parsed.uploadedVideo?.length || 0,
          audioTracks: parsed.audioTracks?.length || 0,
          age: `${Math.round(age / 1000)}s ago`
        });

        if (parsed.pages) setPages(parsed.pages);
        if (parsed.uploadedAudio) setUploadedAudio(parsed.uploadedAudio);
        if (parsed.uploadedImage) setUploadedImage(parsed.uploadedImage);
        if (parsed.uploadedVideo) setUploadedVideo(parsed.uploadedVideo);
        if (parsed.audioTracks) setAudioTracks(parsed.audioTracks);
        if (parsed.currentProject) setCurrentProject(parsed.currentProject);
      } else {
        console.log('⏰ Saved state too old (>1 hour), clearing and will load from backend');
        sessionStorage.removeItem('designEditor_inMemoryState');
      }
    } catch (error) {
      console.error('❌ Failed to restore in-memory state:', error);
      sessionStorage.removeItem('designEditor_inMemoryState');
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Save in-memory state to sessionStorage whenever it changes
   */
  useEffect(() => {
    const stateToSave = {
      pages,
      uploadedAudio,
      uploadedImage,
      uploadedVideo,
      audioTracks,
      currentProject,
      timestamp: Date.now()
    };
    
    sessionStorage.setItem('designEditor_inMemoryState', JSON.stringify(stateToSave));
    console.log('💾 Auto-saved in-memory state to sessionStorage');
  }, [pages, uploadedAudio, uploadedImage, uploadedVideo, audioTracks, currentProject]);
};

