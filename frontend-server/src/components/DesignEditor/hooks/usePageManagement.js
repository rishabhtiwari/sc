import { useState } from 'react';

/**
 * Helper to create a default page
 */
const createDefaultPage = (index = 0) => ({
  id: `page-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
  name: `Page ${index + 1}`,
  elements: [],
  background: { type: 'solid', color: '#ffffff' },
  duration: 5,
  startTime: index * 5
});

/**
 * Custom hook for managing pages (add, delete, reorder, navigate)
 */
export const usePageManagement = (pages, setPages) => {
  const [currentPageIndex, setCurrentPageIndex] = useState(0);

  /**
   * Add a new page
   */
  const handleAddPage = () => {
    const newPage = createDefaultPage(pages.length);
    setPages(prevPages => [...prevPages, newPage]);
    setCurrentPageIndex(pages.length); // Switch to new page
  };

  /**
   * Add multiple pages at once (for slide generation)
   * @param {Array} slidePages - Array of slide objects with elements, background, etc.
   */
  const handleAddMultiplePages = (slidePages) => {
    console.log('📄 handleAddMultiplePages called with', slidePages?.length, 'slides');
    console.log('📄 Slide pages:', slidePages);

    if (!slidePages || slidePages.length === 0) {
      console.warn('⚠️ No slide pages provided');
      return;
    }

    setPages(prevPages => {
      // Calculate start time for new slides (position at end of existing slides)
      const existingDuration = prevPages.reduce((sum, p) => {
        const pStart = p.startTime !== undefined ? p.startTime : 0;
        const pDur = p.duration || 5;
        return Math.max(sum, pStart + pDur);
      }, 0);

      const newPages = slidePages.map((slide, index) => ({
        id: slide.id || `page-${Date.now()}-${index}`,
        name: slide.name || `Slide ${prevPages.length + index + 1}`,
        elements: slide.elements || [],
        background: slide.background || { type: 'solid', color: '#ffffff' },
        duration: slide.duration || 5,
        startTime: existingDuration + (index * 5), // Position new slides sequentially after existing ones
        transition: slide.transition || 'fade'
      }));

      console.log('📄 Created new pages:', newPages);
      console.log('📄 Current pages before update:', prevPages);

      const updatedPages = [...prevPages, ...newPages];
      console.log('📄 Updated pages:', updatedPages);

      return updatedPages;
    });
  };

  /**
   * Delete a page
   */
  const handleDeletePage = (pageIndex) => {
    if (pages.length === 1) {
      console.warn('Cannot delete the last page');
      return;
    }

    setPages(prevPages => prevPages.filter((_, i) => i !== pageIndex));
    
    // Adjust current page index if needed
    if (currentPageIndex >= pages.length - 1) {
      setCurrentPageIndex(Math.max(0, pages.length - 2));
    } else if (currentPageIndex > pageIndex) {
      setCurrentPageIndex(currentPageIndex - 1);
    }
  };

  /**
   * Duplicate a page
   */
  const handleDuplicatePage = (pageIndex) => {
    const pageToDuplicate = pages[pageIndex];
    const duplicatedPage = {
      ...pageToDuplicate,
      id: `page-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: `${pageToDuplicate.name} (Copy)`,
      elements: pageToDuplicate.elements.map(el => ({
        ...el,
        id: `element-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      }))
    };

    setPages(prevPages => {
      const newPages = [...prevPages];
      newPages.splice(pageIndex + 1, 0, duplicatedPage);
      return newPages;
    });
  };

  /**
   * Update page background
   */
  const handleBackgroundChange = (background) => {
    setPages(prevPages => {
      const updatedPages = [...prevPages];
      updatedPages[currentPageIndex] = {
        ...updatedPages[currentPageIndex],
        background
      };
      return updatedPages;
    });
  };

  /**
   * Navigate to a specific page
   */
  const handlePageChange = (pageIndex) => {
    if (pageIndex >= 0 && pageIndex < pages.length) {
      setCurrentPageIndex(pageIndex);
    }
  };

  /**
   * Navigate to next page
   */
  const handleNextPage = () => {
    if (currentPageIndex < pages.length - 1) {
      setCurrentPageIndex(currentPageIndex + 1);
    }
  };

  /**
   * Navigate to previous page
   */
  const handlePreviousPage = () => {
    if (currentPageIndex > 0) {
      setCurrentPageIndex(currentPageIndex - 1);
    }
  };

  return {
    currentPageIndex,
    currentPage: pages[currentPageIndex],
    handleAddPage,
    handleAddMultiplePages,
    handleDeletePage,
    handleDuplicatePage,
    handleBackgroundChange,
    handlePageChange,
    handleNextPage,
    handlePreviousPage,
    setCurrentPageIndex
  };
};

