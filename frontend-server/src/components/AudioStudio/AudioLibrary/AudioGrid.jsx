import React from 'react';
import AudioCard from './AudioCard';

/**
 * Audio Grid Component
 * Grid layout for audio files
 */
const AudioGrid = ({ audioFiles, onDelete, onAddToCanvas }) => {
  return (
    <div className="space-y-3">
      {audioFiles.map((audio) => (
        <AudioCard
          key={audio.audio_id}
          audio={audio}
          onDelete={onDelete}
          onAddToCanvas={onAddToCanvas}
        />
      ))}
    </div>
  );
};

export default AudioGrid;

