import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Button, AuthenticatedImage, AuthenticatedVideo } from '../../common';
import { templateService, productService } from '../../../services';
import { useToast } from '../../../hooks/useToast';

/**
 * Step 5: Template Selection with User Templates & Variables
 */
const Step5_TemplateSelection = forwardRef(({ formData, onComplete }, ref) => {
  console.log('🎨 Step5_TemplateSelection - formData:', formData);
  console.log('🎨 Step5_TemplateSelection - formData.template_id:', formData.template_id);
  console.log('🎨 Step5_TemplateSelection - formData.media_files:', formData.media_files);
  console.log('🎨 Step5_TemplateSelection - formData.template_variables:', formData.template_variables);

  const [selectedTemplate, setSelectedTemplate] = useState(formData.template_id || null);
  const [templates, setTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [selectedTemplateDetails, setSelectedTemplateDetails] = useState(null);
  const [templateVariables, setTemplateVariables] = useState(formData.template_variables || {});
  const [mediaFiles, setMediaFiles] = useState(formData.media_files || []);
  const [uploadingMedia, setUploadingMedia] = useState(false);
  // section_mapping maps section titles to arrays of media objects with type and url
  // Format: {"opening_hook": [{"type": "video", "url": "..."}, {"type": "image", "url": "..."}]}
  const [sectionMapping, setSectionMapping] = useState(formData.section_mapping || {});
  // Single distribution mode for both images and videos
  const [distributionMode, setDistributionMode] = useState(formData.distribution_mode || 'auto'); // 'auto' or 'manual'
  const [expandedSection, setExpandedSection] = useState(null); // Track which section is expanded for media selection
  const [playingVideoIndex, setPlayingVideoIndex] = useState(null); // Track which video is currently playing
  const [deletingIndices, setDeletingIndices] = useState(new Set()); // Track which videos are being deleted
  const { showToast } = useToast();

  console.log('🎨 Initial selectedTemplate state:', selectedTemplate);
  console.log('🎨 Initial mediaFiles state:', mediaFiles);
  console.log('🎨 Initial templateVariables state:', templateVariables);
  console.log('🎨 Initial sectionMapping state:', sectionMapping);
  console.log('🎨 Initial distributionMode state:', distributionMode);
  console.log('🎨 formData.section_mapping from props:', formData.section_mapping);
  console.log('🎨 formData.distribution_mode from props:', formData.distribution_mode);

  // Sync state with formData when it changes (e.g., when user comes back to edit)
  useEffect(() => {
    console.log('🔄 Syncing formData to state:', {
      section_mapping: formData.section_mapping,
      distribution_mode: formData.distribution_mode,
      media_files: formData.media_files?.length,
      template_variables: formData.template_variables,
      template_id: formData.template_id
    });

    if (formData.section_mapping) {
      console.log('🔄 Syncing sectionMapping from formData:', formData.section_mapping);
      setSectionMapping(formData.section_mapping);
    }

    // Always sync distribution_mode, even if it's 'auto' (the default)
    if (formData.distribution_mode !== undefined) {
      console.log('🔄 Syncing distributionMode from formData:', formData.distribution_mode);
      setDistributionMode(formData.distribution_mode);
    }

    if (formData.media_files) {
      setMediaFiles(formData.media_files);
    }
    if (formData.template_variables) {
      setTemplateVariables(formData.template_variables);
    }
    if (formData.template_id) {
      setSelectedTemplate(formData.template_id);
    }
  }, [formData.section_mapping, formData.distribution_mode, formData.media_files, formData.template_variables, formData.template_id]);

  // Monitor mediaFiles state changes for debugging
  useEffect(() => {
    console.log('📊 [STATE CHANGE] mediaFiles updated:');
    console.log('  - Count:', mediaFiles.length);
    console.log('  - Files:', JSON.stringify(mediaFiles, null, 2));
    console.log('  - Images:', mediaFiles.filter(f => f.type === 'image').length);
    console.log('  - Videos:', mediaFiles.filter(f => f.type === 'video').length);
  }, [mediaFiles]);

  // Reconstruct mediaFiles from template_variables if mediaFiles is empty
  useEffect(() => {
    console.log('🔍 Checking if reconstruction needed:', {
      mediaFilesLength: mediaFiles.length,
      templateVariablesKeys: Object.keys(templateVariables),
      templateVariables: templateVariables
    });

    if (mediaFiles.length === 0 && templateVariables && Object.keys(templateVariables).length > 0) {
      console.log('🔄 Reconstructing mediaFiles from template_variables:', templateVariables);
      const reconstructedFiles = [];

      // Check for dynamic_images array
      if (templateVariables.dynamic_images && Array.isArray(templateVariables.dynamic_images)) {
        console.log('📸 Found dynamic_images:', templateVariables.dynamic_images);
        templateVariables.dynamic_images.forEach((url, index) => {
          // Skip blob URLs - they're invalid after page reload
          if (url && !url.startsWith('blob:')) {
            reconstructedFiles.push({
              url: url,
              type: 'image',
              name: `Image ${index + 1}`,
            });
          } else {
            console.warn('⚠️ Skipping invalid blob URL for image:', url);
          }
        });
      }

      // Check for dynamic_videos array
      if (templateVariables.dynamic_videos && Array.isArray(templateVariables.dynamic_videos)) {
        console.log('🎥 Found dynamic_videos:', templateVariables.dynamic_videos);

        // Also check for timing metadata
        const timings = templateVariables.dynamic_videos_timings || [];
        console.log('🎥 Found dynamic_videos_timings:', timings);

        templateVariables.dynamic_videos.forEach((url, index) => {
          // Skip blob URLs - they're invalid after page reload
          if (url && !url.startsWith('blob:')) {
            const timing = timings[index] || {};
            reconstructedFiles.push({
              url: url,
              type: 'video',
              name: `Video ${index + 1}`,
              duration: timing.duration || 5 // Use timing duration or default to 5s
            });
          } else {
            console.warn('⚠️ Skipping invalid blob URL for video:', url);
          }
        });
      }

      if (reconstructedFiles.length > 0) {
        console.log('✅ Reconstructed mediaFiles:', reconstructedFiles);
        setMediaFiles(reconstructedFiles);
      } else {
        console.log('⚠️ No files to reconstruct');
      }
    }
  }, [mediaFiles.length, templateVariables.dynamic_images, templateVariables.dynamic_videos]);

  // Parse AI summary sections
  const getAISections = () => {
    if (!formData.ai_summary) return [];

    const sections = [];
    const lines = formData.ai_summary.split('\n');

    for (const line of lines) {
      if (line.startsWith('## ')) {
        const title = line.substring(3).trim();
        sections.push({ title });
      }
    }

    return sections;
  };

  const aiSections = getAISections();

  // Debug logging for distribution mode visibility
  console.log('🎯 Distribution Mode Debug:', {
    hasImages: mediaFiles.filter(f => f.type === 'image').length > 0,
    hasVideos: mediaFiles.filter(f => f.type === 'video').length > 0,
    aiSectionsLength: aiSections.length,
    aiSections: aiSections,
    formDataAiSummary: formData.ai_summary,
    shouldShowDistributionMode: (mediaFiles.filter(f => f.type === 'image').length > 0 || mediaFiles.filter(f => f.type === 'video').length > 0) && aiSections.length > 0
  });

  // Helper function to normalize section titles for consistent mapping
  const normalizeSectionTitle = (title) => {
    return title.toLowerCase().replace(/\s+/g, '_').replace(/&/g, 'and');
  };

  // Handle adding/removing media (images or videos) for a section
  const toggleMediaForSection = (sectionTitle, mediaIndex, mediaType) => {
    console.log('🎬 toggleMediaForSection called:', { sectionTitle, mediaIndex, mediaType, currentMapping: sectionMapping });

    const normalizedTitle = normalizeSectionTitle(sectionTitle);
    const updatedMapping = { ...sectionMapping };

    if (!updatedMapping[normalizedTitle]) {
      updatedMapping[normalizedTitle] = [];
    }

    const mediaFile = mediaFiles[mediaIndex];
    if (!mediaFile) {
      console.error('❌ Media file not found at index:', mediaIndex);
      return;
    }

    // Check if this media is already in the section
    const existingIndex = updatedMapping[normalizedTitle].findIndex(
      item => item.url === mediaFile.url && item.type === mediaType
    );

    if (existingIndex > -1) {
      // Remove media from section
      console.log('➖ Removing media', mediaIndex, 'from section', normalizedTitle);
      updatedMapping[normalizedTitle] = updatedMapping[normalizedTitle].filter((_, idx) => idx !== existingIndex);
      if (updatedMapping[normalizedTitle].length === 0) {
        delete updatedMapping[normalizedTitle];
      }
    } else {
      // Add media to section
      console.log('➕ Adding media', mediaIndex, 'to section', normalizedTitle);
      updatedMapping[normalizedTitle].push({
        type: mediaType,
        url: mediaFile.url
      });
    }

    console.log('💾 Saving updated section mapping:', updatedMapping);
    setSectionMapping(updatedMapping);
  };

  // Wrapper functions for images and videos
  const toggleImageForSection = (sectionTitle, imageIndex) => {
    toggleMediaForSection(sectionTitle, imageIndex, 'image');
  };

  const toggleVideoForSection = (sectionTitle, videoIndex) => {
    toggleMediaForSection(sectionTitle, videoIndex, 'video');
  };

  // Check if media is assigned to a section
  const isMediaInSection = (sectionTitle, mediaIndex, mediaType) => {
    const normalizedTitle = normalizeSectionTitle(sectionTitle);
    const mediaFile = mediaFiles[mediaIndex];
    if (!mediaFile) return false;

    const sectionMedia = sectionMapping[normalizedTitle] || [];
    return sectionMedia.some(item => item.url === mediaFile.url && item.type === mediaType);
  };

  const isImageInSection = (sectionTitle, imageIndex) => {
    return isMediaInSection(sectionTitle, imageIndex, 'image');
  };

  const isVideoInSection = (sectionTitle, videoIndex) => {
    return isMediaInSection(sectionTitle, videoIndex, 'video');
  };

  // Get count of images assigned to a section
  const getSectionImageCount = (sectionTitle) => {
    const normalizedTitle = normalizeSectionTitle(sectionTitle);
    const sectionMedia = sectionMapping[normalizedTitle] || [];
    return sectionMedia.filter(item => item.type === 'image').length;
  };

  // Get count of videos assigned to a section
  const getSectionVideoCount = (sectionTitle) => {
    const normalizedTitle = normalizeSectionTitle(sectionTitle);
    const sectionMedia = sectionMapping[normalizedTitle] || [];
    return sectionMedia.filter(item => item.type === 'video').length;
  };

  // Monitor sectionMapping changes
  useEffect(() => {
    console.log('📊 [STATE CHANGE] sectionMapping updated:', sectionMapping);
  }, [sectionMapping]);

  // Load templates from API (ecommerce category only)
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setLoadingTemplates(true);
        const response = await templateService.listTemplates('ecommerce');

        if (response.status === 'success' && response.templates) {
          // Only show real templates from the API
          setTemplates(response.templates);
          console.log('📋 Loaded templates:', response.templates.map(t => ({ id: t.template_id, name: t.name })));
          console.log('📋 Looking for template_id:', formData.template_id);

          // Check if the formData.template_id exists in the loaded templates
          const matchingTemplate = response.templates.find(t => t.template_id === formData.template_id);
          if (matchingTemplate) {
            console.log('✅ Found matching template:', matchingTemplate.name);
          } else {
            // Template not found or not set - auto-select the first available template
            if (response.templates.length > 0) {
              const firstTemplate = response.templates[0];
              if (formData.template_id) {
                console.warn('⚠️ Template ID from formData not found in loaded templates:', formData.template_id);
                console.log('🔄 Auto-selecting first available template:', firstTemplate.name);
              } else {
                console.log('🔄 No template selected, auto-selecting first available template:', firstTemplate.name);
              }

              setSelectedTemplate(firstTemplate.template_id);

              // Template ID is already set in local state
            }
          }
        } else {
          setTemplates([]);
        }
      } catch (error) {
        console.error('Error loading templates:', error);
        setTemplates([]);
      } finally {
        setLoadingTemplates(false);
      }
    };

    fetchTemplates();
  }, []);

  // Track if we've already initialized variables for this template
  const [initializedTemplate, setInitializedTemplate] = useState(null);

  // Load selected template details when selection changes
  useEffect(() => {
    const loadTemplateDetails = async () => {
      if (!selectedTemplate) return;

      const template = templates.find(t => t.template_id === selectedTemplate);
      if (template) {
        console.log('📋 Selected template:', template);
        console.log('📋 Template variables:', template.variables);
        setSelectedTemplateDetails(template);

        // Check if we need to initialize or re-populate template variables
        // Initialize if:
        // 1. We haven't initialized this template yet, OR
        // 2. Template variables exist but media arrays are empty while we have media files
        const hasEmptyMediaArrays = template.variables && Object.entries(template.variables).some(([key, config]) => {
          if (config.type === 'array' && (config.item_type === 'image' || config.item_type === 'video')) {
            const currentValue = templateVariables[key];
            const mediaType = config.item_type;
            const availableMedia = mediaFiles.filter(f => f.type === mediaType);
            // Empty or missing array but we have media files available
            return (!currentValue || currentValue.length === 0) && availableMedia.length > 0;
          }
          return false;
        });

        const shouldInitialize = (initializedTemplate !== selectedTemplate && Object.keys(templateVariables).length === 0) || hasEmptyMediaArrays;

        console.log('🔍 Initialization check:', {
          initializedTemplate,
          selectedTemplate,
          templateVariablesCount: Object.keys(templateVariables).length,
          hasEmptyMediaArrays,
          shouldInitialize,
          mediaFilesCount: mediaFiles.length
        });

        if (template.variables && shouldInitialize) {
          console.log('🔄 Initializing/Re-populating template variables...');
          const initialVars = { ...templateVariables }; // Preserve existing non-media variables
          Object.entries(template.variables).forEach(([key, config]) => {
            console.log(`🔍 Processing variable: ${key}`, config);
            // Auto-populate array variables with product media
            if (config.type === 'array' && config.item_type === 'image') {
              // Use product images for image arrays
              const productImages = mediaFiles.filter(f => f.type === 'image');
              initialVars[key] = productImages.map(file => file.url || file);
              console.log(`✅ Auto-populated ${key} with ${initialVars[key].length} product images`);
            }
            else if (config.type === 'array' && config.item_type === 'video') {
              // Use product videos for video arrays
              const productVideos = mediaFiles.filter(f => f.type === 'video');
              initialVars[key] = productVideos.map(file => file.url || file);
              console.log(`✅ Auto-populated ${key} with ${initialVars[key].length} product videos`);

              // Also add timing metadata for videos
              const timingVarName = `${key}_timings`;
              const timings = productVideos.map((video) => ({
                start_time: 0,
                duration: video.duration || 5
              }));
              initialVars[timingVarName] = timings;
              console.log(`✅ Auto-populated ${timingVarName} with timings:`, timings);
            }
            // Use default value if available (only if not already set)
            else if (config.default !== undefined && !initialVars[key]) {
              initialVars[key] = config.default;
            }
            // For other types, initialize with empty value (only if not already set)
            else if (!initialVars[key]) {
              if (config.type === 'text') {
                initialVars[key] = '';
              }
              else if (config.type === 'number') {
                initialVars[key] = config.min || 0;
              }
              else if (config.type === 'color') {
                initialVars[key] = '#000000';
              }
            }
          });
          console.log('✅ Final initialized variables:', initialVars);
          setTemplateVariables(initialVars);
          setInitializedTemplate(selectedTemplate);
        }
      }
    };

    loadTemplateDetails();
  }, [selectedTemplate, templates, mediaFiles]);

  const handleTemplateSelect = (templateId) => {
    setSelectedTemplate(templateId);
    // Clear previous template variables when switching templates
    setTemplateVariables({});
    setSelectedTemplateDetails(null);
    setInitializedTemplate(null); // Reset initialization flag
  };

  const handleVariableChange = (varName, value) => {
    const updatedVars = { ...templateVariables, [varName]: value };
    setTemplateVariables(updatedVars);
  };



  // Get video duration using HTML5 video element
  const getVideoDuration = (file) => {
    return new Promise((resolve) => {
      console.log(`🎥 Getting duration for video file: ${file.name}`);

      const video = document.createElement('video');
      video.preload = 'metadata';

      video.onloadedmetadata = () => {
        const duration = video.duration;
        console.log(`✅ Video duration for ${file.name}: ${duration}s`);
        window.URL.revokeObjectURL(video.src);
        resolve(duration);
      };

      video.onerror = (error) => {
        console.error(`❌ Could not get duration for ${file.name}:`, error);
        window.URL.revokeObjectURL(video.src);
        resolve(5); // Return default 5s if we can't get duration
      };

      try {
        video.src = URL.createObjectURL(file);
      } catch (error) {
        console.error(`❌ Error creating object URL for ${file.name}:`, error);
        resolve(5); // Return default 5s on error
      }
    });
  };

  const handleFileUpload = async (event, type = 'image') => {
    const files = Array.from(event.target.files);

    if (files.length === 0) return;

    console.log(`📤 handleFileUpload called with type: ${type}, files:`, files.map(f => ({ name: f.name, type: f.type, size: f.size })));

    // Validate file types
    const validImageTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
    const validVideoTypes = ['video/mp4', 'video/webm', 'video/mov', 'video/quicktime'];
    const validTypes = type === 'image' ? validImageTypes : validVideoTypes;

    const invalidFiles = files.filter(file => !validTypes.includes(file.type));

    if (invalidFiles.length > 0) {
      console.error('❌ Invalid file types:', invalidFiles.map(f => ({ name: f.name, type: f.type })));
      const allowedFormats = type === 'image' ? 'JPG, PNG, WEBP, GIF' : 'MP4, WEBM, MOV';
      showToast(`⚠️ Invalid file type. Please upload ${type === 'image' ? 'images' : 'videos'} (${allowedFormats})`, 'error', 5000);
      return;
    }

    try {
      setUploadingMedia(true);

      console.log('🌐 Creating blob URLs for browser-only storage (will upload on Next/Preview)');

      // For videos, get duration
      const filesWithDuration = [];
      for (const file of files) {
        let duration = 0;
        if (type === 'video') {
          console.log(`🎥 Getting duration for video: ${file.name}`);
          duration = await getVideoDuration(file);
          console.log(`🎥 Duration for ${file.name}: ${duration}s`);
        }
        filesWithDuration.push({ file, duration });
      }

      // Create blob URLs for preview (don't upload to server yet)
      const newFiles = filesWithDuration.map(({ file, duration }) => {
        const blobUrl = URL.createObjectURL(file);
        const newFile = {
          url: blobUrl,
          type: type,
          name: file.name,
          duration: duration,
          file: file, // Keep reference to original file for later upload
          isLocal: true // Flag to indicate this is browser-only, not uploaded yet
        };
        console.log(`✅ Created blob URL for ${file.name}:`, blobUrl);
        return newFile;
      });

      const updatedMedia = [...mediaFiles, ...newFiles];
      console.log('✅ Updated media files (browser-only):', updatedMedia);

      setMediaFiles(updatedMedia);

      // Don't update template variables yet - wait until files are uploaded to server
      // This prevents blob URLs from being saved to backend
      console.log('ℹ️ Skipping template variable update until files are uploaded to server');

      showToast(`✅ ${files.length} ${type}(s) added (will upload when you click Next/Preview)`, 'success');
    } catch (error) {
      console.error('❌ Error processing files:', error);
      const errorMsg = error.message || 'Unknown error';
      showToast(`❌ Failed to process ${type}s: ${errorMsg}`, 'error', 6000);
    } finally {
      setUploadingMedia(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const handleRemoveMedia = async (index) => {
    console.log('═══════════════════════════════════════════════════════');
    console.log('🗑️ [STEP 1] handleRemoveMedia called');
    console.log('🗑️ Index to remove:', index);
    console.log('🗑️ Total mediaFiles count:', mediaFiles.length);
    console.log('🗑️ All mediaFiles:', JSON.stringify(mediaFiles, null, 2));

    const fileToRemove = mediaFiles[index];
    console.log('🗑️ [STEP 2] File to remove:', JSON.stringify(fileToRemove, null, 2));
    console.log('🗑️ File URL:', fileToRemove?.url);
    console.log('🗑️ File type:', fileToRemove?.type);
    console.log('🗑️ File name:', fileToRemove?.name);

    // Immediately remove from UI to prevent further rendering
    const updatedMediaImmediate = mediaFiles.filter((_, i) => i !== index);
    setMediaFiles(updatedMediaImmediate);
    console.log('🗑️ [STEP 2.5] Immediately updated UI, new count:', updatedMediaImmediate.length);

    // Check if URL starts with blob:
    const isBlobUrl = fileToRemove?.url?.startsWith('blob:');
    console.log('🗑️ [STEP 3] Is blob URL?', isBlobUrl);

    // If it's a blob URL (newly uploaded, not yet saved), just revoke and remove from state
    if (isBlobUrl) {
      console.log('🗑️ [STEP 4-BLOB] Processing as blob URL');
      try {
        URL.revokeObjectURL(fileToRemove.url);
        console.log('🗑️ ✅ Revoked blob URL:', fileToRemove.url);
      } catch (error) {
        console.warn('🗑️ ⚠️ Failed to revoke blob URL:', error);
      }

      const updatedMedia = mediaFiles.filter((_, i) => i !== index);
      console.log('🗑️ [STEP 5-BLOB] Updated media after removal:', updatedMedia);
      console.log('🗑️ New media count:', updatedMedia.length);

      console.log('🗑️ [STEP 6-BLOB] Updating state...');
      setMediaFiles(updatedMedia);

      // Don't update template variables for local files - they haven't been uploaded yet
      console.log('🗑️ Skipping template variable update for local file removal');

      console.log('🗑️ [STEP 7-BLOB] ✅ Blob removal complete');
      showToast(`${fileToRemove?.type || 'Media'} removed successfully`, 'success');
      console.log('═══════════════════════════════════════════════════════');
      return;
    }

    // If it's a server URL, call the API to delete it
    if (fileToRemove?.url) {
      console.log('🗑️ [STEP 4-SERVER] Processing as server URL');
      try {
        // Extract filename from URL
        // URL format: /api/ecommerce/public/product/{product_id}/videos/{filename}
        const urlParts = fileToRemove.url.split('/');
        const filename = urlParts[urlParts.length - 1];
        const mediaType = urlParts[urlParts.length - 2]; // 'videos' or 'images'

        console.log('🗑️ [STEP 5-SERVER] Extracted info:');
        console.log('  - URL parts:', urlParts);
        console.log('  - Filename:', filename);
        console.log('  - Media type:', mediaType);
        console.log('  - Product ID:', formData.product_id);

        console.log('🗑️ [STEP 6-SERVER] Calling API to delete from server...');
        // Call API to delete the file
        const deleteResponse = await productService.deleteMedia(formData.product_id, filename, mediaType);
        console.log('🗑️ [STEP 7-SERVER] API delete response:', deleteResponse);
        console.log('🗑️ [STEP 7.1-SERVER] API delete response.data:', deleteResponse.data);

        // Use the updated data from the backend response
        const responseData = deleteResponse.data || deleteResponse;
        const updatedMediaFiles = responseData.media_files || updatedMediaImmediate;
        const updatedTemplateVars = responseData.template_variables || templateVariables;
        const updatedSectionMapping = responseData.section_mapping || sectionMapping;

        console.log('🗑️ [STEP 8-SERVER] Backend response data:');
        console.log('  - media_files:', updatedMediaFiles);
        console.log('  - template_variables:', updatedTemplateVars);
        console.log('  - section_mapping:', updatedSectionMapping);

        console.log('🗑️ [STEP 9-SERVER] Updating state with backend data...');

        // Update all states with the backend response
        setMediaFiles(updatedMediaFiles);
        setTemplateVariables(updatedTemplateVars);
        setSectionMapping(updatedSectionMapping);

        console.log('🗑️ [STEP 9.1-SERVER] All states updated with backend data');

        // State already updated with backend data
        console.log('🗑️ [STEP 9.2-SERVER] State updated with backend data');

        console.log('🗑️ [STEP 10-SERVER] ✅ Server deletion complete');
        showToast(`${fileToRemove?.type || 'Media'} removed successfully`, 'success');
        console.log('═══════════════════════════════════════════════════════');
      } catch (error) {
        console.error('🗑️ [ERROR] ❌ Error deleting media:', error);
        console.error('🗑️ [ERROR] Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        });
        showToast(`Failed to delete ${fileToRemove?.type || 'media'}: ${error.response?.data?.message || error.message}`, 'error');
        console.log('═══════════════════════════════════════════════════════');
      }
    } else {
      console.log('🗑️ [WARNING] ⚠️ No URL found for file to remove');
      console.log('═══════════════════════════════════════════════════════');
    }
  };

  const handleReorderMedia = (index, direction) => {
    const newMedia = [...mediaFiles];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newMedia.length) return;

    [newMedia[index], newMedia[targetIndex]] = [newMedia[targetIndex], newMedia[index]];
    setMediaFiles(newMedia);

    // Update template variables
    updateArrayVariablesWithMedia(newMedia);
  };

  const updateArrayVariablesWithMedia = (media) => {
    if (!selectedTemplateDetails?.variables) {
      console.log('⚠️ No template variables to update');
      return;
    }

    console.log('🔄 Updating array variables with media:', media);
    console.log('🔄 Template variables config:', selectedTemplateDetails.variables);

    const updatedVars = { ...templateVariables };
    let hasChanges = false;

    Object.entries(selectedTemplateDetails.variables).forEach(([key, config]) => {
      if (config.type === 'array' && config.item_type === 'image') {
        const images = media.filter(f => f.type === 'image');
        updatedVars[key] = images.map(f => f.url);
        console.log(`✅ Updated ${key} with ${images.length} images:`, updatedVars[key]);
        hasChanges = true;
      } else if (config.type === 'array' && config.item_type === 'video') {
        const videos = media.filter(f => f.type === 'video');
        updatedVars[key] = videos.map(f => f.url);
        console.log(`✅ Updated ${key} with ${videos.length} videos:`, updatedVars[key]);

        // Also add timing metadata for videos with duration
        const timingVarName = `${key}_timings`;
        const timings = videos.map((video) => ({
          start_time: 0, // Will be calculated by backend based on sequence
          duration: video.duration || 5 // Use video's actual duration or default to 5s
        }));
        updatedVars[timingVarName] = timings;
        console.log(`✅ Updated ${timingVarName} with timings:`, timings);

        hasChanges = true;
      }
    });

    if (hasChanges) {
      console.log('✅ Saving updated template variables:', updatedVars);
      setTemplateVariables(updatedVars);
    } else {
      console.log('⚠️ No changes to template variables');
    }
  };

  // Toggle video play/pause
  const handleVideoPlayPause = (e, idx) => {
    e.stopPropagation(); // Prevent event bubbling
    const videoElement = e.currentTarget.querySelector('video') || e.target.closest('.video-container')?.querySelector('video');

    if (!videoElement) {
      console.warn('Video element not found');
      return;
    }

    if (playingVideoIndex === idx) {
      // Pause the video
      videoElement.pause();
      videoElement.currentTime = 0;
      setPlayingVideoIndex(null);
    } else {
      // Pause any currently playing video
      if (playingVideoIndex !== null) {
        const currentlyPlayingVideo = document.querySelector(`[data-video-index="${playingVideoIndex}"] video`);
        if (currentlyPlayingVideo) {
          currentlyPlayingVideo.pause();
          currentlyPlayingVideo.currentTime = 0;
        }
      }
      // Play the new video
      videoElement.play().catch(err => {
        console.warn('Failed to play video:', err);
      });
      setPlayingVideoIndex(idx);
    }
  };

  // Expose handleNext to parent via ref
  useImperativeHandle(ref, () => ({
    handleNext
  }));

  const handleNext = async () => {
    console.log('🚀 handleNext called in Step5_TemplateSelection');
    console.log('📋 selectedTemplate:', selectedTemplate);
    console.log('📋 selectedTemplateDetails:', selectedTemplateDetails);
    console.log('📋 templateVariables:', templateVariables);
    console.log('📋 mediaFiles:', mediaFiles);

    // Check if a template is selected
    if (!selectedTemplate) {
      console.log('❌ No template selected');
      showToast('⚠️ Please select a video template before proceeding', 'error', 5000);
      return;
    }

    // Validate required variables
    if (selectedTemplateDetails?.variables) {
      const missingVars = [];
      const mediaArrayVars = []; // Track media array variables (images/videos)

      Object.entries(selectedTemplateDetails.variables).forEach(([key, config]) => {
        console.log(`🔍 Checking variable: ${key}`, { config, value: templateVariables[key] });

        // Track media array variables separately
        if (config.type === 'array' && (config.item_type === 'image' || config.item_type === 'video')) {
          mediaArrayVars.push({ key, config, value: templateVariables[key] });
        } else if (config.required) {
          // For non-media variables, check normally
          const value = templateVariables[key];
          if (value === undefined || value === null || value === '' ||
              (Array.isArray(value) && value.length === 0)) {
            console.log(`❌ Missing required variable: ${key}`);
            missingVars.push(key);
          }
        }
      });

      // For media arrays: require at least ONE type (images OR videos), not both
      if (mediaArrayVars.length > 0) {
        const hasAnyMedia = mediaArrayVars.some(({ value }) =>
          Array.isArray(value) && value.length > 0
        );

        if (!hasAnyMedia) {
          console.log('❌ No media files uploaded (images or videos)');
          showToast('⚠️ Please upload at least one image or video for the template', 'error', 5000);
          return;
        }
        console.log('✅ Media validation passed - at least one media type has files');
      }

      if (missingVars.length > 0) {
        console.log('❌ Validation failed. Missing variables:', missingVars);
        const formattedVars = missingVars.map(v => v.replace(/_/g, ' ')).join(', ');
        showToast(`⚠️ Please fill in required fields: ${formattedVars}`, 'error', 6000);
        return;
      }
      console.log('✅ All required variables validated');
    }

    let finalMediaFiles = mediaFiles;
    let finalTemplateVariables = templateVariables;
    let finalSectionMapping = sectionMapping; // Will be updated if files are uploaded

    // Check if media files need to be uploaded to server
    if (mediaFiles.length > 0 && formData.product_id) {
      try {
        console.log('🔍 Checking media files for upload:', mediaFiles);

        // Separate files that need uploading from those already on server
        // Files with isLocal flag or File objects need uploading
        const localFiles = mediaFiles.filter(f => f.isLocal || f.file);
        // Files with server URLs (starting with /api/ or http) are already uploaded
        const serverUrlFiles = mediaFiles.filter(f => !f.isLocal && !f.file && f.url && (f.url.startsWith('/api/') || f.url.startsWith('http')));

        console.log('🔍 Local files (need upload):', localFiles.length);
        console.log('🔍 Files with server URLs (already uploaded):', serverUrlFiles.length);

        // Upload local files to server
        if (localFiles.length > 0) {
          setUploadingMedia(true);

          const actualFiles = localFiles.map(f => f.file);
          console.log('📤 Uploading local files to server:', actualFiles);
          console.log('📤 File details:', actualFiles.map(f => ({ name: f.name, type: f.type, size: f.size })));

          const response = await productService.uploadMedia(formData.product_id, actualFiles);
          console.log('📤 Upload response:', response);

          if (response.data && response.data.urls) {
            const uploadedUrls = response.data.urls;
            console.log('✅ Got uploaded URLs from server:', uploadedUrls);

            // Revoke blob URLs before replacing them
            localFiles.forEach(f => {
              if (f.url && f.url.startsWith('blob:')) {
                try {
                  URL.revokeObjectURL(f.url);
                  console.log('🗑️ Revoked blob URL:', f.url);
                } catch (error) {
                  console.warn('⚠️ Failed to revoke blob URL:', error);
                }
              }
            });

            // Map uploaded URLs to media file objects, preserving type and duration from original files
            const newlyUploadedFiles = uploadedUrls.map((url, index) => {
              // Get type and duration from original file
              const originalFile = localFiles[index];
              const type = originalFile?.type || 'image';
              const duration = originalFile?.duration || 0;

              return {
                url: url,
                type: type, // Use type from original file (frontend knows this!)
                name: url.split('/').pop().split('?')[0] || `media-${index + 1}`,
                duration: duration,
                isLocal: false // Mark as uploaded
              };
            });

            // Combine with already uploaded files (from server)
            finalMediaFiles = [...serverUrlFiles, ...newlyUploadedFiles];
            console.log('✅ Final media files (existing + newly uploaded):', finalMediaFiles);

            // Update sectionMapping to replace blob URLs with server URLs
            const updatedSectionMapping = {};
            Object.keys(sectionMapping).forEach(sectionKey => {
              updatedSectionMapping[sectionKey] = sectionMapping[sectionKey].map(mediaItem => {
                // Find if this blob URL was uploaded
                const localFileIndex = localFiles.findIndex(f => f.url === mediaItem.url);
                if (localFileIndex !== -1 && uploadedUrls[localFileIndex]) {
                  // Replace blob URL with server URL
                  console.log(`🔄 Replacing blob URL in section ${sectionKey}:`, mediaItem.url, '→', uploadedUrls[localFileIndex]);
                  return {
                    ...mediaItem,
                    url: uploadedUrls[localFileIndex]
                  };
                }
                // Keep existing server URLs unchanged
                return mediaItem;
              });
            });

            // Update the sectionMapping state and the final variable
            setSectionMapping(updatedSectionMapping);
            finalSectionMapping = updatedSectionMapping; // Update the variable that will be saved
            console.log('✅ Updated sectionMapping with server URLs:', updatedSectionMapping);

            showToast('Media uploaded successfully', 'success');
          } else {
            console.error('❌ No all_media_urls in response:', response.data);
            showToast('Upload failed: Invalid response from server', 'error');
            setUploadingMedia(false);
            return;
          }

          setUploadingMedia(false);
        } else if (serverUrlFiles.length > 0) {
          // All files are already uploaded, just use them
          console.log('ℹ️ All media files already uploaded, using existing URLs');
          finalMediaFiles = serverUrlFiles;
        } else {
          console.log('ℹ️ No media files to process');
        }

        // Update state with final media files (with server URLs)
        if (finalMediaFiles.length > 0 && finalMediaFiles !== mediaFiles) {
          console.log('🔄 Updating state with server URLs');
          setMediaFiles(finalMediaFiles);
        }

        // Update template variables with final media URLs
        if (finalMediaFiles.length > 0) {
          const updatedVars = { ...templateVariables };
          let hasChanges = false;

          Object.entries(selectedTemplateDetails?.variables || {}).forEach(([key, config]) => {
            if (config.type === 'array' && config.item_type === 'image') {
              const images = finalMediaFiles.filter(f => f.type === 'image');
              updatedVars[key] = images.map(f => f.url);
              hasChanges = true;
            } else if (config.type === 'array' && config.item_type === 'video') {
              const videos = finalMediaFiles.filter(f => f.type === 'video');
              updatedVars[key] = videos.map(f => f.url);

              // Also add timing metadata for videos with duration
              const timingVarName = `${key}_timings`;
              const timings = videos.map((video, idx) => ({
                start_time: 0, // Will be calculated by backend based on sequence
                duration: video.duration || 5 // Use video's actual duration or default to 5s
              }));
              updatedVars[timingVarName] = timings;

              hasChanges = true;
            }
          });

          if (hasChanges) {
            finalTemplateVariables = updatedVars;
            console.log('✅ Updated template variables with media URLs:', finalTemplateVariables);
          }
        }
      } catch (error) {
        console.error('❌ Error saving media:', error);
        console.error('❌ Error details:', error.response?.data || error.message);
        showToast(`Failed to save media files: ${error.response?.data?.error || error.message}`, 'error');
        setUploadingMedia(false);
        return;
      }
    }

    // Save distribution_mode, section_mapping, and template_variables to backend
    if (formData.product_id) {
      try {
        const dataToSave = {
          template_id: selectedTemplate,
          template_variables: finalTemplateVariables,
          distribution_mode: distributionMode,
          section_mapping: finalSectionMapping
        };
        console.log('💾 Saving template settings to backend...');
        console.log('💾 Product ID:', formData.product_id);
        console.log('💾 Data to save:', dataToSave);
        console.log('💾 Current sectionMapping state:', finalSectionMapping);
        console.log('💾 Current distributionMode state:', distributionMode);

        const response = await productService.updateProduct(formData.product_id, dataToSave);
        console.log('✅ Saved template settings to backend');
        console.log('✅ Backend response:', response);
      } catch (error) {
        console.error('❌ Error saving template settings:', error);
        console.error('❌ Error details:', error.response?.data || error.message);
        showToast('Failed to save template settings', 'error');
        return;
      }
    }

    console.log('🎉 All validations passed, calling onComplete with data:', {
      template_id: selectedTemplate,
      template_variables: finalTemplateVariables,
      media_files: finalMediaFiles,
      distribution_mode: distributionMode,
      section_mapping: finalSectionMapping
    });

    onComplete({
      template_id: selectedTemplate,
      template_variables: finalTemplateVariables,
      media_files: finalMediaFiles,
      distribution_mode: distributionMode,
      section_mapping: finalSectionMapping
    });

    console.log('✅ onComplete called successfully');
  };

  const handleCreateTemplate = () => {
    // Open template management page in new tab
    window.open('/template-management', '_blank');
  };

  if (loadingTemplates) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading templates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">🎨 Template Selection</h3>
        <p className="text-gray-600">Choose a template for your product video</p>
      </div>

      {/* Template Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Existing Templates */}
        {templates.map((template) => (
          <button
            key={template.template_id}
            onClick={() => handleTemplateSelect(template.template_id)}
            className={`p-6 border-2 rounded-lg text-left transition-all ${
              selectedTemplate === template.template_id
                ? 'border-indigo-500 bg-indigo-50 shadow-lg'
                : 'border-gray-300 hover:border-indigo-300 hover:shadow-md'
            }`}
          >
            {/* Thumbnail or Preview */}
            {template.thumbnail ? (
              <div className="mb-4">
                <img
                  src={template.thumbnail}
                  alt={template.name}
                  className="w-full h-32 object-cover rounded-md"
                />
              </div>
            ) : (
              <div className="flex items-center justify-center mb-4">
                <div className="text-6xl">🎬</div>
              </div>
            )}

            {/* Template Info */}
            <div className="flex items-start justify-between mb-2">
              <h4 className="font-semibold text-gray-900 text-lg">
                {template.name}
              </h4>
              {selectedTemplate === template.template_id && (
                <span className="text-indigo-600 text-2xl font-bold">✓</span>
              )}
            </div>
            <p className="text-sm text-gray-600 mb-4">{template.description || 'Custom template'}</p>
          </button>
        ))}

        {/* Create Template Card */}
        <button
          onClick={handleCreateTemplate}
          className="p-6 border-2 border-dashed border-gray-300 rounded-lg text-center transition-all hover:border-indigo-400 hover:bg-indigo-50 hover:shadow-md"
        >
          <div className="flex flex-col items-center justify-center h-full min-h-[200px]">
            <div className="rounded-full bg-indigo-100 p-4 mb-4">
              <span className="text-4xl">➕</span>
            </div>
            <h4 className="font-semibold text-gray-900 text-lg mb-2">Create New Template</h4>
            <p className="text-sm text-gray-600">Design your own custom template</p>
          </div>
        </button>
      </div>

      {/* Template Variables Section */}
      {selectedTemplateDetails && selectedTemplateDetails.variables &&
       Object.keys(selectedTemplateDetails.variables).length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>⚙️</span>
            Template Variables
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Customize the template by providing values for these variables
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(selectedTemplateDetails.variables).map(([varName, varConfig]) => (
              <div key={varName}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {varConfig.description || varName}
                  {varConfig.required && <span className="text-red-500 ml-1">*</span>}
                </label>

                {varConfig.type === 'text' && (
                  <input
                    type="text"
                    value={templateVariables[varName] || ''}
                    onChange={(e) => handleVariableChange(varName, e.target.value)}
                    placeholder={varConfig.default || `Enter ${varName}`}
                    maxLength={varConfig.max_length}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                )}

                {varConfig.type === 'color' && (
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={templateVariables[varName] || varConfig.default || '#000000'}
                      onChange={(e) => handleVariableChange(varName, e.target.value)}
                      className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                    />
                    <input
                      type="text"
                      value={templateVariables[varName] || varConfig.default || '#000000'}
                      onChange={(e) => handleVariableChange(varName, e.target.value)}
                      placeholder="#000000"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                )}

                {varConfig.type === 'number' && (
                  <input
                    type="number"
                    value={templateVariables[varName] || ''}
                    onChange={(e) => handleVariableChange(varName, parseFloat(e.target.value))}
                    placeholder={varConfig.default?.toString() || '0'}
                    min={varConfig.min}
                    max={varConfig.max}
                    step={varConfig.step || 1}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                )}

                {varConfig.type === 'font' && (
                  <select
                    value={templateVariables[varName] || varConfig.default || ''}
                    onChange={(e) => handleVariableChange(varName, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">Select font...</option>
                    <option value="Arial">Arial</option>
                    <option value="Arial-Bold">Arial Bold</option>
                    <option value="Helvetica">Helvetica</option>
                    <option value="Times-New-Roman">Times New Roman</option>
                    <option value="Georgia">Georgia</option>
                    <option value="Courier">Courier</option>
                  </select>
                )}

                {varConfig.type === 'array' && varConfig.item_type === 'image' && (
                  <div className="space-y-3 col-span-2">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start gap-2 mb-3">
                        <span className="text-lg">📸</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-blue-900 mb-1">Product Images Required</p>
                          <p className="text-xs text-blue-700">
                            Upload images or add them via URL. They will be used in the video template.
                          </p>
                        </div>
                      </div>

                      {/* Upload Options */}
                      <div className="space-y-3">
                        {/* File Upload */}
                        <div className="flex gap-2">
                          <input
                            type="file"
                            id="image-upload"
                            multiple
                            accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
                            onChange={(e) => handleFileUpload(e, 'image')}
                            className="hidden"
                          />
                          <label
                            htmlFor="image-upload"
                            className="flex-1 px-3 py-2 text-sm border-2 border-dashed border-blue-300 rounded-lg text-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors"
                          >
                            <span className="text-blue-700">📁 Choose files to upload</span>
                          </label>
                        </div>
                      </div>

                      {/* Uploaded Images - Simple Preview */}
                      {mediaFiles.filter(f => f.type === 'image').length > 0 ? (
                        <div className="space-y-3 mt-4">
                          <div className="flex items-center justify-between">
                            <p className="text-xs font-medium text-blue-900">
                              {mediaFiles.filter(f => f.type === 'image').length} image(s) added
                            </p>
                            {distributionMode === 'manual' && aiSections.length > 0 && (
                              <p className="text-xs text-blue-700">
                                💡 Expand sections above to assign media
                              </p>
                            )}
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                            {mediaFiles.map((file, idx) => file.type === 'image' && (
                              <div key={file.url || idx} className="bg-white border-2 border-blue-300 rounded-lg overflow-hidden">
                                {/* Image Preview */}
                                <div className="relative group">
                                  <div className="aspect-square bg-gray-100">
                                    <AuthenticatedImage
                                      src={file.url}
                                      alt={`Product ${idx + 1}`}
                                      className="w-full h-full object-cover"
                                    />
                                  </div>
                                  <div className="absolute top-1 left-1 bg-indigo-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-md">
                                    {idx + 1}
                                  </div>
                                  <div className="absolute top-1 right-1">
                                    <button
                                      onClick={() => handleRemoveMedia(idx)}
                                      className="bg-red-500 text-white rounded-full p-1 shadow-md hover:bg-red-600 text-xs"
                                      title="Remove"
                                    >
                                      ✕
                                    </button>
                                  </div>
                                </div>

                                {/* File Name */}
                                <div className="p-1.5 bg-white border-t border-blue-200">
                                  <p className="text-xs text-gray-600 truncate text-center" title={file.name}>
                                    {file.name || `Image ${idx + 1}`}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="bg-yellow-50 border border-yellow-200 rounded p-2 text-center mt-4">
                          <p className="text-xs text-yellow-700">No images added yet. Add at least one image above.</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {varConfig.type === 'array' && varConfig.item_type === 'video' && (
                  <div className="space-y-3 col-span-2">
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <div className="flex items-start gap-2 mb-3">
                        <span className="text-lg">🎥</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-purple-900 mb-1">Product Videos Required</p>
                          <p className="text-xs text-purple-700">
                            Upload videos or add them via URL. They will be used in the video template.
                          </p>
                        </div>
                      </div>

                      {/* Upload Options */}
                      <div className="space-y-3">
                        {/* File Upload */}
                        <div className="flex gap-2">
                          <input
                            type="file"
                            id="video-upload"
                            multiple
                            accept="video/mp4,video/webm,video/mov,video/quicktime"
                            onChange={(e) => handleFileUpload(e, 'video')}
                            className="hidden"
                          />
                          <label
                            htmlFor="video-upload"
                            className="flex-1 px-3 py-2 text-sm border-2 border-dashed border-purple-300 rounded-lg text-center cursor-pointer hover:border-purple-500 hover:bg-purple-50 transition-colors"
                          >
                            <span className="text-purple-700">📁 Choose files to upload</span>
                          </label>
                        </div>
                      </div>

                      {/* Uploaded Videos */}
                      {mediaFiles.filter(f => f.type === 'video').length > 0 ? (
                        <div className="space-y-3 mt-4">
                          <div className="flex items-center justify-between">
                            <p className="text-xs font-medium text-purple-900">
                              {mediaFiles.filter(f => f.type === 'video').length} video(s) added
                            </p>
                            {distributionMode === 'manual' && aiSections.length > 0 && (
                              <p className="text-xs text-purple-700">
                                💡 Expand sections above to assign media
                              </p>
                            )}
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                            {mediaFiles.map((file, idx) => file.type === 'video' && (
                              <div key={file.url || idx} className="bg-white border-2 border-purple-300 rounded-lg overflow-hidden">
                                {/* Video Preview */}
                                <div
                                  className="relative group video-container cursor-pointer"
                                  data-video-index={idx}
                                  onClick={(e) => handleVideoPlayPause(e, idx)}
                                >
                                  <div className="aspect-video bg-gray-900">
                                    <AuthenticatedVideo
                                      src={file.url}
                                      className="w-full h-full object-contain"
                                      controls={false}
                                      preload="metadata"
                                      onError={(e) => {
                                        console.error('Video load error:', file.url, e);
                                      }}
                                      onEnded={() => {
                                        setPlayingVideoIndex(null);
                                      }}
                                    />
                                  </div>
                                  <div className="absolute top-1 left-1 bg-purple-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-md pointer-events-none">
                                    {mediaFiles.filter(f => f.type === 'video').findIndex((_, i) => {
                                      let videoIdx = 0;
                                      for (let j = 0; j <= idx; j++) {
                                        if (mediaFiles[j].type === 'video') {
                                          if (j === idx) return true;
                                          videoIdx++;
                                        }
                                      }
                                      return false;
                                    }) + 1}
                                  </div>
                                  <div className="absolute top-1 right-1 flex gap-1">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleRemoveMedia(idx);
                                      }}
                                      className="bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center hover:bg-red-600 text-xs shadow-md"
                                      title="Remove"
                                    >
                                      ✕
                                    </button>
                                  </div>
                                  {/* Duration Badge */}
                                  {file.duration > 0 && (
                                    <div className="absolute bottom-1 right-1 bg-black bg-opacity-75 text-white text-xs px-1.5 py-0.5 rounded pointer-events-none">
                                      {file.duration.toFixed(1)}s
                                    </div>
                                  )}
                                  {/* Play/Pause icon overlay */}
                                  {playingVideoIndex !== idx && (
                                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                      <div className="bg-black bg-opacity-50 rounded-full p-2 group-hover:bg-opacity-70 transition-all">
                                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                                          <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                                        </svg>
                                      </div>
                                    </div>
                                  )}
                                  {playingVideoIndex === idx && (
                                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                                      <div className="bg-black bg-opacity-50 rounded-full p-2 group-hover:bg-opacity-70 transition-all">
                                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                                          <path d="M5.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75A.75.75 0 007.25 3h-1.5zM12.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75a.75.75 0 00-.75-.75h-1.5z" />
                                        </svg>
                                      </div>
                                    </div>
                                  )}
                                </div>
                                {/* Video Info */}
                                <div className="p-2 bg-purple-50">
                                  <p className="text-xs text-gray-700 truncate font-medium">{file.name}</p>
                                  {file.duration > 0 && (
                                    <p className="text-xs text-purple-600 mt-0.5">Duration: {file.duration.toFixed(1)}s</p>
                                  )}
                                  <div className="flex gap-1 mt-1">
                                    {idx > 0 && (
                                      <button
                                        onClick={() => handleReorderMedia(idx, 'up')}
                                        className="flex-1 bg-purple-100 rounded px-2 py-1 hover:bg-purple-200 text-xs text-purple-700"
                                        title="Move up"
                                      >
                                        ⬆️
                                      </button>
                                    )}
                                    {idx < mediaFiles.length - 1 && (
                                      <button
                                        onClick={() => handleReorderMedia(idx, 'down')}
                                        className="flex-1 bg-purple-100 rounded px-2 py-1 hover:bg-purple-200 text-xs text-purple-700"
                                        title="Move down"
                                      >
                                        ⬇️
                                      </button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="bg-yellow-50 border border-yellow-200 rounded p-2 text-center">
                          <p className="text-xs text-yellow-700">No videos added yet. Add at least one video above.</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {varConfig.description && (
                  <p className="text-xs text-gray-500 mt-1">{varConfig.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Distribution Mode Toggle - Always visible when media and AI sections exist */}
      {(mediaFiles.filter(f => f.type === 'image').length > 0 || mediaFiles.filter(f => f.type === 'video').length > 0) && aiSections.length > 0 && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h5 className="text-sm font-semibold text-indigo-900">Media Distribution Mode</h5>
              <p className="text-xs text-indigo-700">Choose how images and videos are assigned to AI sections</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setDistributionMode('auto');
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  distributionMode === 'auto'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-white text-indigo-600 border border-indigo-300 hover:bg-indigo-50'
                }`}
              >
                🤖 Auto
              </button>
              <button
                onClick={() => {
                  setDistributionMode('manual');
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  distributionMode === 'manual'
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-white text-indigo-600 border border-indigo-300 hover:bg-indigo-50'
                }`}
              >
                ✋ Manual
              </button>
            </div>
          </div>

          {distributionMode === 'auto' ? (
            <div className="bg-white border border-indigo-200 rounded p-3">
              <div className="flex items-start gap-2">
                <span className="text-lg">✨</span>
                <div className="flex-1">
                  <p className="text-xs font-medium text-indigo-900 mb-1">Automatic Distribution</p>
                  <p className="text-xs text-indigo-700">
                    Images and videos will be intelligently distributed across audio sections based on timing.
                    The system ensures no audio section is left without visuals.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-indigo-200 rounded p-3 space-y-3">
              <div className="flex items-start gap-2">
                <span className="text-lg">🎯</span>
                <div className="flex-1">
                  <p className="text-xs font-medium text-indigo-900 mb-1">Manual Assignment</p>
                  <p className="text-xs text-indigo-700">
                    Map images and videos to each AI summary section below. Click on a section to select media.
                  </p>
                </div>
              </div>

              {/* AI Sections with Image and Video Mapping */}
              <div className="space-y-2">
                {aiSections.map((section, sIdx) => (
                  <div key={sIdx} className="bg-white border-2 border-indigo-300 rounded-lg overflow-hidden">
                    {/* Section Header */}
                    <button
                      onClick={() => setExpandedSection(expandedSection === sIdx ? null : sIdx)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-indigo-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-lg">{expandedSection === sIdx ? '📂' : '📁'}</span>
                        <div className="text-left">
                          <p className="text-sm font-semibold text-indigo-900">{section.title}</p>
                          <p className="text-xs text-indigo-600">
                            {getSectionImageCount(section.title)} image(s), {getSectionVideoCount(section.title)} video(s) assigned
                          </p>
                        </div>
                      </div>
                      <span className="text-indigo-600 text-xl">
                        {expandedSection === sIdx ? '▼' : '▶'}
                      </span>
                    </button>

                    {/* Media Selection Grid (Images and Videos) */}
                    {expandedSection === sIdx && (
                      <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-t-2 border-indigo-200">
                        <p className="text-xs text-indigo-700 mb-3">
                          💡 Click on images or videos to assign/unassign them to this section
                        </p>

                        {/* Images */}
                        {mediaFiles.filter(f => f.type === 'image').length > 0 && (
                          <div className="mb-4">
                            <p className="text-xs font-semibold text-indigo-900 mb-2">📷 Images</p>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                              {mediaFiles.map((file, imgIdx) => file.type === 'image' && (
                                <button
                                  key={imgIdx}
                                  onClick={() => toggleImageForSection(section.title, imgIdx)}
                                  className={`relative group border-2 rounded-lg overflow-hidden transition-all ${
                                    isImageInSection(section.title, imgIdx)
                                      ? 'border-green-500 ring-2 ring-green-300 shadow-lg'
                                      : 'border-gray-300 hover:border-indigo-400'
                                  }`}
                                >
                                  <div className="aspect-square bg-gray-100">
                                    <AuthenticatedImage
                                      src={file.url}
                                      alt={`Product ${imgIdx + 1}`}
                                      className="w-full h-full object-cover"
                                    />
                                  </div>

                                  {/* Selection Indicator */}
                                  {isImageInSection(section.title, imgIdx) && (
                                    <div className="absolute inset-0 bg-green-500 bg-opacity-30 flex items-center justify-center">
                                      <div className="bg-green-500 text-white rounded-full p-2 shadow-lg">
                                        <span className="text-2xl">✓</span>
                                      </div>
                                    </div>
                                  )}

                                  {/* Image Number Badge */}
                                  <div className="absolute top-1 left-1 bg-indigo-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-md">
                                    {imgIdx + 1}
                                  </div>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Videos */}
                        {mediaFiles.filter(f => f.type === 'video').length > 0 && (
                          <div className="mb-4">
                            <p className="text-xs font-semibold text-indigo-900 mb-2">🎥 Videos</p>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                              {mediaFiles.map((file, vidIdx) => file.type === 'video' && (
                                <button
                                  key={vidIdx}
                                  onClick={() => toggleVideoForSection(section.title, vidIdx)}
                                  className={`relative group border-2 rounded-lg overflow-hidden transition-all ${
                                    isVideoInSection(section.title, vidIdx)
                                      ? 'border-green-500 ring-2 ring-green-300 shadow-lg'
                                      : 'border-gray-300 hover:border-indigo-400'
                                  }`}
                                >
                                  <div className="aspect-video bg-gray-900">
                                    <AuthenticatedVideo
                                      src={file.url}
                                      className="w-full h-full object-contain"
                                      preload="metadata"
                                      onError={(e) => {
                                        console.error('Video load error:', file.url, e);
                                      }}
                                    />
                                  </div>

                                  {/* Selection Indicator */}
                                  {isVideoInSection(section.title, vidIdx) && (
                                    <div className="absolute inset-0 bg-green-500 bg-opacity-30 flex items-center justify-center">
                                      <div className="bg-green-500 text-white rounded-full p-2 shadow-lg">
                                        <span className="text-2xl">✓</span>
                                      </div>
                                    </div>
                                  )}

                                  {/* Video Number Badge */}
                                  <div className="absolute top-1 left-1 bg-indigo-600 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-md">
                                    {vidIdx + 1}
                                  </div>

                                  {/* Duration Badge */}
                                  {file.duration > 0 && (
                                    <div className="absolute bottom-1 right-1 bg-black bg-opacity-75 text-white text-xs px-1.5 py-0.5 rounded">
                                      {file.duration.toFixed(1)}s
                                    </div>
                                  )}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Upload More Media for This Section */}
                        <div className="mt-3 pt-3 border-t border-indigo-200 space-y-2">
                          <input
                            type="file"
                            id={`section-image-upload-${sIdx}`}
                            multiple
                            accept="image/jpeg,image/jpg,image/png,image/webp,image/gif"
                            onChange={(e) => handleFileUpload(e, 'image')}
                            className="hidden"
                          />
                          <label
                            htmlFor={`section-image-upload-${sIdx}`}
                            className="block px-3 py-2 text-xs border-2 border-dashed border-indigo-300 rounded-lg text-center cursor-pointer hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
                          >
                            <span className="text-indigo-700">📁 Upload more images for this section</span>
                          </label>

                          <input
                            type="file"
                            id={`section-video-upload-${sIdx}`}
                            multiple
                            accept="video/mp4,video/webm,video/mov,video/quicktime"
                            onChange={(e) => handleFileUpload(e, 'video')}
                            className="hidden"
                          />
                          <label
                            htmlFor={`section-video-upload-${sIdx}`}
                            className="block px-3 py-2 text-xs border-2 border-dashed border-indigo-300 rounded-lg text-center cursor-pointer hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
                          >
                            <span className="text-indigo-700">📁 Upload more videos for this section</span>
                          </label>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Template Preview Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">💡 Template Features:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• All templates are optimized for social media</li>
          <li>• Supports both 16:9 and 9:16 aspect ratios</li>
          <li>• Customizable colors and fonts</li>
          <li>• Professional animations and transitions</li>
        </ul>
      </div>


    </div>
  );
});

Step5_TemplateSelection.displayName = 'Step5_TemplateSelection';

export default Step5_TemplateSelection;

