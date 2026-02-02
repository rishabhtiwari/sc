import projectService from '../../../services/projectService';
import { imageLibrary, videoLibrary, audioLibrary } from '../../../services/assetLibraryService';

/**
 * Upload a blob URL to the appropriate asset library
 * This ensures assets are properly cataloged in MongoDB collections
 */
export const uploadBlobToAsset = async (blob, type, name) => {
  try {
    console.log(`📤 Uploading ${type} to library:`, name);

    // Fetch the blob data
    const response = await fetch(blob);
    const blobData = await response.blob();

    // Create a File object
    const file = new File([blobData], name, { type: blobData.type });

    let uploadResult;

    // Upload to the appropriate library based on type
    if (type === 'image') {
      console.log(`📸 Uploading to image library...`);
      uploadResult = await imageLibrary.upload(file, name);

      if (!uploadResult.success || !uploadResult.image) {
        throw new Error('Failed to upload image to library');
      }

      console.log(`✅ Uploaded to image library:`, uploadResult.image.image_id);

      return {
        asset_id: uploadResult.image.image_id,
        url: uploadResult.image.url  // Library URL: /api/assets/download/image-assets/...
      };
    }
    else if (type === 'video') {
      console.log(`🎬 Uploading to video library...`);

      // Extract video duration if possible
      let duration = 0;
      try {
        const videoUrl = URL.createObjectURL(blobData);
        const video = document.createElement('video');
        video.src = videoUrl;
        await new Promise((resolve) => {
          video.onloadedmetadata = () => {
            duration = video.duration;
            URL.revokeObjectURL(videoUrl);
            resolve();
          };
          video.onerror = () => {
            URL.revokeObjectURL(videoUrl);
            resolve();
          };
        });
      } catch (error) {
        console.warn('Could not extract video duration:', error);
      }

      uploadResult = await videoLibrary.upload(file, name, duration);

      if (!uploadResult.success || !uploadResult.video) {
        throw new Error('Failed to upload video to library');
      }

      console.log(`✅ Uploaded to video library:`, uploadResult.video.video_id);

      return {
        asset_id: uploadResult.video.video_id,
        url: uploadResult.video.url  // Library URL: /api/assets/download/video-assets/...
      };
    }
    else if (type === 'audio') {
      console.log(`🎵 Uploading to audio library...`);

      // Extract audio duration if possible
      let duration = 0;
      try {
        const audioUrl = URL.createObjectURL(blobData);
        const audio = new Audio(audioUrl);
        await new Promise((resolve) => {
          audio.onloadedmetadata = () => {
            duration = audio.duration;
            URL.revokeObjectURL(audioUrl);
            resolve();
          };
          audio.onerror = () => {
            URL.revokeObjectURL(audioUrl);
            resolve();
          };
        });
      } catch (error) {
        console.warn('Could not extract audio duration:', error);
      }

      uploadResult = await audioLibrary.upload(file, name, duration);

      if (!uploadResult.success || !uploadResult.audio) {
        throw new Error('Failed to upload audio to library');
      }

      console.log(`✅ Uploaded to audio library:`, uploadResult.audio.audio_id);

      return {
        asset_id: uploadResult.audio.audio_id,
        url: uploadResult.audio.url  // Library URL: /api/assets/download/audio-assets/...
      };
    }
    else {
      // Fallback for other types - use generic asset upload
      console.log(`📦 Uploading to generic asset storage...`);
      const asset = await projectService.uploadAsset(file, type);

      if (!asset || !asset.asset_id) {
        throw new Error(`Failed to upload ${type}: Invalid response from server`);
      }

      console.log(`✅ Uploaded ${type}:`, asset.asset_id);

      return {
        asset_id: asset.asset_id,
        url: asset.url
      };
    }
  } catch (error) {
    console.error(`❌ Failed to upload ${type}:`, error);
    throw error;
  }
};

/**
 * Check if a URL is a blob URL
 */
const isBlobUrl = (url) => {
  return url && url.startsWith('blob:');
};

/**
 * Check if a URL is from the asset library
 */
const isLibraryUrl = (url) => {
  return url && url.startsWith('/api/assets/download/');
};

/**
 * Check if a URL is from the audio generation service (temporary or proxied)
 */
