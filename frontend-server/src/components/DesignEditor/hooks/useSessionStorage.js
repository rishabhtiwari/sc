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
   */
  useEffect(() => {
    const savedState = sessionStorage.getItem('designEditor_inMemoryState');
    if (!savedState) return;

    try {
      const parsed = JSON.parse(savedState);
      const age = Date.now() - (parsed.timestamp || 0);
      
      // Only restore if less than 1 hour old and not loading a project from URL
      const projectIdFromUrl = new URLSearchParams(location.search).get('project');
      
      if (age < 60 * 60 * 1000 && !projectIdFromUrl) {
        console.log('🔄 Restoring in-memory state from sessionStorage:', {
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
      } else if (projectIdFromUrl) {
        console.log('⏭️ Skipping sessionStorage restore - loading project from URL:', projectIdFromUrl);
      } else {
        console.log('⏰ Saved state too old, ignoring');
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

