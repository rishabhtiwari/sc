import React, { useState, useEffect } from 'react';
import { useToast } from '../../../hooks/useToast';
import api from '../../../services/api';

/**
 * Text Studio - Full-screen modal for AI text generation
 * Similar to Audio Studio but for text content
 */
const TextStudio = ({ isOpen, onClose, onAddToCanvas }) => {
  const [activeSection, setActiveSection] = useState('generate'); // 'generate' or 'library'
  const [promptTemplates, setPromptTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [generatedText, setGeneratedText] = useState('');
  const [generating, setGenerating] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [textLibrary, setTextLibrary] = useState([]);
  const { showToast } = useToast();

  // Load templates when studio opens
  useEffect(() => {
    if (isOpen) {
      fetchPromptTemplates();
      fetchTextLibrary();
    }
  }, [isOpen]);

  const fetchPromptTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const response = await api.get('/prompt-templates', {
        params: { category: 'text_generation' }
      });
      if (response.data.status === 'success') {
        setPromptTemplates(response.data.templates || []);
      }
    } catch (error) {
      console.error('Error fetching prompt templates:', error);
      showToast('Failed to load templates', 'error');
    } finally {
      setLoadingTemplates(false);
    }
  };

  const fetchTextLibrary = async () => {
    try {
      const response = await api.get('/assets/', {
        params: { asset_type: 'document', folder: 'text-library' }
      });
      if (response.data.success) {
        setTextLibrary(response.data.assets || []);
      }
    } catch (error) {
      console.error('Error fetching text library:', error);
    }
  };

  const handleGenerateText = async () => {
    if (!selectedTemplate) {
      showToast('Please select a template', 'error');
      return;
    }

    setGenerating(true);
    try {
      const response = await api.post(
        `/prompt-templates/${selectedTemplate.template_id}/generate`,
        { context: {} }
      );

      if (response.data.status === 'success' && response.data.data) {
        const content = response.data.data.content || response.data.data;
        setGeneratedText(content);
        showToast('Text generated successfully!', 'success');
      }
    } catch (error) {
      console.error('Error generating text:', error);
      showToast('Failed to generate text', 'error');
    } finally {
      setGenerating(false);
    }
  };

  const handleDone = () => {
    if (!generatedText) {
      showToast('No text to add', 'error');
      return;
    }

    // Add text to canvas
    onAddToCanvas({
      type: 'text',
      text: generatedText,
      fontSize: 24,
      fontWeight: 'normal',
      color: '#000000',
      fontFamily: 'Arial, sans-serif'
    });

    showToast('Text added to canvas', 'success');
    
    // Close the studio
    onClose();
    
    // Reset state
    setGeneratedText('');
    setSelectedTemplate(null);
  };

  const handleSaveToLibrary = async () => {
    if (!generatedText) {
      showToast('No text to save', 'error');
      return;
    }

    try {
      const blob = new Blob([generatedText], { type: 'text/plain' });
      const formData = new FormData();
      formData.append('file', blob, `text_${Date.now()}.txt`);
      formData.append('asset_type', 'document');
      formData.append('folder', 'text-library');
      formData.append('title', `Generated Text - ${new Date().toLocaleString()}`);
      formData.append('description', `Template: ${selectedTemplate?.name || 'Custom'}`);

      const response = await api.post('/assets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.success) {
        showToast('Text saved to library', 'success');
        fetchTextLibrary();
      }
    } catch (error) {
      console.error('Error saving to library:', error);
      showToast('Failed to save to library', 'error');
    }
  };

  const handleLoadFromLibrary = async (item) => {
    try {
      const response = await api.get(`/assets/${item.asset_id}/download`);
      setGeneratedText(response.data);
      setActiveSection('generate');
      showToast('Text loaded from library', 'success');
    } catch (error) {
      showToast('Failed to load text', 'error');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-2xl w-[95%] h-[95%] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold text-gray-900">📝 Text Studio</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setActiveSection('generate')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeSection === 'generate'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Generate AI Text
              </button>
              <button
                onClick={() => setActiveSection('library')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeSection === 'library'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Text Library
              </button>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          {activeSection === 'generate' ? (
            <div className="h-full flex">
              {/* Left Panel - Template Selection */}
              <div className="w-1/3 border-r border-gray-200 p-6 overflow-y-auto">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Select Template
                </h3>
                {loadingTemplates ? (
                  <div className="text-center py-8 text-gray-500">
                    Loading templates...
                  </div>
                ) : promptTemplates.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No templates available
                  </div>
                ) : (
                  <div className="space-y-3">
                    {promptTemplates.map((template) => (
                      <button
                        key={template.template_id}
                        onClick={() => setSelectedTemplate(template)}
                        className={`w-full p-4 border-2 rounded-lg text-left transition-all ${
                          selectedTemplate?.template_id === template.template_id
                            ? 'border-blue-500 bg-blue-50 shadow-md'
                            : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="text-3xl">📝</div>
                          <div className="flex-1">
                            <div className="font-semibold text-gray-900">
                              {template.name}
                            </div>
                            <div className="text-sm text-gray-600 mt-1">
                              {template.description}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Right Panel - Generation & Preview */}
              <div className="flex-1 p-6 flex flex-col">
                <div className="flex-1 flex flex-col">
                  {/* Generate Button */}
                  <div className="mb-6">
                    <button
                      onClick={handleGenerateText}
                      disabled={generating || !selectedTemplate}
                      className="w-full px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-lg transition-all"
                    >
                      {generating ? (
                        <span className="flex items-center justify-center gap-2">
                          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Generating...
                        </span>
                      ) : (
                        '✨ Generate Text'
                      )}
                    </button>
                  </div>

                  {/* Preview Area */}
                  <div className="flex-1 flex flex-col">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Generated Text Preview
                    </h3>
                    <div className="flex-1 border-2 border-gray-300 rounded-lg p-6 bg-gray-50 overflow-y-auto">
                      {generatedText ? (
                        <div className="text-gray-900 text-lg leading-relaxed whitespace-pre-wrap">
                          {generatedText}
                        </div>
                      ) : (
                        <div className="h-full flex items-center justify-center text-gray-400">
                          <div className="text-center">
                            <div className="text-6xl mb-4">📄</div>
                            <div className="text-lg">
                              Select a template and click Generate Text
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // Text Library View
            <div className="h-full p-6 overflow-y-auto">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Saved Texts
              </h3>
              {textLibrary.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-6xl mb-4">📚</div>
                  <div className="text-lg">No saved texts yet</div>
                  <div className="text-sm mt-2">
                    Generate and save texts to build your library
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-4">
                  {textLibrary.map((item) => (
                    <div
                      key={item.asset_id}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-all"
                    >
                      <div className="font-semibold text-gray-900 mb-2">
                        {item.title}
                      </div>
                      <div className="text-sm text-gray-600 mb-3">
                        {item.description}
                      </div>
                      <button
                        onClick={() => handleLoadFromLibrary(item)}
                        className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                      >
                        Load Text
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer - Action Buttons */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <button
              onClick={handleSaveToLibrary}
              disabled={!generatedText}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              💾 Save to Library
            </button>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleDone}
                disabled={!generatedText}
                className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
              >
                ✓ Done - Add to Canvas
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TextStudio;

