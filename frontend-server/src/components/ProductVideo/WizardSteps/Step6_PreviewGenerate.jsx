import React, { useState } from 'react';
import { Button } from '../../common';
import { productService } from '../../../services';
import { useToast } from '../../../hooks/useToast';

/**
 * Step 6: Preview & Generate
 */
const Step6_PreviewGenerate = ({ formData, onComplete, onUpdate }) => {
  const [generating, setGenerating] = useState(false);
  const [videoStatus, setVideoStatus] = useState(formData.generated_video?.status || 'pending');
  const { showToast } = useToast();

  const handleGenerate = async () => {
    if (!formData.product_id) {
      showToast('Product ID not found', 'error');
      return;
    }

    try {
      setGenerating(true);
      setVideoStatus('processing');

      const response = await productService.generateVideo(formData.product_id, {
        template_id: formData.template_id
      });

      if (response.data.status === 'success') {
        showToast('Video generation started successfully', 'success');
        setVideoStatus('processing');
      }
    } catch (error) {
      console.error('Error generating video:', error);
      showToast('Failed to start video generation', 'error');
      setVideoStatus('failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">👁️ Preview & Generate</h3>
        <p className="text-gray-600">Review your settings and generate the final video</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Product Info */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
            <span className="text-xl mr-2">📦</span>
            Product Information
          </h4>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-600">Name:</span>
              <span className="ml-2 font-medium">{formData.product_name}</span>
            </div>
            <div>
              <span className="text-gray-600">Category:</span>
              <span className="ml-2 font-medium">{formData.category}</span>
            </div>
            {formData.price && (
              <div>
                <span className="text-gray-600">Price:</span>
                <span className="ml-2 font-medium">
                  {formData.currency} {formData.price}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* AI Summary */}
        <div className="bg-indigo-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
            <span className="text-xl mr-2">🤖</span>
            AI Summary
          </h4>
          <p className="text-sm text-gray-700 italic">"{formData.ai_summary}"</p>
        </div>

        {/* Media Files */}
        <div className="bg-green-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
            <span className="text-xl mr-2">🖼️</span>
            Media Files
          </h4>
          <p className="text-sm text-gray-700">
            {formData.media_files?.length || 0} file(s) uploaded
          </p>
          <div className="flex gap-2 mt-2">
            {formData.media_files?.slice(0, 3).map((file, index) => (
              <div key={index} className="w-12 h-12 bg-gray-200 rounded"></div>
            ))}
            {formData.media_files?.length > 3 && (
              <div className="w-12 h-12 bg-gray-200 rounded flex items-center justify-center text-xs">
                +{formData.media_files.length - 3}
              </div>
            )}
          </div>
        </div>

        {/* Template */}
        <div className="bg-purple-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
            <span className="text-xl mr-2">🎨</span>
            Template
          </h4>
          <p className="text-sm text-gray-700 font-medium">{formData.template_id}</p>
          <p className="text-xs text-gray-600 mt-1">Professional video template</p>
        </div>
      </div>

      {/* Video Preview Placeholder */}
      <div className="bg-black rounded-lg aspect-video flex items-center justify-center">
        {videoStatus === 'processing' ? (
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p>Generating video...</p>
          </div>
        ) : videoStatus === 'completed' ? (
          <div className="text-center text-white">
            <div className="text-6xl mb-4">✅</div>
            <p>Video generated successfully!</p>
          </div>
        ) : (
          <div className="text-center text-white">
            <div className="text-6xl mb-4">🎬</div>
            <p>Video preview will appear here</p>
          </div>
        )}
      </div>

      {/* Generation Info */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h4 className="font-medium text-yellow-900 mb-2">⚡ Video Generation:</h4>
        <ul className="text-sm text-yellow-800 space-y-1">
          <li>• Video generation typically takes 2-5 minutes</li>
          <li>• You'll receive a notification when it's ready</li>
          <li>• You can close this wizard and check back later</li>
          <li>• The video will be available in your products list</li>
        </ul>
      </div>

      {/* Generate Button */}
      <div className="flex justify-center">
        <Button
          variant="primary"
          size="lg"
          onClick={handleGenerate}
          loading={generating}
          disabled={generating || videoStatus === 'processing'}
          className="px-8"
        >
          {videoStatus === 'processing'
            ? '⏳ Generating...'
            : videoStatus === 'completed'
            ? '✅ Video Generated'
            : '🎬 Generate Video'}
        </Button>
      </div>
    </div>
  );
};

export default Step6_PreviewGenerate;

