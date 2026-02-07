import React, { useState, useEffect, useRef } from 'react';
import { TimelineContext } from './TimelineContext';

/**
 * Generic Timeline Component
 * 
 * A reusable timeline component with fixed start and end boundaries.
 * All content (slides, audio, video) must fit within these boundaries.
 * 
 * @param {Object} props
 * @param {React.RefObject} props.containerRef - Reference to parent container for boundary calculation
 * @param {number} props.duration - Total duration of timeline in seconds
 * @param {number} props.currentTime - Current playhead position in seconds
 * @param {boolean} props.isPlaying - Whether timeline is playing
 * @param {Function} props.onSeek - Callback when seeking to a new time
 * @param {Function} props.onPlay - Callback when play is triggered
 * @param {Function} props.onPause - Callback when pause is triggered
 * @param {Object} props.padding - Padding for timeline boundaries (default: { left: 40, right: 40 })
 * @param {React.ReactNode} props.children - Timeline tracks and content
 */
const Timeline = ({
  containerRef,
  duration = 30,
  currentTime = 0,
  isPlaying = false,
  onSeek,
  onPlay,
  onPause,
  padding = { left: 40, right: 40 },
  children
}) => {
  const timelineRef = useRef(null);
  const [containerWidth, setContainerWidth] = useState(0);

  // Measure container width
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef?.current) {
        const width = containerRef.current.clientWidth;
        setContainerWidth(width);
        console.log('📏 Timeline container width:', width);
      }
    };

    updateWidth();
    
    // Use ResizeObserver for more accurate tracking
    const resizeObserver = new ResizeObserver(updateWidth);
    if (containerRef?.current) {
      resizeObserver.observe(containerRef.current);
    }

    window.addEventListener('resize', updateWidth);
    
    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', updateWidth);
    };
  }, [containerRef]);

  // Calculate available width and scaling
  const paddingTotal = padding.left + padding.right;
  const availableWidth = containerWidth - paddingTotal;
  const pixelsPerSecond = duration > 0 ? availableWidth / duration : 50;

  // Debug logging
  useEffect(() => {
    console.log('📊 Timeline Scaling:', {
      containerWidth,
      paddingTotal,
      availableWidth,
      duration,
      pixelsPerSecond,
      totalTimelineWidth: duration * pixelsPerSecond
    });
  }, [containerWidth, duration, pixelsPerSecond, availableWidth, paddingTotal]);

  // Time conversion functions
  const timeToPixels = (time) => {
    const pixels = time * pixelsPerSecond;
    return Math.max(0, pixels); // Only clamp to 0, allow extending beyond available width
  };

  const pixelsToTime = (pixels) => {
    return pixels / pixelsPerSecond;
  };

  // Handle timeline click to seek
  const handleTimelineClick = (e) => {
    if (!timelineRef.current) return;

    // Don't seek if clicking on interactive elements
    if (e.target.classList.contains('cursor-ew-resize') || 
        e.target.classList.contains('cursor-move') ||
        e.target.closest('.cursor-ew-resize') ||
        e.target.closest('.cursor-move')) {
      return;
    }

    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left - padding.left;
    const time = pixelsToTime(clickX);

    if (onSeek) {
      onSeek(Math.max(0, Math.min(time, duration)));
    }
  };

  // Format time as MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Context value
  const contextValue = {
    timeToPixels,
    pixelsToTime,
    availableWidth,
    containerWidth,
    padding,
    totalDuration: duration,
    currentTime,
    isPlaying,
    onSeek,
    onPlay,
    onPause,
    formatTime
  };

  console.log('🎬 Timeline render:', {
    containerWidth,
    availableWidth,
    duration,
    pixelsPerSecond,
    endPosition: timeToPixels(duration)
  });

  return (
    <TimelineContext.Provider value={contextValue}>
      <div
        ref={timelineRef}
        className="relative h-full bg-gray-50"
        onClick={handleTimelineClick}
        style={{
          paddingLeft: `${padding.left}px`,
          paddingRight: `${padding.right}px`
        }}
      >
        {/* Content */}
        {children}

        {/* Playhead - Rendered AFTER content to appear on top */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-500 pointer-events-none"
          style={{
            left: `${padding.left + Math.min(timeToPixels(currentTime), timeToPixels(duration))}px`,
            zIndex: 9999
          }}
        >
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-3 h-3 bg-red-500 rounded-full shadow-sm"></div>
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2 px-1 py-0.5 bg-red-500 text-white text-xs rounded whitespace-nowrap">
            {formatTime(currentTime)}
          </div>
        </div>

        {/* Timeline End Boundary Marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-green-500 pointer-events-none opacity-30"
          style={{
            left: `${padding.left + timeToPixels(duration)}px`,
            zIndex: 9998
          }}
          title="Timeline End Boundary"
        >
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 px-1 py-0.5 bg-green-500 text-white text-xs rounded">
            END
          </div>
        </div>
      </div>
    </TimelineContext.Provider>
  );
};

export default Timeline;

