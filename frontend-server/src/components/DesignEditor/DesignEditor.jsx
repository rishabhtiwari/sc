import React, { useState } from 'react';
import Sidebar from './Sidebar/Sidebar';
import Canvas from './Canvas/Canvas';
import PropertiesPanel from './PropertiesPanel/PropertiesPanel';
import ConfirmDialog from '../common/ConfirmDialog';

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
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, slideIndex: null });
  const [showBackgroundPicker, setShowBackgroundPicker] = useState(false);

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
          <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-center gap-3">
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
        )}

        <Canvas
          elements={currentPageElements}
          selectedElement={selectedElement}
          onSelectElement={handleSelectElement}
          onUpdateElement={handleUpdateElement}
          onDeleteElement={handleDeleteElement}
          background={currentPage?.background}
        />

        {/* Slide Management Controls - Below Canvas */}
        {pages.length > 1 && (
          <div className="bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowBackgroundPicker(!showBackgroundPicker)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium text-sm flex items-center gap-2"
              >
                🎨 Change Background
              </button>

              {showBackgroundPicker && (
                <div className="flex items-center gap-2 ml-2">
                  <span className="text-sm text-gray-600">Background:</span>
                  <input
                    type="color"
                    value={currentPage?.background?.color || '#ffffff'}
                    onChange={(e) => {
                      const newPages = [...pages];
                      newPages[currentPageIndex] = {
                        ...newPages[currentPageIndex],
                        background: { type: 'solid', color: e.target.value }
                      };
                      setPages(newPages);
                    }}
                    className="w-10 h-10 rounded cursor-pointer border border-gray-300"
                  />
                  <button
                    onClick={() => {
                      const newPages = [...pages];
                      newPages[currentPageIndex] = {
                        ...newPages[currentPageIndex],
                        background: {
                          type: 'gradient',
                          angle: 135,
                          colors: ['#667eea', '#764ba2']
                        }
                      };
                      setPages(newPages);
                    }}
                    className="px-3 py-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded text-xs font-medium"
                  >
                    Gradient
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={() => setDeleteDialog({ isOpen: true, slideIndex: currentPageIndex })}
              disabled={pages.length === 1}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm flex items-center gap-2"
            >
              🗑️ Delete Slide
            </button>
          </div>
        )}
      </div>

      {/* Right Properties Panel */}
      {selectedElement && (
        <PropertiesPanel
          element={selectedElement}
          onUpdate={(updates) => handleUpdateElement(selectedElement.id, updates)}
          onDelete={() => handleDeleteElement(selectedElement.id)}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, slideIndex: null })}
        onConfirm={() => {
          const newPages = pages.filter((_, index) => index !== deleteDialog.slideIndex);
          if (newPages.length > 0) {
            setPages(newPages);
            setCurrentPageIndex(Math.max(0, deleteDialog.slideIndex - 1));
          }
          setDeleteDialog({ isOpen: false, slideIndex: null });
        }}
        title="Delete Slide"
        description="This action cannot be undone"
        message={`Are you sure you want to delete slide ${deleteDialog.slideIndex + 1}?`}
        warningMessage="This will permanently delete the slide and all its content."
        confirmText="Delete Slide"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default DesignEditor;

