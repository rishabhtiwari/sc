import React, { useState, useEffect, useRef } from 'react';
import { useToast } from '../../../hooks/useToast';
import api from '../../../services/api';
import { AiEditor } from 'aieditor';
import 'aieditor/dist/style.css';

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
  const { showToast } = useToast();
  const editorRef = useRef(null);
  const aiEditorInstance = useRef(null);

  // Load templates when studio opens
  useEffect(() => {
    if (isOpen) {
      fetchAllTemplates();
      fetchTextLibrary();
    }
  }, [isOpen]);

  // Initialize AIEditor when generated text changes
  useEffect(() => {
    if (generatedText && editorRef.current && !aiEditorInstance.current) {
      aiEditorInstance.current = new AiEditor({
        element: editorRef.current,
        placeholder: 'Generated content will appear here...',
        content: generatedText,
        editable: true,
        toolbarKeys: ['undo', 'redo', '|', 'bold', 'italic', 'underline', '|', 'heading', 'bulletList', 'orderedList', '|', 'link'],
      });
    } else if (generatedText && aiEditorInstance.current) {
      // Update content if editor already exists
      aiEditorInstance.current.setContent(generatedText);
    }

    // Cleanup on unmount
    return () => {
      if (aiEditorInstance.current) {
        aiEditorInstance.current.destroy();
        aiEditorInstance.current = null;
      }
    };
  }, [generatedText]);

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

  const handleDone = () => {
    if (!generatedText) {
      showToast('No text to add', 'error');
      return;
    }

    // Get content from AIEditor if it exists, otherwise use generatedText
    let finalText = generatedText;
    if (aiEditorInstance.current) {
      finalText = aiEditorInstance.current.getMarkdown() || aiEditorInstance.current.getText() || generatedText;
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

    // Cleanup editor
    if (aiEditorInstance.current) {
      aiEditorInstance.current.destroy();
      aiEditorInstance.current = null;
    }
  };

  const handleSaveToLibrary = async () => {
    if (!generatedText) {
      showToast('No text to save', 'error');
      return;
    }

    try {
      // Get content from AIEditor if it exists
      let contentToSave = generatedText;
      if (aiEditorInstance.current) {
        contentToSave = aiEditorInstance.current.getMarkdown() || aiEditorInstance.current.getText() || generatedText;
      }

      const blob = new Blob([contentToSave], { type: 'text/plain' });
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
          {/* Left Sidebar - Categories, Templates & Variables (w-80) */}
          <div className="w-80 border-r border-gray-200 bg-white overflow-y-auto">
            <div className="p-4">
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
                      {/* AIEditor for Rich Text Display */}
                      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-4">
                        <div
                          ref={editorRef}
                          className="min-h-[400px]"
                          style={{
                            padding: '20px',
                            fontSize: '16px',
                            lineHeight: '1.6'
                          }}
                        />
                      </div>

                      {/* Action Buttons */}
                      <div className="flex justify-center gap-3">
                        <button
                          onClick={handleSaveToLibrary}
                          className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium shadow-sm"
                        >
                          💾 Save to Text Library
                        </button>
                        <button
                          onClick={handleDone}
                          className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-semibold shadow-sm"
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

