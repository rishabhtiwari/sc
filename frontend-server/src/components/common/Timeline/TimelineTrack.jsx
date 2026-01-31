import React from 'react';

/**
 * Timeline Track Component
 * 
 * Represents a single track in the timeline (e.g., slides, audio, video).
 * 
 * @param {Object} props
 * @param {string} props.type - Type of track ('slides', 'audio', 'video')
 * @param {number} props.height - Height of the track in pixels
 * @param {string} props.label - Optional label for the track
 * @param {string} props.className - Additional CSS classes
 * @param {React.ReactNode} props.children - Track content (blocks)
 */
const TimelineTrack = ({
  type = 'generic',
  height = 80,
  label,
  className = '',
  children
}) => {
  const getTrackStyles = () => {
    switch (type) {
      case 'slides':
        return 'bg-white border-b border-gray-200';
      case 'audio':
        return 'bg-gray-50 border-b border-gray-100';
      case 'video':
        return 'bg-blue-50 border-b border-blue-100';
      default:
        return 'bg-white border-b border-gray-200';
    }
  };

  return (
    <div
      className={`relative ${getTrackStyles()} ${className}`}
      style={{ height: `${height}px` }}
    >
      {label && (
        <div className="absolute top-0 left-0 px-2 py-1 text-xs font-semibold text-gray-600 bg-white bg-opacity-80 z-10">
          {label}
        </div>
      )}
      {children}
    </div>
  );
};

export default TimelineTrack;

