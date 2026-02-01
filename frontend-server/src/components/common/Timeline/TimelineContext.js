import { createContext, useContext } from 'react';

/**
 * Timeline Context
 * Provides timeline calculations and state to all child components
 */
export const TimelineContext = createContext({
  // Time conversion functions
  timeToPixels: (time) => 0,
  pixelsToTime: (pixels) => 0,
  
  // Dimensions
  availableWidth: 0,
  containerWidth: 0,
  padding: { left: 40, right: 40 },
  
  // Timeline state
  totalDuration: 0,
  currentTime: 0,
  isPlaying: false,
  
  // Callbacks
  onSeek: (time) => {},
  onPlay: () => {},
  onPause: () => {},
});

/**
 * Hook to access timeline context
 */
export const useTimeline = () => {
  const context = useContext(TimelineContext);
  if (!context) {
    throw new Error('useTimeline must be used within a Timeline component');
  }
  return context;
};

