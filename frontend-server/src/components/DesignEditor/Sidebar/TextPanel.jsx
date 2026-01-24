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

      // Store text and show template selector
      setPendingText(text);
      setIsTemplateSelectorOpen(true);

      showToast('Text file loaded! Choose a template to create slides', 'success');
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

    // Store text and show template selector
    setPendingText(pastedText);
    setIsPasteModalOpen(false);
    setIsTemplateSelectorOpen(true);

    showToast('Text loaded! Choose a template to create slides', 'success');
  };

  // Handle AI-generated text
  const handleAddAIText = (textData) => {
    const text = textData.text || textData;

    // Store text and show template selector
    setPendingText(text);
    setIsTextStudioOpen(false);
    setIsTemplateSelectorOpen(true);

    showToast('AI text generated! Choose a template to create slides', 'success');
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
      <div className="space-y-6">
        {/* Text Input Methods */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-900">Add Text Content</h3>
          <div className="space-y-2">
            {/* Upload Text File */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center group"
            >
              <div className="text-3xl mb-2">📤</div>
              <div className="text-sm font-medium text-gray-900 group-hover:text-blue-600">
                Upload Text File
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Upload .txt file
              </div>
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
              className="w-full p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center group"
            >
              <div className="text-3xl mb-2">📋</div>
              <div className="text-sm font-medium text-gray-900 group-hover:text-blue-600">
                Paste Text
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Insert or paste your text
              </div>
            </button>

            {/* Generate with AI */}
            <button
              onClick={() => setIsTextStudioOpen(true)}
              className="w-full p-4 border-2 border-dashed border-purple-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all text-center group bg-gradient-to-r from-blue-50 to-purple-50"
            >
              <div className="text-3xl mb-2">✨</div>
              <div className="text-sm font-medium text-gray-900 group-hover:text-purple-600">
                Generate with AI
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Use AI to create text
              </div>
            </button>
          </div>
        </div>

        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Or use quick text styles</h3>
        </div>

        {/* Text Presets */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-900">Text Styles</h3>
        <div className="space-y-2">
          {textPresets.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handleAddText(preset)}
              className="w-full p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
            >
              <div
                style={{
                  fontSize: `${Math.min(preset.fontSize / 2, 24)}px`,
                  fontWeight: preset.fontWeight,
                  color: preset.color
                }}
              >
                {preset.text}
              </div>
              <div className="text-xs text-gray-500 mt-1">{preset.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Font Combinations */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Font Combinations</h3>
        <div className="space-y-2">
          <button className="w-full p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left">
            <div className="font-bold text-lg">Modern Sans</div>
            <div className="text-sm text-gray-600">Clean and professional</div>
          </button>
          <button className="w-full p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left">
            <div className="font-serif text-lg font-bold">Classic Serif</div>
            <div className="text-sm text-gray-600">Elegant and timeless</div>
          </button>
          <button className="w-full p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left">
            <div className="font-mono text-lg font-bold">Tech Mono</div>
            <div className="text-sm text-gray-600">Modern and technical</div>
          </button>
        </div>
      </div>

      {/* Text Effects */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Text Effects</h3>
        <div className="grid grid-cols-2 gap-2">
          <button className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-2xl mb-1">🌈</div>
            <div className="text-xs font-medium">Gradient</div>
          </button>
          <button className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-2xl mb-1">💫</div>
            <div className="text-xs font-medium">Shadow</div>
          </button>
          <button className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-2xl mb-1">✨</div>
            <div className="text-xs font-medium">Glow</div>
          </button>
          <button className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-2xl mb-1">🎨</div>
            <div className="text-xs font-medium">Outline</div>
          </button>
        </div>
      </div>

        {/* Tips */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">💡 Tips</h4>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>• Upload, paste, or generate text with AI</li>
            <li>• Double-click text to edit</li>
            <li>• Use consistent fonts for better design</li>
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

