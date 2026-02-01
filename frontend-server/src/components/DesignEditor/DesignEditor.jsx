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

// Utils
import { computeVideoTracks } from './utils';

// Components
import Canvas from './Canvas/Canvas';
import Sidebar from './Sidebar/Sidebar';
import PropertiesPanel from './PropertiesPanel/PropertiesPanel';
import AudioTimelineRefactored from './AudioTimeline/AudioTimelineRefactored';
import ConfirmDialog from '../common/ConfirmDialog';

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

  // UI State - Default to 'text' tool selected (sidebar open)
  const [selectedTool, setSelectedTool] = useState('text');
  const [zoom, setZoom] = useState(1);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, slideIndex: null });

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

    // Also remove from media library if it's an image or video
    if (elementToDelete) {
      if (elementToDelete.type === 'image' && elementToDelete.src) {
        setUploadedImage(prev => prev.filter(img => img.url !== elementToDelete.src));
      } else if (elementToDelete.type === 'video' && elementToDelete.src) {
        setUploadedVideo(prev => prev.filter(vid => vid.url !== elementToDelete.src));
      }
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

  // Auto-open Properties Panel when element is selected
  useEffect(() => {
    if (selectedElement) {
      setIsPropertiesPanelOpen(true);
    }
  }, [selectedElement]);

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
        url: addAsset.src || addAsset.url,
        title: addAsset.name || addAsset.title || 'Audio',
        type: 'audio',
        duration: addAsset.duration || 0,
        libraryId: addAsset.libraryId
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
  }, [location.state?.addAsset]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Clear processed asset ref when location changes
   */
  useEffect(() => {
    if (!location.state?.addAsset && processedAssetRef.current) {
      console.log('🧹 Clearing processed asset ref');
      processedAssetRef.current = null;
    }
  }, [location]);

  /**
   * Handle audio track operations
   */
  const handleAddAudioTrack = (audioFile, audioUrl) => {
    console.log('🎬 handleAddAudioTrack called:', { audioFile, audioUrl });

    // Create audio element to get duration
    const audio = new Audio(audioUrl);
    const trackId = `audio-${Date.now()}`;

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
          name: audioFile.name || 'Audio Track',
          src: audioUrl,
          duration: audio.duration,
          startTime: startTime,
          volume: 100,
          fadeIn: 0,
          fadeOut: 0,
          type: audioFile.name?.toLowerCase().includes('voiceover')
            ? 'voiceover'
            : audioFile.name?.toLowerCase().includes('sfx')
            ? 'sfx'
            : 'music' // Auto-detect type from filename
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
    });
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
    if (track && track.src) {
      setUploadedAudio(prev => prev.filter(audio => audio.url !== track.src));
    }
  };

  /**
   * Handle video track update - Updates the video element in the page
   */
  const handleVideoUpdate = (trackId, updates) => {
    console.log('🎬 Updating video element:', trackId, updates);
    setPages(prevPages => prevPages.map(page => ({
      ...page,
      elements: page.elements.map(el =>
        el.id === trackId ? { ...el, ...updates } : el
      )
    })));
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
    setPages(prevPages => prevPages.map((page, index) =>
      index === slideIndex ? { ...page, ...updates } : page
    ));
  };

  const handleAudioSelect = (audioId) => {
    console.log('🎵 Audio selected:', audioId);
    const track = audioTracks.find(t => t.id === audioId);
    if (track) {
      setSelectedElement({ ...track, type: 'audio' });
    }
  };

  const handleVideoSelect = (videoId) => {
    console.log('🎬 Video selected:', videoId);
    const videoElement = currentPage?.elements.find(el => el.id === videoId);
    if (videoElement) {
      handleSelectElement(videoElement);
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
   * Handle play/pause for timeline
   */
  const handlePlay = () => {
    console.log('▶️ Play button clicked');
    setIsPlaying(true);
  };

  const handlePause = () => {
    console.log('⏸️ Pause button clicked');
    setIsPlaying(false);

    // Pause all audio elements
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
                if (videoRef && isFinite(videoRef.duration) && videoRef.duration > 0) {
                  // Calculate if this video should be playing based on page timing
                  const pageStartTime = pages.slice(0, pageIndex).reduce((sum, p) => sum + (p.duration || 5), 0);
                  const pageEndTime = pageStartTime + (page.duration || 5);

                  if (newTime >= pageStartTime && newTime < pageEndTime) {
                    // Video should be playing
                    const videoTime = newTime - pageStartTime;

                    if (videoRef.paused) {
                      // Start playing the video
                      if (isFinite(videoTime) && videoTime >= 0) {
                        console.log(`🎬 Starting video ${element.id} at ${videoTime.toFixed(2)}s`);
                        videoRef.currentTime = Math.min(videoTime, videoRef.duration);
                        videoRef.play().catch(err => console.error('Video play error:', err));
                      }
                    } else {
                      // Sync video time if it drifts too much
                      const drift = Math.abs(videoRef.currentTime - videoTime);
                      if (drift > 0.5 && isFinite(videoTime)) {
                        videoRef.currentTime = Math.min(videoTime, videoRef.duration);
                      }
                    }
                  } else if (!videoRef.paused) {
                    // Video should not be playing
                    videoRef.pause();
                  }
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
    audioTracks.forEach(track => {
      if (!audioRefs.current[track.id] && track.src) {
        console.log(`🎵 Creating audio element for track: ${track.id}`);
        const audio = new Audio(track.src);
        audio.volume = (track.volume || 100) / 100;
        audio.loop = false;
        audioRefs.current[track.id] = audio;
      }
    });

    // Cleanup removed tracks
    Object.keys(audioRefs.current).forEach(trackId => {
      if (!audioTracks.find(t => t.id === trackId)) {
        console.log(`🗑️ Removing audio element for track: ${trackId}`);
        const audio = audioRefs.current[trackId];
        if (audio) {
          audio.pause();
          audio.src = '';
        }
        delete audioRefs.current[trackId];
      }
    });
  }, [audioTracks]);

  /**
   * Auto-navigate to the slide that corresponds to current playhead position
   */
  useEffect(() => {
    if (pages.length > 0) {
      // Calculate which slide should be visible based on current time
      let accumulatedTime = 0;
      for (let i = 0; i < pages.length; i++) {
        const slideDuration = pages[i].duration || 5;
        if (currentTime >= accumulatedTime && currentTime < accumulatedTime + slideDuration) {
          if (currentPageIndex !== i) {
            console.log(`Auto-switching to slide ${i + 1} at time ${currentTime.toFixed(2)}s`);
            setCurrentPageIndex(i);
          }
          break;
        }
        accumulatedTime += slideDuration;
      }
    }
  }, [currentTime, pages]); // eslint-disable-line react-hooks/exhaustive-deps

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

    // Remove from timeline if it exists there
    if (audioId) {
      setAudioTracks(prev => prev.filter(track => track.id !== audioId));
    }

    // Remove from media library
    if (mediaId) {
      setUploadedAudio(prev => prev.filter(audio => audio.id !== mediaId));
    }

    setAudioDeleteDialog({ isOpen: false, audioId: null, audioTitle: null, mediaId: null });
    showToast('Audio deleted', 'success');
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

    // Remove from canvas if it exists there
    if (videoId) {
      setPages(prevPages => prevPages.map(page => ({
        ...page,
        elements: page.elements.filter(el => el.id !== videoId)
      })));
    }

    // Remove from media library
    if (mediaId) {
      setUploadedVideo(prev => prev.filter(video => video.id !== mediaId));
    }

    setVideoDeleteDialog({ isOpen: false, videoId: null, videoTitle: null, mediaId: null });
    showToast('Video deleted', 'success');
  };

  /**
   * Handle image delete request
   */
  const handleImageDeleteRequest = (imageUrl, imageTitle, mediaId) => {
    // Find all image elements with this URL across all pages
    const imageElements = [];
    pages.forEach((page, pageIndex) => {
      page.elements.forEach(element => {
        if (element.type === 'image' && element.src === imageUrl) {
          imageElements.push({ element, pageIndex });
        }
      });
    });

    if (imageElements.length > 0) {
      // If image is on canvas, show confirmation dialog
      setImageDeleteDialog({
        isOpen: true,
        imageElements,
        imageTitle,
        mediaId
      });
    } else {
      // Image not on canvas, just delete from media library
      handleDeleteImage(mediaId);
      showToast('Image deleted from library', 'success');
    }
  };

  const confirmImageDelete = () => {
    const { imageElements, mediaId } = imageDeleteDialog;

    // Remove all instances from canvas
    if (imageElements && imageElements.length > 0) {
      imageElements.forEach(({ element }) => {
        setPages(prevPages => prevPages.map(page => ({
          ...page,
          elements: page.elements.filter(el => el.id !== element.id)
        })));
      });
    }

    // Remove from media library
    if (mediaId) {
      setUploadedImage(prev => prev.filter(image => image.id !== mediaId));
    }

    setImageDeleteDialog({ isOpen: false, imageElements: null, imageTitle: null, mediaId: null });
    showToast('Image deleted', 'success');
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
    setCurrentProject(null);
    setSelectedElement(null);
    showToast('New project created', 'success');
  };

  return (
    <div className="flex h-full bg-gray-50">
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
              returnPath: location.pathname + location.search
            }
          })}
          onOpenImageLibrary={() => navigate('/asset-management/images', {
            state: {
              fromEditor: true,
              returnPath: location.pathname + location.search
            }
          })}
          onOpenVideoLibrary={() => navigate('/asset-management/videos', {
            state: {
              fromEditor: true,
              returnPath: location.pathname + location.search
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
          </div>
          {currentProject && (
            <div className="text-sm text-gray-600">
              <span className="font-medium">Project:</span> {currentProject.name}
            </div>
          )}
        </div>

        {/* Page Navigation */}
        {pages.length > 1 && (
          <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
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
            </div>
            <div className="flex items-center gap-2">
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
        )}

        {/* Canvas */}
        <Canvas
          elements={currentPage?.elements || []}
          selectedElement={selectedElement}
          onSelectElement={handleSelectElement}
          onUpdateElement={handleUpdateElement}
          onDeleteElement={handleDeleteElement}
          background={currentPage?.background}
        />

        {/* Audio Timeline */}
        {(audioTracks.length > 0 || videoTracks.length > 0) && (
          <AudioTimelineRefactored
            audioTracks={audioTracks}
            videoTracks={videoTracks}
            slides={pages}
            currentTime={currentTime}
            isPlaying={isPlaying}
            selectedAudioId={selectedElement?.type === 'audio' ? selectedElement.id : null}
            selectedVideoId={selectedElement?.type === 'video' ? selectedElement.id : null}
            onAudioUpdate={handleAudioUpdate}
            onAudioDelete={handleAudioDelete}
            onAudioSelect={handleAudioSelect}
            onVideoUpdate={handleVideoUpdate}
            onVideoDelete={handleVideoDelete}
            onVideoSelect={handleVideoSelect}
            onSlideUpdate={handleSlideUpdate}
            onSeek={handleSeek}
            onPlay={handlePlay}
            onPause={handlePause}
          />
        )}
      </div>

      {/* Properties Panel - Always show if open, regardless of selection */}
      {isPropertiesPanelOpen && (
        <PropertiesPanel
          element={selectedElement}
          onUpdate={(updates) => handleUpdateElement(selectedElement.id, updates)}
          onDelete={() => handleDeleteElement(selectedElement.id)}
          onClose={() => setIsPropertiesPanelOpen(false)}
        />
      )}

      {/* Toggle Properties Panel Button - Show when panel is closed */}
      {!isPropertiesPanelOpen && (
        <button
          onClick={() => setIsPropertiesPanelOpen(true)}
          className="fixed right-4 top-20 z-50 bg-blue-600 text-white p-3 rounded-lg shadow-lg hover:bg-blue-700 transition-all"
          title="Open Properties Panel"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
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
        title="Delete Audio"
        message={`Are you sure you want to delete "${audioDeleteDialog.audioTitle}"?`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />

      <ConfirmDialog
        isOpen={videoDeleteDialog.isOpen}
        onClose={() => setVideoDeleteDialog({ isOpen: false, videoId: null, videoTitle: null, mediaId: null })}
        onConfirm={confirmVideoDelete}
        title="Delete Video"
        description="This action cannot be undone"
        message={`Are you sure you want to delete "${videoDeleteDialog.videoTitle}"?`}
        warningMessage="This will permanently delete the video from both the timeline and media library."
        confirmText="Delete Video"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Delete Image Confirmation Dialog */}
      <ConfirmDialog
        isOpen={imageDeleteDialog.isOpen}
        onClose={() => setImageDeleteDialog({ isOpen: false, imageElements: null, imageTitle: null, mediaId: null })}
        onConfirm={confirmImageDelete}
        title="Delete Image"
        description="This action cannot be undone"
        message={`Are you sure you want to delete "${imageDeleteDialog.imageTitle}"?`}
        warningMessage={
          imageDeleteDialog.imageElements && imageDeleteDialog.imageElements.length > 0
            ? `This image is used in ${imageDeleteDialog.imageElements.length} place(s) on the canvas. It will be removed from all locations.`
            : "This will permanently delete the image from the media library."
        }
        confirmText="Delete Image"
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
    </div>
  );
};

export default DesignEditor;

