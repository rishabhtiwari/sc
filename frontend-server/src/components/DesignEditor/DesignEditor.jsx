import React, { useState, useRef, useEffect } from 'react';
import Sidebar from './Sidebar/Sidebar';
import Canvas from './Canvas/Canvas';
import PropertiesPanel from './PropertiesPanel/PropertiesPanel';
import AudioTimelineRefactored from './AudioTimeline/AudioTimelineRefactored';
import ConfirmDialog from '../common/ConfirmDialog';

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
      duration: 5 // Default 5 seconds per slide
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

  // Uploaded Media State (lifted from MediaPanel to persist across tab switches)
  const [uploadedMedia, setUploadedMedia] = useState([]);

  // Audio Delete Confirmation Dialog
  const [audioDeleteDialog, setAudioDeleteDialog] = useState({
    isOpen: false,
    audioId: null,
    audioTitle: null,
    mediaId: null
  });

  /**
   * Handle adding element to canvas (adds to current page)
   */
  const handleAddElement = (element) => {
    const newElement = {
      id: `element-${Date.now()}`,
      ...element,
      x: element.x || 100,
      y: element.y || 100,
    };

    // Update current page's elements
    const updatedPages = pages.map((page, index) => {
      if (index === currentPageIndex) {
        return {
          ...page,
          elements: [...(page.elements || []), newElement]
        };
      }
      return page;
    });

    setPages(updatedPages);
    setCanvasElements([...canvasElements, newElement]); // Keep for backward compatibility
    setSelectedElement(newElement);
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

    const newPages = slidePages.map((slide, index) => ({
      id: slide.id || `page-${Date.now()}-${index}`,
      name: slide.name || `Slide ${pages.length + index + 1}`,
      elements: slide.elements || [],
      background: slide.background || { type: 'solid', color: '#ffffff' },
      duration: slide.duration || 5,
      transition: slide.transition || 'fade'
    }));

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
    // Create audio element to get duration
    const audio = new Audio(audioUrl);
    const trackId = `audio-${Date.now()}`;

    audio.addEventListener('loadedmetadata', () => {
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
   */
  const handleAudioDelete = (trackId) => {
    setAudioTracks(audioTracks.filter(track => track.id !== trackId));
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
    const { audioId } = audioDeleteDialog;

    // Delete from audio tracks only (keep in uploaded media for re-use)
    if (audioId) {
      handleAudioDelete(audioId);
    }

    // Close dialog
    setAudioDeleteDialog({ isOpen: false, audioId: null, audioTitle: null, mediaId: null });
  };

  /**
   * Handle slide duration update
   */
  const handleSlideUpdate = (slideIndex, updates) => {
    const newPages = pages.map((page, index) =>
      index === slideIndex ? { ...page, ...updates } : page
    );
    setPages(newPages);
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
        uploadedMedia={uploadedMedia}
        onUploadedMediaChange={setUploadedMedia}
      />

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
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
          <div className="flex-1 overflow-hidden" style={{ minHeight: 0 }}>
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
            slides={pages}
            currentTime={currentTime}
            isPlaying={isPlaying}
            selectedAudioId={selectedAudioTrack?.id}
            onAudioUpdate={handleAudioUpdate}
            onAudioDelete={handleAudioDelete}
            onAudioSelect={handleAudioSelect}
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
            onDelete={() => handleAudioDelete(currentTrack.id)}
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

      {/* Remove Audio from Timeline Confirmation Dialog */}
      <ConfirmDialog
        isOpen={audioDeleteDialog.isOpen}
        onClose={() => setAudioDeleteDialog({ isOpen: false, audioId: null, audioTitle: null, mediaId: null })}
        onConfirm={confirmAudioDelete}
        title="Remove from Timeline"
        description="Audio will stay in your media library"
        message={`Remove "${audioDeleteDialog.audioTitle}" from timeline?`}
        warningMessage="You can re-add this audio anytime by clicking on it in Your Media section."
        confirmText="Remove from Timeline"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default DesignEditor;

