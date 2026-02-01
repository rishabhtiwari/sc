import React from 'react';
import AudioLibraryPanel from '../../AudioStudio/AudioLibrary/AudioLibraryPanel';

/**
 * Audio Library Modal - Full-screen modal for browsing audio library
 * Similar to AudioStudio modal but focused on library browsing
 */
const AudioLibrary = ({ isOpen, onClose, onAddToCanvas }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-2xl w-[95%] h-[95%] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">📁</span>
              <h1 className="text-2xl font-bold text-gray-900">Audio Library</h1>
            </div>
            <button
              onClick={onClose}
              className="text-gray-600 hover:text-gray-900 text-2xl font-bold transition-colors"
            >
              ✕
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Browse and add audio files from your library to the timeline
          </p>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
          <AudioLibraryPanel 
            onAddToCanvas={onAddToCanvas}
          />
        </div>
      </div>
    </div>
  );
};

export default AudioLibrary;

