import React, { useState, useEffect } from 'react';
import { useTimeline } from '../../common/Timeline';

/**
 * Video Block Component
 * Renders a single video block on the timeline with thumbnail and stretch handles
 */
const VideoBlock = ({
  track,
  index,
  isSelected,
  onSelect,
  onUpdate,
  onDelete
}) => {
  const { timeToPixels, pixelsToTime, formatTime } = useTimeline();
  const [isStretching, setIsStretching] = useState(false);
  const [stretchStart, setStretchStart] = useState(null);
  const [thumbnail, setThumbnail] = useState(null);

  const startTime = track.startTime || 0;
  const duration = track.duration || 5;
  const originalDuration = track.originalDuration || track.duration || 5;

  const blockWidth = timeToPixels(duration);
  const leftPosition = timeToPixels(startTime);

  // Generate video thumbnail
  useEffect(() => {
    if (track.url) {
      const video = document.createElement('video');
      video.src = track.url;
      video.crossOrigin = 'anonymous';
      
      video.addEventListener('loadeddata', () => {
        video.currentTime = 0.1; // Seek to 0.1s for thumbnail
      });

      video.addEventListener('seeked', () => {
        const canvas = document.createElement('canvas');
        canvas.width = 160;
        canvas.height = 90;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        setThumbnail(canvas.toDataURL());
      });
    }
  }, [track.url]);

  // Handle stretch start
  const handleStretchStart = (e, edge) => {
    e.stopPropagation();
    e.preventDefault();
    
    setIsStretching(true);
    setStretchStart({
      x: e.clientX,
      startTime,
      duration,
      edge
    });
  };

  // Handle mouse move
  useEffect(() => {
    if (!isStretching || !stretchStart) return;

    const handleMouseMove = (e) => {
      const deltaX = e.clientX - stretchStart.x;
      const deltaTime = pixelsToTime(deltaX);

      if (stretchStart.edge === 'right') {
        const newDuration = Math.max(0.5, stretchStart.duration + deltaTime);
        onUpdate({ duration: newDuration });
      } else if (stretchStart.edge === 'left') {
        const newStartTime = Math.max(0, stretchStart.startTime + deltaTime);
        const newDuration = Math.max(0.5, stretchStart.duration - deltaTime);
        onUpdate({ startTime: newStartTime, duration: newDuration });
      }
    };

    const handleMouseUp = () => {
      setIsStretching(false);
      setStretchStart(null);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isStretching, stretchStart, pixelsToTime, onUpdate]);

  // Calculate if video is stretched or trimmed
  const isStretched = duration > originalDuration;
  const isTrimmed = duration < originalDuration;

  return (
    <div
      className={`absolute top-0 h-full rounded shadow-md cursor-move transition-all ${
        isSelected
          ? 'ring-2 ring-orange-400 ring-offset-1'
          : 'hover:shadow-lg'
      } bg-gradient-to-r from-orange-600 to-orange-500 border-2 border-orange-400`}
      style={{
        left: `${leftPosition}px`,
        width: `${blockWidth}px`,
        minWidth: '40px'
      }}
      onClick={(e) => {
        e.stopPropagation();
        onSelect();
      }}
    >
      {/* Video Thumbnail Background */}
      {thumbnail && (
        <div 
          className="absolute inset-0 rounded opacity-40"
          style={{
            backgroundImage: `url(${thumbnail})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'repeat-x'
          }}
        />
      )}

      {/* Video Info Overlay */}
      <div className="relative h-full flex flex-col justify-between p-2">
        <div className="flex items-start justify-between gap-1">
          <div className="flex-1 min-w-0">
            <div className="text-xs font-semibold text-white truncate flex items-center gap-1">
              <span>🎥</span>
              <span>{track.name || `Video ${index + 1}`}</span>
            </div>
            <div className="text-xs text-orange-100 mt-0.5">
              {formatTime(duration)}
              {isStretched && <span className="ml-1">🔁</span>}
              {isTrimmed && <span className="ml-1">✂️</span>}
            </div>
          </div>
        </div>
      </div>

      {/* Left Stretch Handle */}
      <div
        className="absolute left-0 top-0 bottom-0 w-2 bg-orange-400 cursor-ew-resize hover:bg-orange-300 transition-colors border-r border-orange-300 z-20"
        onMouseDown={(e) => handleStretchStart(e, 'left')}
        onClick={(e) => e.stopPropagation()}
        title="Drag to adjust start time"
      />

      {/* Right Stretch Handle */}
      <div
        className="absolute right-0 top-0 bottom-0 w-2 bg-orange-400 cursor-ew-resize hover:bg-orange-300 transition-colors border-l border-orange-300 z-20"
        onMouseDown={(e) => handleStretchStart(e, 'right')}
        onClick={(e) => e.stopPropagation()}
        title="Drag to adjust duration"
      />
    </div>
  );
};

export default VideoBlock;

