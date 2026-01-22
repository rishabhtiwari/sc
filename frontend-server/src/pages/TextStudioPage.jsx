import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TextStudio from '../components/DesignEditor/TextStudio/TextStudio';

/**
 * Text Studio Page - Standalone page for AI text generation
 * Reuses the TextStudio component from Design Editor
 * 
 * Features:
 * 1. AI Text Generation with Templates
 * 2. Custom Prompt Input
 * 3. Text Library Management
 * 4. Rich Text Editing with Tiptap
 */
const TextStudioPage = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(true);

  const handleClose = () => {
    setIsOpen(false);
    // Navigate back to previous page or dashboard
    navigate(-1);
  };

  const handleAddToCanvas = (textData) => {
    // For standalone page, we don't have a canvas
    // Just show a success message or download the text
    console.log('Text generated:', textData);
  };

  return (
    <div className="h-screen bg-gray-50">
      <TextStudio
        isOpen={isOpen}
        onClose={handleClose}
        onAddToCanvas={handleAddToCanvas}
      />
    </div>
  );
};

export default TextStudioPage;

