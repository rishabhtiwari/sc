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
      <div className="bg-white rounded-lg shadow-2xl w-[95%] h-[95%] flex flex-col overflow-hidden">
        {/* Header - Similar to Audio Studio */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">📝</span>
              <h1 className="text-2xl font-bold text-gray-900">Text Studio</h1>
            </div>
            <button
              onClick={onClose}
              className="text-gray-600 hover:text-gray-900 text-2xl font-bold transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tabs - Similar to Audio Studio */}
        <div className="bg-white border-b border-gray-200 flex-shrink-0">
          <div className="flex px-6">
            <button
              onClick={() => setActiveSection('generate')}
              className={`px-6 py-3 font-medium border-b-2 transition-all ${
                activeSection === 'generate'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <span className="mr-2">✨</span>
              Generate AI Text
            </button>
            <button
              onClick={() => setActiveSection('library')}
              className={`px-6 py-3 font-medium border-b-2 transition-all ${
                activeSection === 'library'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <span className="mr-2">📚</span>
              Text Library
            </button>
          </div>
        </div>

        {/* Main Content - Three Column Layout */}
        <div className="flex flex-1 min-h-0 bg-gray-50">
          {/* Left Sidebar - Template Selection (w-80) */}
          <div className="w-80 border-r border-gray-200 bg-white overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  📋 Templates
                </h3>
                <button
                  onClick={() => window.open('/prompt-templates', '_blank')}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                >
                  Browse All
                </button>
              </div>

              {loadingTemplates ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="animate-spin text-3xl mb-2">⏳</div>
                  <p className="text-sm">Loading...</p>
                </div>
              ) : promptTemplates.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">📝</div>
                  <p className="text-sm">No templates</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {promptTemplates.map((template) => (
                    <button
                      key={template.template_id}
                      onClick={() => setSelectedTemplate(template)}
                      className={`w-full p-3 border-2 rounded-lg text-left transition-all ${
                        selectedTemplate?.template_id === template.template_id
                          ? 'border-blue-500 bg-blue-50 shadow-md'
                          : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <div className="text-2xl">📝</div>
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-sm text-gray-900 truncate">
                            {template.name}
                          </div>
                          <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                            {template.description}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Middle Section - Main Content Area */}
          <div className="flex-1 overflow-y-auto">
            {activeSection === 'generate' ? (
              <div className="flex flex-col h-full bg-gray-50 overflow-hidden">
                {/* Header with Info */}
                <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">✨ AI Text Generation</h2>
                      <p className="text-sm text-gray-600">
                        {selectedTemplate
                          ? `Using template: ${selectedTemplate.name}`
                          : 'Select a template to get started'}
                      </p>
                    </div>
                    <button
                      onClick={() => window.open('/prompt-templates', '_blank')}
                      className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                    >
                      📋 Browse All Templates
                    </button>
                  </div>
                </div>

                {/* Preview/Output Area */}
                <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4">
                  {!generatedText ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center">
                        <div className="text-6xl mb-4">📝</div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-2">
                          Ready to Generate Text
                        </h3>
                        <p className="text-gray-600 max-w-md">
                          {selectedTemplate
                            ? `Click Generate to create: ${selectedTemplate.description}`
                            : 'Select a template from the left sidebar and click Generate to create professional text content.'}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-900">Generated Text</h3>
                        <div className="flex gap-2">
                          <button
                            onClick={handleSaveToLibrary}
                            className="px-3 py-1.5 bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100 transition-colors text-sm font-medium"
                          >
                            💾 Save
                          </button>
                          <button
                            onClick={handleDone}
                            className="px-3 py-1.5 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors text-sm font-medium"
                          >
                            ✓ Add to Canvas
                          </button>
                        </div>
                      </div>
                      <div className="text-gray-900 text-base leading-relaxed whitespace-pre-wrap">
                        {generatedText}
                      </div>
                    </div>
                  )}
                </div>

                {/* Input Bar - Fixed at Bottom */}
                <div className="bg-white border-t border-gray-200 px-6 py-4 flex-shrink-0">
                  <div className="flex items-center gap-3">
                    <div className="flex-1">
                      <input
                        type="text"
                        placeholder={selectedTemplate ? "Add context or leave empty for default generation..." : "Select a template first..."}
                        disabled={!selectedTemplate}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                      />
                    </div>
                    <button
                      onClick={handleGenerateText}
                      disabled={generating || !selectedTemplate}
                      className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-all"
                    >
                      {generating ? (
                        <span className="flex items-center gap-2">
                          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Generating...
                        </span>
                      ) : (
                        '✨ Generate'
                      )}
                    </button>
                  </div>
                  {selectedTemplate && (
                    <p className="text-xs text-gray-500 mt-2">
                      Template: {selectedTemplate.description}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              // Text Library Full View
              <div className="p-6">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    📚 Saved Texts
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
                    <div className="grid grid-cols-2 gap-4">
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
              </div>
            )}
          </div>

          {/* Right Panel - Text Library Sidebar (1/3 width) - Similar to Audio Studio */}
          <div className="w-96 border-l border-gray-200 bg-white overflow-y-auto">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                📚 Text Library
              </h3>
              {textLibrary.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-2">📝</div>
                  <p className="text-sm text-gray-600">No saved texts yet</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Generate text to see it here
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {textLibrary.map((item) => (
                    <div
                      key={item.asset_id}
                      className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition-all cursor-pointer"
                      onClick={() => handleLoadFromLibrary(item)}
                    >
                      <div className="font-medium text-gray-900 text-sm mb-1">
                        {item.title}
                      </div>
                      <div className="text-xs text-gray-600 line-clamp-2">
                        {item.description}
                      </div>
                      <div className="text-xs text-gray-400 mt-2">
                        {new Date(item.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TextStudio;

