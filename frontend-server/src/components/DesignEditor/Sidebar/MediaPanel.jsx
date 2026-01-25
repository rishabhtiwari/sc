import React, { useState, useRef } from 'react';
import { useToast } from '../../../hooks/useToast';

/**
 * Media Panel
 * Features: Upload videos, audio, stock media
 */
const MediaPanel = ({ onAddElement, onAddAudioTrack }) => {
  const [uploadedMedia, setUploadedMedia] = useState([]);
  const videoInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const { showToast } = useToast();

  const handleVideoUpload = (event) => {
    const files = Array.from(event.target.files);
    
    files.forEach((file) => {
      if (file.type.startsWith('video/')) {
        const url = URL.createObjectURL(file);
        const newVideo = {
          id: `video-${Date.now()}-${Math.random()}`,
          type: 'video',
          url,
          title: file.name
        };
        setUploadedMedia(prev => [...prev, newVideo]);
        showToast('Video uploaded successfully', 'success');
      }
    });
  };

  const handleAudioUpload = (event) => {
    const files = Array.from(event.target.files);

    files.forEach((file) => {
      if (file.type.startsWith('audio/')) {
        const url = URL.createObjectURL(file);
        const newAudio = {
          id: `audio-${Date.now()}-${Math.random()}`,
          type: 'audio',
          url,
          title: file.name,
          file: file // Store file reference
        };
        setUploadedMedia(prev => [...prev, newAudio]);

        // Add to audio timeline if callback provided
        if (onAddAudioTrack) {
          onAddAudioTrack(file, url);
          showToast('Audio added to timeline', 'success');
        } else {
          showToast('Audio uploaded successfully', 'success');
        }
      }
    });
  };

  const handleAddMedia = (media) => {
    onAddElement({
      type: media.type,
      src: media.url,
      width: media.type === 'video' ? 400 : 300,
      height: media.type === 'video' ? 300 : 100
    });
    showToast(`${media.type} added to canvas`, 'success');
  };

  return (
    <div className="space-y-6">
      {/* Upload Video */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">🎬 Upload Video</h3>
        <input
          ref={videoInputRef}
          type="file"
          accept="video/*"
          multiple
          onChange={handleVideoUpload}
          className="hidden"
        />
        <button
          onClick={() => videoInputRef.current?.click()}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-2 shadow-sm"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Upload Video
        </button>
        <p className="text-xs text-gray-500 text-center">MP4, MOV, AVI up to 100MB</p>
      </div>

      {/* Upload Audio */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">🎵 Upload Audio</h3>
        <input
          ref={audioInputRef}
          type="file"
          accept="audio/*"
          multiple
          onChange={handleAudioUpload}
          className="hidden"
        />
        <button
          onClick={() => audioInputRef.current?.click()}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-2 shadow-sm"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Upload Audio
        </button>
        <p className="text-xs text-gray-500 text-center">MP3, WAV, OGG up to 50MB</p>
      </div>

      {/* Uploaded Media */}
      {uploadedMedia.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-900">Your Media</h3>
          <div className="space-y-2">
            {uploadedMedia.map((media) => (
              <div
                key={media.id}
                onClick={() => handleAddMedia(media)}
                className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="text-2xl">
                    {media.type === 'video' ? '🎬' : '🎵'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {media.title}
                    </div>
                    <div className="text-xs text-gray-500 capitalize">{media.type}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stock Media */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Stock Media</h3>
        <div className="text-sm text-gray-500 text-center py-8">
          Stock media library coming soon
        </div>
      </div>
    </div>
  );
};

export default MediaPanel;

