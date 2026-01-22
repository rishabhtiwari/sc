import React from 'react';
import TextStudio from '../components/DesignEditor/TextStudio/TextStudio';

/**
 * Text Studio Page - Standalone full-page version for AI text generation
 * Reuses the TextStudio component in 'page' mode (NOT a modal popup)
 *
 * Features:
 * 1. AI Text Generation with Templates
 * 2. Custom Prompt Input
 * 3. Text Library Management
 * 4. Rich Text Editing with Tiptap
 */
const TextStudioPage = () => {
  const handleAddToCanvas = (textData) => {
    // For standalone page, we don't have a canvas
    // Could implement download or copy to clipboard here
    console.log('Text generated:', textData);
  };

  return (
    <TextStudio
      isOpen={true}
      onClose={null}
      onAddToCanvas={handleAddToCanvas}
      mode="page"
    />
  );
};

export default TextStudioPage;

