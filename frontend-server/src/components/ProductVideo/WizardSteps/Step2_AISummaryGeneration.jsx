import React from 'react';
import { Button, AIContentGenerator } from '../../common';
import { useToast } from '../../../hooks/useToast';

/**
 * Step 2: AI Summary Generation
 */
const Step2_AISummaryGeneration = ({ formData, onComplete, onUpdate }) => {
  const { showToast } = useToast();

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

  const handleContentGenerated = (content) => {
    // Update parent formData when content is generated
    onUpdate({ ai_summary: content });
  };

  const handleContentChange = (content) => {
    // Update parent formData when content is edited
    onUpdate({ ai_summary: content });
  };

  const handleNext = () => {
    const summary = getInitialSummary();
    if (!summary || !summary.trim()) {
      showToast('Please generate or enter an AI summary', 'error');
      return;
    }

    onComplete({ ai_summary: summary });
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

      {/* AI Content Generator */}
      <AIContentGenerator
        endpoint={`/products/${formData.product_id}/generate-summary`}
        inputData={{}}
        initialContent={getInitialSummary()}
        onContentGenerated={handleContentGenerated}
        onContentChange={handleContentChange}
        label="AI Generated Summary"
        placeholder="Click 'Generate' to create an AI summary"
        showEditMode={true}
        showSections={true}
      />

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
          disabled={!getInitialSummary().trim()}
        >
          Next: Configure Audio →
        </Button>
      </div>
    </div>
  );
};

export default Step2_AISummaryGeneration;
