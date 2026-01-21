import React, { useState, useEffect } from 'react';
import { useToast } from '../../../hooks/useToast';
import api from '../../../services/api';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import { marked } from 'marked';

/**
 * Text Studio - Full-screen modal for AI text generation
 * Similar to Audio Studio but for text content
 */
const TextStudio = ({ isOpen, onClose, onAddToCanvas }) => {
  const [activeSection, setActiveSection] = useState('generate'); // 'generate' or 'library'
  const [allTemplates, setAllTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showAllCategories, setShowAllCategories] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateVariables, setTemplateVariables] = useState({});
  const [generatedText, setGeneratedText] = useState('');
  const [generating, setGenerating] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [textLibrary, setTextLibrary] = useState([]);
  const [customPrompt, setCustomPrompt] = useState('');
  const { showToast } = useToast();

  // Tiptap editor instance
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: 'Generated content will appear here...',
      }),
    ],
    content: '',
    editorProps: {
      attributes: {
        class: 'prose prose-lg max-w-none focus:outline-none min-h-[400px] p-6',
      },
    },
  });

  // Load templates when studio opens
  useEffect(() => {
    if (isOpen) {
      fetchAllTemplates();
      fetchTextLibrary();
    }
  }, [isOpen]);

  // Update Tiptap editor content when generated text changes
  useEffect(() => {
    if (editor && generatedText) {
      // Convert Markdown to HTML using marked
      const htmlContent = marked.parse(generatedText);
      // Set HTML content in Tiptap editor
      editor.commands.setContent(htmlContent);
    }
  }, [generatedText, editor]);

  // Fetch all templates and extract categories
  const fetchAllTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const response = await api.get('/prompt-templates');
      if (response.data.status === 'success') {
        const templates = response.data.templates || [];
        setAllTemplates(templates);

        // Extract unique categories
        const uniqueCategories = [...new Set(templates.map(t => t.category))];
        const categoryData = uniqueCategories.map(cat => ({
          id: cat,
          name: formatCategoryName(cat),
          icon: getCategoryIcon(cat),
          count: templates.filter(t => t.category === cat).length
        }));
        setCategories(categoryData);

        // Select first category by default
        if (categoryData.length > 0) {
          setSelectedCategory(categoryData[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching prompt templates:', error);
      showToast('Failed to load templates', 'error');
    } finally {
      setLoadingTemplates(false);
    }
  };

  // Format category name for display
  const formatCategoryName = (category) => {
    return category
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Get icon for category
  const getCategoryIcon = (category) => {
    const icons = {
      'text_generation': '✨',
      'ecommerce': '🛒',
      'social_media': '📱',
      'news': '📰',
      'marketing': '📢',
      'product_summary': '📦',
      'section_content': '📄',
      'custom': '⚙️'
    };
    return icons[category] || '📝';
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

  // Handle template selection
  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setGeneratedText(''); // Clear previous generation

    // Initialize variables with defaults
    const initialVars = {};
    (template.variables || []).forEach(variable => {
      initialVars[variable.name] = variable.default || '';
    });
    setTemplateVariables(initialVars);
  };

  // Handle variable input change
  const handleVariableChange = (varName, value) => {
    setTemplateVariables(prev => ({
      ...prev,
      [varName]: value
    }));
  };

  // Generate text with template and variables
  const handleGenerateText = async () => {
    if (!selectedTemplate) {
      showToast('Please select a template', 'error');
      return;
    }

    // Validate required variables
    const missingVars = (selectedTemplate.variables || [])
      .filter(v => v.required && !templateVariables[v.name])
      .map(v => v.name);

    if (missingVars.length > 0) {
      showToast(`Please fill in required fields: ${missingVars.join(', ')}`, 'error');
      return;
    }

    setGenerating(true);
    try {
      const response = await api.post(
        `/prompt-templates/${selectedTemplate.template_id}/generate`,
        { context: templateVariables }
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

  const handleCustomPromptGenerate = async () => {
    if (!customPrompt.trim()) {
      showToast('Please enter a prompt', 'error');
      return;
    }

    setGenerating(true);
    try {
      // Use the LLM generate endpoint - expects 'query' parameter
      const response = await api.post('/llm/generate', {
        query: customPrompt,
        use_rag: false,
        detect_code: false,
        max_tokens: 5000,
        temperature: 0.7,
        top_p: 0.95
      });

      if (response.data.status === 'success' && response.data.data) {
        const content = response.data.data.response || response.data.data.content || response.data.data.text || response.data.data;
        setGeneratedText(content);
        setSelectedTemplate(null); // Clear template selection
        showToast('Text generated successfully!', 'success');
      }
    } catch (error) {
      console.error('Error generating from custom prompt:', error);
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

    // Get content from Tiptap editor (plain text without HTML tags)
    let finalText = generatedText;
    if (editor) {
      finalText = editor.getText() || generatedText;
    }

    // Add text to canvas
    onAddToCanvas({
      type: 'text',
      text: finalText,
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
    if (editor) {
      editor.commands.clearContent();
    }
  };

  const handleSaveToLibrary = async () => {
    if (!generatedText) {
      showToast('No text to save', 'error');
      return;
    }

    try {
      // Get content from Tiptap editor (plain text)
      let contentToSave = generatedText;
      if (editor) {
        contentToSave = editor.getText() || generatedText;
      }

      const formData = new FormData();
      const blob = new Blob([contentToSave], { type: 'text/plain' });
      formData.append('file', blob, `text_${Date.now()}.txt`);
      formData.append('asset_type', 'document');
      formData.append('folder', 'text-library');
      formData.append('title', `Generated Text - ${new Date().toLocaleString()}`);
      formData.append('description', `Template: ${selectedTemplate?.name || 'Custom'}`);

      console.log('📤 Uploading text to library:', {
        blobSize: blob.size,
        blobType: blob.type,
        contentLength: contentToSave.length
      });

      // Let axios automatically detect FormData and set correct Content-Type with boundary
      const response = await api.post('/assets/upload', formData);

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

  const handleDeleteFromLibrary = async (item, event) => {
    // Prevent triggering the parent onClick (load)
    event.stopPropagation();

    if (!confirm(`Delete "${item.title}"?`)) {
      return;
    }

    try {
      const response = await api.delete(`/assets/${item.asset_id}`);
      if (response.data.success) {
        showToast('Text deleted from library', 'success');
        fetchTextLibrary();
      }
    } catch (error) {
      console.error('Error deleting from library:', error);
      showToast('Failed to delete text', 'error');
    }
  };

  const handleDownloadText = async (item, event) => {
    // Prevent triggering the parent onClick (load)
    event.stopPropagation();

    try {
      const response = await api.get(`/assets/${item.asset_id}/download`);
      const blob = new Blob([response.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = item.name || 'text.txt';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      showToast('Text downloaded', 'success');
    } catch (error) {
      console.error('Error downloading text:', error);
      showToast('Failed to download text', 'error');
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
          {/* Left Sidebar - Categories, Templates & Variables (w-80) */}
          <div className="w-80 border-r border-gray-200 bg-white overflow-y-auto">
            <div className="p-4">
              {/* Custom Prompt Section */}
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">
                  💬 Ask AI Anything
                </h3>
                <div className="space-y-2">
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="Type your question or prompt here... (e.g., 'Write a product description for wireless headphones')"
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={4}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                        handleCustomPromptGenerate();
                      }
                    }}
                  />
                  <button
                    onClick={handleCustomPromptGenerate}
                    disabled={generating || !customPrompt.trim()}
                    className="w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm transition-all shadow-sm"
                  >
                    {generating ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Generating...
                      </span>
                    ) : (
                      '✨ Generate with AI'
                    )}
                  </button>
                  <p className="text-xs text-gray-500 text-center">
                    Or use templates below ↓
                  </p>
                </div>
              </div>

              {/* Divider */}
              <div className="border-t border-gray-200 mb-6"></div>

              {/* Categories Section */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-900">Categories</h3>
                  <button
                    onClick={() => window.open('/prompt-templates', '_blank')}
                    className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Browse All
                  </button>
                </div>

                {loadingTemplates ? (
                  <div className="text-center py-4">
                    <div className="animate-spin text-2xl">⏳</div>
                  </div>
                ) : (
                  <>
                    {/* Show first 3 categories */}
                    <div className="flex flex-wrap gap-2 mb-2">
                      {categories.slice(0, showAllCategories ? categories.length : 3).map((category) => (
                        <button
                          key={category.id}
                          onClick={() => {
                            setSelectedCategory(category.id);
                            setSelectedTemplate(null);
                            setGeneratedText('');
                          }}
                          className={`flex items-center gap-2 px-3 py-2 rounded-full border-2 transition-all ${
                            selectedCategory === category.id
                              ? 'border-blue-500 bg-blue-50 text-blue-700'
                              : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300'
                          }`}
                        >
                          <span className="text-lg">{category.icon}</span>
                          <span className="text-xs font-medium">{category.name}</span>
                          <span className="text-xs bg-gray-200 px-1.5 py-0.5 rounded-full">{category.count}</span>
                        </button>
                      ))}
                    </div>

                    {/* More button */}
                    {categories.length > 3 && (
                      <button
                        onClick={() => setShowAllCategories(!showAllCategories)}
                        className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                      >
                        {showAllCategories ? '− Show Less' : `+ ${categories.length - 3} More`}
                      </button>
                    )}
                  </>
                )}
              </div>

              {/* Templates Section */}
              {selectedCategory && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Templates</h3>
                  {allTemplates.filter(t => t.category === selectedCategory).length === 0 ? (
                    <div className="text-center py-4 text-gray-500">
                      <div className="text-3xl mb-1">📝</div>
                      <p className="text-xs">No templates</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {allTemplates
                        .filter(t => t.category === selectedCategory)
                        .map((template) => (
                          <button
                            key={template.template_id}
                            onClick={() => handleTemplateSelect(template)}
                            className={`w-full p-2.5 border-2 rounded-lg text-left transition-all ${
                              selectedTemplate?.template_id === template.template_id
                                ? 'border-blue-500 bg-blue-50 shadow-sm'
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                            }`}
                          >
                            <div className="font-medium text-xs text-gray-900 truncate">
                              {template.name}
                            </div>
                            <div className="text-xs text-gray-600 mt-0.5 line-clamp-2">
                              {template.description}
                            </div>
                          </button>
                        ))}
                    </div>
                  )}
                </div>
              )}

              {/* Variables Section */}
              {selectedTemplate && selectedTemplate.variables && selectedTemplate.variables.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Template Variables</h3>
                  <div className="space-y-3">
                    {selectedTemplate.variables.map((variable) => (
                      <div key={variable.name}>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          {variable.description || variable.name}
                          {variable.required && <span className="text-red-500 ml-1">*</span>}
                        </label>
                        {variable.type === 'long_text' ? (
                          <textarea
                            value={templateVariables[variable.name] || ''}
                            onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                            placeholder={variable.default || `Enter ${variable.name}...`}
                            className="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={3}
                          />
                        ) : (
                          <input
                            type={variable.type === 'number' ? 'number' : 'text'}
                            value={templateVariables[variable.name] || ''}
                            onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                            placeholder={variable.default || `Enter ${variable.name}...`}
                            className="w-full px-3 py-2 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Generate Button */}
              {selectedTemplate && (
                <button
                  onClick={handleGenerateText}
                  disabled={generating}
                  className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-all"
                >
                  {generating ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Generating...
                    </span>
                  ) : (
                    '✨ Generate Text'
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Middle Section - Main Content Area */}
          <div className="flex-1 overflow-y-auto">
            {activeSection === 'generate' ? (
              <div className="flex flex-col h-full bg-gray-50">
                {/* Header with Info */}
                <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900">✨ Generated Content</h2>
                      <p className="text-sm text-gray-600">
                        {selectedTemplate
                          ? `Template: ${selectedTemplate.name}`
                          : 'Select a category and template to get started'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Preview/Output Area */}
                <div className="flex-1 min-h-0 overflow-y-auto p-6">
                  {!generatedText ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="text-center max-w-md">
                        <div className="text-6xl mb-4">📝</div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-2">
                          Ready to Generate Text
                        </h3>
                        <p className="text-gray-600">
                          {selectedTemplate
                            ? 'Fill in the template variables on the left and click Generate to create your content.'
                            : 'Select a category and template from the left sidebar to get started.'}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="max-w-4xl mx-auto">
                      {/* Tiptap Editor for Rich Text Display */}
                      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-4">
                        <EditorContent editor={editor} />
                      </div>

                      {/* Action Buttons */}
                      <div className="flex justify-center gap-3">
                        <button
                          onClick={handleSaveToLibrary}
                          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors font-medium"
                        >
                          💾 Save to Library
                        </button>
                        <button
                          onClick={handleDone}
                          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 transition-colors font-medium"
                        >
                          ✓ Add to Canvas
                        </button>
                      </div>
                    </div>
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
                          {/* Show text preview if available */}
                          {item.metadata?.preview && (
                            <div className="text-sm text-gray-700 mb-2 p-2 bg-gray-50 rounded border border-gray-100 line-clamp-3">
                              "{item.metadata.preview}"
                            </div>
                          )}
                          <div className="text-sm text-gray-600 mb-3">
                            {item.description}
                          </div>
                          <div className="text-xs text-gray-400 mb-3">
                            {new Date(item.created_at).toLocaleDateString()}
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleLoadFromLibrary(item)}
                              className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                            >
                              📄 Load Text
                            </button>
                            <button
                              onClick={(e) => handleDeleteFromLibrary(item, e)}
                              className="px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 text-sm"
                              title="Delete"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Panel - Text Library Sidebar - Matching Audio Studio Style */}
          <div className="w-96 border-l border-gray-200 bg-white overflow-y-auto">
            <div className="p-4">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-gray-900">
                  📚 Text Library
                </h3>
                <button
                  onClick={() => setActiveSection('library')}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                >
                  View All →
                </button>
              </div>

              {/* Categories */}
              <div className="mb-4">
                <div className="space-y-1">
                  <div className="flex items-center justify-between px-3 py-2 text-sm font-medium text-gray-700 bg-blue-50 rounded-lg border border-blue-200">
                    <span>📄 All Texts ({textLibrary.length})</span>
                  </div>
                </div>
              </div>

              {/* Recents Section */}
              <div className="mb-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                  <span>🕒</span>
                  <span>Recents</span>
                </div>
              </div>

              {/* Text Items */}
              {textLibrary.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-5xl mb-3">📝</div>
                  <p className="text-sm text-gray-600 font-medium">No saved texts yet</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Generate and save texts to build your library
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {textLibrary.slice(0, 10).map((item) => (
                    <div
                      key={item.asset_id}
                      className="group relative bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md hover:border-blue-300 transition-all"
                    >
                      {/* Text Icon & Preview */}
                      <div className="flex gap-3 mb-2">
                        <div className="flex-shrink-0 w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-xl">
                          📝
                        </div>
                        <div className="flex-1 min-w-0">
                          {/* Preview Text */}
                          {item.metadata?.preview && (
                            <div className="text-xs text-gray-700 line-clamp-2 mb-1 leading-relaxed">
                              "{item.metadata.preview}"
                            </div>
                          )}
                          {/* Template info */}
                          <div className="text-xs text-gray-500 truncate">
                            {item.metadata?.description || 'Custom text'}
                          </div>
                        </div>
                      </div>

                      {/* Date */}
                      <div className="text-xs text-gray-400 mb-2">
                        {new Date(item.created_at).toLocaleDateString()}
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleLoadFromLibrary(item)}
                          className="flex-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700 transition-colors font-medium"
                        >
                          📄 Load
                        </button>
                        <button
                          onClick={(e) => handleDownloadText(item, e)}
                          className="px-3 py-1.5 bg-gray-100 text-gray-700 text-xs rounded-md hover:bg-gray-200 transition-colors"
                          title="Download"
                        >
                          ⬇️
                        </button>
                        <button
                          onClick={(e) => handleDeleteFromLibrary(item, e)}
                          className="px-3 py-1.5 bg-red-50 text-red-600 text-xs rounded-md hover:bg-red-100 transition-colors"
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>

                      {/* More Options Menu (3 dots) */}
                      <button
                        className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="More options"
                      >
                        ⋮
                      </button>
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

