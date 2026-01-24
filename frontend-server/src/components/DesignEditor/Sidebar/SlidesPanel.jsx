import React, { useState, useRef } from 'react';
import { generateSlidesFromText } from '../../../utils/slideGenerator';
import TextStudio from '../../TextStudio/TextStudio';

/**
 * Slides Panel - Create and manage slides
 */
const SlidesPanel = ({ onAddMultiplePages }) => {
  const [isPasteModalOpen, setIsPasteModalOpen] = useState(false);
  const [isTextStudioOpen, setIsTextStudioOpen] = useState(false);
  const [pastedText, setPastedText] = useState('');
  const fileInputRef = useRef(null);

  const showToast = (message, type) => {
    console.log(`${type.toUpperCase()}: ${message}`);
  };

  // Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.txt')) {
      showToast('Please upload a .txt file', 'error');
      return;
    }

    try {
      const text = await file.text();
      const slides = generateSlidesFromText(text, 'title');

      if (slides.length > 0 && onAddMultiplePages) {
        onAddMultiplePages(slides);
        showToast(`Created ${slides.length} slide${slides.length > 1 ? 's' : ''} successfully!`, 'success');
      } else {
        showToast('Failed to generate slides', 'error');
      }
    } catch (error) {
      console.error('Error reading file:', error);
      showToast('Failed to read file', 'error');
    }
  };

  // Handle paste text
  const handlePasteText = () => {
    if (!pastedText.trim()) {
      showToast('Please enter some text', 'error');
      return;
    }

    const slides = generateSlidesFromText(pastedText, 'title');

    if (slides.length > 0 && onAddMultiplePages) {
      onAddMultiplePages(slides);
      showToast(`Created ${slides.length} slide${slides.length > 1 ? 's' : ''} successfully!`, 'success');
      setIsPasteModalOpen(false);
      setPastedText('');
    } else {
      showToast('Failed to generate slides', 'error');
    }
  };

  // Handle AI-generated text
  const handleAddAIText = (textData) => {
    const text = textData.text || textData;
    const slides = generateSlidesFromText(text, 'title');

    if (slides.length > 0 && onAddMultiplePages) {
      onAddMultiplePages(slides);
      showToast(`Created ${slides.length} slide${slides.length > 1 ? 's' : ''} successfully!`, 'success');
      setIsTextStudioOpen(false);
    } else {
      showToast('Failed to generate slides', 'error');
    }
  };

  return (
    <>
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">📊 Create Slides from Text</h3>

        <div className="space-y-2">
          {/* Upload Text File */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-2 shadow-sm"
          >
            <span>📤</span>
            Upload Text File
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt"
            onChange={handleFileUpload}
            className="hidden"
          />

          {/* Paste Text */}
          <button
            onClick={() => setIsPasteModalOpen(true)}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-2 shadow-sm"
          >
            <span>📋</span>
            Paste Text
          </button>

          {/* Generate with AI */}
          <button
            onClick={() => setIsTextStudioOpen(true)}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-2 shadow-sm"
          >
            <span>✨</span>
            Generate with AI
          </button>
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">💡 How it works</h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>• Upload or paste your text content</li>
            <li>• Slides are auto-generated with modern templates</li>
            <li>• Navigate between slides using page controls</li>
            <li>• Add text, images, and media to customize</li>
          </ul>
        </div>
      </div>

      {/* Paste Text Modal */}
      {isPasteModalOpen && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-2xl w-[600px] max-h-[80vh] flex flex-col">
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-3xl">📋</span>
                  <h2 className="text-xl font-bold text-gray-900">Paste Your Text</h2>
                </div>
                <button
                  onClick={() => {
                    setIsPasteModalOpen(false);
                    setPastedText('');
                  }}
                  className="text-gray-600 hover:text-gray-900 text-2xl font-bold transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <textarea
                value={pastedText}
                onChange={(e) => setPastedText(e.target.value)}
                placeholder="Paste your text here..."
                className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
            </div>

            <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex-shrink-0 flex justify-end gap-3">
              <button
                onClick={() => {
                  setIsPasteModalOpen(false);
                  setPastedText('');
                }}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePasteText}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create Slides
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Text Studio Modal */}
      {isTextStudioOpen && (
        <TextStudio
          mode="modal"
          onClose={() => setIsTextStudioOpen(false)}
          onAddText={handleAddAIText}
        />
      )}
    </>
  );
};

export default SlidesPanel;

