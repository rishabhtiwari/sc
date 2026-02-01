import { useState } from 'react';

/**
 * Custom hook for managing media uploads (audio, image, video)
 */
export const useMediaManagement = () => {
  const [uploadedAudio, setUploadedAudio] = useState([]);
  const [uploadedImage, setUploadedImage] = useState([]);
  const [uploadedVideo, setUploadedVideo] = useState([]);

  /**
   * Add audio to media list
   */
  const handleAddAudio = (audioData) => {
    setUploadedAudio(prev => {
      // Check if already exists
      const exists = prev.some(a => a.url === audioData.url || a.audio_url === audioData.audio_url);
      if (exists) {
        console.log('🎵 Audio already in list, skipping');
        return prev;
      }
      
      console.log('🎵 Adding audio to media list:', audioData.title);
      return [...prev, audioData];
    });
  };

  /**
   * Add image to media list
   */
  const handleAddImage = (imageData) => {
    setUploadedImage(prev => {
      // Check if already exists
      const exists = prev.some(i => i.url === imageData.url);
      if (exists) {
        console.log('🖼️ Image already in list, skipping');
        return prev;
      }
      
      console.log('🖼️ Adding image to media list:', imageData.name);
      return [...prev, imageData];
    });
  };

  /**
   * Add video to media list
   */
  const handleAddVideo = (videoData) => {
    setUploadedVideo(prev => {
      // Check if already exists
      const exists = prev.some(v => v.url === videoData.url);
      if (exists) {
        console.log('🎬 Video already in list, skipping');
        return prev;
      }
      
      console.log('🎬 Adding video to media list:', videoData.name);
      return [...prev, videoData];
    });
  };

  /**
   * Delete audio from media list
   */
  const handleDeleteAudio = (audioId) => {
    setUploadedAudio(prev => prev.filter(a => a.id !== audioId && a.audio_id !== audioId));
  };

  /**
   * Delete image from media list
   */
  const handleDeleteImage = (imageId) => {
    setUploadedImage(prev => prev.filter(i => i.id !== imageId && i.image_id !== imageId));
  };

  /**
   * Delete video from media list
   */
  const handleDeleteVideo = (videoId) => {
    setUploadedVideo(prev => prev.filter(v => v.id !== videoId && v.video_id !== videoId));
  };

  /**
   * Clear all media
   */
  const handleClearAllMedia = () => {
    setUploadedAudio([]);
    setUploadedImage([]);
    setUploadedVideo([]);
  };

  return {
    // State
    uploadedAudio,
    uploadedImage,
    uploadedVideo,
    
    // Setters (for external updates)
    setUploadedAudio,
    setUploadedImage,
    setUploadedVideo,
    
    // Actions
    handleAddAudio,
    handleAddImage,
    handleAddVideo,
    handleDeleteAudio,
    handleDeleteImage,
    handleDeleteVideo,
    handleClearAllMedia
  };
};

