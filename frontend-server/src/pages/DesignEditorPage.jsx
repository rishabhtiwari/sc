import React, { useRef } from 'react';
import DesignEditor from '../components/DesignEditor/DesignEditor';

/**
 * Design Editor Page - Canva/Veed.io style editor
 *
 * Features:
 * - Canvas editor with drag & drop
 * - AI Tools (image generation, background removal, etc.)
 * - Media library (images, videos, audio)
 * - Text editor with fonts and effects
 * - Elements (shapes, icons, stickers)
 * - Export to image/video
 */
const DesignEditorPage = () => {
  // Ref to access DesignEditor methods
  const designEditorRef = useRef(null);

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Page Header with Project Controls */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Design Editor</h1>
            <span className="text-sm text-gray-500">Create stunning visuals with AI</span>
          </div>
        </div>

        {/* Project Control Buttons - Moved from DesignEditor */}
        <div id="project-controls-container" className="flex items-center gap-3">
          {/* Buttons will be rendered here by DesignEditor using a portal */}
        </div>
      </div>

      {/* Design Editor Component */}
      <div className="flex-1 overflow-hidden">
        <DesignEditor ref={designEditorRef} />
      </div>
    </div>
  );
};

export default DesignEditorPage;

