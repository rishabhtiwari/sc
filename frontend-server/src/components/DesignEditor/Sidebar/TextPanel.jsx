import React, { useState, useRef } from 'react';
import { useToast } from '../../../hooks/useToast';
import TextStudio from '../TextStudio/TextStudio';
import TemplateSelectorModal from '../Modals/TemplateSelectorModal';
import { generateSlidesFromText } from '../../../utils/slideGenerator';
import api from '../../../services/api';

/**
 * Text Panel
 * Features: Upload text, Paste text, Generate with AI, Text presets, Slide templates
 */
const TextPanel = ({ onAddElement, onAddMultiplePages }) => {
  const { showToast } = useToast();
  const [isTextStudioOpen, setIsTextStudioOpen] = useState(false);
  const [isPasteModalOpen, setIsPasteModalOpen] = useState(false);
  const [isTemplateSelectorOpen, setIsTemplateSelectorOpen] = useState(false);
  const [pastedText, setPastedText] = useState('');
  const [pendingText, setPendingText] = useState(''); // Text waiting for template selection
  const fileInputRef = useRef(null);

  const textPresets = [
    {
      id: 'heading',
      name: 'Heading',
      text: 'Add a heading',
      fontSize: 48,
      fontWeight: 'bold',
      color: '#000000'
    },
    {
      id: 'subheading',
      name: 'Subheading',
      text: 'Add a subheading',
      fontSize: 32,
      fontWeight: '600',
      color: '#374151'
    },
    {
      id: 'body',
      name: 'Body Text',
      text: 'Add body text',
      fontSize: 16,
      fontWeight: 'normal',
      color: '#6B7280'
    },
    {
      id: 'caption',
      name: 'Caption',
      text: 'Add a caption',
      fontSize: 12,
      fontWeight: 'normal',
      color: '#9CA3AF'
    }
  ];

  const handleAddText = (preset) => {
    onAddElement({
      type: 'text',
      text: preset.text,
      fontSize: preset.fontSize,
      fontWeight: preset.fontWeight,
      color: preset.color,
      fontFamily: 'Arial, sans-serif'
    });
    showToast(`${preset.name} added to canvas`, 'success');
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
      // Read file content
      const text = await file.text();

      // Auto-generate slides with default 'content' template
      const slides = generateSlidesFromText(text, 'content');

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

    // Auto-generate slides with default 'content' template
    const slides = generateSlidesFromText(pastedText, 'content');

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

    // Auto-generate slides with default 'content' template
    const slides = generateSlidesFromText(text, 'content');

    if (slides.length > 0 && onAddMultiplePages) {
      onAddMultiplePages(slides);
      showToast(`Created ${slides.length} slide${slides.length > 1 ? 's' : ''} successfully!`, 'success');
      setIsTextStudioOpen(false);
    } else {
      showToast('Failed to generate slides', 'error');
    }
  };

  // Handle template selection
  const handleTemplateSelect = (templateId) => {
    console.log('🎨 Template selected:', templateId);
    console.log('📝 Pending text:', pendingText?.substring(0, 100) + '...');

    if (!pendingText) {
      console.error('❌ No pending text');
      showToast('No text to convert', 'error');
      return;
    }

    try {
      // Generate slides from text using selected template
      console.log('🔄 Generating slides...');
      const slides = generateSlidesFromText(pendingText, templateId);
      console.log('✅ Generated slides:', slides);

      if (slides.length === 0) {
        console.error('❌ No slides generated');
        showToast('Failed to generate slides', 'error');
        return;
      }

      // Check if onAddMultiplePages is available (for multi-page support)
      console.log('🔍 Checking onAddMultiplePages:', typeof onAddMultiplePages);

      if (onAddMultiplePages && typeof onAddMultiplePages === 'function') {
        console.log('✅ Calling onAddMultiplePages with', slides.length, 'slides');
        onAddMultiplePages(slides);
        showToast(`Created ${slides.length} slide${slides.length > 1 ? 's' : ''} successfully!`, 'success');
      } else {
        console.warn('⚠️ onAddMultiplePages not available, using fallback');
        // Fallback: Add first slide only
        if (slides[0] && slides[0].elements) {
          console.log('📄 Adding elements from first slide:', slides[0].elements);
          slides[0].elements.forEach(element => {
            onAddElement(element);
          });
          showToast('Slide created! (Multi-page support coming soon)', 'success');
        }
      }

      // Clear pending text
      setPendingText('');
      setPastedText('');
    } catch (error) {
      console.error('❌ Error generating slides:', error);
      showToast('Failed to generate slides', 'error');
    }
  };

  return (
    <>
      <div className="space-y-4">
        {/* Professional Blue Buttons */}
        <div className="space-y-3">
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
            <li>• Upload or paste your text</li>
            <li>• Slides are auto-generated with professional templates</li>
            <li>• Navigate between slides using page controls</li>
            <li>• Edit text directly on canvas</li>
          </ul>
        </div>
      </div>

      {/* Paste Text Modal */}
      {isPasteModalOpen && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-2xl w-[600px] max-h-[80vh] flex flex-col">
            {/* Header */}
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
                  ✕
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 flex-1 overflow-y-auto">
              <textarea
                value={pastedText}
                onChange={(e) => setPastedText(e.target.value)}
                placeholder="Paste or type your text here..."
                className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                autoFocus
              />
              <p className="text-sm text-gray-500 mt-2">
                {pastedText.length} characters
              </p>
            </div>

            {/* Footer */}
            <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
              <button
                onClick={() => {
                  setIsPasteModalOpen(false);
                  setPastedText('');
                }}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePasteText}
                disabled={!pastedText.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Add to Canvas
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Text Studio Modal */}
      {isTextStudioOpen && (
        <TextStudio
          isOpen={isTextStudioOpen}
          mode="modal"
          onClose={() => setIsTextStudioOpen(false)}
          onAddToCanvas={handleAddAIText}
        />
      )}

      {/* Template Selector Modal */}
      {isTemplateSelectorOpen && (
        <TemplateSelectorModal
          isOpen={isTemplateSelectorOpen}
          onClose={() => {
            setIsTemplateSelectorOpen(false);
            setPendingText('');
          }}
          onSelectTemplate={handleTemplateSelect}
          text={pendingText}
        />
      )}
    </>
  );
};

export default TextPanel;

