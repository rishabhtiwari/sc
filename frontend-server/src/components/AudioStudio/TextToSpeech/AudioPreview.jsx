import React, { useState, useRef, useEffect } from 'react';
import { Card, Button } from '../../common';
import { useToast } from '../../../hooks/useToast';
import { useAudioLibrary } from '../../../hooks/useAudioLibrary';

/**
 * Audio Preview Component
 * Displays generated audio with playback controls and save option
 */
const AudioPreview = ({ audio }) => {
  const { showToast } = useToast();
  const { saveToLibrary, saving } = useAudioLibrary();
  const audioRef = useRef(null);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;

    const handleTimeUpdate = () => {
      setCurrentTime(audioElement.currentTime);
    };

    const handleLoadedMetadata = () => {
      setDuration(audioElement.duration);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    audioElement.addEventListener('timeupdate', handleTimeUpdate);
    audioElement.addEventListener('loadedmetadata', handleLoadedMetadata);
    audioElement.addEventListener('ended', handleEnded);

    return () => {
      audioElement.removeEventListener('timeupdate', handleTimeUpdate);
      audioElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audioElement.removeEventListener('ended', handleEnded);
    };
  }, [audio.url]);

  const togglePlayPause = () => {
    const audioElement = audioRef.current;
    if (!audioElement) return;

    if (isPlaying) {
      audioElement.pause();
    } else {
      audioElement.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e) => {
    const audioElement = audioRef.current;
    if (!audioElement) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * duration;
    
    audioElement.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSaveToLibrary = async () => {
    try {
      await saveToLibrary({
        name: `Voiceover - ${new Date().toLocaleString()}`,
        type: 'voiceover',
        source: 'tts',
        url: audio.url,
        duration: duration,
        generation_config: {
          provider: 'kokoro',
          model: 'kokoro-82m',
          voice: audio.voice,
          text: audio.text,
          settings: audio.settings
        }
      });
      
      showToast('Audio saved to library!', 'success');
    } catch (error) {
      showToast(error.message || 'Failed to save audio', 'error');
    }
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = audio.url;
    link.download = `voiceover_${Date.now()}.wav`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Download started', 'success');
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <Card title="🎧 Audio Preview">
      <audio ref={audioRef} src={audio.url} preload="metadata" />
      
      <div className="space-y-4">
        {/* Waveform / Progress Bar */}
        <div
          onClick={handleSeek}
          className="relative h-16 bg-gray-100 rounded-lg cursor-pointer overflow-hidden"
        >
          {/* Progress */}
          <div
            className="absolute top-0 left-0 h-full bg-blue-200 transition-all"
            style={{ width: `${progress}%` }}
          />
          
          {/* Waveform visualization (simplified) */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex items-center gap-0.5 h-full py-2">
              {Array.from({ length: 50 }).map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-blue-400 rounded-full"
                  style={{
                    height: `${Math.random() * 60 + 20}%`,
                    opacity: i / 50 < progress / 100 ? 1 : 0.3
                  }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Time Display */}
        <div className="flex justify-between text-sm text-gray-600">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3">
          {/* Play/Pause Button */}
          <button
            onClick={togglePlayPause}
            className="w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center transition-colors"
          >
            {isPlaying ? '⏸️' : '▶️'}
          </button>

          {/* Save to Library Button */}
          <Button
            onClick={handleSaveToLibrary}
            disabled={saving}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white"
          >
            {saving ? 'Saving...' : '💾 Save to Library'}
          </Button>

          {/* Download Button */}
          <Button
            onClick={handleDownload}
            className="bg-gray-600 hover:bg-gray-700 text-white"
          >
            ⬇️ Download
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default AudioPreview;

