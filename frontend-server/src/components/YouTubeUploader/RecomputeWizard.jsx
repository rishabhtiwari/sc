import React, { useState } from 'react';
import { Button } from '../common';
import NewsSelector from './NewsSelector';

/**
 * Recompute Wizard Component - Wizard for recomputing long videos with manual selection option
 */
const RecomputeWizard = ({ config, onConfirm, onCancel, loading }) => {
  const [step, setStep] = useState(1); // 1: Choose mode, 2: Select articles (if manual)
  const [mode, setMode] = useState(null); // 'auto' or 'manual'
  const [selectedArticleIds, setSelectedArticleIds] = useState([]);

  const handleModeSelect = (selectedMode) => {
    setMode(selectedMode);
    
    if (selectedMode === 'auto') {
      // Auto mode: skip to confirmation
      setStep(3);
    } else {
      // Manual mode: go to article selection
      setStep(2);
    }
  };

  const handleArticleSelection = (articleIds) => {
    setSelectedArticleIds(articleIds);
  };

  const handleNext = () => {
    if (step === 2) {
      // From article selection to confirmation
      setStep(3);
    }
  };

  const handleBack = () => {
    if (step === 3) {
      setStep(mode === 'manual' ? 2 : 1);
    } else if (step === 2) {
      setStep(1);
      setMode(null);
    }
  };

  const handleConfirm = () => {
    if (mode === 'auto') {
      // Auto mode: no article_ids
      onConfirm(null);
    } else {
      // Manual mode: pass selected article_ids
      onConfirm(selectedArticleIds);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Recompute Video</h2>
              <p className="text-sm text-gray-600 mt-1">{config.title}</p>
            </div>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600 text-2xl"
              disabled={loading}
            >
              ×
            </button>
          </div>

          {/* Progress Steps */}
          <div className="mt-6 flex items-center justify-center">
            <div className="flex items-center space-x-4">
              {/* Step 1 */}
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}>
                  1
                </div>
                <span className="ml-2 text-sm font-medium text-gray-700">Choose Mode</span>
              </div>

              {/* Connector */}
              <div className={`w-12 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>

              {/* Step 2 */}
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}>
                  2
                </div>
                <span className="ml-2 text-sm font-medium text-gray-700">
                  {mode === 'manual' ? 'Select Articles' : 'Review'}
                </span>
              </div>

              {/* Connector */}
              <div className={`w-12 h-1 ${step >= 3 ? 'bg-blue-600' : 'bg-gray-200'}`}></div>

              {/* Step 3 */}
              <div className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}>
                  3
                </div>
                <span className="ml-2 text-sm font-medium text-gray-700">Confirm</span>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step 1: Choose Mode */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                How would you like to select videos?
              </h3>

              {/* Auto Mode Card */}
              <button
                onClick={() => handleModeSelect('auto')}
                className="w-full text-left p-6 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
              >
                <div className="flex items-start gap-4">
                  <div className="text-4xl">🤖</div>
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-gray-900 group-hover:text-blue-700">
                      Automatic Selection
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Use the configuration filters to automatically select the latest {config.videoCount} news articles
                    </p>
                    <div className="mt-3 text-xs text-gray-500">
                      <div>• Country: {config.country?.toUpperCase() || 'Any'}</div>
                      <div>• Language: {config.language?.toUpperCase() || 'Any'}</div>
                      <div>• Categories: {config.categories?.length > 0 ? config.categories.join(', ') : 'All'}</div>
                    </div>
                  </div>
                  <div className="text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
                    →
                  </div>
                </div>
              </button>

              {/* Manual Mode Card */}
              <button
                onClick={() => handleModeSelect('manual')}
                className="w-full text-left p-6 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
              >
                <div className="flex items-start gap-4">
                  <div className="text-4xl">🎯</div>
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-gray-900 group-hover:text-blue-700">
                      Manual Selection
                    </h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Manually select and order specific news articles for this video
                    </p>
                    <div className="mt-3 text-xs text-gray-500">
                      <div>• Choose specific articles</div>
                      <div>• Drag and drop to reorder</div>
                      <div>• Full control over content</div>
                    </div>
                  </div>
                  <div className="text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
                    →
                  </div>
                </div>
              </button>
            </div>
          )}

          {/* Step 2: Manual Article Selection */}
          {step === 2 && mode === 'manual' && (
            <div>
              <NewsSelector
                config={config}
                onSelectionChange={handleArticleSelection}
                onClose={() => {}}
                embedded={true}
              />
            </div>
          )}

          {/* Step 3: Confirmation */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Confirm Recompute
              </h3>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">Configuration Summary</h4>
                <div className="space-y-2 text-sm text-blue-800">
                  <div><span className="font-medium">Title:</span> {config.title}</div>
                  <div><span className="font-medium">Mode:</span> {mode === 'auto' ? '🤖 Automatic Selection' : '🎯 Manual Selection'}</div>
                  {mode === 'auto' && (
                    <>
                      <div><span className="font-medium">Video Count:</span> {config.videoCount}</div>
                      <div><span className="font-medium">Country:</span> {config.country?.toUpperCase() || 'Any'}</div>
                      <div><span className="font-medium">Language:</span> {config.language?.toUpperCase() || 'Any'}</div>
                      <div><span className="font-medium">Categories:</span> {config.categories?.length > 0 ? config.categories.join(', ') : 'All'}</div>
                    </>
                  )}
                  {mode === 'manual' && (
                    <div><span className="font-medium">Selected Articles:</span> {selectedArticleIds.length}</div>
                  )}
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <span className="text-yellow-600 text-xl">⚠️</span>
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium">This will recompute the video</p>
                    <p className="mt-1">The existing video will be replaced with a new one based on your selection.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex gap-3">
            {step > 1 && step < 3 && (
              <Button
                variant="secondary"
                onClick={handleBack}
                disabled={loading}
              >
                ← Back
              </Button>
            )}
            
            <Button
              variant="secondary"
              onClick={onCancel}
              disabled={loading}
              className={step === 1 ? 'flex-1' : ''}
            >
              Cancel
            </Button>

            {step === 2 && mode === 'manual' && (
              <Button
                variant="primary"
                onClick={handleNext}
                disabled={selectedArticleIds.length === 0}
                className="flex-1"
              >
                Next: Review → ({selectedArticleIds.length} selected)
              </Button>
            )}

            {step === 3 && (
              <Button
                variant="danger"
                onClick={handleConfirm}
                loading={loading}
                disabled={loading || (mode === 'manual' && selectedArticleIds.length === 0)}
                className="flex-1"
              >
                {loading ? 'Processing...' : '✓ Confirm & Recompute'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecomputeWizard;

