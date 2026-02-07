import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useToast } from '../../hooks/useToast';

// Custom hooks
import {
  useSessionStorage,
  useElementManagement,
  usePageManagement,
  useMediaManagement,
  useProjectState,
  useVideoPlayback
} from './hooks';
import { fetchAuthenticatedAudio } from '../../hooks/useAuthenticatedAudio';

// Utils
import { computeVideoTracks } from './utils';

// Components
import Canvas from './Canvas/Canvas';
import Sidebar from './Sidebar/Sidebar';
import PropertiesPanel from './PropertiesPanel/PropertiesPanel';
import AudioTimelineRefactored from './AudioTimeline/AudioTimelineRefactored';
import ConfirmDialog from '../common/ConfirmDialog';
import ExportDialog from './ExportDialog/ExportDialog';
import ExportsListDialog from './ExportDialog/ExportsListDialog';

/**
 * DesignEditor - Main component (refactored)
 * Uses custom hooks to manage state and logic
 */
const DesignEditor = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();

  // Debug: Log when component mounts/unmounts
  useEffect(() => {
    console.log('🎨 DesignEditor mounted');
    return () => console.log('🎨 DesignEditor unmounted');
  }, []);

  // UI State - Restore selectedTool from navigation state, or default to 'text'
  const [selectedTool, setSelectedTool] = useState(location.state?.returnTool || 'text');
  const [zoom, setZoom] = useState(1);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, slideIndex: null });
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showExportsListDialog, setShowExportsListDialog] = useState(false);

  // Pages state (initialized with one default page)
  const [pages, setPages] = useState([{
    id: 'page-1',
    name: 'Page 1',
    elements: [],
    background: { type: 'solid', color: '#ffffff' },
    duration: 5,
    startTime: 0
  }]);

  // Audio tracks state
  const [audioTracks, setAudioTracks] = useState([]);

  // Loading state for audio/video assets
  const [loadingAssets, setLoadingAssets] = useState(new Set());
  const [assetsReady, setAssetsReady] = useState(false);

  // Project name editing state
  const [isEditingProjectName, setIsEditingProjectName] = useState(false);
  const [editedProjectName, setEditedProjectName] = useState('');

  // Page Management Hook
  const {
    currentPageIndex,
    currentPage,
    handleAddPage,
    handleAddMultiplePages,
    handleDeletePage,
    handleDuplicatePage,
    handleBackgroundChange,
    handlePageChange,
    handleNextPage,
    handlePreviousPage,
    setCurrentPageIndex
  } = usePageManagement(pages, setPages);

  // Media Management Hook
  const {
    uploadedAudio,
    uploadedImage,
    uploadedVideo,
    setUploadedAudio,
    setUploadedImage,
    setUploadedVideo,
    handleAddAudio,
    handleAddImage,
    handleAddVideo,
    handleDeleteAudio,
    handleDeleteImage,
    handleDeleteVideo
  } = useMediaManagement();

  // Element Management Hook
  const {
    selectedElement,
    handleAddElement,
    handleUpdateElement,
    handleDeleteElement: handleDeleteElementBase,
    handleSelectElement,
    handleDeselectElement
  } = useElementManagement(pages, setPages, currentPageIndex);

  /**
   * Wrapper for handleDeleteElement that also removes from media library
   * Only removes from media library if NO other instances exist on canvas
   */
  const handleDeleteElement = (elementId) => {
    // Find the element to get its type and URL
    let elementToDelete = null;
    pages.forEach(page => {
      const el = page.elements.find(e => e.id === elementId);
      if (el) {
        elementToDelete = el;
      }
    });

    // Delete from canvas
    handleDeleteElementBase(elementId);

    // Check if there are any other instances of this asset on the canvas
    // Only remove from media library if this was the LAST instance
    if (elementToDelete && (elementToDelete.type === 'image' || elementToDelete.type === 'video')) {
      const assetUrl = elementToDelete.src;

      // Count remaining instances of this asset across all pages (after deletion)
      // We need to use setTimeout to ensure the deletion has been processed
      setTimeout(() => {
        let remainingInstances = 0;
        pages.forEach(page => {
          page.elements.forEach(el => {
            if (el.id !== elementId && el.type === elementToDelete.type && el.src === assetUrl) {
              remainingInstances++;
            }
          });
        });

        console.log(`🔍 Remaining instances of ${elementToDelete.type} (${assetUrl}):`, remainingInstances);

        // Only remove from media library if no instances remain
        if (remainingInstances === 0) {
          console.log(`🗑️ No more instances, removing from media library`);
          if (elementToDelete.type === 'image') {
            setUploadedImage(prev => prev.filter(img => img.url !== assetUrl));
          } else if (elementToDelete.type === 'video') {
            setUploadedVideo(prev => prev.filter(vid => vid.url !== assetUrl));
          }
        } else {
          console.log(`✅ ${remainingInstances} instance(s) remain, keeping in media library`);
        }
      }, 0);
    }
  };

  // Project State Hook
  const {
    currentProject,
    isSaving,
    isLoading,
    setCurrentProject,
    handleSaveProject,
    handleLoadProject
  } = useProjectState({
    pages,
    audioTracks,
    uploadedAudio,
    uploadedImage,
    uploadedVideo,
    setPages,
    setAudioTracks,
    setUploadedAudio,
    setUploadedImage,
    setUploadedVideo
  });

  // Video Playback Hook
  const {
    isPlaying,
    currentTime,
    videoElementRefs,
    handlePlayPause,
    handleSeek,
    registerVideoRef,
    unregisterVideoRef,
    setIsPlaying,
    setCurrentTime
  } = useVideoPlayback(pages, currentPageIndex);

  // Delete Dialog States
  const [audioDeleteDialog, setAudioDeleteDialog] = useState({ isOpen: false, audioId: null, audioTitle: null, mediaId: null });
  const [videoDeleteDialog, setVideoDeleteDialog] = useState({ isOpen: false, videoId: null, videoTitle: null, mediaId: null });
  const [imageDeleteDialog, setImageDeleteDialog] = useState({ isOpen: false, imageElements: null, imageTitle: null, mediaId: null });

  // Properties Panel State (user can manually close/open)
  const [isPropertiesPanelOpen, setIsPropertiesPanelOpen] = useState(false);
  const [propertiesPanelWidth, setPropertiesPanelWidth] = useState(320); // Default 320px
  const [timelineHeight, setTimelineHeight] = useState(300); // Default 300px
  const [isResizingPropertiesPanel, setIsResizingPropertiesPanel] = useState(false);
  const [isResizingTimeline, setIsResizingTimeline] = useState(false);

  // Auto-open Properties Panel when element is selected
  useEffect(() => {
    if (selectedElement) {
      setIsPropertiesPanelOpen(true);
    }
  }, [selectedElement]);

  // Handle properties panel resize
  useEffect(() => {
    if (!isResizingPropertiesPanel) return;

    const handleMouseMove = (e) => {
      e.preventDefault();
      const newWidth = window.innerWidth - e.clientX;
      setPropertiesPanelWidth(Math.max(280, Math.min(600, newWidth)));
    };

    const handleMouseUp = () => {
      setIsResizingPropertiesPanel(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.body.style.cursor = 'ew-resize';
    document.body.style.userSelect = 'none';

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizingPropertiesPanel]);

  // Handle timeline resize
  useEffect(() => {
    if (!isResizingTimeline) return;

    let startY = null;
    let startHeight = timelineHeight;

    const handleMouseMove = (e) => {
      e.preventDefault();
      if (startY === null) {
        startY = e.clientY;
        return;
      }
      // Calculate delta: dragging UP (negative) should INCREASE height
      const deltaY = startY - e.clientY;
      const newHeight = startHeight + deltaY;
      setTimelineHeight(Math.max(200, Math.min(800, newHeight)));
    };

    const handleMouseUp = () => {
      setIsResizingTimeline(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.body.style.cursor = 'ns-resize';
    document.body.style.userSelect = 'none';

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizingTimeline, timelineHeight]);

  // Session Storage Hook (auto-save/restore)
  useSessionStorage({
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
  });

  // Compute video tracks from pages
  const videoTracks = useMemo(() => computeVideoTracks(pages), [pages]);

  // Track processed assets to prevent duplicate processing
  const processedAssetRef = useRef(null);

  // Audio refs for playback control
  const audioRefs = useRef({});

  /**
   * Handle adding asset from library (audio, image, video)
   */
  useEffect(() => {
    const addAsset = location.state?.addAsset;
    if (!addAsset) return;

    const assetKey = `${addAsset.type}-${addAsset.src || addAsset.url}`;

    // Check if we've already processed this asset
    if (processedAssetRef.current === assetKey) {
      console.log('⏭️ Asset already processed, skipping:', assetKey);
      return;
    }

    console.log('📥 Processing new asset from library:', addAsset);

    // Mark as processed
    processedAssetRef.current = assetKey;

    // Add to appropriate media list
    if (addAsset.type === 'audio') {
      console.log('🎵 Adding audio to media list only (not to timeline)');
      handleAddAudio({
        id: addAsset.libraryId || `media-${Date.now()}`,
        url: addAsset.src || addAsset.url || addAsset.audio_url,
        title: addAsset.name || addAsset.title || 'Audio',
        type: 'audio',
        duration: addAsset.duration || 0,
        libraryId: addAsset.libraryId,
        audio_id: addAsset.audio_id,
        assetId: addAsset.assetId
      });
    } else if (addAsset.type === 'image') {
      console.log('🖼️ Adding image to media list only (not to canvas)');
      handleAddImage({
        id: addAsset.libraryId || `media-${Date.now()}`,
        url: addAsset.src || addAsset.url,
        title: addAsset.name || addAsset.title || 'Image',
        type: 'image',
        libraryId: addAsset.libraryId
      });
    } else if (addAsset.type === 'video') {
      console.log('🎬 Adding video to media list only (not to canvas)');
      handleAddVideo({
        id: addAsset.libraryId || `media-${Date.now()}`,
        url: addAsset.src || addAsset.url,
        title: addAsset.name || addAsset.title || 'Video',
        type: 'video',
        duration: addAsset.duration || 0,
        libraryId: addAsset.libraryId
      });
    }
  }, [location.state]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Clear processed asset ref when navigating away from design editor
   */
  useEffect(() => {
    // Clear the ref when we navigate away from the design editor (to library, etc.)
    // This ensures that when we come back with a new asset, it will be processed
    const isLeavingEditor = !location.pathname.includes('/design-editor');
    if (isLeavingEditor && processedAssetRef.current) {
      console.log('🧹 Clearing processed asset ref (navigating away from editor)');
      processedAssetRef.current = null;
    }
  }, [location.pathname]);

  /**
   * Restore selected tool when returning from library
   */
  useEffect(() => {
    if (location.state?.returnTool && location.state.returnTool !== selectedTool) {
      console.log('🔧 Restoring selected tool:', location.state.returnTool);
      setSelectedTool(location.state.returnTool);
    }
  }, [location.state?.returnTool]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Handle audio track operations
   * @param {Object|File} audioFile - File object or audio metadata object with name, audio_id, etc.
   * @param {string} audioUrl - URL to the audio file
   */
  const handleAddAudioTrack = async (audioFile, audioUrl) => {
    console.log('🎬 handleAddAudioTrack called:', { audioFile, audioUrl });

    const trackId = `audio-${Date.now()}`;

    try {
      // Use the centralized authentication utility
      const processedUrl = await fetchAuthenticatedAudio(audioUrl);

      // Create audio element to get duration
      const audio = new Audio(processedUrl);
      console.log('🎬 Created audio element with ID:', trackId);

      audio.addEventListener('loadedmetadata', () => {
        console.log('🎬 Audio metadata loaded. Duration:', audio.duration);
        setAudioTracks(prevTracks => {
          // Calculate the end time of the last audio track
          let startTime = 0;
          if (prevTracks.length > 0) {
            // Find the maximum end time among all existing tracks
            const maxEndTime = Math.max(...prevTracks.map(track =>
              (track.startTime || 0) + (track.duration || 0)
            ));
            startTime = maxEndTime; // Position new audio at the end
          }

          const newTrack = {
            id: trackId,
            name: audioFile.name || audioFile.title || 'Audio Track',
            src: processedUrl, // Use the processed (authenticated) URL
            url: audioUrl, // Keep original URL for reference
            duration: audio.duration,
            startTime: startTime,
            volume: 100,
            fadeIn: 0,
            fadeOut: 0,
            type: audioFile.name?.toLowerCase().includes('voiceover')
              ? 'voiceover'
              : audioFile.name?.toLowerCase().includes('sfx')
              ? 'sfx'
              : 'music', // Auto-detect type from filename
            // Preserve audio_id/libraryId if it exists (from audio library)
            assetId: audioFile.audio_id || audioFile.libraryId || audioFile.assetId,
            libraryId: audioFile.audio_id || audioFile.libraryId
          };

          const updatedTracks = [...prevTracks, newTrack];
          console.log('✅ Audio track added:', newTrack, 'Start time:', startTime, 'Duration:', audio.duration);
          return updatedTracks;
        });

        // Set initial volume
        audio.volume = 1.0; // 100%
        showToast('Audio added to timeline', 'success');
      });

      audio.addEventListener('error', (e) => {
        console.error('❌ Audio loading error:', e);
        console.error('❌ Audio error details:', {
          error: audio.error,
          code: audio.error?.code,
          message: audio.error?.message,
          src: audio.src
        });
        showToast('Failed to load audio', 'error');
      });
    } catch (error) {
      console.error('❌ Error in handleAddAudioTrack:', error);
      showToast('Failed to add audio to timeline', 'error');
    }
  };

  /**
   * Handle audio track update (drag, stretch, properties)
   */
  const handleAudioUpdate = (trackId, updates) => {
    setAudioTracks(prevTracks =>
      prevTracks.map(track =>
        track.id === trackId ? { ...track, ...updates } : track
      )
    );
  };

  /**
   * Handle audio track delete
   */
  const handleAudioDelete = (trackId) => {
    // Find the track to get its URL
    const track = audioTracks.find(t => t.id === trackId);

    // Remove from timeline
    setAudioTracks(prevTracks => prevTracks.filter(track => track.id !== trackId));

    // Also remove from media library if it exists there
    const trackUrl = track?.src || track?.url;
    if (track && trackUrl) {
      setUploadedAudio(prev => prev.filter(audio => audio.url !== trackUrl));
    }
  };

  /**
   * Handle video track update - Updates the video element in the page
   */
  const handleVideoUpdate = (trackId, updates) => {
    console.log('🎬 Updating video element:', trackId, updates);
    setPages(prevPages => {
      // First pass: Update the video element and page duration
      const updatedPages = prevPages.map(page => {
        // Check if this page contains the video being updated
        const hasVideo = page.elements.some(el => el.id === trackId);

        if (hasVideo && updates.duration !== undefined) {
          // If video duration is being updated, also update page duration
          const updatedElements = page.elements.map(el =>
            el.id === trackId ? { ...el, ...updates } : el
          );

          // Find the maximum duration among all video elements on this page
          const maxVideoDuration = Math.max(
            ...updatedElements
              .filter(el => el.type === 'video')
              .map(el => el.duration || 0),
            5 // Minimum page duration
          );

          console.log('📄 Updating page duration to match video:', maxVideoDuration);

          return {
            ...page,
            elements: updatedElements,
            duration: maxVideoDuration
          };
        }

        // No duration update needed, just update the element
        return {
          ...page,
          elements: page.elements.map(el =>
            el.id === trackId ? { ...el, ...updates } : el
          )
        };
      });

      // Second pass: Recalculate startTime for all slides to prevent overlap
      let accumulatedTime = 0;
      const repositionedPages = updatedPages.map((page, index) => {
        const pageWithStartTime = {
          ...page,
          startTime: accumulatedTime
        };
        accumulatedTime += page.duration || 5;
        return pageWithStartTime;
      });

      console.log('📐 Repositioned slides to prevent overlap');
      return repositionedPages;
    });
  };

  /**
   * Handle video track delete
   */
  const handleVideoDelete = (trackId) => {
    // Find the video element to get its URL
    let videoUrl = null;
    pages.forEach(page => {
      const videoEl = page.elements.find(el => el.id === trackId && el.type === 'video');
      if (videoEl) {
        videoUrl = videoEl.src;
      }
    });

    // Remove from canvas
    setPages(prevPages => prevPages.map(page => ({
      ...page,
      elements: page.elements.filter(el => el.id !== trackId)
    })));

    // Also remove from media library if it exists there
    if (videoUrl) {
      setUploadedVideo(prev => prev.filter(video => video.url !== videoUrl));
    }
  };

  /**
   * Handle slide duration update
   */
  const handleSlideUpdate = (slideIndex, updates) => {
    setPages(prevPages => {
      // First pass: Update the specific slide
      const updatedPages = prevPages.map((page, index) =>
        index === slideIndex ? { ...page, ...updates } : page
      );

      // Second pass: Recalculate startTime for all slides to prevent overlap
      let accumulatedTime = 0;
      const repositionedPages = updatedPages.map((page) => {
        const pageWithStartTime = {
          ...page,
          startTime: accumulatedTime
        };
        accumulatedTime += page.duration || 5;
        return pageWithStartTime;
      });

      console.log('📐 Repositioned slides after duration update');
      return repositionedPages;
    });
  };

  const handleAudioSelect = (audioId) => {
    console.log('🎵 Audio selected:', audioId);
    const track = audioTracks.find(t => t.id === audioId);
    if (track) {
      handleSelectElement({ ...track, type: 'audio' });
    }
  };

  const handleVideoSelect = (videoId) => {
    console.log('🎬 Video selected:', videoId);
    const videoElement = currentPage?.elements.find(el => el.id === videoId);
    if (videoElement) {
      handleSelectElement(videoElement);
    }
  };

  const handleSlideSelect = (slideIndex) => {
    console.log('📊 Slide selected:', slideIndex);
    const slide = pages[slideIndex];
    if (slide) {
      // Create a slide element object for the properties panel
      const slideElement = {
        ...slide,
        type: 'slide',
        id: slide.id || `slide-${slideIndex}`,
        name: slide.name || `Slide ${slideIndex + 1}`,
        slideIndex // Store the index for updates
      };
      handleSelectElement(slideElement);
    }
  };

  /**
   * Apply fade in/out effect to audio element
   */
  const applyFadeEffect = (audio, track, currentTrackTime) => {
    if (!audio || !track) return;

    const baseVolume = (track.volume || 100) / 100;
    const fadeIn = track.fadeIn || 0;
    const fadeOut = track.fadeOut || 0;
    const duration = track.duration || 0;

    let volumeMultiplier = 1;

    // Apply fade in
    if (fadeIn > 0 && currentTrackTime < fadeIn) {
      volumeMultiplier = currentTrackTime / fadeIn;
    }

    // Apply fade out
    if (fadeOut > 0 && currentTrackTime > duration - fadeOut) {
      volumeMultiplier = (duration - currentTrackTime) / fadeOut;
    }

    // Apply the calculated volume
    audio.volume = baseVolume * Math.max(0, Math.min(1, volumeMultiplier));
  };

  /**
   * Check if all assets are ready for playback
   */
  useEffect(() => {
    setAssetsReady(loadingAssets.size === 0);
  }, [loadingAssets]);

  /**
   * Handle play/pause for timeline
   */
  const handlePlay = () => {
    // Check if assets are still loading
    if (loadingAssets.size > 0) {
      console.log('⏳ Assets still loading, cannot play yet');
      showToast('Please wait, loading media assets...', 'info');
      return;
    }

    console.log('▶️ Play button clicked');

    // First, pause all currently playing audio to prevent overlap
    audioTracks.forEach(track => {
      const audio = audioRefs.current[track.id];
      if (audio && !audio.paused) {
        audio.pause();
      }
    });

    // Pause all video elements
    pages.forEach(page => {
      page.elements.forEach(element => {
        if (element.type === 'video') {
          const videoRef = videoElementRefs.current[element.id];
          if (videoRef && !videoRef.paused) {
            videoRef.pause();
          }
        }
      });
    });

    // Now start playback
    setIsPlaying(true);
  };

  const handlePause = () => {
    console.log('⏸️ Pause button clicked');
    setIsPlaying(false);

    // Pause all audio elements
    audioTracks.forEach(track => {
      const audio = audioRefs.current[track.id];
      if (audio && !audio.paused) {
        console.log(`⏸️ Pausing audio ${track.id}`);
        audio.pause();
      }
    });

    // Pause all video elements
    pages.forEach(page => {
      page.elements.forEach(element => {
        if (element.type === 'video') {
          const videoRef = videoElementRefs.current[element.id];
          if (videoRef && !videoRef.paused) {
            console.log(`⏸️ Pausing video ${element.id}`);
            videoRef.pause();
          }
        }
      });
    });
  };

  /**
   * Update playhead position during playback
   */
  useEffect(() => {
    let animationFrame;

    if (isPlaying) {
      console.log('🎬 Playback loop started');
      const updatePlayhead = () => {
        setCurrentTime(prevTime => {
          const newTime = prevTime + 0.016; // ~60fps

          // Calculate total duration
          const totalDuration = (() => {
            const audioDuration = audioTracks.length > 0
              ? Math.max(...audioTracks.map(track => (track.startTime || 0) + (track.duration || 0)))
              : 0;
            const slidesDuration = pages.length > 0
              ? pages.reduce((sum, s) => sum + (s.duration || 5), 0)
              : 0;
            return Math.max(audioDuration, slidesDuration, 30);
          })();

          // Stop playback when reaching the end
          if (newTime >= totalDuration) {
            setIsPlaying(false);
            // Pause all audio
            audioTracks.forEach(track => {
              const audio = audioRefs.current[track.id];
              if (audio && !audio.paused) {
                audio.pause();
              }
            });
            return totalDuration;
          }

          // Update audio elements
          audioTracks.forEach(track => {
            const audio = audioRefs.current[track.id];
            if (audio) {
              const trackTime = newTime - track.startTime;
              const originalDuration = audio.duration; // Original audio file duration
              const displayDuration = track.duration; // Stretched/trimmed duration on timeline

              // Skip if audio metadata not loaded yet (duration is NaN)
              if (!isFinite(originalDuration) || originalDuration <= 0) {
                return;
              }

              if (trackTime >= 0 && trackTime <= displayDuration) {
                if (audio.paused) {
                  // Calculate actual audio position when starting playback
                  const actualAudioTime = trackTime % originalDuration;
                  // Validate the calculated time before setting
                  if (isFinite(actualAudioTime) && actualAudioTime >= 0) {
                    console.log(`🎵 Starting audio track ${track.id} at ${actualAudioTime.toFixed(2)}s`);
                    audio.currentTime = actualAudioTime;
                    audio.play().catch(err => console.error('Audio play error:', err));
                  }
                } else {
                  // Check if audio needs to loop (reached end of original duration)
                  if (audio.currentTime >= originalDuration - 0.05) {
                    audio.currentTime = 0; // Loop back to start
                  }
                }

                // Apply fade in/out effect continuously during playback
                applyFadeEffect(audio, track, trackTime);
              } else if (!audio.paused) {
                audio.pause();
              }
            }
          });

          // Update video elements on canvas
          pages.forEach((page, pageIndex) => {
            page.elements.forEach(element => {
              if (element.type === 'video') {
                const videoRef = videoElementRefs.current[element.id];

                // Debug logging
                if (!videoRef) {
                  console.log(`⚠️ Video ref not found for element ${element.id}`);
                  console.log('Available video refs:', Object.keys(videoElementRefs.current));
                  return;
                }

                if (!isFinite(videoRef.duration) || videoRef.duration <= 0) {
                  console.log(`⚠️ Video ${element.id} metadata not loaded yet (duration: ${videoRef.duration})`);
                  return;
                }

                // Calculate if this video should be playing based on page timing
                // Use explicit startTime if available, otherwise calculate sequentially
                const pageStartTime = page.startTime !== undefined
                  ? page.startTime
                  : pages.slice(0, pageIndex).reduce((sum, p) => sum + (p.duration || 5), 0);
                const pageEndTime = pageStartTime + (page.duration || 5);

                console.log(`🎬 Video ${element.id}: currentTime=${newTime.toFixed(2)}s, pageStart=${pageStartTime.toFixed(2)}s, pageEnd=${pageEndTime.toFixed(2)}s, pageIndex=${pageIndex}, currentPageIndex=${currentPageIndex}`);

                if (newTime >= pageStartTime && newTime < pageEndTime) {
                  // Video should be playing
                  const videoTime = newTime - pageStartTime;

                  // Get the original (natural) duration and stretched duration
                  const originalDuration = element.originalDuration || videoRef.duration;
                  const stretchedDuration = element.duration || videoRef.duration;

                  // Calculate looped video time if video is stretched beyond its natural duration
                  // If stretched to 20s and video is 4s, it should loop 5 times
                  const loopedVideoTime = videoTime % originalDuration;

                  if (videoRef.paused) {
                    // Start playing the video
                    if (isFinite(loopedVideoTime) && loopedVideoTime >= 0) {
                      console.log(`🎬 Starting video ${element.id} at ${loopedVideoTime.toFixed(2)}s (looped from ${videoTime.toFixed(2)}s, stretched: ${stretchedDuration.toFixed(2)}s, original: ${originalDuration.toFixed(2)}s)`);
                      videoRef.currentTime = loopedVideoTime;
                      videoRef.play().catch(err => console.error('Video play error:', err));
                    }
                  } else {
                    // Sync video time if it drifts too much
                    const drift = Math.abs(videoRef.currentTime - loopedVideoTime);
                    if (drift > 0.5 && isFinite(loopedVideoTime)) {
                      console.log(`🔄 Syncing video ${element.id} time: ${loopedVideoTime.toFixed(2)}s (was ${videoRef.currentTime.toFixed(2)}s)`);
                      videoRef.currentTime = loopedVideoTime;
                    }
                  }
                } else if (!videoRef.paused) {
                  // Video should not be playing
                  console.log(`🎬 Pausing video ${element.id} (outside page time range)`);
                  videoRef.pause();
                }
              }
            });
          });

          return newTime;
        });

        animationFrame = requestAnimationFrame(updatePlayhead);
      };

      animationFrame = requestAnimationFrame(updatePlayhead);
    }

    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [isPlaying, audioTracks, pages]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Create Audio elements for audio tracks
   */
  useEffect(() => {
    const createAudioElements = async () => {
      // Track which assets are loading
      const loadingSet = new Set();

      for (const track of audioTracks) {
        const audioUrl = track.src || track.url; // Support both 'src' and 'url' properties
        if (!audioRefs.current[track.id] && audioUrl) {
          console.log(`🎵 Creating audio element for track: ${track.id}, URL: ${audioUrl?.substring(0, 50)}`);

          // Mark as loading
          loadingSet.add(track.id);
          setLoadingAssets(prev => new Set([...prev, track.id]));

          try {
            // Use the centralized authentication utility
            const processedUrl = await fetchAuthenticatedAudio(audioUrl);
            console.log(`✅ Processed audio URL for track ${track.id}`);

            const audio = new Audio(processedUrl);
            audio.volume = (track.volume || 100) / 100;
            audio.loop = false;

            // Add loadedmetadata listener to track when audio is ready
            audio.addEventListener('loadedmetadata', () => {
              console.log(`✅ Audio metadata loaded for ${track.id}`);
              setLoadingAssets(prev => {
                const newSet = new Set(prev);
                newSet.delete(track.id);
                return newSet;
              });
            });

            // Add event listeners to sync audio state with React state
            audio.addEventListener('ended', () => {
              console.log(`🎵 Audio track ${track.id} ended`);
              // Check if all audio tracks have ended
              const allAudioEnded = audioTracks.every(t => {
                const a = audioRefs.current[t.id];
                return !a || a.ended || a.paused;
              });
              if (allAudioEnded) {
                console.log('⏹️ All audio ended, stopping playback');
                setIsPlaying(false);
              }
            });

            audio.addEventListener('pause', () => {
              console.log(`⏸️ Audio track ${track.id} paused`);
            });

            audio.addEventListener('play', () => {
              console.log(`▶️ Audio track ${track.id} playing`);
            });

            audio.addEventListener('error', (e) => {
              console.error(`❌ Audio track ${track.id} error:`, e);
              setIsPlaying(false);
              // Remove from loading set on error
              setLoadingAssets(prev => {
                const newSet = new Set(prev);
                newSet.delete(track.id);
                return newSet;
              });
            });

            audioRefs.current[track.id] = audio;
          } catch (error) {
            console.error(`❌ Error creating audio element for ${track.id}:`, error);
            // Remove from loading set on error
            setLoadingAssets(prev => {
              const newSet = new Set(prev);
              newSet.delete(track.id);
              return newSet;
            });
          }
        }
      }
    };

    createAudioElements();

    // Cleanup removed tracks
    Object.keys(audioRefs.current).forEach(trackId => {
      if (!audioTracks.find(t => t.id === trackId)) {
        console.log(`🗑️ Removing audio element for track: ${trackId}`);
        const audio = audioRefs.current[trackId];
        if (audio) {
          audio.pause();
          audio.src = '';
          // Remove event listeners
          audio.removeEventListener('ended', () => {});
          audio.removeEventListener('pause', () => {});
          audio.removeEventListener('play', () => {});
          audio.removeEventListener('error', () => {});
        }
        delete audioRefs.current[trackId];
      }
    });
  }, [audioTracks]);

  /**
   * Auto-navigate to the slide that corresponds to current playhead position
   * Only during playback - don't auto-switch when user is editing
   */
  useEffect(() => {
    // Only auto-navigate during playback, not when editing
    if (!isPlaying || pages.length === 0) return;

    // Calculate which slide should be visible based on current time
    for (let i = 0; i < pages.length; i++) {
      const page = pages[i];
      // Use explicit startTime if available, otherwise calculate sequentially
      const pageStartTime = page.startTime !== undefined
        ? page.startTime
        : pages.slice(0, i).reduce((sum, p) => sum + (p.duration || 5), 0);
      const pageEndTime = pageStartTime + (page.duration || 5);

      if (currentTime >= pageStartTime && currentTime < pageEndTime) {
        if (currentPageIndex !== i) {
          console.log(`Auto-switching to slide ${i + 1} at time ${currentTime.toFixed(2)}s (page start: ${pageStartTime.toFixed(2)}s)`);
          setCurrentPageIndex(i);
        }
        break;
      }
    }
  }, [currentTime, pages, isPlaying]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAudioDeleteRequest = (audioId, audioTitle, mediaId) => {
    setAudioDeleteDialog({
      isOpen: true,
      audioId,
      audioTitle,
      mediaId
    });
  };

  const confirmAudioDelete = () => {
    const { audioId, mediaId } = audioDeleteDialog;

    // Find the media item to get its URL
    const mediaItem = uploadedAudio.find(audio => audio.id === mediaId);
    const mediaUrl = mediaItem?.url;

    // Remove from timeline - check by both ID and URL
    setAudioTracks(prev => prev.filter(track => {
      // Remove if ID matches OR URL matches
      if (audioId && track.id === audioId) return false;
      if (mediaUrl && track.url === mediaUrl) return false;
      return true;
    }));

    // Remove from media list (NOT from backend library - users must delete from library page)
    if (mediaId) {
      setUploadedAudio(prev => prev.filter(audio => audio.id !== mediaId));
    }

    setAudioDeleteDialog({ isOpen: false, audioId: null, audioTitle: null, mediaId: null });
    showToast('Audio removed from editor', 'success');
  };

  /**
   * Handle video delete request
   */
  const handleVideoDeleteRequest = (videoId, videoTitle, mediaId) => {
    setVideoDeleteDialog({
      isOpen: true,
      videoId,
      videoTitle,
      mediaId
    });
  };

  const confirmVideoDelete = () => {
    const { videoId, mediaId } = videoDeleteDialog;

    // Find the media item to get its URL
    const mediaItem = uploadedVideo.find(video => video.id === mediaId);
    const mediaUrl = mediaItem?.url;

    // Remove from canvas - check by both ID and URL
    setPages(prevPages => prevPages.map(page => ({
      ...page,
      elements: page.elements.filter(el => {
        // Remove if it's a video element AND (ID matches OR URL matches)
        if (el.type === 'video') {
          if (videoId && el.id === videoId) return false;
          if (mediaUrl && el.src === mediaUrl) return false;
        }
        return true;
      })
    })));

    // Remove from media list (NOT from backend library - users must delete from library page)
    if (mediaId) {
      setUploadedVideo(prev => prev.filter(video => video.id !== mediaId));
    }

    setVideoDeleteDialog({ isOpen: false, videoId: null, videoTitle: null, mediaId: null });
    showToast('Video removed from editor', 'success');
  };

  /**
   * Handle image delete request
   */
  const handleImageDeleteRequest = (imageUrl, imageTitle, mediaId) => {
    // Show confirmation dialog
    setImageDeleteDialog({
      isOpen: true,
      imageUrl,
      imageTitle,
      mediaId
    });
  };

  const confirmImageDelete = () => {
    const { imageUrl, mediaId } = imageDeleteDialog;

    // Find the media item to get its URL if not provided
    const mediaItem = uploadedImage.find(image => image.id === mediaId);
    const mediaUrl = imageUrl || mediaItem?.url;

    // Remove all instances from canvas - check by URL
    if (mediaUrl) {
      setPages(prevPages => prevPages.map(page => ({
        ...page,
        elements: page.elements.filter(el => {
          // Remove if it's an image element AND URL matches
          if (el.type === 'image' && el.src === mediaUrl) {
            return false;
          }
          return true;
        })
      })));
    }

    // Remove from media list (NOT from backend library - users must delete from library page)
    if (mediaId) {
      setUploadedImage(prev => prev.filter(image => image.id !== mediaId));
    }

    setImageDeleteDialog({ isOpen: false, imageUrl: null, imageTitle: null, mediaId: null });
    showToast('Image removed from editor', 'success');
  };

  /**
   * Handle save with toast notification
   */
  const handleSaveWithToast = async () => {
    try {
      await handleSaveProject();
      showToast('Project saved successfully', 'success');
    } catch (error) {
      showToast(`Failed to save project: ${error.message}`, 'error');
    }
  };

  /**
   * Handle create new project
   */
  const handleCreateNewProject = () => {
    // Reset to default state
    setPages([{
      id: 'page-1',
      name: 'Page 1',
      elements: [],
      background: { type: 'solid', color: '#ffffff' },
      duration: 5,
      startTime: 0
    }]);
    setCurrentPageIndex(0);
    setAudioTracks([]);

    // Create a new project with default name
    const defaultName = `Project ${new Date().toLocaleDateString()}`;
    setCurrentProject({
      name: defaultName,
      project_id: null // Will be assigned when saved
    });

    setIsEditingProjectName(false);
    setEditedProjectName('');
    showToast('New project created', 'success');
  };

  /**
   * Handle project name edit start
   */
  const handleStartEditingProjectName = () => {
    setEditedProjectName(currentProject?.name || '');
    setIsEditingProjectName(true);
  };

  /**
   * Handle project name save
   */
  const handleSaveProjectName = () => {
    if (editedProjectName.trim()) {
      setCurrentProject(prev => ({
        ...prev,
        name: editedProjectName.trim()
      }));
      setIsEditingProjectName(false);
      showToast('Project name updated', 'success');
    } else {
      setIsEditingProjectName(false);
    }
  };

  /**
   * Handle project name cancel
   */
  const handleCancelEditingProjectName = () => {
    setIsEditingProjectName(false);
    setEditedProjectName('');
  };

  return (
    <div className="flex h-full bg-gray-50 relative">
      {/* Sidebar */}
      <Sidebar
          selectedTool={selectedTool}
          onSelectTool={setSelectedTool}
          onAddElement={handleAddElement}
          onAddMultiplePages={handleAddMultiplePages}
          onAddAudioTrack={handleAddAudioTrack}
          currentBackground={currentPage?.background}
          onBackgroundChange={handleBackgroundChange}
          audioTracks={audioTracks}
          onAudioSelect={handleAudioSelect}
          onAudioDeleteRequest={handleAudioDeleteRequest}
          videoTracks={videoTracks}
          onVideoDeleteRequest={handleVideoDeleteRequest}
          onImageDeleteRequest={handleImageDeleteRequest}
          uploadedAudio={uploadedAudio}
          onUploadedAudioChange={setUploadedAudio}
          uploadedImage={uploadedImage}
          onUploadedImageChange={setUploadedImage}
          uploadedVideo={uploadedVideo}
          onUploadedVideoChange={setUploadedVideo}
          onOpenAudioLibrary={() => navigate('/audio-studio/library', {
            state: {
              fromEditor: true,
              returnPath: location.pathname + location.search,
              returnTool: selectedTool  // Preserve selected tool
            }
          })}
          onOpenImageLibrary={() => navigate('/asset-management/images', {
            state: {
              fromEditor: true,
              returnPath: location.pathname + location.search,
              returnTool: selectedTool  // Preserve selected tool
            }
          })}
          onOpenVideoLibrary={() => navigate('/asset-management/videos', {
            state: {
              fromEditor: true,
              returnPath: location.pathname + location.search,
              returnTool: selectedTool  // Preserve selected tool
            }
          })}
        />

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
        {/* Project Toolbar */}
        <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Create New Project */}
            <button
              onClick={handleCreateNewProject}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center gap-2 shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Project
            </button>

            {/* Save Project */}
            <button
              onClick={handleSaveWithToast}
              disabled={isSaving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center gap-2 shadow-sm"
            >
              {isSaving ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Saving...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                  </svg>
                  Save
                </>
              )}
            </button>

            {/* Load Project */}
            <button
              onClick={() => navigate('/asset-management/projects', { state: { fromEditor: true } })}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center gap-2 shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 2 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
              </svg>
              Load
            </button>

            {/* Export Project */}
            <button
              onClick={() => setShowExportDialog(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium text-sm flex items-center gap-2 shadow-sm"
              title={!currentProject?.project_id ? 'Save your project first to enable export' : 'Export project to video, audio, or JSON'}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export
              {!currentProject?.project_id && (
                <span className="ml-1 text-xs bg-yellow-500 text-white px-2 py-0.5 rounded">Save first</span>
              )}
            </button>

            {/* View Exports */}
            <button
              onClick={() => setShowExportsListDialog(true)}
              disabled={!currentProject?.exports || currentProject.exports.length === 0}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center gap-2 shadow-sm"
              title={currentProject?.exports?.length > 0 ? `View ${currentProject.exports.length} export(s)` : 'No exports yet'}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Exports {currentProject?.exports?.length > 0 && `(${currentProject.exports.length})`}
            </button>
          </div>

          {/* Project Name - Editable */}
          <div className="flex items-center gap-2">
            {isEditingProjectName ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={editedProjectName}
                  onChange={(e) => setEditedProjectName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSaveProjectName();
                    } else if (e.key === 'Escape') {
                      handleCancelEditingProjectName();
                    }
                  }}
                  className="px-3 py-1.5 border border-blue-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-medium"
                  placeholder="Enter project name"
                  autoFocus
                />
                <button
                  onClick={handleSaveProjectName}
                  className="p-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  title="Save name"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </button>
                <button
                  onClick={handleCancelEditingProjectName}
                  className="p-1.5 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                  title="Cancel"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Project:</span>{' '}
                  <span className="text-gray-900">
                    {currentProject?.name || 'Untitled Project'}
                  </span>
                </div>
                {currentProject && (
                  <button
                    onClick={handleStartEditingProjectName}
                    className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                    title="Edit project name"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Page Navigation */}
        {pages.length > 1 && (
          <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-center">
            <div className="flex items-center gap-3">
              <button
                onClick={handlePreviousPage}
                disabled={currentPageIndex === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
              >
                ← Previous
              </button>
              <span className="text-sm font-semibold text-gray-900 px-3 py-2 bg-gray-100 rounded-lg">
                Slide {currentPageIndex + 1} / {pages.length}
              </span>
              <button
                onClick={handleNextPage}
                disabled={currentPageIndex === pages.length - 1}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
              >
                Next →
              </button>
              <div className="flex items-center gap-2 ml-4 pl-4 border-l border-gray-300">
                <button
                  onClick={() => handleDuplicatePage(currentPageIndex)}
                  className="w-8 h-8 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center text-base shadow-sm"
                  title="Duplicate current slide"
                >
                  +
                </button>
                <button
                  onClick={() => setDeleteDialog({ isOpen: true, slideIndex: currentPageIndex })}
                  className="w-8 h-8 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center text-base shadow-sm"
                  title="Delete current slide"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Canvas */}
        <Canvas
          elements={currentPage?.elements || []}
          selectedElement={selectedElement}
          onSelectElement={handleSelectElement}
          onUpdateElement={handleUpdateElement}
          onDeleteElement={handleDeleteElement}
          background={currentPage?.background}
          registerVideoRef={registerVideoRef}
          unregisterVideoRef={unregisterVideoRef}
        />

        {/* Audio Timeline with Resize Handle */}
        {(audioTracks.length > 0 || videoTracks.length > 0) && (
          <div
            className="relative border-t border-gray-200"
            style={{ height: `${timelineHeight}px` }}
          >
            {/* Resize Handle - Larger hit area */}
            <div
              className="absolute top-0 left-0 right-0 h-2 cursor-ns-resize hover:bg-blue-100 transition-colors z-50 group flex items-center justify-center"
              onMouseDown={(e) => {
                e.preventDefault();
                setIsResizingTimeline(true);
              }}
              title="Drag to resize timeline"
            >
              <div className="w-16 h-1 bg-gray-400 group-hover:bg-blue-500 rounded-full transition-colors"></div>
            </div>

            <div className="h-full pt-2 flex flex-col">
              <AudioTimelineRefactored
                audioTracks={audioTracks}
                videoTracks={videoTracks}
                slides={pages}
                currentTime={currentTime}
                isPlaying={isPlaying}
                loadingAssets={loadingAssets}
                selectedAudioId={selectedElement?.type === 'audio' ? selectedElement.id : null}
                selectedVideoId={selectedElement?.type === 'video' ? selectedElement.id : null}
                selectedSlideIndex={selectedElement?.type === 'slide' ? selectedElement.slideIndex : null}
                onAudioUpdate={handleAudioUpdate}
                onAudioDelete={handleAudioDelete}
                onAudioSelect={handleAudioSelect}
                onVideoUpdate={handleVideoUpdate}
                onVideoDelete={handleVideoDelete}
                onVideoSelect={handleVideoSelect}
                onSlideUpdate={handleSlideUpdate}
                onSlideSelect={handleSlideSelect}
                onSeek={handleSeek}
                onPlay={handlePlay}
                onPause={handlePause}
              />
            </div>
          </div>
        )}
      </div>

      {/* Properties Panel with Resize Handle - Absolutely positioned to extend full height */}
      {isPropertiesPanelOpen && (
        <div
          className="absolute top-0 right-0 bottom-0 bg-gray-50 border-l border-gray-200 flex flex-col shadow-lg z-40"
          style={{ width: `${propertiesPanelWidth}px` }}
        >
          {/* Resize Handle - Larger hit area */}
          <div
            className="absolute top-0 left-0 bottom-0 w-2 cursor-ew-resize hover:bg-blue-100 transition-colors z-50 group flex items-center justify-center"
            onMouseDown={(e) => {
              e.preventDefault();
              setIsResizingPropertiesPanel(true);
            }}
            title="Drag to resize properties panel"
          >
            <div className="h-16 w-1 bg-gray-400 group-hover:bg-blue-500 rounded-full transition-colors"></div>
          </div>

          <div className="pl-2 flex-1 flex flex-col h-full overflow-hidden">
            <PropertiesPanel
            element={selectedElement}
            onUpdate={(updates) => {
              if (selectedElement?.type === 'slide') {
                // Handle slide updates
                handleSlideUpdate(selectedElement.slideIndex, updates);
              } else if (selectedElement?.type === 'audio') {
                // Handle audio track updates
                handleAudioUpdate(selectedElement.id, updates);
              } else {
                // Handle regular element updates
                handleUpdateElement(selectedElement.id, updates);
              }
            }}
            onDelete={() => {
              if (selectedElement?.type === 'audio') {
                handleAudioDelete(selectedElement.id);
              } else {
                handleDeleteElement(selectedElement.id);
              }
            }}
            onClose={() => setIsPropertiesPanelOpen(false)}
          />
          </div>
        </div>
      )}

      {/* Delete Slide Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, slideIndex: null })}
        onConfirm={() => {
          const newPages = pages.filter((_, index) => index !== deleteDialog.slideIndex);
          if (newPages.length > 0) {
            setPages(newPages);
            setCurrentPageIndex(Math.max(0, deleteDialog.slideIndex - 1));
          }
          setDeleteDialog({ isOpen: false, slideIndex: null });
        }}
        title="Delete Slide"
        description="This action cannot be undone"
        message={`Are you sure you want to delete slide ${deleteDialog.slideIndex + 1}?`}
        warningMessage="This will permanently delete the slide and all its content."
        confirmText="Delete Slide"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Delete Audio Confirmation Dialog */}
      <ConfirmDialog
        isOpen={audioDeleteDialog.isOpen}
        onClose={() => setAudioDeleteDialog({ isOpen: false, audioId: null, audioTitle: null, mediaId: null })}
        onConfirm={confirmAudioDelete}
        title="Remove Audio"
        message={`Are you sure you want to remove "${audioDeleteDialog.audioTitle}" from the editor?`}
        warningMessage="This will remove the audio from the timeline and media list. To permanently delete from the library, go to the Audio Library page."
        confirmText="Remove"
        cancelText="Cancel"
        variant="danger"
      />

      <ConfirmDialog
        isOpen={videoDeleteDialog.isOpen}
        onClose={() => setVideoDeleteDialog({ isOpen: false, videoId: null, videoTitle: null, mediaId: null })}
        onConfirm={confirmVideoDelete}
        title="Remove Video"
        message={`Are you sure you want to remove "${videoDeleteDialog.videoTitle}" from the editor?`}
        warningMessage="This will remove the video from the canvas and media list. To permanently delete from the library, go to the Video Library page."
        confirmText="Remove"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Delete Image Confirmation Dialog */}
      <ConfirmDialog
        isOpen={imageDeleteDialog.isOpen}
        onClose={() => setImageDeleteDialog({ isOpen: false, imageElements: null, imageTitle: null, mediaId: null })}
        onConfirm={confirmImageDelete}
        title="Remove Image"
        message={`Are you sure you want to remove "${imageDeleteDialog.imageTitle}" from the editor?`}
        warningMessage={
          imageDeleteDialog.imageElements && imageDeleteDialog.imageElements.length > 0
            ? `This image is used in ${imageDeleteDialog.imageElements.length} place(s) on the canvas. It will be removed from all locations and the media list. To permanently delete from the library, go to the Image Library page.`
            : "This will remove the image from the media list. To permanently delete from the library, go to the Image Library page."
        }
        confirmText="Remove"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-[100] flex items-center justify-center">
          <div className="bg-white rounded-lg p-8 shadow-2xl flex flex-col items-center gap-4">
            <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-lg font-medium text-gray-900">Loading project...</p>
            <p className="text-sm text-gray-500">Please wait while we load your project</p>
          </div>
        </div>
      )}

      {/* Export Dialog */}
      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        project={currentProject}
      />

      {/* Exports List Dialog */}
      <ExportsListDialog
        isOpen={showExportsListDialog}
        onClose={() => setShowExportsListDialog(false)}
        project={currentProject}
      />
    </div>
  );
};

export default DesignEditor;

