import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import projectService from '../../../services/projectService';
import { prepareProjectData, extractMediaFromProject } from '../utils/projectDataHelpers';

/**
 * Custom hook for managing project state (save, load, current project)
 */
export const useProjectState = ({
  pages,
  audioTracks,
  uploadedAudio,
  uploadedImage,
  uploadedVideo,
  setPages,
  setAudioTracks,
  setUploadedAudio,
  setUploadedImage,
  setUploadedVideo
}) => {
  const location = useLocation();
  const [currentProject, setCurrentProject] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Save project
   */
  const handleSaveProject = async () => {
    try {
      setIsSaving(true);

      console.log('💾 Current state before save:');
      console.log('  📄 Pages:', pages.length);
      pages.forEach((page, index) => {
        console.log(`    Page ${index} (${page.name}):`, {
          id: page.id,
          elementCount: page.elements.length,
          elements: page.elements
        });
      });
      console.log('  🎬 Video tracks (computed):', audioTracks.length);
      console.log('  🎵 Audio tracks:', audioTracks.length);

      // Prepare project data (uploads blobs, etc.)
      const projectData = await prepareProjectData(
        pages,
        audioTracks,
        uploadedAudio,
        uploadedImage,
        uploadedVideo,
        currentProject
      );

      // Save or update project
      let savedProject;
      if (currentProject?.project_id) {
        console.log('💾 Updating existing project:', currentProject.project_id);
        savedProject = await projectService.updateProject(
          currentProject.project_id,
          projectData
        );
      } else {
        console.log('💾 Creating new project');
        savedProject = await projectService.saveProject(projectData);
      }

      setCurrentProject(savedProject);
      console.log('✅ Project saved:', savedProject.project_id);

      return savedProject;
    } catch (error) {
      console.error('❌ Failed to save project:', error);
      console.error('❌ Error response:', error.response?.data);
      console.error('❌ Error details:', JSON.stringify(error.response?.data, null, 2));
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Load project by ID
   */
  const handleLoadProject = async (projectId) => {
    try {
      setIsLoading(true);
      console.log('📂 Loading project:', projectId);

      // Clear sessionStorage when explicitly loading a project
      // This ensures we get fresh data from backend, not cached state
      sessionStorage.removeItem('designEditor_inMemoryState');
      console.log('🗑️ Cleared sessionStorage - loading fresh project from backend');

      const project = await projectService.loadProject(projectId);
      
      console.log('📂 Loaded project:', project);
      console.log('📄 Pages in loaded project:', project.pages?.length || 0);
      project.pages?.forEach((page, index) => {
        console.log(`  📄 Page ${index} (${page.name}):`, {
          id: page.id,
          elementCount: page.elements?.length || 0
        });
        // Log each element individually for better visibility
        page.elements?.forEach((el, elIndex) => {
          console.log(`    🔹 Element ${elIndex}:`, {
            type: el.type,
            id: el.id,
            icon: el.icon,
            emoji: el.emoji,
            shapeType: el.shapeType,
            width: el.width,
            height: el.height,
            fontSize: el.fontSize,
            text: el.text?.substring(0, 30),
            hasSrc: !!el.src
          });
          // Log full element object for icons/stickers to debug
          if (el.type === 'icon' || el.type === 'sticker') {
            console.log(`      🔍 Full ${el.type} element:`, el);
          }
        });
      });

      // Restore state
      setPages(project.pages || []);
      setAudioTracks(project.audioTracks || []);
      setCurrentProject(project);

      // Extract and restore media library
      const extractedMedia = extractMediaFromProject(project);

      console.log('📦 Current audio in state:', uploadedAudio.length);
      console.log('📦 Current image in state:', uploadedImage.length);
      console.log('📦 Current video in state:', uploadedVideo.length);

      // Merge current media with extracted media (don't overwrite)
      setUploadedAudio(prev => {
        const merged = [...prev];
        extractedMedia.audio.forEach(audio => {
          if (!merged.some(a => a.url === audio.url)) {
            merged.push(audio);
          }
        });
        return merged;
      });

      setUploadedImage(prev => {
        const merged = [...prev];
        extractedMedia.image.forEach(image => {
          if (!merged.some(i => i.url === image.url)) {
            merged.push(image);
          }
        });
        return merged;
      });

      setUploadedVideo(prev => {
        const merged = [...prev];
        extractedMedia.video.forEach(video => {
          if (!merged.some(v => v.url === video.url)) {
            merged.push(video);
          }
        });
        return merged;
      });

      console.log('✅ Media after extraction and merge:', {
        audio: extractedMedia.audio.length,
        image: extractedMedia.image.length,
        video: extractedMedia.video.length
      });

      console.log('✅ Project loaded successfully');
      return project;
    } catch (error) {
      console.error('❌ Failed to load project:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Auto-load project from URL on mount
   * If there's a project ID in URL, ALWAYS load it from backend (clear sessionStorage first)
   * This ensures clicking a project from the Projects page always loads that specific project
   */
  useEffect(() => {
    const projectId = new URLSearchParams(location.search).get('project');

    if (projectId) {
      console.log('📂 Project ID in URL, loading from backend:', projectId);
      // Clear sessionStorage to ensure we load fresh data from backend
      sessionStorage.removeItem('designEditor_inMemoryState');
      console.log('🗑️ Cleared sessionStorage to load fresh project');

      handleLoadProject(projectId).catch(error => {
        console.error('Failed to load project from URL:', error);
      });
    } else {
      console.log('📭 No project ID in URL - will use sessionStorage or start fresh');
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    currentProject,
    isSaving,
    isLoading,
    setCurrentProject,
    handleSaveProject,
    handleLoadProject
  };
};

