/**
 * Asset Library Service
 * Handles image and video library operations
 */
import api from './api';

/**
 * Image Library Operations
 */
export const imageLibrary = {
  /**
   * Upload image to library
   */
  async upload(file, name = null) {
    try {
      console.log('🔍 imageLibrary.upload called with:', { file, name, fileType: file?.type, fileSize: file?.size });

      const formData = new FormData();
      formData.append('file', file);

      // Log FormData contents
      console.log('📦 FormData created, has file:', formData.has('file'));

      // Send name as query parameter (backend expects it as Query param)
      const params = new URLSearchParams();
      params.append('name', name || file.name);

      console.log('🚀 Sending POST request to:', `/image-library/library?${params.toString()}`);

      // Don't set Content-Type header - let browser set it with boundary
      const response = await api.post(`/image-library/library?${params.toString()}`, formData);

      console.log('✅ Upload successful:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error uploading image to library:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Get all images from library
   */
  async list(page = 1, pageSize = 50, folder = null) {
    try {
      const params = { page, page_size: pageSize };
      if (folder) params.folder = folder;

      const response = await api.get('/image-library/library', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching image library:', error);
      throw error;
    }
  },

  /**
   * Delete image from library
   */
  async delete(imageId) {
    try {
      const response = await api.delete(`/image-library/library/${imageId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting image from library:', error);
      throw error;
    }
  },
};

/**
 * Video Library Operations
 */
export const videoLibrary = {
  /**
   * Upload video to library
   */
  async upload(file, name = null, duration = 0) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Send name and duration as query parameters (backend expects them as Query params)
      const params = new URLSearchParams();
      params.append('name', name || file.name);
      params.append('duration', duration.toString());

      // Don't set Content-Type header - let browser set it with boundary
      const response = await api.post(`/video-library/library?${params.toString()}`, formData);

      return response.data;
    } catch (error) {
      console.error('Error uploading video to library:', error);
      throw error;
    }
  },

  /**
   * Get all videos from library
   */
  async list(page = 1, pageSize = 50, folder = null) {
    try {
      const params = { page, page_size: pageSize };
      if (folder) params.folder = folder;

      const response = await api.get('/video-library/library', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching video library:', error);
      throw error;
    }
  },

  /**
   * Delete video from library
   */
  async delete(videoId) {
    try {
      const response = await api.delete(`/video-library/library/${videoId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting video from library:', error);
      throw error;
    }
  },
};

/**
 * Audio Library Operations (for consistency)
 */
export const audioLibrary = {
  /**
   * Upload audio file to library
   * This is a two-step process:
   * 1. Upload file to get a URL
   * 2. Save metadata to audio library
   */
  async upload(file, name = null, duration = 0) {
    try {
      console.log('🎵 Uploading audio file to library:', name || file.name);

      // Step 1: Upload the file to get a URL
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type', 'audio');
      formData.append('name', name || file.name);

      const uploadResponse = await api.post('/assets/upload', formData);

      if (!uploadResponse.data || !uploadResponse.data.asset_id) {
        throw new Error('Failed to upload audio file');
      }

      const audioUrl = uploadResponse.data.url;
      const assetId = uploadResponse.data.asset_id;

      console.log('✅ Audio file uploaded, saving to library...');

      // Step 2: Save to audio library with metadata
      const libraryData = {
        audio_url: audioUrl,
        text: name || file.name,
        duration: duration,
        voice: 'uploaded',
        voice_name: 'Uploaded Audio',
        language: 'en',
        speed: 1.0,
        model: 'uploaded',
        folder: '',
        tags: []
      };

      const libraryResponse = await api.post('/audio-studio/library', libraryData);

      if (!libraryResponse.data || !libraryResponse.data.asset_id) {
        console.warn('Failed to save audio to library, using direct upload');
        return {
          success: true,
          audio: {
            audio_id: assetId,
            url: audioUrl,
            name: name || file.name,
            duration: duration
          }
        };
      }

      console.log('✅ Audio saved to library:', libraryResponse.data.asset_id);

      return {
        success: true,
        audio: {
          audio_id: libraryResponse.data.asset_id,
          url: libraryResponse.data.url || audioUrl,
          name: name || file.name,
          duration: duration
        }
      };
    } catch (error) {
      console.error('Error uploading audio to library:', error);
      throw error;
    }
  },

  /**
   * Get all audio from library
   */
  async list(page = 1, pageSize = 50) {
    try {
      const params = { page, page_size: pageSize };
      const response = await api.get('/audio-studio/library', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching audio library:', error);
      throw error;
    }
  },

  /**
   * Delete audio from library
   */
  async delete(audioId) {
    try {
      const response = await api.delete(`/audio-studio/library/${audioId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting audio from library:', error);
      throw error;
    }
  },
};

export default {
  imageLibrary,
  videoLibrary,
  audioLibrary,
};

