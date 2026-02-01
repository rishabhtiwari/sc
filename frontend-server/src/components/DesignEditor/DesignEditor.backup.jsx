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

  // UI State
  const [selectedTool, setSelectedTool] = useState(null);
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
    handleDeleteElement,
    handleSelectElement,
    handleDeselectElement
  } = useElementManagement(pages, setPages, currentPageIndex);

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
    unregisterVideoRef
  } = useVideoPlayback(pages, currentPageIndex);

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

  // Delete confirmation dialogs
  const [audioDeleteDialog, setAudioDeleteDialog] = useState({
    isOpen: false,
    audioId: null,
    audioTitle: null,
    mediaId: null
  });

  const [videoDeleteDialog, setVideoDeleteDialog] = useState({
    isOpen: false,
    videoId: null,
    videoTitle: null,
    mediaId: null
  });

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
        id: `media-${Date.now()}`,
        url: addAsset.src || addAsset.url,
        title: addAsset.name || addAsset.title,
        type: 'audio',
        libraryId: addAsset.libraryId
      });
    } else if (addAsset.type === 'image') {
      console.log('🖼️ Adding image to media list only (not to canvas)');
      handleAddImage({
        id: `media-${Date.now()}`,
        url: addAsset.src || addAsset.url,
        title: addAsset.name || addAsset.title,
        type: 'image',
        libraryId: addAsset.libraryId
      });
    } else if (addAsset.type === 'video') {
      console.log('🎬 Adding video to media list only (not to canvas)');
      handleAddVideo({
        id: `media-${Date.now()}`,
        url: addAsset.src || addAsset.url,
        title: addAsset.name || addAsset.title,
        type: 'video',
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
    setAudioTracks(prevTracks => prevTracks.filter(track => track.id !== trackId));
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
    setPages(prevPages => prevPages.map(page => ({
      ...page,
      elements: page.elements.filter(el => el.id !== trackId)
    })));
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
   * Handle play/pause for timeline
   */
  const handlePlay = () => {
    handlePlayPause();
  };

  const handlePause = () => {
    if (isPlaying) {
      handlePlayPause();
    }
  };

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

    // Remove from timeline
    if (audioId) {
      setAudioTracks(prev => prev.filter(track => track.id !== audioId));
    }

    // Remove from media list
    if (mediaId) {
      handleDeleteAudio(mediaId);
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

    // Remove from canvas
    if (videoId) {
      handleDeleteElement(videoId);
    }

    // Remove from media list
    if (mediaId) {
      handleDeleteVideo(mediaId);
    }

    setVideoDeleteDialog({ isOpen: false, videoId: null, videoTitle: null, mediaId: null });
    showToast('Video deleted', 'success');
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

      {/* Properties Panel */}
      {selectedElement && (
        <PropertiesPanel
          element={selectedElement}
          onUpdate={(updates) => handleUpdateElement(selectedElement.id, updates)}
          onDelete={() => handleDeleteElement(selectedElement.id)}
          onClose={() => handleDeselectElement()}
        />
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

