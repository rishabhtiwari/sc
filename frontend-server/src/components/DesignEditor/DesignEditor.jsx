import React, { useState } from 'react';
import Sidebar from './Sidebar/Sidebar';
import Canvas from './Canvas/Canvas';
import PropertiesPanel from './PropertiesPanel/PropertiesPanel';

/**
 * Main Design Editor Component
 * Layout: Sidebar | Canvas | Properties Panel
 */
const DesignEditor = () => {
  const [selectedTool, setSelectedTool] = useState(null);
  const [selectedElement, setSelectedElement] = useState(null);
  const [canvasElements, setCanvasElements] = useState([]);
  const [pages, setPages] = useState([
    {
      id: 'page-1',
      name: 'Page 1',
      elements: [],
      background: { type: 'solid', color: '#ffffff' }
    }
  ]);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);

  /**
   * Handle adding element to canvas (adds to current page)
   */
  const handleAddElement = (element) => {
    const newElement = {
      id: `element-${Date.now()}`,
      ...element,
      x: element.x || 100,
      y: element.y || 100,
    };

    // Update current page's elements
    const updatedPages = pages.map((page, index) => {
      if (index === currentPageIndex) {
        return {
          ...page,
          elements: [...(page.elements || []), newElement]
        };
      }
      return page;
    });

    setPages(updatedPages);
    setCanvasElements([...canvasElements, newElement]); // Keep for backward compatibility
    setSelectedElement(newElement);
  };

  /**
   * Handle adding multiple pages (for slide generation)
   */
  const handleAddMultiplePages = (slidePages) => {
    console.log('📄 DesignEditor: handleAddMultiplePages called with', slidePages?.length, 'slides');
    console.log('📄 DesignEditor: Slide pages:', slidePages);

    if (!slidePages || slidePages.length === 0) {
      console.warn('⚠️ DesignEditor: No slide pages provided');
      return;
    }

    const newPages = slidePages.map((slide, index) => ({
      id: slide.id || `page-${Date.now()}-${index}`,
      name: slide.name || `Slide ${pages.length + index + 1}`,
      elements: slide.elements || [],
      background: slide.background || { type: 'solid', color: '#ffffff' },
      duration: slide.duration || 5,
      transition: slide.transition || 'fade'
    }));

    console.log('📄 DesignEditor: Created new pages:', newPages);
    console.log('📄 DesignEditor: Current pages before update:', pages);

    const updatedPages = [...pages, ...newPages];
    console.log('📄 DesignEditor: Updated pages:', updatedPages);

    setPages(updatedPages);
    setCurrentPageIndex(pages.length); // Switch to first new page

    console.log('✅ DesignEditor: Pages state updated, new page index:', pages.length);
  };

  /**
   * Handle element selection
   */
  const handleSelectElement = (element) => {
    setSelectedElement(element);
  };

  /**
   * Handle element update (updates element in current page)
   */
  const handleUpdateElement = (elementId, updates) => {
    // Update in pages
    const updatedPages = pages.map((page, index) => {
      if (index === currentPageIndex) {
        return {
          ...page,
          elements: page.elements.map(el =>
            el.id === elementId ? { ...el, ...updates } : el
          )
        };
      }
      return page;
    });

    setPages(updatedPages);
    setCanvasElements(canvasElements.map(el =>
      el.id === elementId ? { ...el, ...updates } : el
    ));

    if (selectedElement?.id === elementId) {
      setSelectedElement({ ...selectedElement, ...updates });
    }
  };

  /**
   * Handle element deletion (deletes from current page)
   */
  const handleDeleteElement = (elementId) => {
    // Delete from pages
    const updatedPages = pages.map((page, index) => {
      if (index === currentPageIndex) {
        return {
          ...page,
          elements: page.elements.filter(el => el.id !== elementId)
        };
      }
      return page;
    });

    setPages(updatedPages);
    setCanvasElements(canvasElements.filter(el => el.id !== elementId));

    if (selectedElement?.id === elementId) {
      setSelectedElement(null);
    }
  };

  // Get current page
  const currentPage = pages[currentPageIndex] || pages[0];
  const currentPageElements = currentPage?.elements || canvasElements;

  return (
    <div className="flex h-full bg-gray-50">
      {/* Left Sidebar - Tools */}
      <Sidebar
        selectedTool={selectedTool}
        onSelectTool={setSelectedTool}
        onAddElement={handleAddElement}
        onAddMultiplePages={handleAddMultiplePages}
      />

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
        {/* Page Navigation */}
        {pages.length > 1 && (
          <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setCurrentPageIndex(Math.max(0, currentPageIndex - 1))}
                disabled={currentPageIndex === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
              >
                ← Previous
              </button>
              <span className="text-sm font-semibold text-gray-900 px-3 py-2 bg-gray-100 rounded-lg">
                Slide {currentPageIndex + 1} / {pages.length}
              </span>
              <button
                onClick={() => setCurrentPageIndex(Math.min(pages.length - 1, currentPageIndex + 1))}
                disabled={currentPageIndex === pages.length - 1}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
              >
                Next →
              </button>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (window.confirm(`Delete slide ${currentPageIndex + 1}?`)) {
                    const newPages = pages.filter((_, index) => index !== currentPageIndex);
                    if (newPages.length > 0) {
                      setPages(newPages);
                      setCurrentPageIndex(Math.max(0, currentPageIndex - 1));
                    }
                  }
                }}
                disabled={pages.length === 1}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
              >
                🗑️ Delete Slide
              </button>
            </div>
          </div>
        )}

        <Canvas
          elements={currentPageElements}
          selectedElement={selectedElement}
          onSelectElement={handleSelectElement}
          onUpdateElement={handleUpdateElement}
          onDeleteElement={handleDeleteElement}
          background={currentPage?.background}
        />
      </div>

      {/* Right Properties Panel */}
      {selectedElement && (
        <PropertiesPanel
          element={selectedElement}
          onUpdate={(updates) => handleUpdateElement(selectedElement.id, updates)}
          onDelete={() => handleDeleteElement(selectedElement.id)}
        />
      )}
    </div>
  );
};

export default DesignEditor;

