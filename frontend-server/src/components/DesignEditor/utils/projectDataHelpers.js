import projectService from '../../../services/projectService';

/**
 * Upload a blob URL to the asset service
 */
export const uploadBlobToAsset = async (blob, type, name) => {
  try {
    console.log(`📤 Uploading ${type}:`, name);
    
    // Fetch the blob data
    const response = await fetch(blob);
    const blobData = await response.blob();
    
    // Create a File object
    const file = new File([blobData], name, { type: blobData.type });
    
    // Upload to asset service
    const asset = await projectService.uploadAsset(file, type);
    console.log(`📦 Upload response:`, asset);

    if (!asset || !asset.asset_id) {
      throw new Error(`Failed to upload ${type}: Invalid response from server`);
    }

    console.log(`✅ Uploaded ${type}:`, asset.asset_id);
    return asset.asset_id;
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
        // If it's a blob URL, upload it
        if (isBlobUrl(element.src)) {
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

    if (audioUrl && isBlobUrl(audioUrl)) {
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
      } catch (error) {
        console.error('Failed to upload audio track:', error);
        // Still include the track but with blob URL (will fail validation)
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
    } else {
      // Map src to url for backend compatibility
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

  // Extract from pages/elements
  if (project.pages) {
    project.pages.forEach(page => {
      page.elements?.forEach(element => {
        if (element.type === 'image' && element.src) {
          extractedMedia.image.push({
            image_id: element.assetId || element.id,
            url: element.src,
            name: element.name || 'Image',
            title: element.name || 'Image'
          });
        } else if (element.type === 'video' && element.src) {
          extractedMedia.video.push({
            video_id: element.assetId || element.id,
            url: element.src,
            name: element.name || 'Video',
            title: element.name || 'Video',
            duration: element.duration
          });
        }
      });
    });
  }

  // Extract from audio tracks
  if (project.audioTracks) {
    project.audioTracks.forEach(track => {
      extractedMedia.audio.push({
        audio_id: track.assetId || track.id,
        url: track.src || track.audio_url,
        audio_url: track.src || track.audio_url,
        title: track.name || 'Audio',
        duration: track.duration
      });
    });
  }

  console.log('📦 Merged media:', {
    audio: extractedMedia.audio.length,
    image: extractedMedia.image.length,
    video: extractedMedia.video.length
  });

  return extractedMedia;
};

