import React, { useRef } from 'react';
import { useToast } from '../../../hooks/useToast';
import { videoLibrary, audioLibrary, imageLibrary } from '../../../services/assetLibraryService';

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
  onImageDeleteRequest,
  uploadedMedia = [],
  onUploadedMediaChange,
  onOpenAudioLibrary,
  onOpenVideoLibrary
}) => {
  const videoInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const { showToast } = useToast();

  // Loading states for uploads
  const [isUploadingVideo, setIsUploadingVideo] = React.useState(false);
  const [isUploadingAudio, setIsUploadingAudio] = React.useState(false);
  const [isUploadingImage, setIsUploadingImage] = useState(false);

  // Determine if we should show video or audio based on panel type
  const isAudioPanel = panelType === 'audio';
  const isVideoPanel = panelType === 'video';

  const handleVideoUpload = async (event) => {
    console.log('🎥 handleVideoUpload called');
    const files = Array.from(event.target.files);
    console.log('📁 Files:', files.length);

    if (files.length === 0) return;

    setIsUploadingVideo(true);
    showToast(`Uploading ${files.length} video(s)...`, 'info');

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
              showToast(`${file.name} uploaded successfully`, 'success');

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
            showToast(`${file.name} uploaded (not saved to library)`, 'warning');
          } finally {
            setIsUploadingVideo(false);
          }
        };

        video.onerror = () => {
          console.error('❌ Error loading video metadata');
          showToast(`Failed to load ${file.name}`, 'error');
          setIsUploadingVideo(false);
        };

        video.src = url;
      }
    }

    // Reset file input to allow re-uploading the same file
    event.target.value = '';
  };

  const handleAudioUpload = async (event) => {
    console.log('🎵 handleAudioUpload called');
    const files = Array.from(event.target.files);
    console.log('📁 Files:', files.length);

    // Reset file input immediately to allow re-uploading the same file
    // But keep reference to files array
    event.target.value = '';

    if (files.length === 0) return;

    setIsUploadingAudio(true);
    showToast(`Uploading ${files.length} audio file(s)...`, 'info');

    for (const file of files) {
      if (file.type.startsWith('audio/')) {
        const url = URL.createObjectURL(file);
        const audio = new Audio();

        audio.onloadedmetadata = async () => {
          try {
            console.log('🎵 Audio metadata loaded, duration:', audio.duration);
            console.log('🎵 File object:', file, 'Type:', file.type, 'Size:', file.size);

            // Upload to audio library
            const libraryResponse = await audioLibrary.upload(file, file.name, audio.duration);

            if (libraryResponse.success && libraryResponse.audio) {
              console.log('✅ Audio uploaded to library:', libraryResponse.audio);

              const newAudio = {
                id: libraryResponse.audio.audio_id,
                type: 'audio',
                url: libraryResponse.audio.url,
                title: libraryResponse.audio.name,
                duration: libraryResponse.audio.duration,
                libraryId: libraryResponse.audio.audio_id,
                assetId: libraryResponse.audio.audio_id
              };

              onUploadedMediaChange(prev => [...prev, newAudio]);
              showToast(`${file.name} uploaded successfully`, 'success');

              // Revoke blob URL after successful upload
              URL.revokeObjectURL(url);
            }
          } catch (error) {
            console.error('❌ Error uploading audio to library:', error);
            console.error('❌ Error details:', error.response?.data);
            showToast(`Failed to upload ${file.name}`, 'error');
          } finally {
            setIsUploadingAudio(false);
          }
        };

        audio.onerror = () => {
          console.error('❌ Error loading audio metadata');
          showToast(`Failed to load ${file.name}`, 'error');
          setIsUploadingAudio(false);
          URL.revokeObjectURL(url);
        };

        audio.src = url;
      }
    }
  };

  /**
   * Handle image file upload
   */
  const handleImageUpload = async (event) => {
    console.log('🖼️ handleImageUpload called');
    const files = Array.from(event.target.files);
    console.log('📁 Files:', files.length);

    if (files.length === 0) return;

    setIsUploadingImage(true);
    showToast(`Uploading ${files.length} image(s)...`, 'info');

    for (const file of files) {
      if (file.type.startsWith('image/')) {
        try {
          console.log('🖼️ Uploading image:', file.name);

          // Upload to image library
          const libraryResponse = await imageLibrary.upload(file, file.name);

          if (libraryResponse.success && libraryResponse.image) {
            console.log('✅ Image uploaded to library:', libraryResponse.image);

            const newImage = {
              id: libraryResponse.image.image_id,
              type: 'image',
              url: libraryResponse.image.url,
              title: libraryResponse.image.name,
              libraryId: libraryResponse.image.image_id,
              assetId: libraryResponse.image.image_id
            };

            onUploadedMediaChange(prev => [...prev, newImage]);
            showToast(`${file.name} uploaded successfully`, 'success');
          }
        } catch (error) {
          console.error('❌ Error uploading image to library:', error);
          console.error('❌ Error details:', error.response?.data);
          showToast(`Failed to upload ${file.name}`, 'error');
        }
      }
    }

    setIsUploadingImage(false);

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
        // Pass audio metadata including audio_id/libraryId to preserve library reference
        const audioMetadata = {
          name: media.title || media.name,
          audio_id: media.audio_id || media.libraryId,
          libraryId: media.libraryId || media.audio_id,
          assetId: media.assetId
        };
        onAddAudioTrack(audioMetadata, media.url);
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
                name: media.title || media.file?.name || 'Video',
                src: media.url,
                width: 640,
                height: 360,
                duration: video.duration,
                originalDuration: video.duration, // Store natural duration for looping
                trimStart: 0,
                trimEnd: video.duration,
                playbackSpeed: 1,
                volume: 100,
                muted: false,
                loop: false,
                file: media.file,
                // Preserve library reference if it exists
                libraryId: media.libraryId || media.video_id,
                assetId: media.assetId || media.libraryId || media.video_id
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
          name: media.title || media.file?.name || 'Video',
          src: media.url,
          width: 640,
          height: 360,
          duration: media.duration,
          originalDuration: media.duration, // Store natural duration for looping
          trimStart: 0,
          trimEnd: media.duration,
          playbackSpeed: 1,
          volume: 100,
          muted: false,
          loop: false,
          file: media.file,
          // Preserve library reference if it exists
          libraryId: media.libraryId || media.video_id,
          assetId: media.assetId || media.libraryId || media.video_id
        });
        showToast('Video added to canvas', 'success');
      }
    } else if (media.type === 'image') {
      // For images - include all default properties
      onAddElement({
        type: 'image',
        name: media.title || media.file?.name || 'Image',
        src: media.url,
        width: 300,
        height: 200,
        x: 100,
        y: 100,
        // Transform properties
        rotation: 0,
        opacity: 1,
        flipX: false,
        flipY: false,
        // Border properties
        borderWidth: 0,
        borderRadius: 0,
        borderColor: '#000000',
        // Effects properties
        brightness: 100,
        contrast: 100,
        saturation: 100,
        blur: 0,
        file: media.file,
        // Preserve library reference if it exists
        libraryId: media.libraryId || media.image_id,
        assetId: media.assetId || media.image_id
      });
      showToast('Image added to canvas', 'success');
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
              disabled={isUploadingVideo}
              className="flex-1 px-3 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center justify-center gap-1.5 shadow-sm"
            >
              {isUploadingVideo ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Uploading...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload
                </>
              )}
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
              disabled={isUploadingAudio}
              className="flex-1 px-3 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center justify-center gap-1.5 shadow-sm"
            >
              {isUploadingAudio ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Uploading...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload
                </>
              )}
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

      {/* Image Section - Show on both tabs */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">🖼️ Images</h3>
        <input
          ref={imageInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleImageUpload}
          className="hidden"
        />
        <button
          onClick={() => imageInputRef.current?.click()}
          disabled={isUploadingImage}
          className="w-full px-3 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center justify-center gap-1.5 shadow-sm"
        >
          {isUploadingImage ? (
            <>
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Uploading...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Upload
            </>
          )}
        </button>
        <p className="text-xs text-gray-500 text-center">PNG, JPG, GIF up to 10MB</p>
      </div>

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
                          // NOTE: We only remove from editor (canvas/timeline/media list), NOT from backend library
                          // Users must go to the asset library to permanently delete assets

                          // If it's audio, find the audio track and delete from both timeline and media library
                          if (media.type === 'audio') {
                            const audioTrack = audioTracks.find(track => track.url === media.url);
                            if (onAudioDeleteRequest) {
                              // Always use delete request handler (shows confirmation)
                              onAudioDeleteRequest(audioTrack?.id || null, media.title, media.id);
                            } else {
                              // Fallback: just delete from media library
                              onUploadedMediaChange(prev => prev.filter(m => m.id !== media.id));
                              showToast('Media removed from editor', 'success');
                            }
                          } else if (media.type === 'video') {
                            // For video, find the video track and delete from both timeline and media library
                            const videoTrack = videoTracks.find(track => track.url === media.url);
                            if (onVideoDeleteRequest) {
                              // Always use delete request handler (shows confirmation)
                              onVideoDeleteRequest(videoTrack?.id || null, media.title, media.id);
                            } else {
                              // Fallback: just delete from media library
                              onUploadedMediaChange(prev => prev.filter(m => m.id !== media.id));
                              showToast('Media removed from editor', 'success');
                            }
                          } else if (media.type === 'image') {
                            // For image, delete from both canvas and media library
                            if (onImageDeleteRequest) {
                              onImageDeleteRequest(media.url, media.title, media.id);
                            } else {
                              // Fallback: just delete from media library
                              onUploadedMediaChange(prev => prev.filter(m => m.id !== media.id));
                              showToast('Image deleted from library', 'success');
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

