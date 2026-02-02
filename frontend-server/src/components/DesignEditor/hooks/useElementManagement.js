import { useState } from 'react';

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

      updatedPages[currentPageIndex] = {
        ...currentPage,
        elements: [...currentPage.elements, newElement]
      };

      console.log('✅ Pages updated. Total pages:', updatedPages.length);
      console.log('✅ Current page elements:', updatedPages[currentPageIndex].elements.length);

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

      updatedPages[currentPageIndex] = {
        ...currentPage,
        elements: currentPage.elements.map(el =>
          el.id === elementId ? { ...el, ...updates } : el
        )
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
      
      updatedPages[currentPageIndex] = {
        ...currentPage,
        elements: currentPage.elements.filter(el => el.id !== elementId)
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

