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
  const [videoUrl, setVideoUrl] = useState(formData.video_url || null);
  const { showToast } = useToast();

  const handleGenerate = async () => {
    if (!formData.product_id) {
      showToast('Product ID not found', 'error');
      return;
    }

    try {
      setGenerating(true);
      setVideoStatus('processing');

      console.log('🎬 Starting video generation for product:', formData.product_id);
      console.log('📋 Template ID:', formData.template_id);
      console.log('🔧 Template variables:', formData.template_variables);
      console.log('🎯 Distribution mode:', formData.distribution_mode);
      console.log('🗂️ Section mapping:', formData.section_mapping);

      const response = await productService.generateVideo(formData.product_id, {
        template_id: formData.template_id,
        template_variables: formData.template_variables || {},
        distribution_mode: formData.distribution_mode || 'auto',
        section_mapping: formData.section_mapping || {}
      });

      console.log('✅ Video generation response:', response.data);

      if (response.data.status === 'success') {
        showToast('Video generated successfully!', 'success');
        setVideoStatus('completed');

        // Get video URL from response
        const generatedVideoUrl = response.data.video_url;
        console.log('🎥 Video URL from response:', generatedVideoUrl);

        if (generatedVideoUrl) {
          // Convert relative URL to absolute if needed
          const fullUrl = generatedVideoUrl.startsWith('http')
            ? generatedVideoUrl
            : `http://localhost:8080${generatedVideoUrl}`;
          console.log('🌐 Full video URL:', fullUrl);
          setVideoUrl(fullUrl);
          onUpdate({ video_url: fullUrl });
        } else {
          console.warn('⚠️ No video URL in response');
        }
      } else {
        console.error('❌ Video generation failed:', response.data);
        showToast('Video generation failed', 'error');
        setVideoStatus('failed');
      }
    } catch (error) {
      console.error('❌ Error generating video:', error);
      console.error('Error details:', error.response?.data);
      showToast('Failed to generate video', 'error');
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

      {/* Video Preview */}
      <div className="bg-black rounded-lg aspect-video flex items-center justify-center overflow-hidden">
        {generating || videoStatus === 'processing' ? (
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-lg font-semibold">Generating video...</p>
            <p className="text-sm text-gray-300 mt-2">This may take 1-2 minutes</p>
          </div>
        ) : videoStatus === 'completed' && videoUrl ? (
          <video
            src={videoUrl}
            controls
            autoPlay
            className="w-full h-full"
            onLoadStart={() => console.log('🎥 Video loading started:', videoUrl)}
            onLoadedData={() => console.log('✅ Video loaded successfully')}
            onError={(e) => {
              console.error('❌ Video load error:', e);
              console.error('Video URL:', videoUrl);
              showToast('Failed to load video', 'error');
            }}
          >
            Your browser does not support the video tag.
          </video>
        ) : videoStatus === 'failed' ? (
          <div className="text-center text-white">
            <div className="text-6xl mb-4">❌</div>
            <p>Video generation failed</p>
            <p className="text-sm text-gray-300 mt-2">Check console for details</p>
          </div>
        ) : (
          <div className="text-center text-white">
            <div className="text-6xl mb-4">🎬</div>
            <p>Video preview will appear here</p>
            <p className="text-sm text-gray-300 mt-2">Click "Generate Video" to start</p>
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

