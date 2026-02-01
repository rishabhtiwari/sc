import React, { useState, useRef, useEffect, useMemo } from 'react';
import Sidebar from './Sidebar/Sidebar';
import Canvas from './Canvas/Canvas';
import PropertiesPanel from './PropertiesPanel/PropertiesPanel';
import AudioTimelineRefactored from './AudioTimeline/AudioTimelineRefactored';
import AudioLibrary from './AudioLibrary/AudioLibrary';
import ProjectDashboard from './ProjectDashboard/ProjectDashboard';
import ConfirmDialog from '../common/ConfirmDialog';
import { useToast } from '../../hooks/useToast';
import projectService from '../../services/projectService';

/**
 * Main Design Editor Component
 * Layout: Sidebar | Canvas | Properties Panel
 */
const DesignEditor = () => {
  const [selectedTool, setSelectedTool] = useState(null);
  const [selectedElement, setSelectedElement] = useState(null);
  const [canvasElements, setCanvasElements] = useState([]);
  const [pages, setPages] = useState([
    {
      id: 'page-1',
      name: 'Page 1',
      elements: [],
      background: { type: 'solid', color: '#ffffff' },
      duration: 5, // Default 5 seconds per slide
      startTime: 0 // Default start time (can be moved independently)
    }
  ]);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, slideIndex: null });

  // Audio Timeline State
  const [audioTracks, setAudioTracks] = useState([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedAudioTrack, setSelectedAudioTrack] = useState(null);
  const audioRefs = useRef({});

  // Video Timeline State - Computed from page elements (derived state)
  const videoTracks = useMemo(() => {
    console.log('🔄 Computing video tracks from pages...');
    const tracks = [];
    let cumulativeTime = 0;

    pages.forEach((page, pageIndex) => {
      const pageStartTime = cumulativeTime;
      const pageDuration = page.duration || 5; // Define pageDuration at page level
      const videoElements = (page.elements || []).filter(el => el.type === 'video');

      console.log(`  📄 Page ${pageIndex} (${page.name}): ${videoElements.length} video(s)`);

      videoElements.forEach((element, elementIndex) => {
        const videoDuration = element.duration || 0;

        // Video is constrained to the slide's time range
        const effectiveDuration = Math.min(videoDuration, pageDuration);
        const trimEnd = videoDuration > pageDuration ? videoDuration - pageDuration : 0;

        const track = {
          id: element.id,
          elementId: element.id,
          name: element.file?.name || element.name || `Video ${tracks.length + 1}`,
          url: element.src,
          src: element.src,
          file: element.file,
          startTime: pageStartTime,
          duration: effectiveDuration,
          originalDuration: videoDuration,
          trimStart: 0,
          trimEnd: trimEnd,
          volume: element.volume || 100,
          playbackSpeed: element.playbackSpeed || 1,
          slideIndex: pageIndex,
          videoType: 'video'
        };

        tracks.push(track);
        console.log(`    🎬 Video ${elementIndex}: ${track.name} (${effectiveDuration}s at ${pageStartTime}s)`);
      });

      cumulativeTime += pageDuration;
    });

    console.log(`✅ Computed ${tracks.length} video track(s) from pages`);
    return tracks;
  }, [pages]);

  const [selectedVideoTrack, setSelectedVideoTrack] = useState(null);
  const videoRefs = useRef({});

  // Video refs for controlling video playback on canvas
  const videoElementRefs = useRef({});

  // Uploaded Media State (lifted from MediaPanel to persist across tab switches)
  // Separate state for audio and video to keep them independent
  const [uploadedAudio, setUploadedAudio] = useState([]);
  const [uploadedVideo, setUploadedVideo] = useState([]);

  // Audio Delete Confirmation Dialog
  const [audioDeleteDialog, setAudioDeleteDialog] = useState({
    isOpen: false,
    audioId: null,
    audioTitle: null,
    mediaId: null
  });

  // Video Delete Confirmation Dialog
  const [videoDeleteDialog, setVideoDeleteDialog] = useState({
    isOpen: false,
    videoId: null,
    videoTitle: null,
    mediaId: null
  });

  // Audio Library Modal State
  const [isAudioLibraryOpen, setIsAudioLibraryOpen] = useState(false);

  // Project State
  const [currentProject, setCurrentProject] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showProjectBrowser, setShowProjectBrowser] = useState(false);

  const { showToast } = useToast();

  /**
   * Handle adding element to canvas (adds to current page)
   */
  const handleAddElement = (element) => {
    console.log('🎨 handleAddElement called with:', {
      type: element.type,
      hasSrc: !!element.src,
      hasFile: !!element.file,
      duration: element.duration,
      width: element.width,
      height: element.height
    });

    const newElement = {
      id: `element-${Date.now()}`,
      ...element,
      x: element.x || 100,
      y: element.y || 100,
    };

    console.log('✅ Created new element:', {
      id: newElement.id,
      type: newElement.type,
      hasSrc: !!newElement.src,
      hasFile: !!newElement.file
    });

    // Calculate start time for video on timeline based on current slide position
    let slideStartTime = 0;
    for (let i = 0; i < currentPageIndex; i++) {
      slideStartTime += pages[i].duration || 5;
    }

    // Update current page's elements
    const updatedPages = pages.map((page, index) => {
      if (index === currentPageIndex) {
        const updatedPage = {
          ...page,
          elements: [...(page.elements || []), newElement]
        };

        console.log(`📄 Adding element to page ${index}:`, {
          pageId: page.id,
          pageName: page.name,
          oldElementCount: page.elements?.length || 0,
          newElementCount: updatedPage.elements.length,
          newElementId: newElement.id,
          newElementType: newElement.type
        });

        // If adding a video element, auto-adjust slide duration to match video length
        if (element.type === 'video') {
          if (element.duration && element.duration > 0) {
            console.log('🎬 Video added with duration:', element.duration);
            updatedPage.duration = Math.ceil(element.duration); // Round up to nearest second
            console.log('📊 Slide duration updated to:', updatedPage.duration);
          } else {
            console.warn('⚠️ Video element has no duration! Element:', element);
            console.warn('⚠️ Slide duration will remain:', page.duration || 5);
          }
        }

        return updatedPage;
      }
      return page;
    });

    console.log('✅ Pages updated. Total pages:', updatedPages.length);
    console.log('✅ Current page elements:', updatedPages[currentPageIndex].elements.length);

    setPages(updatedPages);
    setCanvasElements([...canvasElements, newElement]); // Keep for backward compatibility
    setSelectedElement(newElement);

    // Video tracks are now computed from page elements automatically via useMemo
    // No need to manually add to videoTracks state
    if (element.type === 'video' && element.duration) {
      console.log('✅ Video element added to page. Video tracks will be computed automatically.');
      setSelectedVideoTrack(newElement.id);
    }
  };

  /**
   * Handle adding multiple pages (for slide generation)
   */
  const handleAddMultiplePages = (slidePages) => {
    console.log('📄 DesignEditor: handleAddMultiplePages called with', slidePages?.length, 'slides');
    console.log('📄 DesignEditor: Slide pages:', slidePages);

    if (!slidePages || slidePages.length === 0) {
      console.warn('⚠️ DesignEditor: No slide pages provided');
      return;
    }

    const newPages = slidePages.map((slide, index) => {
      // Calculate start time for new slides (position at end of existing slides)
      const existingDuration = pages.reduce((sum, p) => {
        const pStart = p.startTime !== undefined ? p.startTime : 0;
        const pDur = p.duration || 5;
        return Math.max(sum, pStart + pDur);
      }, 0);

      return {
        id: slide.id || `page-${Date.now()}-${index}`,
        name: slide.name || `Slide ${pages.length + index + 1}`,
        elements: slide.elements || [],
        background: slide.background || { type: 'solid', color: '#ffffff' },
        duration: slide.duration || 5,
        startTime: existingDuration + (index * 5), // Position new slides sequentially after existing ones
        transition: slide.transition || 'fade'
      };
    });

    console.log('📄 DesignEditor: Created new pages:', newPages);
    console.log('📄 DesignEditor: Current pages before update:', pages);

    const updatedPages = [...pages, ...newPages];
    console.log('📄 DesignEditor: Updated pages:', updatedPages);

    setPages(updatedPages);
    setCurrentPageIndex(pages.length); // Switch to first new page

    console.log('✅ DesignEditor: Pages state updated, new page index:', pages.length);
  };

  /**
   * Handle element selection
   */
  const handleSelectElement = (element) => {
    setSelectedElement(element);
  };

  /**
   * Handle element update (updates element in current page)
   */
  const handleUpdateElement = (elementId, updates) => {
    // Update in pages
    const updatedPages = pages.map((page, index) => {
      if (index === currentPageIndex) {
        return {
          ...page,
          elements: page.elements.map(el =>
            el.id === elementId ? { ...el, ...updates } : el
          )
        };
      }
      return page;
    });

    setPages(updatedPages);
    setCanvasElements(canvasElements.map(el =>
      el.id === elementId ? { ...el, ...updates } : el
    ));

    if (selectedElement?.id === elementId) {
      setSelectedElement({ ...selectedElement, ...updates });
    }
  };

  /**
   * Handle element deletion (deletes from current page)
   */
  const handleDeleteElement = (elementId) => {
    // Delete from pages
    const updatedPages = pages.map((page, index) => {
      if (index === currentPageIndex) {
        return {
          ...page,
          elements: page.elements.filter(el => el.id !== elementId)
        };
      }
      return page;
    });

    setPages(updatedPages);
    setCanvasElements(canvasElements.filter(el => el.id !== elementId));

    if (selectedElement?.id === elementId) {
      setSelectedElement(null);
    }
  };

  // Get current page
  const currentPage = pages[currentPageIndex] || pages[0];
  const currentPageElements = currentPage?.elements || canvasElements;

  // Handle background change
  const handleBackgroundChange = (background) => {
    const newPages = [...pages];
    newPages[currentPageIndex] = {
      ...newPages[currentPageIndex],
      background
    };
    setPages(newPages);
  };

  /**
   * Handle adding audio track
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
          name: audioFile.name,
          url: audioUrl,
          duration: audio.duration,
          startTime: startTime, // Auto-position at end of existing audio
          volume: 100, // Default volume 100%
          fadeIn: 0,
          fadeOut: 0,
          type: audioFile.name.toLowerCase().includes('voice') || audioFile.name.toLowerCase().includes('speech')
            ? 'voiceover'
            : audioFile.name.toLowerCase().includes('sfx') || audioFile.name.toLowerCase().includes('effect')
            ? 'sfx'
            : 'music' // Auto-detect type from filename
        };

        const updatedTracks = [...prevTracks, newTrack];
        console.log('✅ Audio track added:', newTrack, 'Start time:', startTime, 'Duration:', audio.duration);
        return updatedTracks;
      });

      // Set initial volume
      audio.volume = 1.0; // 100%
      audioRefs.current[trackId] = audio;
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
   * Handle adding audio from library
   * Adds to both uploadedAudio (media list) AND timeline
   */
  const handleAddFromLibrary = (audioData) => {
    console.log('📁 handleAddFromLibrary called with:', audioData);

    const url = audioData.url || audioData.audio_url;
    const title = audioData.title || 'Library Audio';

    console.log('📁 Extracted URL:', url);
    console.log('📁 Extracted Title:', title);

    if (!url) {
      console.error('❌ No URL provided!');
      showToast('Failed to add audio - no URL', 'error');
      return;
    }

    // Add to uploadedAudio (so it appears in "Your Media")
    const newAudio = {
      id: `audio-${Date.now()}-${Math.random()}`,
      type: 'audio',
      url: url,
      title: title,
      file: { name: title }
    };
    console.log('📁 Adding to uploadedAudio:', newAudio);
    setUploadedAudio(prev => [...prev, newAudio]);

    // Add to timeline
    console.log('📁 Calling handleAddAudioTrack with:', { name: title }, url);
    handleAddAudioTrack({ name: title }, url);

    showToast('Audio added to timeline and media library', 'success');
    setIsAudioLibraryOpen(false);
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
   * Handle audio track update (drag, stretch, properties)
   */
  const handleAudioUpdate = (trackId, updates) => {
    setAudioTracks(prevTracks => {
      const updatedTracks = prevTracks.map(track =>
        track.id === trackId ? { ...track, ...updates } : track
      );
      return updatedTracks;
    });

    // Apply volume/fade changes immediately to audio element
    if ((updates.volume !== undefined || updates.fadeIn !== undefined || updates.fadeOut !== undefined) && audioRefs.current[trackId]) {
      const track = audioTracks.find(t => t.id === trackId);
      if (track) {
        const audio = audioRefs.current[trackId];
        const currentTrackTime = audio.currentTime;
        applyFadeEffect(audio, { ...track, ...updates }, currentTrackTime);
      }
    }
  };

  /**
   * Handle audio track delete
   * Removes from BOTH timeline AND uploaded media list
   */
  const handleAudioDelete = (trackId) => {
    // Find the track to get its URL
    const track = audioTracks.find(t => t.id === trackId);

    // Remove from timeline
    setAudioTracks(audioTracks.filter(track => track.id !== trackId));

    // Remove from uploaded media list (match by URL)
    if (track?.url) {
      setUploadedAudio(prev => prev.filter(m => m.url !== track.url));
    }

    // Clean up audio ref
    if (audioRefs.current[trackId]) {
      const audio = audioRefs.current[trackId];
      audio.pause();
      audio.src = '';
      delete audioRefs.current[trackId];
    }

    // Deselect if this track was selected
    if (selectedAudioTrack?.id === trackId) {
      setSelectedAudioTrack(null);
    }
  };

  /**
   * Handle audio track selection
   */
  const handleAudioSelect = (trackId) => {
    const track = audioTracks.find(t => t.id === trackId);
    setSelectedAudioTrack(track || null);
    // Deselect canvas element when audio is selected
    setSelectedElement(null);
  };

  /**
   * Handle video track update - Updates the video element in the page
   */
  const handleVideoUpdate = (trackId, updates) => {
    console.log('🎬 Updating video element:', trackId, updates);

    // Update the video element in the corresponding page
    setPages(prevPages => prevPages.map(page => ({
      ...page,
      elements: page.elements.map(el =>
        el.id === trackId ? { ...el, ...updates } : el
      )
    })));

    // Video tracks will be recomputed automatically via useMemo
    console.log('✅ Video element updated. Video tracks will be recomputed automatically.');
  };

  /**
   * Handle video track delete - Removes the video element from the page
   */
  const handleVideoDelete = (trackId) => {
    const track = videoTracks.find(t => t.id === trackId);

    // Revoke blob URL to free memory
    if (track?.url && track.url.startsWith('blob:')) {
      URL.revokeObjectURL(track.url);
    }

    // Remove video element from page
    setPages(prevPages => prevPages.map(page => ({
      ...page,
      elements: page.elements.filter(el => el.id !== trackId)
    })));

    // Remove from uploaded media list (match by URL)
    if (track?.src) {
      setUploadedVideo(prev => prev.filter(m => m.url !== track.src));
    }

    // Clean up video ref
    if (videoRefs.current[trackId]) {
      const video = videoRefs.current[trackId];
      video.pause();
      video.src = '';
      delete videoRefs.current[trackId];
    }

    // Deselect if this track was selected
    if (selectedVideoTrack === trackId) {
      setSelectedVideoTrack(null);
    }

    // Video tracks will be recomputed automatically via useMemo
    console.log('✅ Video element deleted. Video tracks will be recomputed automatically.');
  };

  /**
   * Handle video track selection
   */
  const handleVideoSelect = (trackId) => {
    const track = videoTracks.find(t => t.id === trackId);
    setSelectedVideoTrack(track?.id || null);

    // Also select the canvas element
    if (track?.elementId) {
      const element = currentPageElements.find(el => el.id === track.elementId);
      if (element) {
        setSelectedElement(element);
      }
    }
  };



  /**
   * Handle audio delete request (opens confirmation dialog)
   */
  const handleAudioDeleteRequest = (audioId, audioTitle, mediaId) => {
    setAudioDeleteDialog({
      isOpen: true,
      audioId,
      audioTitle,
      mediaId
    });
  };

  /**
   * Confirm audio deletion
   */
  const confirmAudioDelete = () => {
    const { audioId, mediaId } = audioDeleteDialog;

    // Delete from audio tracks (timeline)
    if (audioId) {
      handleAudioDelete(audioId);
    }

    // Delete from uploaded audio (media library)
    if (mediaId) {
      setUploadedAudio(prev => prev.filter(m => m.id !== mediaId));
    }

    // Close dialog
    setAudioDeleteDialog({ isOpen: false, audioId: null, audioTitle: null, mediaId: null });
  };

  /**
   * Handle video delete request (opens confirmation dialog)
   */
  const handleVideoDeleteRequest = (videoId, videoTitle, mediaId) => {
    setVideoDeleteDialog({
      isOpen: true,
      videoId,
      videoTitle,
      mediaId
    });
  };

  /**
   * Confirm video deletion
   */
  const confirmVideoDelete = () => {
    const { videoId, mediaId } = videoDeleteDialog;

    // Delete from video tracks (timeline) and canvas
    if (videoId) {
      handleVideoDelete(videoId);

      // Also close properties panel if this video element is selected
      if (selectedElement && selectedElement.id === videoId) {
        setSelectedElement(null);
      }
    }

    // Delete from media library
    if (mediaId) {
      setUploadedVideo(prev => prev.filter(m => m.id !== mediaId));
    }

    // Close dialog
    setVideoDeleteDialog({ isOpen: false, videoId: null, videoTitle: null, mediaId: null });
  };

  /**
   * Handle slide duration update
   */
  const handleSlideUpdate = (slideIndex, updates) => {
    const newPages = pages.map((page, index) =>
      index === slideIndex ? { ...page, ...updates } : page
    );
    setPages(newPages);

    // Video tracks will be recomputed automatically from page elements via useMemo
    if (updates.duration !== undefined) {
      console.log('📊 Slide duration updated to:', updates.duration, 'for slide:', slideIndex);
      console.log('✅ Video tracks will be recomputed automatically to match new slide duration.');
    }
  };

  /**
   * Handle timeline seek
   */
  const handleSeek = (time) => {
    setCurrentTime(time);
    // Update all audio elements and apply fade effects
    audioTracks.forEach(track => {
      const audio = audioRefs.current[track.id];
      if (audio) {
        const trackTime = time - track.startTime;
        const originalDuration = audio.duration;

        if (trackTime >= 0 && trackTime <= track.duration) {
          // Calculate actual audio position (loop if stretched)
          const actualAudioTime = trackTime % originalDuration;
          audio.currentTime = actualAudioTime;
          applyFadeEffect(audio, track, trackTime);
        }
      }
    });
  };

  /**
   * Handle play
   */
  const handlePlay = () => {
    setIsPlaying(true);
    // Play all audio tracks that should be playing at current time
    audioTracks.forEach(track => {
      const audio = audioRefs.current[track.id];
      if (audio && currentTime >= track.startTime && currentTime < track.startTime + track.duration) {
        const trackTime = currentTime - track.startTime;
        const originalDuration = audio.duration;

        // Calculate actual audio position (loop if stretched)
        const actualAudioTime = trackTime % originalDuration;
        audio.currentTime = actualAudioTime;
        applyFadeEffect(audio, track, trackTime);
        audio.play();
      }
    });
  };

  /**
   * Handle pause
   */
  const handlePause = () => {
    setIsPlaying(false);
    // Pause all audio tracks
    Object.values(audioRefs.current).forEach(audio => {
      if (audio) {
        audio.pause();
      }
    });
  };

  /**
   * Prepare project data for saving
   * Uploads blob URLs to asset service and replaces with asset IDs
   */
  const prepareProjectData = async () => {
    try {
      console.log('💾 Preparing project data...');
      console.log('📄 Pages to process:', pages.length);

      // Process pages and upload any blob URLs
      const processedPages = await Promise.all(
        pages.map(async (page, pageIndex) => {
          console.log(`📄 Processing page ${pageIndex}:`, {
            id: page.id,
            name: page.name,
            elementCount: page.elements?.length || 0
          });

          const processedElements = await Promise.all(
            page.elements.map(async (element, elementIndex) => {
              console.log(`  🔍 Element ${elementIndex}:`, {
                type: element.type,
                id: element.id,
                hasSrc: !!element.src,
                hasFile: !!element.file,
                srcType: element.src?.substring(0, 10)
              });

              if ((element.type === 'video' || element.type === 'image') && element.src) {
                // If it's a blob URL, upload to asset service
                if (element.src.startsWith('blob:')) {
                  if (element.file) {
                    console.log(`  📤 Uploading ${element.type}:`, element.file.name);
                    const asset = await projectService.uploadAsset(element.file, element.type);
                    console.log(`  ✅ Uploaded successfully:`, {
                      asset_id: asset.asset_id,
                      url: asset.storage?.url?.substring(0, 50)
                    });
                    return {
                      ...element,
                      assetId: asset.asset_id,
                      src: asset.storage.url,
                      file: undefined // Remove file object from saved data
                    };
                  } else {
                    console.warn(`  ⚠️ ${element.type} has blob URL but no file object!`, element.id);
                  }
                } else {
                  console.log(`  ℹ️ ${element.type} already has non-blob URL`);
                }
                // If already has assetId, keep it
                return element;
              }
              return element;
            })
          );

          console.log(`  ✅ Page ${pageIndex} processed: ${processedElements.length} elements`);

          // Process background if it has video or image
          let processedBackground = { ...page.background };
          if (page.background.videoAssetId || page.background.imageAssetId) {
            // Already has asset IDs, keep them
            processedBackground = page.background;
          }

          return {
            ...page,
            elements: processedElements,
            background: processedBackground
          };
        })
      );

      console.log('✅ All pages processed:', processedPages.length);

      // Process audio tracks
      const processedAudioTracks = await Promise.all(
        audioTracks.map(async (track) => {
          if (track.url && track.url.startsWith('blob:')) {
            if (track.file) {
              const asset = await projectService.uploadAsset(track.file, 'audio');
              return {
                ...track,
                assetId: asset.asset_id,
                url: asset.storage.url,
                file: undefined
              };
            }
          }
          return track;
        })
      );

      // Video tracks are no longer stored separately - they're part of page elements
      console.log('✅ Videos are stored in page elements (not separate videoTracks)');

      // Calculate total duration
      const audioDuration = processedAudioTracks.length > 0
        ? Math.max(...processedAudioTracks.map(track => (track.startTime || 0) + (track.duration || 0)))
        : 0;
      const slidesDuration = processedPages.reduce((sum, page) => sum + (page.duration || 5), 0);
      const totalDuration = Math.max(audioDuration, slidesDuration, 30);

      return {
        name: currentProject?.name || `Project ${new Date().toLocaleDateString()}`,
        description: currentProject?.description || '',
        settings: {
          canvas: {
            width: 1920,
            height: 1080,
            backgroundColor: '#ffffff'
          },
          duration: totalDuration,
          fps: 30,
          quality: 'high'
        },
        pages: processedPages,
        audioTracks: processedAudioTracks,
        // videoTracks are no longer stored separately - they're in page elements
        videoTracks: [],
        status: 'draft',
        tags: []
      };
    } catch (error) {
      console.error('Error preparing project data:', error);
      throw error;
    }
  };

  /**
   * Handle save project
   */
  const handleSaveProject = async () => {
    try {
      setIsSaving(true);
      showToast('Saving project...', 'info');

      // Log current state before saving
      console.log('💾 Current state before save:');
      console.log('  📄 Pages:', pages.length);
      pages.forEach((page, index) => {
        console.log(`    Page ${index} (${page.name}):`, {
          id: page.id,
          elementCount: page.elements?.length || 0,
          elements: page.elements?.map(el => ({
            id: el.id,
            type: el.type,
            hasSrc: !!el.src,
            hasFile: !!el.file
          }))
        });
      });
      console.log('  🎬 Video tracks (computed):', videoTracks.length);
      console.log('  🎵 Audio tracks:', audioTracks.length);

      const projectData = await prepareProjectData();

      console.log('💾 Project data prepared:', {
        pages: projectData.pages?.length,
        audioTracks: projectData.audioTracks?.length,
        note: 'Videos are stored in page elements'
      });

      let savedProject;
      if (currentProject?.project_id) {
        // Update existing project
        savedProject = await projectService.updateProject(currentProject.project_id, projectData);
        showToast('Project updated successfully', 'success');
      } else {
        // Create new project
        savedProject = await projectService.saveProject(projectData);
        showToast('Project saved successfully', 'success');
      }

      setCurrentProject(savedProject);
    } catch (error) {
      console.error('Error saving project:', error);
      showToast(`Failed to save project: ${error.message}`, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Extract media items from loaded project to populate sidebar media lists
   */
  const extractMediaFromProject = (project) => {
    console.log('📦 Extracting media from project:', project);

    // Extract audio from audio tracks
    const audioItems = (project.audioTracks || []).map(track => ({
      id: track.id || `audio-${Date.now()}-${Math.random()}`,
      type: 'audio',
      url: track.url,
      title: track.name || 'Audio',
      duration: track.duration,
      // Note: No file object since it's already uploaded to MinIO
    }));

    // Extract videos from video tracks
    const videoFromTracks = (project.videoTracks || []).map(track => ({
      id: track.id || `video-${Date.now()}-${Math.random()}`,
      type: 'video',
      url: track.url || track.src,
      title: track.name || 'Video',
      duration: track.duration || track.originalDuration,
    }));

    // Extract videos from page elements
    const videoFromElements = [];
    (project.pages || []).forEach(page => {
      (page.elements || []).forEach(el => {
        if (el.type === 'video' && el.src) {
          // Check if not already in videoFromTracks
          const exists = videoFromTracks.some(v => v.url === el.src);
          if (!exists) {
            videoFromElements.push({
              id: el.id || `video-${Date.now()}-${Math.random()}`,
              type: 'video',
              url: el.src,
              title: 'Video Element',
              duration: el.duration,
            });
          }
        }
      });
    });

    // Combine all videos
    const allVideos = [...videoFromTracks, ...videoFromElements];

    console.log('📦 Extracted media:', {
      audio: audioItems.length,
      video: allVideos.length
    });

    return {
      audio: audioItems,
      video: allVideos
    };
  };

  /**
   * Handle load project
   */
  const handleLoadProject = async (projectId) => {
    try {
      setIsLoading(true);
      showToast('Loading project...', 'info');

      const project = await projectService.loadProject(projectId);

      console.log('📂 Loaded project:', project);

      // Restore state
      setPages(project.pages || []);
      setAudioTracks(project.audioTracks || []);
      // videoTracks are computed from pages automatically via useMemo
      setCurrentProject(project);
      setCurrentPageIndex(0);
      setCurrentTime(0);
      setIsPlaying(false);

      // Extract and populate media lists for sidebar
      const media = extractMediaFromProject(project);
      setUploadedAudio(media.audio);
      setUploadedVideo(media.video);

      console.log('✅ Media lists populated:', {
        uploadedAudio: media.audio.length,
        uploadedVideo: media.video.length
      });

      showToast('Project loaded successfully', 'success');
      setShowProjectBrowser(false);
    } catch (error) {
      console.error('Error loading project:', error);
      showToast(`Failed to load project: ${error.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Update playhead position during playback
   */
  useEffect(() => {
    let animationFrame;

    if (isPlaying) {
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

              if (trackTime >= 0 && trackTime <= displayDuration) {
                if (audio.paused) {
                  // Calculate actual audio position when starting playback
                  const actualAudioTime = trackTime % originalDuration;
                  audio.currentTime = actualAudioTime;
                  audio.play().catch(err => console.error('Audio play error:', err));
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
  }, [isPlaying, audioTracks, pages]);

  /**
   * Auto-navigate to the slide that corresponds to current playhead position
   * Works both during playback AND when marker is moved manually
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
  }, [currentTime, pages]);

  /**
   * Control video playback based on timeline position and current slide
   * Videos play when their slide is active and timeline is playing
   */
  useEffect(() => {
    const currentPage = pages[currentPageIndex];
    if (!currentPage) return;

    // Find all video elements on the current page
    const videoElements = currentPage.elements?.filter(el => el.type === 'video') || [];

    // Calculate the time offset within the current slide
    let slideStartTime = 0;
    for (let i = 0; i < currentPageIndex; i++) {
      slideStartTime += pages[i].duration || 5;
    }
    const timeInSlide = currentTime - slideStartTime;

    console.log('🎬 Video playback control:', {
      currentPageIndex,
      videoCount: videoElements.length,
      isPlaying,
      currentTime,
      slideStartTime,
      timeInSlide,
      slideDuration: currentPage.duration || 5
    });

    videoElements.forEach(videoElement => {
      // Find the video DOM element
      const videoEl = document.querySelector(`video[data-video-element-id="${videoElement.id}"]`);

      if (videoEl) {
        console.log('🎬 Found video element:', videoElement.id, {
          paused: videoEl.paused,
          currentTime: videoEl.currentTime,
          readyState: videoEl.readyState,
          duration: videoEl.duration
        });

        // Store ref for cleanup
        videoElementRefs.current[videoElement.id] = videoEl;

        // Apply video properties
        videoEl.volume = (videoElement.volume || 100) / 100;
        videoEl.playbackRate = videoElement.playbackSpeed || 1;
        videoEl.loop = videoElement.loop || false;
        videoEl.muted = videoElement.muted !== undefined ? videoElement.muted : true;

        if (isPlaying && timeInSlide >= 0 && timeInSlide < (currentPage.duration || 5)) {
          console.log('🎬 Should play video:', videoElement.id);

          // Sync video time with timeline position
          if (Math.abs(videoEl.currentTime - timeInSlide) > 0.5) {
            console.log('🎬 Syncing video time:', timeInSlide);
            videoEl.currentTime = timeInSlide;
          }

          // Play video if paused
          if (videoEl.paused) {
            console.log('🎬 Playing video:', videoElement.id);
            videoEl.play().catch(err => {
              console.error('❌ Video play error:', err);
              // Try to play muted if autoplay is blocked
              if (err.name === 'NotAllowedError') {
                console.log('🎬 Retrying with muted=true');
                videoEl.muted = true;
                videoEl.play().catch(err2 => console.error('❌ Video play error (muted):', err2));
              }
            });
          }
        } else {
          // Pause video if not in active range
          if (!videoEl.paused) {
            console.log('🎬 Pausing video:', videoElement.id);
            videoEl.pause();
          }
        }
      } else {
        console.warn('⚠️ Video element not found in DOM:', videoElement.id);
      }
    });

    // Pause videos on other slides
    pages.forEach((page, pageIndex) => {
      if (pageIndex !== currentPageIndex) {
        const otherVideoElements = page.elements?.filter(el => el.type === 'video') || [];
        otherVideoElements.forEach(videoElement => {
          const videoEl = document.querySelector(`video[data-video-element-id="${videoElement.id}"]`);
          if (videoEl && !videoEl.paused) {
            console.log('🎬 Pausing video on other slide:', videoElement.id);
            videoEl.pause();
            videoEl.currentTime = 0;
          }
        });
      }
    });
  }, [currentTime, isPlaying, currentPageIndex, pages]);

  /**
   * Cleanup blob URLs on unmount to prevent memory leaks
   */
  useEffect(() => {
    return () => {
      // Cleanup video blob URLs
      uploadedVideo.forEach(video => {
        if (video.url && video.url.startsWith('blob:')) {
          URL.revokeObjectURL(video.url);
        }
      });

      // Cleanup audio blob URLs
      uploadedAudio.forEach(audio => {
        if (audio.url && audio.url.startsWith('blob:')) {
          URL.revokeObjectURL(audio.url);
        }
      });
    };
  }, []); // Empty deps - only run on unmount

  return (
    <div className="flex h-full bg-gray-50">
      {/* Left Sidebar - Tools */}
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
        uploadedAudio={uploadedAudio}
        onUploadedAudioChange={setUploadedAudio}
        uploadedVideo={uploadedVideo}
        onUploadedVideoChange={setUploadedVideo}
        onOpenAudioLibrary={() => setIsAudioLibraryOpen(true)}
      />

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
        {/* Project Toolbar */}
        <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={handleSaveProject}
              disabled={isSaving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center gap-2"
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
                  Save Project
                </>
              )}
            </button>
            <button
              onClick={() => setShowProjectBrowser(true)}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
              </svg>
              Load Project
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
          <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-center gap-3">
            <button
              onClick={() => setCurrentPageIndex(Math.max(0, currentPageIndex - 1))}
              disabled={currentPageIndex === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
            >
              ← Previous
            </button>
            <span className="text-sm font-semibold text-gray-900 px-3 py-2 bg-gray-100 rounded-lg">
              Slide {currentPageIndex + 1} / {pages.length}
            </span>
            <button
              onClick={() => setCurrentPageIndex(Math.min(pages.length - 1, currentPageIndex + 1))}
              disabled={currentPageIndex === pages.length - 1}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
            >
              Next →
            </button>

            {/* Slide Controls - Add & Delete */}
            <div className="flex items-center gap-2 ml-4 border-l border-gray-300 pl-4">
              <button
                onClick={() => {
                  // Duplicate current slide
                  const currentSlide = pages[currentPageIndex];
                  const newSlide = {
                    ...currentSlide,
                    id: `page-${Date.now()}`,
                    name: `Slide ${pages.length + 1}`,
                    elements: currentSlide.elements.map(el => ({
                      ...el,
                      id: `element-${Date.now()}-${Math.random()}`
                    }))
                  };
                  const newPages = [
                    ...pages.slice(0, currentPageIndex + 1),
                    newSlide,
                    ...pages.slice(currentPageIndex + 1)
                  ];
                  setPages(newPages);
                  setCurrentPageIndex(currentPageIndex + 1);
                }}
                className="w-8 h-8 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center text-lg font-bold shadow-sm"
                title="Duplicate current slide"
              >
                +
              </button>
              <button
                onClick={() => setDeleteDialog({ isOpen: true, slideIndex: currentPageIndex })}
                className="w-8 h-8 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center text-base shadow-sm"
                title="Delete current slide"
              >
                🗑️
              </button>
            </div>
          </div>
        )}

        <div className="flex-1 flex flex-col overflow-hidden" style={{ minHeight: 0 }}>
          {/* Canvas Area - Takes remaining space */}
          <div className="flex-1 overflow-hidden relative" style={{ minHeight: 0 }}>
            <Canvas
              elements={currentPageElements}
              selectedElement={selectedElement}
              onSelectElement={handleSelectElement}
              onUpdateElement={handleUpdateElement}
              onDeleteElement={handleDeleteElement}
              background={currentPage?.background}
            />
          </div>

          {/* Audio Timeline at Bottom - Fixed height */}
          <AudioTimelineRefactored
            audioTracks={audioTracks}
            videoTracks={videoTracks}
            slides={pages}
            currentTime={currentTime}
            isPlaying={isPlaying}
            selectedAudioId={selectedAudioTrack?.id}
            selectedVideoId={selectedVideoTrack}
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
        </div>
      </div>

      {/* Right Properties Panel */}
      {selectedElement && (
        <PropertiesPanel
          element={selectedElement}
          onUpdate={(updates) => handleUpdateElement(selectedElement.id, updates)}
          onDelete={() => handleDeleteElement(selectedElement.id)}
          onClose={() => setSelectedElement(null)}
        />
      )}

      {/* Audio Properties Panel */}
      {selectedAudioTrack && (() => {
        // Find the current audio track from audioTracks (to get latest values)
        const currentTrack = audioTracks.find(track => track.id === selectedAudioTrack.id);
        if (!currentTrack) return null;

        // Find the corresponding media ID from uploadedAudio
        const mediaItem = uploadedAudio.find(m => m.url === currentTrack.url);
        const mediaId = mediaItem?.id || null;

        return (
          <PropertiesPanel
            element={{
              ...currentTrack,
              type: 'audio',
              audioType: currentTrack.type // Preserve the audio type (music/voiceover/sfx)
            }}
            onUpdate={(updates) => {
              // If audioType is being updated, map it back to type
              if (updates.audioType !== undefined) {
                updates.type = updates.audioType;
                delete updates.audioType;
              }
              handleAudioUpdate(currentTrack.id, updates);
            }}
            onDelete={() => handleAudioDeleteRequest(currentTrack.id, currentTrack.name, mediaId)}
            onClose={() => setSelectedAudioTrack(null)}
          />
        );
      })()}

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
        description="This action cannot be undone"
        message={`Are you sure you want to delete "${audioDeleteDialog.audioTitle}"?`}
        warningMessage="This will permanently delete the audio from both the timeline and media library."
        confirmText="Delete Audio"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Delete Video Confirmation Dialog */}
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

      {/* Audio Library Modal */}
      <AudioLibrary
        isOpen={isAudioLibraryOpen}
        onClose={() => setIsAudioLibraryOpen(false)}
        onAddToCanvas={handleAddFromLibrary}
      />

      {/* Project Dashboard */}
      {showProjectBrowser && (
        <ProjectDashboard
          onClose={() => setShowProjectBrowser(false)}
          onOpenProject={handleLoadProject}
        />
      )}
    </div>
  );
};

export default DesignEditor;