const isAudioServiceUrl = (url) => {
  return url && (
    url.startsWith('/api/audio/proxy/') ||  // Proxied audio generation URLs
    url.startsWith('/temp/') ||              // Temporary audio files
    url.includes('audio-generation')         // Direct audio generation service URLs
  );
};

/**
 * Prepare project data for saving
 * Converts in-memory state to API format, uploading blob URLs
 */
export const prepareProjectData = async (
  pages,
  audioTracks,
  uploadedAudio,
  uploadedImage,
  uploadedVideo,
  currentProject
) => {
  console.log('💾 Preparing project data...');
  console.log('📄 Pages to process:', pages.length);

  const processedPages = [];

  // Process each page
  for (let i = 0; i < pages.length; i++) {
    const page = pages[i];
    console.log(`📄 Processing page ${i}:`, {
      id: page.id,
      name: page.name,
      elementCount: page.elements.length
    });

    const processedElements = [];

    // Process each element
    for (let j = 0; j < page.elements.length; j++) {
      const element = page.elements[j];
      console.log(`  🔍 Element ${j}:`, {
        type: element.type,
        id: element.id,
        hasSrc: !!element.src,
        hasFile: !!element.file,
        srcType: element.src?.substring(0, 10)
      });

      // Handle video and image elements with src
      if ((element.type === 'video' || element.type === 'image') && element.src) {
        console.log(`  🔍 Checking ${element.type} URL:`, {
          src: element.src,
          srcLength: element.src.length,
          srcStart: element.src.substring(0, 50),
          isBlob: isBlobUrl(element.src),
          isLibrary: isLibraryUrl(element.src),
          hasLibraryId: !!element.libraryId,
          hasAssetId: !!element.assetId
        });

        // Check if element already has an assetId or libraryId (from library)
        // If so, skip upload even if it's not a library URL pattern
        if (element.assetId || element.libraryId) {
          console.log(`  ✅ ${element.type} already in library (assetId: ${element.assetId || element.libraryId}), skipping upload`);
          processedElements.push({
            ...element,
            assetId: element.assetId || element.libraryId,
            file: undefined
          });
        }
        // If it's a blob URL, upload it
        else if (isBlobUrl(element.src)) {
          console.log(`  📤 Uploading blob ${element.type}:`, element.src.substring(0, 50));

          try {
            const uploadResult = await uploadBlobToAsset(
              element.src,
              element.type,
              element.name || `${element.type}-${Date.now()}`
            );

            processedElements.push({
              ...element,
              src: uploadResult.url,
              assetId: uploadResult.asset_id,
              file: undefined // Remove file object
            });

            console.log(`  ✅ Uploaded ${element.type}, new URL:`, uploadResult.url);
          } catch (error) {
            console.error(`  ❌ Failed to upload ${element.type}:`, error);
            // Keep original element if upload fails
            processedElements.push(element);
          }
        }
        // If it's a library URL, keep it as-is
        else if (isLibraryUrl(element.src)) {
          console.log(`  ℹ️ ${element.type} from library, keeping URL:`, element.src.substring(0, 50));
          processedElements.push({
            ...element,
            file: undefined
          });
        }
        // Other URLs (external, etc.)
        else {
          console.log(`  ℹ️ ${element.type} with external URL:`, element.src.substring(0, 50));
          processedElements.push({
            ...element,
            file: undefined
          });
        }
      }
      // All other element types (text, shape, icon, sticker, bullets) - save as-is
      else {
        console.log(`  ✅ Keeping ${element.type} element as-is`);
        processedElements.push(element);
      }
    }

    console.log(`  ✅ Page ${i} processed: ${processedElements.length} elements`);

    processedPages.push({
      ...page,
      elements: processedElements
    });
  }

  console.log('✅ All pages processed:', processedPages.length);

  // Process audio tracks (similar to elements)
  const processedAudioTracks = [];
  for (const track of audioTracks) {
    const audioUrl = track.src || track.url;

    console.log(`🎵 Processing audio track: ${track.name}`, {
      url: audioUrl?.substring(0, 50),
      isBlob: isBlobUrl(audioUrl),
      isLibrary: isLibraryUrl(audioUrl),
      isAudioService: isAudioServiceUrl(audioUrl),
      hasAssetId: !!track.assetId,
      hasLibraryId: !!track.libraryId
    });

    // Check if audio already has an assetId or libraryId (from audio library)
    // If so, skip upload even if it's an audio service URL
    if (track.assetId || track.libraryId) {
      console.log(`  ✅ Audio already in library (assetId: ${track.assetId || track.libraryId}), skipping upload`);
      processedAudioTracks.push({
        id: track.id,
        name: track.name,
        url: audioUrl,
        assetId: track.assetId || track.libraryId,
        type: track.type || 'music',
        startTime: track.startTime || 0,
        duration: track.duration || 0,
        volume: track.volume || 100,
        fadeIn: track.fadeIn || 0,
        fadeOut: track.fadeOut || 0,
        playbackSpeed: track.playbackSpeed || 1
      });
    }
    // If it's a blob URL or audio service URL (temporary) and no assetId, upload it
    else if (audioUrl && (isBlobUrl(audioUrl) || isAudioServiceUrl(audioUrl))) {
      const urlType = isBlobUrl(audioUrl) ? 'blob' : 'audio service';
      console.log(`  📤 Uploading ${urlType} audio: ${track.name}`);
      try {
        const uploadResult = await uploadBlobToAsset(
          audioUrl,
          'audio',
          track.name || `audio-${Date.now()}`
        );

        processedAudioTracks.push({
          id: track.id,
          name: track.name,
          url: uploadResult.url,
          assetId: uploadResult.asset_id,
          type: track.type || 'music',
          startTime: track.startTime || 0,
          duration: track.duration || 0,
          volume: track.volume || 100,
          fadeIn: track.fadeIn || 0,
          fadeOut: track.fadeOut || 0,
          playbackSpeed: track.playbackSpeed || 1
        });
        console.log(`  ✅ Uploaded audio, new URL: ${uploadResult.url}`);
      } catch (error) {
        console.error('  ❌ Failed to upload audio track:', error);
        // Still include the track but with original URL (will fail validation)
        processedAudioTracks.push({
          id: track.id,
          name: track.name,
          url: audioUrl,
          type: track.type || 'music',
          startTime: track.startTime || 0,
          duration: track.duration || 0,
          volume: track.volume || 100,
          fadeIn: track.fadeIn || 0,
          fadeOut: track.fadeOut || 0,
          playbackSpeed: track.playbackSpeed || 1
        });
      }
    }
    // If it's a library URL, keep it as-is
    else if (audioUrl && isLibraryUrl(audioUrl)) {
      console.log(`  ℹ️ Audio from library, keeping URL: ${audioUrl.substring(0, 50)}`);
      processedAudioTracks.push({
        id: track.id,
        name: track.name,
        url: audioUrl,
        assetId: track.assetId,
        type: track.type || 'music',
        startTime: track.startTime || 0,
        duration: track.duration || 0,
        volume: track.volume || 100,
        fadeIn: track.fadeIn || 0,
        fadeOut: track.fadeOut || 0,
        playbackSpeed: track.playbackSpeed || 1
      });
    }
    // Other URLs (external, etc.)
    else if (audioUrl) {
      console.log(`  ℹ️ Audio with external URL: ${audioUrl.substring(0, 50)}`);
      processedAudioTracks.push({
        id: track.id,
        name: track.name,
        url: audioUrl,
        assetId: track.assetId,
        type: track.type || 'music',
        startTime: track.startTime || 0,
        duration: track.duration || 0,
        volume: track.volume || 100,
        fadeIn: track.fadeIn || 0,
        fadeOut: track.fadeOut || 0,
        playbackSpeed: track.playbackSpeed || 1
      });
    } else {
      console.warn(`  ⚠️ Audio track has no URL: ${track.name}`);
    }
  }

  console.log('✅ Videos are stored in page elements (not separate videoTracks)');

  // Calculate total duration from pages
  const totalDuration = processedPages.reduce((sum, page) => sum + (page.duration || 5), 0);

  // Build final project data
  const projectData = {
    name: currentProject?.name || `Project ${new Date().toLocaleDateString()}`,
    settings: {
      canvas: {
        width: 1920,
        height: 1080,
        background: '#ffffff'
      },
      duration: totalDuration,
      fps: 30,
      quality: '1080p'
    },
    pages: processedPages,
    audioTracks: processedAudioTracks,
    videoTracks: [], // Empty - videos are in page elements
    mediaLibrary: {
      uploadedAudio: uploadedAudio,
      uploadedImage: uploadedImage,
      uploadedVideo: uploadedVideo
    },
    status: 'draft',
    tags: []
  };

  console.log('💾 Project data prepared:', {
    pages: projectData.pages?.length,
    audioTracks: projectData.audioTracks?.length,
    note: 'Videos are stored in page elements'
  });

  // Log detailed element data to verify icons/stickers are included
  console.log('📦 Detailed project data being sent to backend:');
  projectData.pages?.forEach((page, index) => {
    console.log(`  📄 Page ${index}:`, {
      name: page.name,
      elementCount: page.elements?.length || 0
    });
    page.elements?.forEach((el, elIndex) => {
      console.log(`    🔹 Element ${elIndex}:`, {
        type: el.type,
        id: el.id,
        icon: el.icon,
        emoji: el.emoji,
        shapeType: el.shapeType,
        width: el.width,
        height: el.height,
        text: el.text?.substring(0, 20)
      });
      // Log full element for icons/stickers
      if (el.type === 'icon' || el.type === 'sticker') {
        console.log(`      🔍 Full ${el.type} being saved:`, el);
      }
    });
  });

  return projectData;
};

