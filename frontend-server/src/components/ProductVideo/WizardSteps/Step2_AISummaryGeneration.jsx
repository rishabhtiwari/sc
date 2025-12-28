import React, { useState, useImperativeHandle, forwardRef } from 'react';
import { Button, AIContentGenerator } from '../../common';
import { useToast } from '../../../hooks/useToast';
import api from '../../../services/api';

/**
 * Step 2: Content Generation
 */
const Step2_AISummaryGeneration = forwardRef(({ formData, onComplete }, ref) => {
  const { showToast } = useToast();

  // Handle both old (string) and new (object) formats for initial state
  const getInitialSummary = () => {
    const aiSummaryData = formData.ai_summary;
    // Return the data as-is (can be JSON object or string)
    if (aiSummaryData) {
      return aiSummaryData;
    }
    return '';
  };

  // Use local state to store the summary until user clicks "Next"
  const [currentSummary, setCurrentSummary] = useState(getInitialSummary());

  // Store template info for saving
  const [selectedTemplateId, setSelectedTemplateId] = useState(formData.prompt_template_id || null);
  const [selectedTemplateVariables, setSelectedTemplateVariables] = useState(formData.prompt_template_variables || {});

  // Store the full response data (includes structured JSON content)
  const [generatedContentData, setGeneratedContentData] = useState(null);

  const handleContentGenerated = (content, fullResponseData) => {
    console.log('🎯 Step2 handleContentGenerated called with:', content);
    console.log('🎯 Full response data:', fullResponseData);

    // SIMPLIFIED: Content is { sections: [...] } from backend
    setCurrentSummary(content);
    setGeneratedContentData(fullResponseData);

    console.log('✅ Stored sections content:', content);
  };

  const handleTemplateSelect = (templateId, templateData, variables) => {
    console.log('🎯 Step2 handleTemplateSelect called:', { templateId, templateData, variables });

    // Store template info for saving later
    setSelectedTemplateId(templateId);
    setSelectedTemplateVariables(variables || {});
  };

  const handleContentChange = (content) => {
    console.log('🎯 Step2 handleContentChange called with:', content);

    // SIMPLIFIED: Content is { sections: [...] } after edits
    setCurrentSummary(content);

    console.log('✅ currentSummary state updated from edit (sections)');
  };

  // Expose handleNext to parent via ref
  useImperativeHandle(ref, () => ({
    handleNext
  }));

  const handleNext = async () => {
    // Use local state instead of formData
    const summary = currentSummary;

    console.log('🔍 Step2 handleNext - Validation:', {
      summary,
      summaryType: typeof summary,
      hasGeneratedData: !!generatedContentData
    });

    // SIMPLIFIED: Validate that summary has sections array
    if (!summary || !summary.sections || summary.sections.length === 0) {
      showToast('⚠️ Please generate content before proceeding', 'error', 5000);
      return false;
    }

    // Save AI summary to product and update status to 'summary_generated'
    if (formData.product_id) {
      try {
        console.log('💾 Saving AI summary to product:', formData.product_id);
        console.log('💾 AI summary data:', summary);

        // SIMPLIFIED: Save sections directly - no conversion needed
        // Also clear section_mapping if prompt template changed (to avoid outdated mappings)
        const updateData = {
          status: 'summary_generated',
          ai_summary: summary,  // { sections: [...] }
          prompt_template_id: selectedTemplateId,
          prompt_template_variables: selectedTemplateVariables
        };

        // Clear section_mapping if prompt template changed
        if (formData.prompt_template_id && formData.prompt_template_id !== selectedTemplateId) {
          console.log('🔄 Prompt template changed - clearing section_mapping');
          updateData.section_mapping = {};
          updateData.distribution_mode = 'auto';
        }

        await api.put(`/products/${formData.product_id}`, updateData);

        console.log('✅ AI summary saved successfully');
        showToast('✅ Content saved successfully', 'success');
      } catch (error) {
        console.error('❌ Error saving AI summary:', error);

        // Provide more specific error messages
        let errorMessage = 'Failed to save AI summary. Please try again.';

        if (error.response) {
          const status = error.response.status;
          const data = error.response.data;

          if (status === 401) {
            errorMessage = '🔒 Session expired. Please log in again.';
          } else if (status === 404) {
            errorMessage = '❌ Product not found. Please refresh and try again.';
          } else if (status === 500) {
            errorMessage = '⚠️ Server error. Please try again later.';
          } else if (data?.message) {
            errorMessage = `❌ ${data.message}`;
          }
        } else if (error.request) {
          errorMessage = '🌐 Network error. Please check your connection.';
        }

        showToast(errorMessage, 'error', 6000);
        return false;
      }
    }

    console.log('✅ Proceeding to next step with data:', {
      ai_summary: summary,
      prompt_template_id: selectedTemplateId,
      prompt_template_variables: selectedTemplateVariables
    });

    // Proceed to next step (Audio Configuration)
    onComplete({
      ai_summary: summary,
      prompt_template_id: selectedTemplateId,
      prompt_template_variables: selectedTemplateVariables
    });

    return true;
  };

  // Build context data for template variable auto-population
  const contextData = {
    product_name: formData.product_name || '',
    description: formData.description || '',
    category: formData.category || 'General',
    price_info: formData.price ? `$${formData.price} ${formData.currency || 'USD'}` : 'Premium quality',
    price: formData.price || '',
    currency: formData.currency || 'USD'
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">🤖 Content Generation</h3>
        <p className="text-gray-600">Generate compelling content for your product video using AI prompt templates</p>
      </div>

      {/* Original Description */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">Original Description:</h4>
        <p className="text-gray-700 text-sm">{formData.description}</p>
      </div>

      {/* AI Content Generator */}
      <AIContentGenerator
        endpoint="/content/generate"
        inputData={{}}
        initialContent={getInitialSummary()}
        initialTemplateId={selectedTemplateId}
        initialTemplateVariables={selectedTemplateVariables}
        onContentGenerated={handleContentGenerated}
        onContentChange={handleContentChange}
        onTemplateSelect={handleTemplateSelect}
        label="Generated Content"
        placeholder="Click 'Generate' to create content for your product"
        showEditMode={true}
        showSections={true}
        showPromptTemplates={true}
        templateCategory="product_summary"
        contextData={contextData}
      />

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">💡 Tips for Great Content:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Select a prompt template that matches your content needs</li>
          <li>• Aim for 300-450 words for a 2-3 minute video narration</li>
          <li>• Use conversational tone suitable for voiceover</li>
          <li>• Focus on what makes your product unique and valuable</li>
        </ul>
      </div>
    </div>
  );
});

Step2_AISummaryGeneration.displayName = 'Step2_AISummaryGeneration';

export default Step2_AISummaryGeneration;
