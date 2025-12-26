import React, { useState } from 'react';
import {
  AIContentGenerator,
  AudioSelector,
  TemplateSelector,
  MediaUploader,
  Button,
  Card
} from '@/components/common';

/**
 * Example: Product Video Creation using Reusable Components
 * 
 * This shows how to use the generic content generation components
 * to build a product video creation workflow
 */
const ProductVideoExample = ({ product, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    product_id: product?._id,
    product_name: product?.name || '',
    description: product?.description || '',
    ai_summary: product?.ai_summary || '',
    audio_url: product?.audio_url || null,
    audio_config: product?.audio_config || {},
    template_id: product?.template_id || null,
    template_variables: product?.template_variables || {},
    media_files: product?.media_files || []
  });

  const updateFormData = (updates) => {
    setFormData(prev => ({ ...prev, ...updates }));
  };

  const handleNext = () => {
    setCurrentStep(prev => prev + 1);
  };

  const handleBack = () => {
    setCurrentStep(prev => prev - 1);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8">
        {['Summary', 'Audio', 'Template', 'Media', 'Generate'].map((step, index) => (
          <div
            key={step}
            className={`flex items-center ${
              index + 1 === currentStep
                ? 'text-indigo-600 font-semibold'
                : index + 1 < currentStep
                ? 'text-green-600'
                : 'text-gray-400'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center ${
                index + 1 === currentStep
                  ? 'bg-indigo-600 text-white'
                  : index + 1 < currentStep
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-300 text-gray-600'
              }`}
            >
              {index + 1 < currentStep ? '✓' : index + 1}
            </div>
            <span className="ml-2">{step}</span>
          </div>
        ))}
      </div>

      {/* Step 1: AI Summary Generation */}
      {currentStep === 1 && (
        <Card title="Generate Product Summary">
          <AIContentGenerator
            endpoint={`/api/products/${formData.product_id}/generate-summary`}
            inputData={{ regenerate: !!formData.ai_summary }}
            initialContent={formData.ai_summary}
            onContentGenerated={(content) => {
              updateFormData({ ai_summary: content });
            }}
            label="AI Generated Product Summary"
            placeholder="Click 'Generate' to create an AI summary of your product"
            showEditMode={true}
            showSections={false}
          />

          <div className="flex justify-end mt-6">
            <Button
              variant="primary"
              onClick={handleNext}
              disabled={!formData.ai_summary}
            >
              Next: Audio →
            </Button>
          </div>
        </Card>
      )}

      {/* Step 2: Audio Generation */}
      {currentStep === 2 && (
        <Card title="Generate Audio">
          <AudioSelector
            endpoint={`/api/products/${formData.product_id}/generate-audio`}
            text={formData.ai_summary}
            initialAudioUrl={formData.audio_url}
            initialConfig={formData.audio_config}
            onAudioGenerated={(url, config) => {
              updateFormData({
                audio_url: url,
                audio_config: config
              });
            }}
            autoDetectLanguage={true}
          />

          <div className="flex justify-between mt-6">
            <Button variant="outline" onClick={handleBack}>
              ← Back
            </Button>
            <Button
              variant="primary"
              onClick={handleNext}
              disabled={!formData.audio_url}
            >
              Next: Template →
            </Button>
          </div>
        </Card>
      )}

      {/* Step 3: Template Selection */}
      {currentStep === 3 && (
        <Card title="Select Template">
          <TemplateSelector
            initialTemplateId={formData.template_id}
            initialVariables={formData.template_variables}
            onTemplateSelected={(templateId, template) => {
              updateFormData({ template_id: templateId });
            }}
            onVariablesChange={(variables) => {
              updateFormData({ template_variables: variables });
            }}
            showVariables={true}
            showPreview={true}
            filterCategory="ecommerce"
          />

          <div className="flex justify-between mt-6">
            <Button variant="outline" onClick={handleBack}>
              ← Back
            </Button>
            <Button
              variant="primary"
              onClick={handleNext}
              disabled={!formData.template_id}
            >
              Next: Media →
            </Button>
          </div>
        </Card>
      )}

      {/* Step 4: Media Upload */}
      {currentStep === 4 && (
        <Card title="Upload Media">
          <MediaUploader
            initialFiles={formData.media_files}
            onFilesChange={(files) => {
              updateFormData({ media_files: files });
            }}
            uploadEndpoint="/api/upload"
            acceptedTypes={['image', 'video']}
            maxFiles={10}
            maxFileSize={100}
            showPreview={true}
          />

          <div className="flex justify-between mt-6">
            <Button variant="outline" onClick={handleBack}>
              ← Back
            </Button>
            <Button
              variant="primary"
              onClick={handleNext}
              disabled={formData.media_files.length === 0}
            >
              Next: Generate →
            </Button>
          </div>
        </Card>
      )}

      {/* Step 5: Generate Video */}
      {currentStep === 5 && (
        <Card title="Generate Video">
          <div className="text-center py-8">
            <h3 className="text-xl font-semibold mb-4">Ready to Generate!</h3>
            <p className="text-gray-600 mb-6">
              Review your settings and click generate to create your product video
            </p>

            <div className="bg-gray-50 rounded-lg p-6 mb-6 text-left">
              <h4 className="font-semibold mb-2">Summary:</h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li>✓ AI Summary: {formData.ai_summary ? 'Generated' : 'Not generated'}</li>
                <li>✓ Audio: {formData.audio_url ? 'Generated' : 'Not generated'}</li>
                <li>✓ Template: {formData.template_id ? 'Selected' : 'Not selected'}</li>
                <li>✓ Media Files: {formData.media_files.length} uploaded</li>
              </ul>
            </div>

            <div className="flex justify-center gap-4">
              <Button variant="outline" onClick={handleBack}>
                ← Back
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  // Call video generation API
                  onComplete(formData);
                }}
              >
                🎬 Generate Video
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ProductVideoExample;