/**
 * Extract media from loaded project
 * Converts API format back to in-memory state
 */
export const extractMediaFromProject = (project) => {
  console.log('📦 Extracting media from project:', project.project_id);

  const extractedMedia = {
    audio: [],
    image: [],
    video: []
  };

  // First, try to use the saved mediaLibrary if it exists
  if (project.mediaLibrary) {
    console.log('📦 Using saved media library from project');
    return {
      audio: project.mediaLibrary.uploadedAudio || [],
      image: project.mediaLibrary.uploadedImage || [],
      video: project.mediaLibrary.uploadedVideo || []
    };
  }

  console.log('📦 No saved media library, extracting from project content');

  // Track unique URLs to avoid duplicates
  const uniqueImages = new Map();
  const uniqueVideos = new Map();

  // Extract from pages/elements
  if (project.pages) {
    project.pages.forEach(page => {
      page.elements?.forEach(element => {
        if (element.type === 'image' && element.src) {
          // Only add if we haven't seen this URL before
          if (!uniqueImages.has(element.src)) {
            uniqueImages.set(element.src, {
              image_id: element.assetId || element.libraryId || element.id,
              id: element.assetId || element.libraryId || element.id,
              url: element.src,
              name: element.name || 'Image',
              title: element.name || 'Image',
              type: 'image',
              libraryId: element.libraryId || element.image_id,
              assetId: element.assetId || element.libraryId
            });
          }
        } else if (element.type === 'video' && element.src) {
          // Only add if we haven't seen this URL before
          if (!uniqueVideos.has(element.src)) {
            uniqueVideos.set(element.src, {
              video_id: element.assetId || element.libraryId || element.id,
              id: element.assetId || element.libraryId || element.id,
              url: element.src,
              name: element.name || 'Video',
              title: element.name || 'Video',
              type: 'video',
              duration: element.duration,
              originalDuration: element.originalDuration,
              libraryId: element.libraryId || element.video_id,
              assetId: element.assetId || element.libraryId
            });
          }
        }
      });
    });
  }

  // Convert Maps to arrays
  extractedMedia.image = Array.from(uniqueImages.values());
  extractedMedia.video = Array.from(uniqueVideos.values());

  // Extract from audio tracks (with deduplication)
  const uniqueAudio = new Map();
  if (project.audioTracks) {
    project.audioTracks.forEach(track => {
      const audioUrl = track.src || track.url || track.audio_url;
      // Only add if we haven't seen this URL before
      if (audioUrl && !uniqueAudio.has(audioUrl)) {
        uniqueAudio.set(audioUrl, {
          audio_id: track.assetId || track.libraryId || track.id,
          id: track.assetId || track.libraryId || track.id,
          url: audioUrl,
          audio_url: audioUrl,
          title: track.name || 'Audio',
          name: track.name || 'Audio',
          type: 'audio',
          duration: track.duration,
          libraryId: track.libraryId || track.audio_id,
          assetId: track.assetId || track.libraryId
        });
      }
    });
  }
  extractedMedia.audio = Array.from(uniqueAudio.values());

  console.log('📦 Merged media:', {
    audio: extractedMedia.audio.length,
    image: extractedMedia.image.length,
    video: extractedMedia.video.length
  });

  return extractedMedia;
};

