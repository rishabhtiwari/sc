import React, { useState, useEffect } from 'react';
import { Button } from '../../common';
import { productService } from '../../../services';
import { useToast } from '../../../hooks/useToast';

/**
 * Parse summary into sections for structured editing
 * Handles:
 * - Markdown headings (## Title)
 * - Bold feature points (**Feature Name:** Content) - grouped under parent section
 * - Numbered bold headings (**1. Title:** Content) - treated as sub-points
 */
const parseSummaryIntoSections = (text) => {
  if (!text) return [];

  const sections = [];
  const lines = text.split('\n');
  let currentSection = null;
  let inKeyFeaturesSection = false;

  lines.forEach((line) => {
    const trimmedLine = line.trim();

    // Check if it's a markdown heading (## Heading)
    if (trimmedLine.startsWith('## ')) {
      // Save previous section
      if (currentSection) {
        sections.push(currentSection);
      }

      // Start new section
      const headingText = trimmedLine.substring(3).trim();
      currentSection = {
        title: headingText,
        content: ''
      };

      // Track if we're in the Key Features & Benefits section
      inKeyFeaturesSection = headingText.toLowerCase().includes('key features') ||
                             headingText.toLowerCase().includes('features & benefits');
    }
    // Check if it's a bold feature point (**Feature Name:** Content)
    else if (trimmedLine.match(/^\*\*.+?:\*\*/)) {
      // If we're in Key Features section, add as sub-point
      if (inKeyFeaturesSection && currentSection) {
        // Extract feature name and content
        const match = trimmedLine.match(/^\*\*(.+?):\*\*\s*(.*)$/);
        if (match) {
          const featureName = match[1].replace(/^\d+\.\s*/, '').trim(); // Remove number if present
          const featureContent = match[2].trim();

          // Add as a formatted sub-point
          const featureText = `**${featureName}:** ${featureContent}`;
          currentSection.content += (currentSection.content ? '\n\n' : '') + featureText;
        }
      } else {
        // Not in Key Features section, treat as new section (backward compatibility)
        if (currentSection) {
          sections.push(currentSection);
        }

        const match = trimmedLine.match(/^\*\*(.+?):\*\*\s*(.*)$/);
        if (match) {
          const title = match[1].replace(/^\d+\.\s*/, '').trim();
          const content = match[2].trim();

          currentSection = {
            title: title,
            content: content
          };
          inKeyFeaturesSection = false;
        }
      }
    }
    else if (currentSection && trimmedLine) {
      // Add content to current section
      // Strip ### from the beginning if present (for sub-headings within content)
      const cleanedLine = trimmedLine.replace(/^###\s*/, '');
      currentSection.content += (currentSection.content ? '\n' : '') + cleanedLine;
    }
  });

  // Add last section
  if (currentSection) {
    sections.push(currentSection);
  }

  return sections;
};

/**
 * Convert sections back to markdown format
 */
const sectionsToMarkdown = (sections) => {
  return sections
    .map(section => `## ${section.title}\n${section.content}`)
    .join('\n\n');
};

/**
 * Render markdown content with formatting
 * Converts:
 * - **text** to <strong>text</strong>
 * - ### Heading to <h4>Heading</h4>
 */
const renderMarkdownContent = (content) => {
  if (!content) return null;

  // Split content by lines to handle headings
  const lines = content.split('\n');

  return lines.map((line, lineIndex) => {
    // Skip empty lines
    if (!line.trim()) {
      return <br key={lineIndex} />;
    }

    // Check if line is a heading (### Heading)
    if (line.trim().startsWith('###')) {
      const headingText = line.trim().substring(3).trim();
      return (
        <h4 key={lineIndex} className="font-bold text-gray-900 text-base mt-3 mb-2">
          {headingText}
        </h4>
      );
    }

    // Check if line has **HEADING:** format (feature heading with description)
    const featureMatchBold = line.match(/^\*\*([^*:]+):\*\*\s*(.*)$/);
    if (featureMatchBold) {
      const heading = featureMatchBold[1].trim();
      const description = featureMatchBold[2].trim();
      return (
        <div key={lineIndex} className="mb-3">
          <strong className="font-bold text-gray-900">{heading}:</strong>
          <span className="text-gray-600 ml-1">{description}</span>
        </div>
      );
    }

    // Check if line has HEADING: format (ALL CAPS heading without ** markers)
    // Match lines that are ALL CAPS followed by colon
    const featureMatchPlain = line.match(/^([A-Z][A-Z\s&-]+):\s*(.*)$/);
    if (featureMatchPlain) {
      const heading = featureMatchPlain[1].trim();
      const description = featureMatchPlain[2].trim();

      // Only treat as heading if it's mostly uppercase (at least 70% uppercase letters)
      const uppercaseRatio = (heading.match(/[A-Z]/g) || []).length / heading.replace(/[^A-Za-z]/g, '').length;

      if (uppercaseRatio > 0.7) {
        return (
          <div key={lineIndex} className="mb-3">
            <strong className="font-bold text-gray-900">{heading}:</strong>
            {description && <span className="text-gray-600 ml-1">{description}</span>}
          </div>
        );
      }
    }

    // Process bold markers in regular text (for inline bold)
    const parts = line.split(/(\*\*[^*]+\*\*)/g);

    const renderedParts = parts.map((part, index) => {
      // Check if this part is bold text
      if (part.startsWith('**') && part.endsWith('**')) {
        const boldText = part.slice(2, -2); // Remove ** from both ends
        return <strong key={index} className="font-bold text-gray-900">{boldText}</strong>;
      }
      // Regular text
      return <span key={index} className="text-gray-600">{part}</span>;
    });

    // Return line with line break
    return (
      <div key={lineIndex} className="mb-2">
        {renderedParts}
      </div>
    );
  });
};

/**
 * Step 2: AI Summary Generation
 */
const Step2_AISummaryGeneration = ({ formData, onComplete, onUpdate }) => {
  // Handle both old (string) and new (object) formats for initial state
  const getInitialSummary = () => {
    const aiSummaryData = formData.ai_summary;
    if (typeof aiSummaryData === 'object' && aiSummaryData?.full_text) {
      return aiSummaryData.full_text;
    } else if (typeof aiSummaryData === 'string') {
      return aiSummaryData;
    }
    return '';
  };

  const [aiSummary, setAiSummary] = useState(getInitialSummary());
  const [sections, setSections] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const { showToast } = useToast();

  // Parse summary into sections when it changes
  useEffect(() => {
    if (aiSummary) {
      const parsed = parseSummaryIntoSections(aiSummary);
      setSections(parsed);
    }
  }, [aiSummary]);

  const handleGenerate = async (regenerate = false) => {
    if (!formData.product_id) {
      showToast('Product ID not found', 'error');
      return;
    }

    try {
      setGenerating(true);
      const response = await productService.generateSummary(formData.product_id, { regenerate });

      if (response.data.status === 'success') {
        const aiSummaryData = response.data.ai_summary || '';

        // Handle both old (string) and new (object) formats
        let summaryText = '';
        if (typeof aiSummaryData === 'object' && aiSummaryData.full_text) {
          // New structured format
          summaryText = aiSummaryData.full_text;
        } else if (typeof aiSummaryData === 'string') {
          // Old plain text format
          summaryText = aiSummaryData;
        }

        setAiSummary(summaryText);
        // Update parent formData immediately
        onUpdate({ ai_summary: aiSummaryData });
        showToast('AI summary generated successfully', 'success');
      } else {
        showToast(response.data.message || 'Failed to generate AI summary', 'error');
      }
    } catch (error) {
      console.error('Error generating summary:', error);
      const errorMsg = error.response?.data?.message || error.message || 'Failed to generate AI summary';
      showToast(errorMsg, 'error');
    } finally {
      setGenerating(false);
    }
  };

  const handleNext = () => {
    if (!aiSummary.trim()) {
      showToast('Please generate or enter an AI summary', 'error');
      return;
    }

    onComplete({ ai_summary: aiSummary });
  };

  const handleSectionUpdate = (index, newContent) => {
    const updatedSections = [...sections];
    updatedSections[index].content = newContent;
    setSections(updatedSections);

    // Update the full summary
    const newSummary = sectionsToMarkdown(updatedSections);
    setAiSummary(newSummary);
    onUpdate({ ai_summary: newSummary });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">🤖 AI Summary Generation</h3>
        <p className="text-gray-600">Generate a compelling summary for your product video</p>
      </div>

      {/* Original Description */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">Original Description:</h4>
        <p className="text-gray-700 text-sm">{formData.description}</p>
      </div>

      {/* AI Summary */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">
            AI Generated Summary
          </label>
          <div className="flex gap-2">
            {aiSummary && (
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
              onClick={() => handleGenerate(!!aiSummary)}
              loading={generating}
              disabled={generating}
            >
              {aiSummary ? '🔄 Regenerate' : '🤖 Generate'}
            </Button>
          </div>
        </div>

        {generating ? (
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6 min-h-[200px]">
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              <span className="ml-3 text-indigo-600">Generating AI summary...</span>
            </div>
          </div>
        ) : aiSummary ? (
          <div className="bg-white border-2 border-indigo-200 rounded-lg overflow-hidden">
            {/* Container Header */}
            <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 px-6 py-4">
              <h3 className="text-white font-semibold text-xl">AI Generated Summary</h3>
            </div>

            {/* All Sections Inside Container */}
            <div className="p-6 space-y-6">
              {sections.map((section, index) => (
                <div key={index} className="border-b border-gray-200 last:border-b-0 pb-6 last:pb-0">
                  {/* Section Title */}
                  <h4 className="text-indigo-700 font-semibold text-lg mb-3 flex items-center gap-2">
                    <span className="bg-indigo-600 text-white rounded-full w-7 h-7 flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </span>
                    {section.title}
                  </h4>

                  {/* Section Content */}
                  <div className="ml-9">
                    {isEditing ? (
                      <textarea
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-800 leading-relaxed"
                        rows="4"
                        value={section.content}
                        onChange={(e) => handleSectionUpdate(index, e.target.value)}
                        placeholder={`Enter content for ${section.title}...`}
                      />
                    ) : (
                      <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                        {renderMarkdownContent(section.content)}
                      </div>
                    )}

                    {/* Word count for this section */}
                    <div className="mt-2 text-xs text-gray-500">
                      {section.content.split(/\s+/).filter(word => word.length > 0).length} words
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6 min-h-[200px]">
            <p className="text-gray-500 italic">Click "Generate" to create an AI summary</p>
          </div>
        )}

        <p className="mt-2 text-sm text-gray-500">
          {aiSummary.split(/\s+/).filter(word => word.length > 0).length} words / {aiSummary.length} characters
          {aiSummary.split(/\s+/).filter(word => word.length > 0).length > 450 && ' (⚠️ Recommended: max 450 words for 2-3 min video)'}
        </p>
      </div>

      {/* Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">💡 Tips for a Great Summary:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Aim for 300-450 words for a 2-3 minute video narration</li>
          <li>• Summary will have 5 sections: Opening Hook, Product Introduction, Key Features & Benefits, Social Proof & Trust, Call-to-Action</li>
          <li>• Use conversational tone suitable for voiceover</li>
          <li>• Focus on what makes your product unique</li>
        </ul>
      </div>

      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleNext}
          disabled={!aiSummary.trim()}
        >
          Next: Configure Audio →
        </Button>
      </div>
    </div>
  );
};

export default Step2_AISummaryGeneration;
