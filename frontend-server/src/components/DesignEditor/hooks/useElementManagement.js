import { useState } from 'react';

// Minimum default slide duration (in seconds)
const MIN_SLIDE_DURATION = 5;

/**
 * Calculate required slide duration based on video elements
 * Duration = max(longest video duration, MIN_SLIDE_DURATION)
 */
const calculateSlideDuration = (elements) => {
  // Find all video elements
  const videoElements = elements.filter(el => el.type === 'video');

  if (videoElements.length === 0) {
    return MIN_SLIDE_DURATION;
  }

  // Find the longest video duration
  const maxVideoDuration = Math.max(
    ...videoElements.map(video => {
      // Use trimEnd if available, otherwise use full duration
      const effectiveDuration = video.trimEnd || video.duration || 0;
      return effectiveDuration;
    })
  );

  // Return max of video duration and minimum slide duration
  return Math.max(maxVideoDuration, MIN_SLIDE_DURATION);
};

/**
 * Custom hook for managing canvas elements (add, update, delete, select)
 */
export const useElementManagement = (pages, setPages, currentPageIndex) => {
  const [selectedElement, setSelectedElement] = useState(null);

  /**
   * Add a new element to the current page
   */
  const handleAddElement = (element) => {
    console.log('🎨 handleAddElement called with:', {
      type: element.type,
      shapeType: element.shapeType,
      icon: element.icon,
      emoji: element.emoji,
      text: element.text,
      hasSrc: !!element.src,
      src: element.src?.substring(0, 100),
      hasFile: !!element.file,
      libraryId: element.libraryId,
      duration: element.duration,
      width: element.width,
      height: element.height
    });

    const newElement = {
      id: element.id || `element-${Date.now()}`,
      type: element.type,
      x: element.x || 100,
      y: element.y || 100,
      width: element.width || (element.type === 'text' ? 300 : element.type === 'video' ? 640 : element.type === 'image' ? 400 : 200),
      height: element.height || (element.type === 'text' ? 100 : element.type === 'video' ? 360 : element.type === 'image' ? 300 : 100),
      ...element
    };

    console.log('✅ Created new element:', {
      id: newElement.id,
      type: newElement.type,
      hasSrc: !!newElement.src,
      src: newElement.src?.substring(0, 100),
      hasFile: !!newElement.file,
      libraryId: newElement.libraryId
    });

    setPages(prevPages => {
      const updatedPages = [...prevPages];
      const currentPage = updatedPages[currentPageIndex];

      console.log('📄 Adding element to page', currentPageIndex + ':', {
        pageId: currentPage.id,
        pageName: currentPage.name,
        oldElementCount: currentPage.elements.length,
        newElementCount: currentPage.elements.length + 1,
        newElementId: newElement.id,
        newElementType: newElement.type
      });

      // Add the new element
      const newElements = [...currentPage.elements, newElement];

      // Calculate new slide duration based on video elements
      const newDuration = calculateSlideDuration(newElements);

      // Log duration adjustment if it changed
      if (newDuration !== currentPage.duration) {
        console.log(`⏱️ Adjusting slide duration: ${currentPage.duration}s → ${newDuration}s`);
      }

      updatedPages[currentPageIndex] = {
        ...currentPage,
        elements: newElements,
        duration: newDuration
      };

      console.log('✅ Pages updated. Total pages:', updatedPages.length);
      console.log('✅ Current page elements:', updatedPages[currentPageIndex].elements.length);
      console.log('✅ Current page duration:', updatedPages[currentPageIndex].duration);

      return updatedPages;
    });
  };

  /**
   * Update an existing element
   */
  const handleUpdateElement = (elementId, updates) => {
    setPages(prevPages => {
      const updatedPages = [...prevPages];
      const currentPage = updatedPages[currentPageIndex];

      // Update the element
      const newElements = currentPage.elements.map(el =>
        el.id === elementId ? { ...el, ...updates } : el
      );

      // Recalculate slide duration if a video element was updated
      const updatedElement = newElements.find(el => el.id === elementId);
      let newDuration = currentPage.duration;

      if (updatedElement?.type === 'video') {
        newDuration = calculateSlideDuration(newElements);

        if (newDuration !== currentPage.duration) {
          console.log(`⏱️ Adjusting slide duration after video update: ${currentPage.duration}s → ${newDuration}s`);
        }
      }

      updatedPages[currentPageIndex] = {
        ...currentPage,
        elements: newElements,
        duration: newDuration
      };

      return updatedPages;
    });

    // Also update selectedElement if it's the one being updated
    if (selectedElement && selectedElement.id === elementId) {
      setSelectedElement(prev => ({ ...prev, ...updates }));
    }
  };

  /**
   * Delete an element
   */
  const handleDeleteElement = (elementId) => {
    setPages(prevPages => {
      const updatedPages = [...prevPages];
      const currentPage = updatedPages[currentPageIndex];

      // Find the element being deleted to check if it's a video
      const deletedElement = currentPage.elements.find(el => el.id === elementId);

      // Filter out the deleted element
      const newElements = currentPage.elements.filter(el => el.id !== elementId);

      // Recalculate slide duration if a video was deleted
      let newDuration = currentPage.duration;

      if (deletedElement?.type === 'video') {
        newDuration = calculateSlideDuration(newElements);

        if (newDuration !== currentPage.duration) {
          console.log(`⏱️ Adjusting slide duration after video deletion: ${currentPage.duration}s → ${newDuration}s`);
        }
      }

      updatedPages[currentPageIndex] = {
        ...currentPage,
        elements: newElements,
        duration: newDuration
      };

      return updatedPages;
    });

    if (selectedElement?.id === elementId) {
      setSelectedElement(null);
    }
  };

  /**
   * Select an element
   */
  const handleSelectElement = (element) => {
    setSelectedElement(element);
  };

  /**
   * Deselect element
   */
  const handleDeselectElement = () => {
    setSelectedElement(null);
  };

  return {
    selectedElement,
    handleAddElement,
    handleUpdateElement,
    handleDeleteElement,
    handleSelectElement,
    handleDeselectElement
  };
};

