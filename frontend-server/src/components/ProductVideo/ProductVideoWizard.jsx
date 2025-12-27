import React, { useState, useRef } from 'react';
import { Button } from '../common';
import Step1_ProductDescription from './WizardSteps/Step1_ProductDescription';
import Step2_AISummaryGeneration from './WizardSteps/Step2_AISummaryGeneration';
import Step4_AudioSelection from './WizardSteps/Step4_AudioSelection';
import Step5_TemplateSelection from './WizardSteps/Step5_TemplateSelection';
import Step6_PreviewGenerate from './WizardSteps/Step6_PreviewGenerate';
import productService from '../../services/productService';

/**
 * Product Video Creation Wizard - Multi-step modal
 */
const ProductVideoWizard = ({ product, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const stepRefs = useRef({});

  console.log('🎬 ProductVideoWizard - Product data:', product);
  console.log('🎬 Product template_variables:', product?.template_variables);
  console.log('🎬 Product distribution_mode:', product?.distribution_mode);

  const [formData, setFormData] = useState({
    product_name: product?.product_name || '',
    description: product?.description || '',
    category: product?.category || 'General',
    price: product?.price || '',
    currency: product?.currency || 'USD',
    ai_summary: product?.ai_summary || '',
    prompt_template_id: product?.prompt_template_id || null,  // Prompt template used for AI summary
    prompt_template_variables: product?.prompt_template_variables || {},  // Variables used in prompt template
    media_files: [],  // Will be reconstructed from template_variables in Step5
    audio: product?.audio || null,
    audio_url: product?.audio_url || null,  // Include existing audio URL
    audio_config: product?.audio_config || null,  // Include existing audio config
    template_id: product?.template_id || null,  // Will be set when templates load in Step5
    template_variables: product?.template_variables || {},  // Template variables (contains media)
    distribution_mode: product?.distribution_mode || 'auto',  // Media distribution mode
    section_mapping: product?.section_mapping || {},  // Manual media-to-section mapping
    product_id: product?._id || null
  });

  console.log('🎬 Initial formData.template_variables:', formData.template_variables);

  const steps = [
    { id: 1, name: 'Description', icon: '📝', component: Step1_ProductDescription },
    { id: 2, name: 'Content Generation', icon: '🤖', component: Step2_AISummaryGeneration },
    { id: 3, name: 'Audio', icon: '🎵', component: Step4_AudioSelection },
    { id: 4, name: 'Template', icon: '🎨', component: Step5_TemplateSelection },
    { id: 5, name: 'Preview', icon: '👁️', component: Step6_PreviewGenerate }
  ];

  const handleNext = () => {
    // Call the current step's handleNext method if it exists
    const currentStepRef = stepRefs.current[currentStep];
    if (currentStepRef && currentStepRef.handleNext) {
      currentStepRef.handleNext();
    } else {
      // If step doesn't have handleNext (like Step6), just move to next step
      if (currentStep < steps.length) {
        setCurrentStep(currentStep + 1);
      }
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepComplete = (stepData) => {
    setFormData({ ...formData, ...stepData });
    // Move to next step
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleFinish = () => {
    if (onComplete) {
      onComplete(formData);
    }
    onClose();
  };

  const CurrentStepComponent = steps[currentStep - 1].component;
  const progress = (currentStep / steps.length) * 100;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">
              {product ? 'Edit Product Video' : 'Create Product Video'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ✕
            </button>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                Step {currentStep} of {steps.length}
              </span>
              <span className="text-sm text-gray-500">{Math.round(progress)}% Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>

          {/* Step Indicators */}
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={`flex flex-col items-center ${
                  index < currentStep - 1
                    ? 'text-green-600'
                    : index === currentStep - 1
                    ? 'text-indigo-600'
                    : 'text-gray-400'
                }`}
              >
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-xl mb-1 ${
                    index < currentStep - 1
                      ? 'bg-green-100'
                      : index === currentStep - 1
                      ? 'bg-indigo-100'
                      : 'bg-gray-100'
                  }`}
                >
                  {index < currentStep - 1 ? '✓' : step.icon}
                </div>
                <span className="text-xs font-medium hidden md:block">{step.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <CurrentStepComponent
            ref={(el) => (stepRefs.current[currentStep] = el)}
            formData={formData}
            onComplete={handleStepComplete}
          />
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 1}
          >
            ← Previous
          </Button>

          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            {currentStep === steps.length ? (
              <Button variant="primary" onClick={handleFinish}>
                🎬 Finish
              </Button>
            ) : (
              <Button variant="primary" onClick={handleNext}>
                Next →
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductVideoWizard;

