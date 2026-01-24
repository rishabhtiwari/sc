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
   * Handle adding element to canvas
   */
  const handleAddElement = (element) => {
    const newElement = {
      id: `element-${Date.now()}`,
      ...element,
      x: element.x || 100,
      y: element.y || 100,
    };
    setCanvasElements([...canvasElements, newElement]);
    setSelectedElement(newElement);
  };

  /**
   * Handle adding multiple pages (for slide generation)
   */
  const handleAddMultiplePages = (slidePages) => {
    if (!slidePages || slidePages.length === 0) return;

    const newPages = slidePages.map((slide, index) => ({
      id: slide.id || `page-${Date.now()}-${index}`,
      name: slide.name || `Slide ${pages.length + index + 1}`,
      elements: slide.elements || [],
      background: slide.background || { type: 'solid', color: '#ffffff' },
      duration: slide.duration || 5,
      transition: slide.transition || 'fade'
    }));

    setPages([...pages, ...newPages]);
    setCurrentPageIndex(pages.length); // Switch to first new page
  };

  /**
   * Handle element selection
   */
  const handleSelectElement = (element) => {
    setSelectedElement(element);
  };

  /**
   * Handle element update
   */
  const handleUpdateElement = (elementId, updates) => {
    setCanvasElements(canvasElements.map(el => 
      el.id === elementId ? { ...el, ...updates } : el
    ));
    if (selectedElement?.id === elementId) {
      setSelectedElement({ ...selectedElement, ...updates });
    }
  };

  /**
   * Handle element deletion
   */
  const handleDeleteElement = (elementId) => {
    setCanvasElements(canvasElements.filter(el => el.id !== elementId));
    if (selectedElement?.id === elementId) {
      setSelectedElement(null);
    }
  };

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
        <Canvas
          elements={canvasElements}
          selectedElement={selectedElement}
          onSelectElement={handleSelectElement}
          onUpdateElement={handleUpdateElement}
          onDeleteElement={handleDeleteElement}
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

