import React, { useState, useEffect } from 'react';
import { Button } from '../';
import { useContentGeneration } from '../../../hooks/useContentGeneration';
import { useToast } from '../../../hooks/useToast';
import PromptTemplateSelector from './PromptTemplateSelector';

/**
 * Default content parser for markdown-style sections
 * Parses content with format: ## Section Name\nContent here...
 * Also handles sections without ## prefix (fallback mode)
 *
 * @param {string} text - Content to parse
 * @returns {Array} Array of section objects with title and content
 */
const defaultParseContent = (text) => {
  if (!text || typeof text !== 'string') {
    return [];
  }

  const sections = [];

  // First, try to split by markdown headings (## Section Name)
  // Handle both cases: text starting with ## and text with \n##
  // Add a newline at the start if text begins with ## to normalize
  let normalizedText = text;
  if (text.trim().startsWith('##')) {
    normalizedText = '\n' + text;
  }

  let parts = normalizedText.split(/\n##\s+/);

  // Check if we found any sections with ##
  let hasMarkdownHeaders = parts.length > 1;

  // If first part is empty (because we added \n at start), remove it
  if (hasMarkdownHeaders && !parts[0].trim()) {
    parts = parts.slice(1);
  }

  // If we found markdown headers, parse them
  if (hasMarkdownHeaders && parts.length > 0) {
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i].trim();
      if (!part) continue;

      // Split into title and content
      const lines = part.split('\n');
      let title = lines[0].trim();

      // Remove ## prefix if it exists (in case text starts with ##)
      if (title.startsWith('##')) {
        title = title.substring(2).trim();
      }

      const content = lines.slice(1).join('\n').trim();

      sections.push({
        title: title,
        content: content
      });
    }
  } else {
    // Fallback: Try to detect sections by common section titles
    // This handles cases where LLM didn't use ## properly
    const commonSections = [
      'Opening Hook',
      'Product Introduction',
      'Key Features & Benefits',
      'Social Proof & Trust',
      'Call-to-Action',
      'Introduction',
      'Features',
      'Benefits',
      'Conclusion'
    ];

    // Build regex pattern to match section titles (case-insensitive)
    const sectionPattern = new RegExp(
      `^(${commonSections.join('|')})\\s*$`,
      'im'
    );

    const lines = text.split('\n');
    let currentSection = null;
    let currentContent = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Check if this line is a section title
      const match = line.match(sectionPattern);

      if (match) {
        // Save previous section if exists
        if (currentSection) {
          sections.push({
            title: currentSection,
            content: currentContent.join('\n').trim()
          });
        }

        // Start new section
        currentSection = match[1];
        currentContent = [];
      } else if (currentSection) {
        // Add line to current section content
        currentContent.push(lines[i]);
      }
    }

    // Add last section
    if (currentSection && currentContent.length > 0) {
      sections.push({
        title: currentSection,
        content: currentContent.join('\n').trim()
      });
    }
  }

  return sections;
};

/**
 * Convert JSON object to sections array
 * Dynamically handles any JSON structure from LLM output
 *
 * @param {Object} jsonContent - JSON object from LLM
 * @returns {Array} Array of section objects with title and content
 */
