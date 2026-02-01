import React, { useRef } from 'react';
import { useToast } from '../../../hooks/useToast';
import { videoLibrary } from '../../../services/assetLibraryService';

/**
 * Media Panel
 * Features: Upload videos, audio, stock media
 */
const MediaPanel = ({
  onAddElement,
  onAddAudioTrack,
  panelType,
  audioTracks = [],
  onAudioSelect,
  onAudioDeleteRequest,
  videoTracks = [],
  onVideoDeleteRequest,
  uploadedMedia = [],
  onUploadedMediaChange,
  onOpenAudioLibrary,
  onOpenVideoLibrary
}) => {
  const videoInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const { showToast } = useToast();

  // Determine if we should show video or audio based on panel type
  const isAudioPanel = panelType === 'audio';
  const isVideoPanel = panelType === 'video';

  const handleVideoUpload = async (event) => {
    console.log('🎥 handleVideoUpload called');
    const files = Array.from(event.target.files);
    console.log('📁 Files:', files.length);

    for (const file of files) {
      if (file.type.startsWith('video/')) {
        const url = URL.createObjectURL(file);

        // Create video element to get duration
        const video = document.createElement('video');
        video.preload = 'metadata';

        video.onloadedmetadata = async () => {
          try {
            console.log('📤 Uploading video to library:', file.name);

            // Upload to video library
            const libraryResponse = await videoLibrary.upload(file, file.name, video.duration);

            if (libraryResponse.success && libraryResponse.video) {
              console.log('✅ Video saved to library:', libraryResponse.video);

              const newVideo = {
                id: libraryResponse.video.video_id,
                type: 'video',
                url: libraryResponse.video.url, // Use library URL (starts with /api/)
                title: libraryResponse.video.name,
                duration: libraryResponse.video.duration,
                libraryId: libraryResponse.video.video_id, // Track library ID for deletion
                // No file property - it's in library now
              };

              console.log('➕ Adding to uploadedMedia:', newVideo);
              onUploadedMediaChange(prev => [...prev, newVideo]);
              showToast('Video uploaded to library', 'success');

              // Revoke blob URL since we have library URL now
              URL.revokeObjectURL(url);
            } else {
              throw new Error('Failed to upload video to library');
            }
          } catch (error) {
            console.error('❌ Error uploading video to library:', error);

            // Fallback: Add with blob URL (old behavior)
            const newVideo = {
              id: `video-${Date.now()}-${Math.random()}`,
              type: 'video',
              url,
              title: file.name,
              file: file,
              duration: video.duration
            };
            onUploadedMediaChange(prev => [...prev, newVideo]);
            showToast('Video uploaded (not saved to library)', 'warning');
          }
        };

        video.src = url;
      }
    }

    // Reset file input to allow re-uploading the same file
    event.target.value = '';
  };

  const handleAudioUpload = (event) => {
    console.log('🎵 handleAudioUpload called');
    const files = Array.from(event.target.files);
    console.log('📁 Files:', files.length);

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
        console.log('➕ Adding to uploadedMedia:', newAudio);
        onUploadedMediaChange(prev => [...prev, newAudio]);

        // Add to audio timeline if callback provided
        if (onAddAudioTrack) {
          console.log('🎬 Calling onAddAudioTrack for:', file.name);
          onAddAudioTrack(file, url);
          showToast('Audio added to timeline', 'success');
        } else {
          showToast('Audio uploaded successfully', 'success');
        }
      }
    });

    // Reset file input to allow re-uploading the same file
    event.target.value = '';
  };

  const handleAddMedia = (media) => {
    console.log('🔍 handleAddMedia called for:', media);
    console.log('🔍 Current audioTracks:', audioTracks);

    // If it's audio, add to timeline instead of canvas
    if (media.type === 'audio') {
      // Check if this audio is already on the timeline
      const existingTrack = audioTracks.find(track => track.url === media.url);
      console.log('🔍 Existing track:', existingTrack);

      if (!existingTrack && onAddAudioTrack) {
        console.log('✅ Calling onAddAudioTrack for:', media.title);
        // Re-create the file object from the media
        const file = media.file || { name: media.title };
        onAddAudioTrack(file, media.url);
        showToast('Audio added to timeline', 'success');
      } else if (existingTrack) {
        console.log('⚠️ Audio already on timeline:', media.title);
        showToast('Audio already on timeline', 'info');
      } else {
        console.log('❌ onAddAudioTrack not available');
      }
    } else if (media.type === 'video') {
      // For video, add to canvas as an element
      console.log('🎬 Adding video to canvas. Duration:', media.duration);

      // If duration is not available, try to get it from the video element
      if (!media.duration || media.duration === 0) {
        console.warn('⚠️ Video duration not available, attempting to extract...');

        const extractDuration = async () => {
          try {
            let videoUrl = media.url;

            // If this is an API URL, fetch it with authentication
            const isApiUrl = media.url.startsWith('/api/');
            if (isApiUrl) {
              const token = localStorage.getItem('auth_token');
              if (!token) {
                console.error('No auth token for video duration extraction');
                showToast('Authentication required', 'error');
                return;
              }

              const response = await fetch(media.url, {
                headers: { 'Authorization': `Bearer ${token}` }
              });

              if (!response.ok) {
                console.error('Failed to fetch video for duration:', response.status);
                showToast('Failed to load video', 'error');
                return;
              }

              const blob = await response.blob();
              videoUrl = URL.createObjectURL(blob);
            }

            const video = document.createElement('video');
            video.preload = 'metadata';
            video.onloadedmetadata = () => {
              console.log('✅ Video duration extracted:', video.duration);
              onAddElement({
                type: 'video',
                src: media.url,
                width: 640,
                height: 360,
                duration: video.duration,
                trimStart: 0,
                trimEnd: video.duration,
                playbackSpeed: 1,
                volume: 100,
                muted: false,
                loop: false,
                file: media.file
              });
              showToast('Video added to canvas', 'success');

              // Cleanup blob URL if we created one
              if (isApiUrl && videoUrl.startsWith('blob:')) {
                URL.revokeObjectURL(videoUrl);
              }
            };
            video.src = videoUrl;
          } catch (error) {
            console.error('Error extracting video duration:', error);
            showToast('Failed to load video', 'error');
          }
        };

        extractDuration();
      } else {
        onAddElement({
          type: 'video',
          src: media.url,
          width: 640,
          height: 360,
          duration: media.duration,
          trimStart: 0,
          trimEnd: media.duration,
          playbackSpeed: 1,
          volume: 100,
          muted: false,
          loop: false,
          file: media.file
        });
        showToast('Video added to canvas', 'success');
      }
    } else {
      // For other media types
      onAddElement({
        type: media.type,
        src: media.url,
        width: 300,
        height: 200
      });
      showToast(`${media.type} added to canvas`, 'success');
    }
  };

  return (
    <div className="space-y-6">
      {/* Video Section - Only show on video tab */}
      {!isAudioPanel && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-900">🎬 Video</h3>
          <input
            ref={videoInputRef}
            type="file"
            accept="video/*"
            multiple
            onChange={handleVideoUpload}
            className="hidden"
          />
          {/* Upload and Library buttons side-by-side */}
          <div className="flex gap-2">
            <button
              onClick={() => videoInputRef.current?.click()}
              className="flex-1 px-3 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-1.5 shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Upload
            </button>
            {onOpenVideoLibrary && (
              <button
                onClick={onOpenVideoLibrary}
                className="flex-1 px-3 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-1.5 shadow-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                </svg>
                Library
              </button>
            )}
          </div>
          <p className="text-xs text-gray-500 text-center">MP4, MOV, AVI up to 100MB</p>
        </div>
      )}

      {/* Audio Section - Only show on audio tab */}
      {!isVideoPanel && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-900">🎵 Audio</h3>
          <input
            ref={audioInputRef}
            type="file"
            accept="audio/*"
            multiple
            onChange={handleAudioUpload}
            className="hidden"
          />
          {/* Upload and Library buttons side-by-side */}
          <div className="flex gap-2">
            <button
              onClick={() => audioInputRef.current?.click()}
              className="flex-1 px-3 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-1.5 shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Upload
            </button>
            {onOpenAudioLibrary && (
              <button
                onClick={onOpenAudioLibrary}
                className="flex-1 px-3 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-1.5 shadow-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                </svg>
                Library
              </button>
            )}
          </div>
          <p className="text-xs text-gray-500 text-center">MP3, WAV, OGG up to 50MB</p>
        </div>
      )}

      {/* Uploaded Media */}
      {uploadedMedia.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-900">Your Media</h3>
          <div className="space-y-2">
            {uploadedMedia.map((media) => (
              <div
                key={media.id}
                className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="text-2xl">
                    {media.type === 'video' ? '🎬' : media.type === 'image' ? '🖼️' : '🎵'}
                  </div>
                  <div
                    className="flex-1 min-w-0 cursor-pointer"
                    onClick={() => handleAddMedia(media)}
                  >
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {media.title}
                    </div>
                    <div className="text-xs text-gray-500 capitalize">{media.type}</div>
                  </div>

                  {/* Action Icons */}
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {/* Properties Icon - Only show for audio on timeline */}
                    {media.type === 'audio' && audioTracks.find(track => track.url === media.url) && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // Find the corresponding audio track
                          const audioTrack = audioTracks.find(track => track.url === media.url);
                          if (audioTrack && onAudioSelect) {
                            onAudioSelect(audioTrack.id);
                          }
                        }}
                        className="p-1.5 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm transition-colors opacity-0 group-hover:opacity-100"
                        title="Edit properties"
                      >
                        ⚙️
                      </button>
                    )}

                    {/* Delete Icon - Always show */}
                    <button
                      onClick={async (e) => {
                        e.stopPropagation();

                        try {
                          // Delete from backend library if it has a libraryId
                          if (media.libraryId && media.type === 'video') {
                            console.log(`🗑️ Deleting video from library: ${media.libraryId}`);
                            await videoLibrary.delete(media.libraryId);
                            console.log('✅ Deleted from library');
                          }

                          // If it's audio, find the audio track and delete from both timeline and media library
                          if (media.type === 'audio') {
                            const audioTrack = audioTracks.find(track => track.url === media.url);
                            if (audioTrack && onAudioDeleteRequest) {
                              // Delete from both timeline and media library
                              onAudioDeleteRequest(audioTrack.id, media.title, media.id);
                            } else {
                              // Audio not on timeline, just delete from media library
                              onUploadedMediaChange(prev => prev.filter(m => m.id !== media.id));
                              showToast('Media deleted', 'success');
                            }
                          } else if (media.type === 'video') {
                            // For video, find the video track and delete from both timeline and media library
                            const videoTrack = videoTracks.find(track => track.url === media.url);
                            if (videoTrack && onVideoDeleteRequest) {
                              // Delete from both timeline and media library
                              onVideoDeleteRequest(videoTrack.id, media.title, media.id);
                            } else {
                              // Video not on timeline, just delete from media library
                              onUploadedMediaChange(prev => prev.filter(m => m.id !== media.id));
                              showToast('Media deleted from library', 'success');
                            }
                          } else {
                            // For other media types, just delete from media library
                            onUploadedMediaChange(prev => prev.filter(m => m.id !== media.id));
                            showToast('Media deleted', 'success');
                          }
                        } catch (error) {
                          console.error('❌ Error deleting media:', error);
                          showToast('Failed to delete media from library', 'error');
                        }
                      }}
                      className="p-1.5 bg-red-500 hover:bg-red-600 text-white rounded text-sm transition-colors opacity-0 group-hover:opacity-100"
                      title="Delete media"
                    >
                      🗑️
                    </button>
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

