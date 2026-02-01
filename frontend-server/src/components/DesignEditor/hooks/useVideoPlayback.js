import { useState, useRef, useEffect } from 'react';

/**
 * Custom hook for managing video playback on canvas
 */
export const useVideoPlayback = (pages, currentPageIndex) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const videoElementRefs = useRef({});

  /**
   * Get all video elements on current page
   */
  const getVideoElements = () => {
    if (!pages[currentPageIndex]) return [];
    return pages[currentPageIndex].elements.filter(el => el.type === 'video');
  };

  /**
   * Play all videos on current page
   */
  const handlePlay = () => {
    console.log('▶️ Playing videos on page', currentPageIndex);
    const videoElements = getVideoElements();
    
    videoElements.forEach(videoEl => {
      const videoRef = videoElementRefs.current[videoEl.id];
      if (videoRef) {
        videoRef.play().catch(err => {
          console.error('Failed to play video:', err);
        });
      }
    });
    
    setIsPlaying(true);
  };

  /**
   * Pause all videos on current page
   */
  const handlePause = () => {
    console.log('⏸️ Pausing videos on page', currentPageIndex);
    const videoElements = getVideoElements();
    
    videoElements.forEach(videoEl => {
      const videoRef = videoElementRefs.current[videoEl.id];
      if (videoRef) {
        videoRef.pause();
      }
    });
    
    setIsPlaying(false);
  };

  /**
   * Toggle play/pause
   */
  const handlePlayPause = () => {
    if (isPlaying) {
      handlePause();
    } else {
      handlePlay();
    }
  };

  /**
   * Seek to specific time
   */
  const handleSeek = (time) => {
    console.log('⏩ Seeking to', time);

    // Validate time is a finite number
    if (!isFinite(time) || time < 0) {
      console.warn('⚠️ Invalid seek time:', time);
      return;
    }

    const videoElements = getVideoElements();

    videoElements.forEach(videoEl => {
      const videoRef = videoElementRefs.current[videoEl.id];
      if (videoRef && isFinite(videoRef.duration)) {
        // Only set currentTime if video metadata is loaded
        videoRef.currentTime = Math.min(time, videoRef.duration);
      }
    });

    setCurrentTime(time);
  };

  /**
   * Stop all videos
   */
  const handleStop = () => {
    handlePause();
    handleSeek(0);
  };

  /**
   * Register a video element ref
   */
  const registerVideoRef = (elementId, ref) => {
    videoElementRefs.current[elementId] = ref;
  };

  /**
   * Unregister a video element ref
   */
  const unregisterVideoRef = (elementId) => {
    delete videoElementRefs.current[elementId];
  };

  /**
   * Pause videos when page changes
   */
  useEffect(() => {
    handlePause();
  }, [currentPageIndex]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    // State
    isPlaying,
    currentTime,
    videoElementRefs,
    
    // Actions
    handlePlay,
    handlePause,
    handlePlayPause,
    handleSeek,
    handleStop,
    registerVideoRef,
    unregisterVideoRef,
    
    // Setters
    setIsPlaying,
    setCurrentTime
  };
};