const convertJsonToSections = (jsonContent) => {
  if (!jsonContent || typeof jsonContent !== 'object') {
    return [];
  }

  const sections = [];

  // Helper to format field name as title
  const formatTitle = (fieldName) => {
    return fieldName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Helper to format content based on type
  const formatContent = (value) => {
    if (Array.isArray(value)) {
      // Handle array of objects (like key_features)
      if (value.length > 0 && typeof value[0] === 'object') {
        return value.map((item, index) => {
          // Extract feature_name/title and description
          const name = item.feature_name || item.title || item.name || `Item ${index + 1}`;
          const desc = item.description || item.content || item.text || '';
          return `**${name}:** ${desc}`;
        }).join('\n\n');
      }
      // Handle array of strings
      return value.map((item, index) => `${index + 1}. ${item}`).join('\n');
    } else if (typeof value === 'object') {
      // Handle nested objects
      return Object.entries(value)
        .map(([key, val]) => `**${formatTitle(key)}:** ${val}`)
        .join('\n\n');
    } else {
      // Handle primitive values (string, number, boolean)
      return String(value);
    }
  };

  // Convert each field to a section
  Object.entries(jsonContent).forEach(([key, value]) => {
    // Skip metadata fields
    if (key === 'sections' || key === 'full_text' || key === 'metadata') {
      return;
    }

    sections.push({
      title: formatTitle(key),
      content: formatContent(value)
    });
  });

  return sections;
};

/**
 * Generic AI Content Generator Component
 * Can be used for product summaries, news articles, social posts, etc.
 *
 * @param {Object} props
 * @param {string} props.endpoint - API endpoint for content generation
 * @param {Object} props.inputData - Data to send to the endpoint
 * @param {string} props.initialContent - Initial content value
 * @param {string} props.initialTemplateId - Initial template ID (for editing)
 * @param {Object} props.initialTemplateVariables - Initial template variables (for editing)
 * @param {Function} props.onContentGenerated - Callback when content is generated
 * @param {Function} props.onContentChange - Callback when content is edited
 * @param {Function} props.onTemplateSelect - Callback when template is selected
 * @param {string} props.label - Label for the content area
 * @param {string} props.placeholder - Placeholder text
 * @param {boolean} props.showEditMode - Show edit/preview toggle
 * @param {boolean} props.showSections - Parse and show content as sections
 * @param {Function} props.parseContent - Custom parser for content sections (uses default markdown parser if not provided)
 * @param {boolean} props.showPromptTemplates - Show prompt template selector
 * @param {string} props.templateCategory - Template category for filtering (e.g., 'product_summary', 'article_summary')
 * @param {Object} props.contextData - Context data for auto-populating template variables (e.g., product_name, description, price)
 * @param {string} props.className - Additional CSS classes
 */
const AIContentGenerator = ({
  endpoint,
  inputData = {},
  initialContent = '',
  initialTemplateId = null,
  initialTemplateVariables = {},
  onContentGenerated,
  onContentChange,
  onTemplateSelect,
  label = 'AI Generated Content',
  placeholder = 'Generated content will appear here...',
  showEditMode = true,
  showSections = false,
  parseContent = null,
  showPromptTemplates = false,
  templateCategory = 'product_summary',
  contextData = {},
  className = ''
}) => {
  const [content, setContent] = useState(initialContent);
  const [isEditing, setIsEditing] = useState(false);
  const [sections, setSections] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState(initialTemplateId);
  const [selectedTemplateData, setSelectedTemplateData] = useState(null);
  const [templateVariables, setTemplateVariables] = useState(initialTemplateVariables);
  const { generating, generate } = useContentGeneration();
  const { showToast } = useToast();

  // Update content when initialContent changes
  useEffect(() => {
    setContent(initialContent);
  }, [initialContent]);

  // Parse content into sections if needed
  useEffect(() => {
    if (showSections && content) {
      // SIMPLIFIED: Content is always { sections: [...] } from backend
      if (typeof content === 'object' && content.sections) {
        console.log('📊 Using sections from backend:', content.sections);
        setSections(content.sections);
      } else {
        console.warn('⚠️ Content does not have expected format: { sections: [...] }');
        setSections([]);
      }
    }
  }, [content, showSections]);

  /**
   * Handle content generation
   */
  const handleGenerate = async (regenerate = false) => {
    // Validate that a template is selected when showPromptTemplates is enabled
    if (showPromptTemplates && !selectedTemplateId) {
      showToast('⚠️ Please select a prompt template before generating content', 'error', 5000);
      return;
    }

    // Validate required template variables
    if (showPromptTemplates && selectedTemplateId && selectedTemplateData) {
      const requiredVars = selectedTemplateData.variables?.filter(v => v.required) || [];
      const missingVars = requiredVars.filter(v => {
        const value = templateVariables[v.name];
        // Check for empty string, null, undefined, or empty array
        if (value === null || value === undefined || value === '') {
          return true;
        }
        if (typeof value === 'string' && value.trim() === '') {
          return true;
        }
        if (Array.isArray(value) && value.length === 0) {
          return true;
        }
        return false;
      });

      if (missingVars.length > 0) {
        const missingNames = missingVars.map(v => v.description || v.name).join(', ');
        showToast(`⚠️ Please fill in all required fields: ${missingNames}`, 'error', 6000);

        // Log for debugging
        console.warn('❌ Missing required template variables:', {
          template: selectedTemplateData.name,
          missingVars: missingVars.map(v => ({
            name: v.name,
            description: v.description,
            currentValue: templateVariables[v.name]
          }))
        });

        return;
      }
    }

    // Build request data with template info
    const requestData = {
      ...inputData,
      regenerate,
      template_id: selectedTemplateId,
      template_variables: templateVariables
    };

    const result = await generate({
      endpoint,
      data: requestData,
      onSuccess: (generatedContent, fullResponse) => {
        // SIMPLIFIED: generatedContent is { sections: [...] } from backend
        console.log('✅ Received content from backend:', generatedContent);
        setContent(generatedContent);
        showToast('✅ Content generated successfully', 'success');

        if (onContentGenerated) {
          // Pass sections content and full response
          onContentGenerated(generatedContent, fullResponse);
        }
      },
      onError: (error) => {
        // Provide more user-friendly error messages
        let errorMessage = error;

        if (typeof error === 'string') {
          if (error.includes('timeout')) {
            errorMessage = '⏱️ Request timed out. Please try again.';
          } else if (error.includes('network')) {
            errorMessage = '🌐 Network error. Please check your connection.';
          } else if (error.includes('401') || error.includes('unauthorized')) {
            errorMessage = '🔒 Session expired. Please log in again.';
          } else if (error.includes('500')) {
            errorMessage = '⚠️ Server error. Please try again later.';
          } else {
            errorMessage = `❌ ${error}`;
          }
        }

        showToast(errorMessage, 'error', 6000);

        // Log detailed error for debugging
        console.error('❌ Content generation failed:', {
          endpoint,
          requestData,
          error
        });
      }
    });

    return result;
  };

  /**
   * Handle content edit
   */
  const handleContentChange = (newContent) => {
    setContent(newContent);
    
    if (onContentChange) {
      onContentChange(newContent);
    }
  };

  /**
   * Handle section update (for structured content)
   * SIMPLIFIED: Just update sections array and notify parent
   */
  const handleSectionUpdate = (index, newSectionContent) => {
    const updatedSections = [...sections];
    updatedSections[index].content = newSectionContent;
    setSections(updatedSections);

    // Update content with new sections
    const updatedContent = {
      sections: updatedSections
    };
    setContent(updatedContent);

    // Notify parent component
    if (onContentChange) {
      onContentChange(updatedContent);
    }
  };

  /**
   * Render section content with proper formatting for sub-headings
   * Handles markdown-style features like:
   * - ### Sub-headings
   * - **Bold text:**
   * - Numbered features (1), (2), etc.
   */
  const renderSectionContent = (content) => {
    if (!content) return null;

    // Split content by lines
    const lines = content.split('\n');
    const elements = [];
    let currentParagraph = [];

    lines.forEach((line, index) => {
      const trimmedLine = line.trim();

      // Check if line starts with ### (sub-heading)
      if (trimmedLine.startsWith('###')) {
        // Flush current paragraph
        if (currentParagraph.length > 0) {
          elements.push(
            <p key={`p-${index}`} className="mb-3 whitespace-pre-wrap">
              {currentParagraph.join('\n')}
            </p>
          );
          currentParagraph = [];
        }

        // Add sub-heading
        const heading = trimmedLine.replace(/^###\s*/, '').trim();
        elements.push(
          <h4 key={`h-${index}`} className="font-semibold text-gray-800 mt-3 mb-1">
            {heading}
          </h4>
        );
      }
      // Check if line starts with **Feature:** pattern
      else if (/^\*\*[^*]+:\*\*/.test(trimmedLine)) {
        // Flush current paragraph
        if (currentParagraph.length > 0) {
          elements.push(
            <p key={`p-${index}`} className="mb-3 whitespace-pre-wrap">
              {currentParagraph.join('\n')}
            </p>
          );
          currentParagraph = [];
        }

        // Parse the feature line
        const match = trimmedLine.match(/^\*\*([^*]+):\*\*\s*(.+)$/);
        if (match) {
          const [, featureName, description] = match;
          elements.push(
            <div key={`f-${index}`} className="mb-3">
              <span className="font-semibold text-gray-800">{featureName}:</span>
              <span className="text-gray-700"> {description}</span>
            </div>
          );
        } else {
          currentParagraph.push(line);
        }
      }
      // Regular line
      else if (trimmedLine) {
        currentParagraph.push(line);
      }
      // Empty line - flush paragraph
      else if (currentParagraph.length > 0) {
        elements.push(
          <p key={`p-${index}`} className="mb-3 whitespace-pre-wrap">
            {currentParagraph.join('\n')}
          </p>
        );
        currentParagraph = [];
      }
    });

    // Flush any remaining paragraph
    if (currentParagraph.length > 0) {
      elements.push(
        <p key={`p-final`} className="mb-3 whitespace-pre-wrap">
          {currentParagraph.join('\n')}
        </p>
      );
    }

    return <div>{elements}</div>;
  };

  return (
    <div className={`ai-content-generator ${className}`}>
      {/* Header with Label and Actions */}
      <div className="flex items-center justify-between mb-2">
        <label className="block text-sm font-medium text-gray-700">
          {label}
        </label>
        <div className="flex gap-2">
          {content && showEditMode && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsEditing(!isEditing)}
            >
              {isEditing ? '👁️ Preview' : '✏️ Edit'}
            </Button>
          )}
          <Button
            size="sm"
            variant="primary"
            onClick={() => handleGenerate(!!content)}
            loading={generating}
            disabled={generating}
          >
            {content ? '🔄 Regenerate' : '🤖 Generate'}
          </Button>
        </div>
      </div>

      {/* Prompt Template Selector */}
      {showPromptTemplates && (
        <div className="mb-4">
          <PromptTemplateSelector
            category={templateCategory}
            selectedTemplateId={selectedTemplateId}
            initialTemplateVariables={initialTemplateVariables}
            onTemplateSelect={(templateId, templateData, variables) => {
              setSelectedTemplateId(templateId);
              setSelectedTemplateData(templateData);
              setTemplateVariables(variables || {});

              // Notify parent component about template selection
              if (onTemplateSelect) {
                onTemplateSelect(templateId, templateData, variables);
              }
            }}
            showCustomPrompt={false}
            contextData={contextData}
          />
        </div>
      )}

      {/* Content Display/Edit Area */}
      {!content && !generating && (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-500">
          {placeholder}
        </div>
      )}

      {generating && (
        <div className="border border-gray-300 rounded-lg p-8 text-center">
          <div className="animate-spin text-4xl mb-2">⚙️</div>
          <p className="text-gray-600">Generating content...</p>
        </div>
      )}

      {content && !generating && (
        <div className="border border-gray-300 rounded-lg p-4">
          {/* SIMPLIFIED: Only section-based editing */}
          {showSections && sections.length > 0 ? (
            <div className="space-y-4">
              {sections.map((section, index) => (
                <div key={index} className="border-b border-gray-200 pb-4 last:border-0">
                  <h3 className="font-semibold text-gray-800 mb-2">{section.title}</h3>
                  {isEditing ? (
                    <textarea
                      className="w-full min-h-[100px] p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      value={section.content}
                      onChange={(e) => handleSectionUpdate(index, e.target.value)}
                    />
                  ) : (
                    <div className="text-gray-700">
                      {renderSectionContent(section.content)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center p-4">
              No sections available
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AIContentGenerator;

