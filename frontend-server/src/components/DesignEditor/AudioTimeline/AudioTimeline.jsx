import React, { useState, useRef, useEffect } from 'react';

/**
 * Audio Timeline Component - Veed.io style timeline at bottom
 * Features:
 * - Display audio tracks with waveforms
 * - Drag to reorder and stretch audio
 * - Sync with slides
 * - Playback controls
 */
const AudioTimeline = ({ 
  audioTracks = [], 
  slides = [], 
  currentTime = 0,
  duration = 0,
  onAudioUpdate,
  onSlideUpdate,
  onSeek,
  onPlay,
  onPause,
  isPlaying = false
}) => {
  const [zoom, setZoom] = useState(1);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isStretching, setIsStretching] = useState(false);
  const [dragStart, setDragStart] = useState(null);
  const [stretchStart, setStretchStart] = useState(null);
  const [dragType, setDragType] = useState(null); // 'audio' or 'slide'
  const [dragIndex, setDragIndex] = useState(null);
  const timelineRef = useRef(null);

  // Calculate total duration (max of all audio tracks or slides)
  const totalDuration = Math.max(
    duration,
    ...audioTracks.map(track => (track.startTime || 0) + (track.duration || 0)),
    ...slides.map((slide, index) => {
      const prevSlides = slides.slice(0, index);
      const startTime = prevSlides.reduce((sum, s) => sum + (s.duration || 5), 0);
      return startTime + (slide.duration || 5);
    })
  );

  // Convert time to pixels
  const timeToPixels = (time) => {
    const pixelsPerSecond = 50 * zoom;
    return time * pixelsPerSecond;
  };

  // Convert pixels to time
  const pixelsToTime = (pixels) => {
    const pixelsPerSecond = 50 * zoom;
    return pixels / pixelsPerSecond;
  };

  // Format time as MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Handle timeline click to seek
  const handleTimelineClick = (e) => {
    if (!timelineRef.current || isDragging || isStretching) return;

    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const time = pixelsToTime(clickX);

    if (onSeek) {
      onSeek(Math.max(0, Math.min(time, totalDuration)));
    }
  };

  // Handle audio track drag start
  const handleAudioDragStart = (e, trackIndex) => {
    e.stopPropagation();
    setIsDragging(true);
    setDragType('audio');
    setDragIndex(trackIndex);
    setDragStart({ x: e.clientX, startTime: audioTracks[trackIndex].startTime });
  };

  // Handle slide drag start
  const handleSlideDragStart = (e, slideIndex) => {
    e.stopPropagation();
    setIsDragging(true);
    setDragType('slide');
    setDragIndex(slideIndex);

    // Calculate current slide start time
    const prevSlides = slides.slice(0, slideIndex);
    const startTime = prevSlides.reduce((sum, s) => sum + (s.duration || 5), 0);
    setDragStart({ x: e.clientX, startTime });
  };

  // Handle stretch start (audio or slide)
  const handleStretchStart = (e, type, index, edge) => {
    e.stopPropagation();
    setIsStretching(true);
    setDragType(type);
    setDragIndex(index);

    if (type === 'audio') {
      const track = audioTracks[index];
      setStretchStart({
        x: e.clientX,
        startTime: track.startTime,
        duration: track.duration,
        edge
      });
    } else {
      const slide = slides[index];
      setStretchStart({
        x: e.clientX,
        duration: slide.duration || 5,
        edge
      });
    }
  };

  // Handle mouse move (drag or stretch)
  const handleMouseMove = (e) => {
    if (!isDragging && !isStretching) return;

    if (isDragging && dragStart) {
      const deltaX = e.clientX - dragStart.x;
      const deltaTime = pixelsToTime(deltaX);
      const newStartTime = Math.max(0, dragStart.startTime + deltaTime);

      if (dragType === 'audio' && onAudioUpdate) {
        onAudioUpdate(audioTracks[dragIndex].id, { startTime: newStartTime });
      } else if (dragType === 'slide' && onSlideUpdate) {
        // For slides, we need to reorder them based on new position
        // This is more complex - for now just update duration
        console.log('Slide drag not fully implemented yet');
      }
    } else if (isStretching && stretchStart) {
      const deltaX = e.clientX - stretchStart.x;
      const deltaTime = pixelsToTime(deltaX);

      if (dragType === 'audio' && onAudioUpdate) {
        if (stretchStart.edge === 'right') {
          const newDuration = Math.max(1, stretchStart.duration + deltaTime);
          onAudioUpdate(audioTracks[dragIndex].id, { duration: newDuration });
        } else if (stretchStart.edge === 'left') {
          const newStartTime = Math.max(0, stretchStart.startTime + deltaTime);
          const newDuration = Math.max(1, stretchStart.duration - deltaTime);
          onAudioUpdate(audioTracks[dragIndex].id, {
            startTime: newStartTime,
            duration: newDuration
          });
        }
      } else if (dragType === 'slide' && onSlideUpdate) {
        const newDuration = Math.max(1, stretchStart.duration + deltaTime);
        onSlideUpdate(dragIndex, { duration: newDuration });
      }
    }
  };

  // Handle mouse up (end drag or stretch)
  const handleMouseUp = () => {
    setIsDragging(false);
    setIsStretching(false);
    setDragStart(null);
    setStretchStart(null);
    setDragType(null);
    setDragIndex(null);
  };

  // Add mouse event listeners
  useEffect(() => {
    if (isDragging || isStretching) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, isStretching, dragStart, stretchStart, dragType, dragIndex]);

  return (
    <div className="bg-gray-900 border-t border-gray-700 flex flex-col" style={{ height: '250px' }}>
      {/* Timeline Header - Controls */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Play/Pause Button */}
          <button
            onClick={isPlaying ? onPause : onPlay}
            className="w-10 h-10 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center justify-center text-white transition-colors"
          >
            {isPlaying ? (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          {/* Time Display */}
          <div className="text-sm font-mono text-gray-300">
            {formatTime(currentTime)} / {formatTime(totalDuration)}
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Zoom:</span>
          <button
            onClick={() => setZoom(Math.max(0.5, zoom - 0.25))}
            className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
          >
            −
          </button>
          <span className="text-sm text-gray-300 min-w-[50px] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom(Math.min(3, zoom + 0.25))}
            className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm"
          >
            +
          </button>
        </div>
      </div>

      {/* Timeline Content */}
      <div className="flex-1 overflow-x-auto overflow-y-hidden">
        <div 
          ref={timelineRef}
          className="relative h-full cursor-pointer"
          style={{ minWidth: `${timeToPixels(totalDuration) + 100}px` }}
          onClick={handleTimelineClick}
        >
          {/* Time Ruler */}
          <div className="absolute top-0 left-0 right-0 h-8 bg-gray-800 border-b border-gray-700 flex items-center">
            {Array.from({ length: Math.ceil(totalDuration) + 1 }).map((_, i) => (
              <div
                key={i}
                className="absolute flex flex-col items-center"
                style={{ left: `${timeToPixels(i)}px` }}
              >
                <div className="w-px h-2 bg-gray-600"></div>
                <span className="text-xs text-gray-400 mt-1">{formatTime(i)}</span>
              </div>
            ))}
          </div>

          {/* Playhead */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-50 pointer-events-none"
            style={{ left: `${timeToPixels(currentTime)}px` }}
          >
            <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-3 h-3 bg-red-500 rounded-full"></div>
          </div>

          {/* Slides Track */}
          <div className="absolute top-8 left-0 right-0 h-16 bg-gray-750">
            <div className="px-2 py-1 text-xs font-semibold text-gray-400 border-b border-gray-700">
              Slides
            </div>
            <div className="relative h-full pt-6">
              {slides.map((slide, index) => {
                // Calculate slide start time based on previous slides
                const prevSlides = slides.slice(0, index);
                const startTime = prevSlides.reduce((sum, s) => sum + (s.duration || 5), 0);
                const slideDuration = slide.duration || 5;

                return (
                  <div
                    key={slide.id || index}
                    className="absolute top-0 h-10 bg-purple-600 hover:bg-purple-500 border border-purple-400 rounded cursor-move transition-colors"
                    style={{
                      left: `${timeToPixels(startTime)}px`,
                      width: `${timeToPixels(slideDuration)}px`
                    }}
                    title={`${slide.name || `Slide ${index + 1}`} (${formatTime(slideDuration)})`}
                    onMouseDown={(e) => handleSlideDragStart(e, index)}
                  >
                    <div className="px-2 py-1 text-xs font-medium text-white truncate">
                      {slide.name || `Slide ${index + 1}`}
                    </div>
                    <div
                      className="absolute bottom-0 right-0 w-2 h-full bg-purple-400 cursor-ew-resize hover:bg-purple-300"
                      onMouseDown={(e) => handleStretchStart(e, 'slide', index, 'right')}
                    ></div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Audio Tracks */}
          <div className="absolute top-24 left-0 right-0 bottom-0">
            {audioTracks.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-gray-500">
                  <div className="text-2xl mb-2">🎵</div>
                  <div className="text-sm">No audio tracks yet</div>
                  <div className="text-xs mt-1">Upload audio from the Media panel</div>
                </div>
              </div>
            ) : (
              audioTracks.map((track, index) => {
                const startTime = track.startTime || 0;
                const trackDuration = track.duration || 0;

                return (
                  <div
                    key={track.id || index}
                    className="relative mb-2"
                    style={{ height: '60px' }}
                  >
                    <div className="px-2 py-1 text-xs font-semibold text-gray-400">
                      Track {index + 1}
                    </div>
                    <div
                      className={`absolute top-6 h-12 rounded cursor-move transition-all ${
                        selectedTrack === track.id
                          ? 'bg-blue-600 border-2 border-blue-400'
                          : 'bg-blue-700 hover:bg-blue-600 border border-blue-500'
                      }`}
                      style={{
                        left: `${timeToPixels(startTime)}px`,
                        width: `${timeToPixels(trackDuration)}px`
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedTrack(track.id);
                      }}
                      onMouseDown={(e) => {
                        // Check if clicking on stretch handles
                        const rect = e.currentTarget.getBoundingClientRect();
                        const clickX = e.clientX - rect.left;
                        if (clickX < 8) {
                          // Left handle
                          return; // Handle will catch this
                        } else if (clickX > rect.width - 8) {
                          // Right handle
                          return; // Handle will catch this
                        } else {
                          // Main body - drag
                          handleAudioDragStart(e, index);
                        }
                      }}
                    >
                      {/* Audio Waveform Placeholder */}
                      <div className="h-full flex items-center px-2">
                        <div className="flex-1 flex items-center gap-0.5 h-8">
                          {Array.from({ length: Math.min(50, Math.floor(timeToPixels(trackDuration) / 4)) }).map((_, i) => (
                            <div
                              key={i}
                              className="flex-1 bg-blue-300 rounded-sm"
                              style={{ height: `${20 + Math.random() * 60}%` }}
                            ></div>
                          ))}
                        </div>
                      </div>

                      {/* Track Info */}
                      <div className="absolute top-1 left-2 text-xs font-medium text-white truncate pr-8">
                        {track.name || 'Audio Track'}
                      </div>

                      {/* Stretch Handles */}
                      <div
                        className="absolute left-0 top-0 bottom-0 w-2 bg-blue-400 cursor-ew-resize hover:bg-blue-300"
                        onMouseDown={(e) => handleStretchStart(e, 'audio', index, 'left')}
                      ></div>
                      <div
                        className="absolute right-0 top-0 bottom-0 w-2 bg-blue-400 cursor-ew-resize hover:bg-blue-300"
                        onMouseDown={(e) => handleStretchStart(e, 'audio', index, 'right')}
                      ></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AudioTimeline;

