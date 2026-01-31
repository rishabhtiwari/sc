import React, { useState, useRef } from 'react';
import { Timeline, TimelineTrack } from '../../common/Timeline';
import SlideBlock from './SlideBlock';
import AudioBlock from './AudioBlock';
import VideoBlock from './VideoBlock';

/**
 * Audio Timeline Component - Refactored with Generic Timeline
 *
 * Uses the generic Timeline component for boundary management
 * All content (slides, audio) stays within fixed boundaries
 */
const AudioTimelineRefactored = ({
  audioTracks = [],
  videoTracks = [],
  slides = [],
  currentTime = 0,
  duration = 0,
  onAudioUpdate,
  onAudioDelete,
  onAudioSelect,
  onVideoUpdate,
  onVideoDelete,
  onVideoSelect,
  onSlideUpdate,
  onSeek,
  onPlay,
  onPause,
  isPlaying = false,
  selectedAudioId = null,
  selectedVideoId = null
}) => {
  const [selectedSlide, setSelectedSlide] = useState(null);
  const [audioWaveforms, setAudioWaveforms] = useState({});
  const [volumeEnvelopes, setVolumeEnvelopes] = useState({});
  const [slideTransitions, setSlideTransitions] = useState({});
  const [stretchState, setStretchState] = useState(null);
  const [dragState, setDragState] = useState(null);
  
  const scrollContainerRef = useRef(null);

  // Calculate total duration
  const totalDuration = (() => {
    const audioDuration = audioTracks.length > 0
      ? Math.max(...audioTracks.map(track => (track.startTime || 0) + (track.duration || 0)))
      : 0;

    const videoDuration = videoTracks.length > 0
      ? Math.max(...videoTracks.map(track => (track.startTime || 0) + (track.duration || 0)))
      : 0;

    const slidesDuration = slides.length > 0
      ? slides.reduce((sum, s) => sum + (s.duration || 5), 0)
      : 0;

    const contentDuration = Math.max(audioDuration, videoDuration, slidesDuration, duration || 0);
    return contentDuration > 0 ? contentDuration : 30;
  })();

  // Audio track color coding
  const getAudioTrackColor = (track) => {
    const type = track.type || 'music';
    const colorMap = {
      music: { bg: 'bg-green-600', hover: 'hover:bg-green-500', border: 'border-green-400', wave: 'bg-green-200', label: 'Music' },
      voiceover: { bg: 'bg-blue-600', hover: 'hover:bg-blue-500', border: 'border-blue-400', wave: 'bg-blue-200', label: 'Voiceover' },
      sfx: { bg: 'bg-purple-600', hover: 'hover:bg-purple-500', border: 'border-purple-400', wave: 'bg-purple-200', label: 'SFX' },
      default: { bg: 'bg-gray-600', hover: 'hover:bg-gray-500', border: 'border-gray-400', wave: 'bg-gray-200', label: 'Audio' }
    };
    return colorMap[type] || colorMap.default;
  };

  // Generate waveform data
  const generateWaveformData = (trackId, duration) => {
    if (audioWaveforms[trackId]) return audioWaveforms[trackId];

    const samples = 200;
    const waveform = [];
    for (let i = 0; i < samples; i++) {
      const baseAmplitude = 0.3 + Math.random() * 0.4;
      const variation = Math.sin(i / 10) * 0.2;
      waveform.push(Math.min(1, Math.max(0.1, baseAmplitude + variation)));
    }

    setAudioWaveforms(prev => ({ ...prev, [trackId]: waveform }));
    return waveform;
  };

  // Get volume envelope
  const getVolumeEnvelope = (trackId) => {
    if (!volumeEnvelopes[trackId]) {
      setVolumeEnvelopes(prev => ({
        ...prev,
        [trackId]: { volume: 100, fadeIn: 0, fadeOut: 0 }
      }));
      return { volume: 100, fadeIn: 0, fadeOut: 0 };
    }
    return volumeEnvelopes[trackId];
  };

  // Handle slide update
  const handleSlideUpdate = (slideIndex, updates) => {
    if (onSlideUpdate) {
      onSlideUpdate(slideIndex, updates);
    }
  };

  // Handle audio update
  const handleAudioUpdate = (trackId, updates) => {
    if (onAudioUpdate) {
      onAudioUpdate(trackId, updates);
    }
  };

  // Handle video update
  const handleVideoUpdate = (trackId, updates) => {
    if (onVideoUpdate) {
      onVideoUpdate(trackId, updates);
    }
  };

  // Calculate slide start times
  const getSlideStartTime = (index) => {
    // If slide has explicit startTime, use it; otherwise calculate sequentially
    if (slides[index].startTime !== undefined) {
      return slides[index].startTime;
    }
    // Fallback to sequential calculation for backward compatibility
    const prevSlides = slides.slice(0, index);
    return prevSlides.reduce((sum, s) => sum + (s.duration || 5), 0);
  };

  return (
    <div className="bg-white border-t border-gray-200 flex flex-col" style={{ height: '300px', flexShrink: 0 }}>
      {/* Timeline Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Play/Pause Button */}
          <button
            onClick={isPlaying ? onPause : onPlay}
            className="w-9 h-9 bg-blue-600 hover:bg-blue-700 rounded-md flex items-center justify-center text-white transition-colors shadow-sm"
          >
            {isPlaying ? '⏸' : '▶'}
          </button>

          <div className="text-xs font-semibold text-gray-600">⏱️ Timeline</div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-xs">
          <span className="text-gray-500">Audio:</span>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-green-600"></span>
            <span className="text-gray-600">Music</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-blue-600"></span>
            <span className="text-gray-600">Voice</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-purple-600"></span>
            <span className="text-gray-600">SFX</span>
          </div>
        </div>
      </div>

      {/* Timeline Content - Using Generic Timeline Component */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto overflow-x-hidden">
        <Timeline
          containerRef={scrollContainerRef}
          duration={totalDuration}
          currentTime={currentTime}
          isPlaying={isPlaying}
          onSeek={onSeek}
          onPlay={onPlay}
          onPause={onPause}
        >
          {/* Slides Track */}
          <TimelineTrack type="slides" height={110} label="📸 Slides / Photos">
            <div className="relative h-full pt-8">
              {slides.map((slide, index) => {
                const slideStartTime = getSlideStartTime(index);
                const slideDuration = slide.duration || 5;
                const slideEndTime = slideStartTime + slideDuration;

                // Check if any video overlaps with this slide
                const hasVideoOverlay = videoTracks.some(video => {
                  const videoStart = video.startTime || 0;
                  const videoEnd = videoStart + (video.duration || 0);
                  return (videoStart < slideEndTime && videoEnd > slideStartTime);
                });

                return (
                  <div key={slide.id || index} className="relative">
                    <SlideBlock
                      slide={slide}
                      index={index}
                      startTime={slideStartTime}
                      duration={slideDuration}
                      isSelected={selectedSlide === index}
                      onSelect={() => setSelectedSlide(index)}
                      onUpdate={(updates) => handleSlideUpdate(index, updates)}
                      onTransitionClick={index < slides.length - 1 ? () => console.log('Transition clicked') : null}
                      allSlides={slides}
                    />
                    {/* Visual indicator when video is playing over this slide */}
                    {hasVideoOverlay && (
                      <div
                        className="absolute inset-0 bg-orange-500 bg-opacity-20 pointer-events-none rounded border border-orange-400 border-dashed"
                        title="Video is playing over this slide"
                      >
                        <div className="absolute top-1 right-1 text-xs bg-orange-500 text-white px-1 rounded">
                          🎥 Video Active
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </TimelineTrack>

          {/* Video Tracks */}
          <TimelineTrack
            type="video"
            height={videoTracks.length > 0 ? (videoTracks.length * 92 + 40) : 100}
            label="🎥 Video"
          >
            <div className="relative pt-8">
              {videoTracks.map((track, index) => (
                <div key={track.id || index} className="relative mb-3" style={{ height: '80px' }}>
                  <VideoBlock
                    track={track}
                    index={index}
                    isSelected={selectedVideoId === track.id}
                    onSelect={() => onVideoSelect && onVideoSelect(track.id)}
                    onUpdate={(updates) => handleVideoUpdate(track.id, updates)}
                    onDelete={() => onVideoDelete && onVideoDelete(track.id)}
                  />
                </div>
              ))}
            </div>
          </TimelineTrack>

          {/* Audio Tracks */}
          <TimelineTrack
            type="audio"
            height={audioTracks.length > 0 ? (audioTracks.length * 92 + 40) : 100}
            label="🎵 Audio"
          >
            <div className="relative pt-8">
              {audioTracks.map((track, index) => (
                <div key={track.id || index} className="relative mb-3" style={{ height: '80px' }}>
                  <AudioBlock
                    track={track}
                    index={index}
                    isSelected={selectedAudioId === track.id}
                    onSelect={() => onAudioSelect && onAudioSelect(track.id)}
                    onUpdate={(updates) => handleAudioUpdate(track.id, updates)}
                    onDelete={() => onAudioDelete && onAudioDelete(track.id)}
                    waveformData={generateWaveformData(track.id, track.duration)}
                    volumeEnvelope={getVolumeEnvelope(track.id)}
                    colors={getAudioTrackColor(track)}
                  />
                </div>
              ))}
            </div>
          </TimelineTrack>
        </Timeline>
      </div>
    </div>
  );
};

export default AudioTimelineRefactored;

