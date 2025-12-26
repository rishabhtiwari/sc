import React, { useState, useEffect } from 'react';
import { Button } from '../';
import { useContentGeneration } from '../../../hooks/useContentGeneration';
import { useToast } from '../../../hooks/useToast';

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
 * Generic AI Content Generator Component
 * Can be used for product summaries, news articles, social posts, etc.
 *
 * @param {Object} props
 * @param {string} props.endpoint - API endpoint for content generation
 * @param {Object} props.inputData - Data to send to the endpoint
 * @param {string} props.initialContent - Initial content value
 * @param {Function} props.onContentGenerated - Callback when content is generated
 * @param {Function} props.onContentChange - Callback when content is edited
 * @param {string} props.label - Label for the content area
 * @param {string} props.placeholder - Placeholder text
 * @param {boolean} props.showEditMode - Show edit/preview toggle
 * @param {boolean} props.showSections - Parse and show content as sections
 * @param {Function} props.parseContent - Custom parser for content sections (uses default markdown parser if not provided)
 * @param {string} props.className - Additional CSS classes
 */
const AIContentGenerator = ({
  endpoint,
  inputData = {},
  initialContent = '',
  onContentGenerated,
  onContentChange,
  label = 'AI Generated Content',
  placeholder = 'Generated content will appear here...',
  showEditMode = true,
  showSections = false,
  parseContent = null,
  className = ''
}) => {
  const [content, setContent] = useState(initialContent);
  const [isEditing, setIsEditing] = useState(false);
  const [sections, setSections] = useState([]);
  const { generating, generate } = useContentGeneration();
  const { showToast } = useToast();

  // Update content when initialContent changes
  useEffect(() => {
    setContent(initialContent);
  }, [initialContent]);

  // Parse content into sections if needed
  useEffect(() => {
    if (showSections && content) {
      // Check if content is already structured (from backend)
      if (typeof content === 'object' && content.sections) {
        // Backend already parsed it - use the sections directly
        console.log('📊 Using structured sections from backend:', content.sections);
        setSections(content.sections);
      } else if (typeof content === 'string') {
        // Plain text - parse it
        const parser = parseContent || defaultParseContent;
        const parsed = parser(content);
        console.log('📝 Parsed sections from text:', parsed);
        setSections(parsed);
      }
    }
  }, [content, showSections, parseContent]);

  /**
   * Handle content generation
   */
  const handleGenerate = async (regenerate = false) => {
    const result = await generate({
      endpoint,
      data: {
        ...inputData,
        regenerate
      },
      onSuccess: (generatedContent) => {
        setContent(generatedContent);
        showToast('Content generated successfully', 'success');
        
        if (onContentGenerated) {
          onContentGenerated(generatedContent);
        }
      },
      onError: (error) => {
        showToast(error, 'error');
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
   */
  const handleSectionUpdate = (index, newSectionContent) => {
    const updatedSections = [...sections];
    updatedSections[index].content = newSectionContent;
    setSections(updatedSections);

    // Convert sections back to full content
    const newContent = updatedSections
      .map(section => `## ${section.title}\n${section.content}`)
      .join('\n\n');

    handleContentChange(newContent);
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
          {isEditing ? (
            <textarea
              className="w-full min-h-[300px] p-2 border-0 focus:outline-none focus:ring-0 resize-none"
              value={typeof content === 'string' ? content : content.full_text || ''}
              onChange={(e) => handleContentChange(e.target.value)}
            />
          ) : showSections && sections.length > 0 ? (
            // Structured section view
            <div className="space-y-4">
              {sections.map((section, index) => (
                <div key={index} className="border-b border-gray-200 pb-4 last:border-0">
                  <h3 className="font-semibold text-gray-800 mb-2">{section.title}</h3>
                  <div className="text-gray-700">
                    {renderSectionContent(section.content)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            // Plain text view
            <div className="prose max-w-none">
              <div className="whitespace-pre-wrap text-gray-700">
                {typeof content === 'string' ? content : content.full_text || ''}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AIContentGenerator;

