import React, { useState, useEffect } from 'react';
import { Card } from '../components/common';
import { useToast } from '../hooks/useToast';
import { imageService } from '../services';
import StatsDisplay from '../components/ImageCleaning/StatsDisplay';
import ImageCanvas from '../components/ImageCleaning/ImageCanvas';
import ControlPanel from '../components/ImageCleaning/ControlPanel';
import AuthenticatedImage from '../components/common/AuthenticatedImage';

/**
 * Image Cleaning Page - Remove watermarks from news images
 */
const ImageCleaningPage = () => {
  const [stats, setStats] = useState({ total: 0, cleaned: 0, skipped: 0, pending: 0 });
  const [statsLoading, setStatsLoading] = useState(false);
  const [currentImage, setCurrentImage] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [brushSize, setBrushSize] = useState(30);
  const [hasMask, setHasMask] = useState(false);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [clearMaskTrigger, setClearMaskTrigger] = useState(0);
  const [autoDetectTrigger, setAutoDetectTrigger] = useState(0);

  // Image config state
  const [imageConfig, setImageConfig] = useState({ auto_mark_cleaned: false });
  const [configLoading, setConfigLoading] = useState(false);

  const { showToast } = useToast();

  // Load image configuration
  const loadImageConfig = async () => {
    setConfigLoading(true);
    try {
      const response = await imageService.getImageConfig();
      const data = response.data?.data || response.data;
      setImageConfig({
        auto_mark_cleaned: data.auto_mark_cleaned || false,
      });
    } catch (error) {
      console.error('Failed to load image config:', error);
      showToast('Failed to load image settings', 'error');
    } finally {
      setConfigLoading(false);
    }
  };

  // Toggle auto-mark cleaned setting
  const toggleAutoMarkCleaned = async () => {
    const newValue = !imageConfig.auto_mark_cleaned;

    try {
      setConfigLoading(true);
      await imageService.updateImageConfig({ auto_mark_cleaned: newValue });
      setImageConfig({ auto_mark_cleaned: newValue });
      showToast(
        newValue
          ? 'Auto-mark enabled: Images will be marked as cleaned automatically'
          : 'Auto-mark disabled: Manual watermark removal required',
        'success'
      );
      // Reload stats as this might affect pending count
      loadStats();
    } catch (error) {
      console.error('Failed to update image config:', error);
      showToast('Failed to update settings', 'error');
    } finally {
      setConfigLoading(false);
    }
  };

  // Load statistics
  const loadStats = async () => {
    setStatsLoading(true);
    try {
      const response = await imageService.getStats();
      const data = response.data?.data || response.data;
      setStats({
        total: data.total || 0,
        cleaned: data.cleaned || 0,
        skipped: data.skipped || 0,
        pending: data.pending || 0,
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
      showToast('Failed to load statistics', 'error');
    } finally {
      setStatsLoading(false);
    }
  };

  // Load next image
  const loadNextImage = async () => {
    setLoading(true);
    try {
      const response = await imageService.getNextImage();
      const data = response.data?.data || response.data;

      if (!data || !data.doc_id) {
        showToast('No more images to process!', 'info');
        setCurrentImage(null);
        setImageData(null);
        return;
      }

      setCurrentImage({
        id: data.doc_id,
        title: data.title || 'Untitled',
        source: data.source?.name || 'Unknown',
        url: data.image_url,
        originalUrl: data.original_image_url,
      });

      // Just set the image URL - no need to convert to base64 yet
      // The ImageCanvas component will handle loading
      if (data.image_url) {
        console.log('Setting image URL:', data.image_url);
        setImageData(data.image_url);
        setHasMask(false);
        showToast('Image loaded successfully', 'success');
      } else {
        showToast('No image URL provided', 'warning');
      }
    } catch (error) {
      console.error('Failed to load next image:', error);
      showToast(error.response?.data?.error || 'Failed to load next image', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Auto-detect watermark
  const handleAutoDetect = () => {
    setAutoDetectTrigger(prev => prev + 1);
    showToast('Auto-detected common watermark areas', 'info');
  };

  // Clear mask
  const handleClearMask = () => {
    setClearMaskTrigger(prev => prev + 1);
    setHasMask(false);
    showToast('Mask cleared', 'info');
  };

  // Process image (remove watermark)
  const handleProcess = async () => {
    if (!currentImage || !hasMask) {
      showToast('Please draw a mask first', 'warning');
      return;
    }

    setProcessing(true);
    try {
      console.log('[Process] Getting canvas data...');
      // Get canvas data from ImageCanvas component
      const canvasData = window.getImageCanvasData?.();
      console.log('[Process] Canvas data:', canvasData ? 'present' : 'null');
      console.log('[Process] Image data length:', canvasData?.imageData?.length);
      console.log('[Process] Mask data length:', canvasData?.maskData?.length);

      if (!canvasData) {
        throw new Error('Failed to get canvas data');
      }

      console.log('[Process] Sending process request for doc_id:', currentImage.id);
      console.log('[Process] Using image URL:', currentImage.url);

      // Send image_url instead of image_data to avoid transferring large base64 data
      const response = await imageService.processImage({
        doc_id: currentImage.id,
        image_url: currentImage.url,  // Use URL instead of base64 data
        mask_data: canvasData.maskData,
      });

      console.log('[Process] Response received:', response.data);
      const data = response.data?.data || response.data;
      console.log('[Process] Processed data:', data);

      // Backend returns 'result_image', not 'processed_image'
      const resultImage = data.result_image || data.processed_image;
      console.log('[Process] Has result_image:', !!resultImage);
      console.log('[Process] Result image length:', resultImage?.length);

      // Update image with processed result
      if (resultImage) {
        const newImageData = `data:image/png;base64,${resultImage}`;
        console.log('[Process] Setting new image data, length:', newImageData.length);
        setImageData(newImageData);
        setHasMask(false);
        setClearMaskTrigger(prev => prev + 1);
        showToast('Watermark removed successfully!', 'success');
      } else {
        console.error('[Process] No result_image in response');
        showToast('No processed image returned', 'error');
      }
    } catch (error) {
      console.error('[Process] Failed to process image:', error);
      console.error('[Process] Error response:', error.response?.data);
      showToast(error.response?.data?.error || 'Failed to remove watermark', 'error');
    } finally {
      setProcessing(false);
    }
  };

  // Save image
  const handleSave = async () => {
    if (!currentImage) {
      showToast('No image to save', 'warning');
      return;
    }

    setLoading(true);
    try {
      console.log('[Save] Auto-mark mode:', imageConfig.auto_mark_cleaned);

      let saveData = {
        doc_id: currentImage.id,
      };

      // Only include image_data if NOT in auto-mark mode
      if (!imageConfig.auto_mark_cleaned) {
        console.log('[Save] Getting canvas data for manual cleaning...');
        const canvasData = window.getImageCanvasData?.();
        console.log('[Save] Canvas data:', canvasData ? 'present' : 'null');
        if (!canvasData) {
          throw new Error('Failed to get canvas data');
        }
        saveData.image_data = canvasData.imageData;
        console.log('[Save] Image data length:', canvasData.imageData?.length);
      }

      console.log('[Save] Saving image for doc_id:', currentImage.id);
      const response = await imageService.saveImage(saveData);

      console.log('[Save] Save response:', response.data);

      const message = response.data?.auto_marked
        ? 'Image marked as cleaned (auto-mark mode)!'
        : 'Image saved and marked as done!';
      showToast(message, 'success');

      // Load next image
      await loadStats();
      await loadNextImage();
    } catch (error) {
      console.error('[Save] Failed to save image:', error);
      console.error('[Save] Error response:', error.response?.data);
      showToast(error.response?.data?.error || 'Failed to save image', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Skip image
  const handleSkip = async () => {
    if (!currentImage) {
      showToast('No image to skip', 'warning');
      return;
    }

    if (!window.confirm('Are you sure you want to skip this image?')) {
      return;
    }

    setLoading(true);
    try {
      await imageService.skipImage(currentImage.id);
      showToast('Image skipped', 'info');
      
      // Load next image
      await loadStats();
      await loadNextImage();
    } catch (error) {
      console.error('Failed to skip image:', error);
      showToast(error.response?.data?.error || 'Failed to skip image', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Load initial data
  useEffect(() => {
    loadStats();
    loadImageConfig();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🎨 Image Cleaning</h1>
          <p className="text-gray-600">Remove watermarks from news images using AI-powered inpainting</p>
        </div>

        {/* Settings Toggle */}
        <Card className="p-4 bg-blue-50 border-blue-200">
          <div className="flex items-center space-x-3">
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-gray-900 mb-1">
                Auto-Mark Images as Cleaned
              </h3>
              <p className="text-xs text-gray-600">
                {imageConfig.auto_mark_cleaned
                  ? 'Images are automatically marked as cleaned without watermark removal'
                  : 'Manual watermark removal required for each image'}
              </p>
            </div>
            <button
              onClick={toggleAutoMarkCleaned}
              disabled={configLoading}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${imageConfig.auto_mark_cleaned ? 'bg-blue-600' : 'bg-gray-300'}
                ${configLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
              aria-label="Toggle auto-mark cleaned"
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${imageConfig.auto_mark_cleaned ? 'translate-x-6' : 'translate-x-1'}
                `}
              />
            </button>
          </div>
        </Card>
      </div>

      {/* Statistics */}
      <StatsDisplay stats={stats} loading={statsLoading} />

      {/* Auto-Mark Mode Notice */}
      {imageConfig.auto_mark_cleaned && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                <strong>Auto-Mark Mode Active:</strong> Images will be marked as cleaned without watermark removal.
                Click "Save & Next" to mark the current image as cleaned and proceed to the next one.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Canvas Area */}
        <div className="lg:col-span-2">
          <Card title={imageConfig.auto_mark_cleaned ? "Image Preview (Auto-Mark Mode)" : "Image Editor"}>
            <div className="relative" style={{ height: '600px' }}>
              {imageConfig.auto_mark_cleaned ? (
                // Auto-mark mode: Just show the image without editing tools
                <div className="w-full h-full flex items-center justify-center bg-gray-100">
                  {imageData ? (
                    <AuthenticatedImage
                      src={imageData}
                      alt="Preview"
                      className="max-w-full max-h-full object-contain"
                    />
                  ) : (
                    <div className="text-center text-gray-500">
                      <p className="text-lg mb-2">No image loaded</p>
                      <p className="text-sm">Click "Load Next Image" to start</p>
                    </div>
                  )}
                </div>
              ) : (
                // Manual mode: Show editing canvas
                <ImageCanvas
                  image={imageData}
                  brushSize={brushSize}
                  onMaskChange={setHasMask}
                  clearMask={clearMaskTrigger}
                  autoDetect={autoDetectTrigger}
                />
              )}

              {/* Loading Overlay */}
              {(loading || processing) && (
                <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-10">
                  <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                    <p className="text-gray-700 font-semibold">
                      {processing ? 'Removing watermark...' : 'Loading...'}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Control Panel */}
        <div className="lg:col-span-1">
          <Card title="Controls">
            <ControlPanel
              brushSize={brushSize}
              onBrushSizeChange={setBrushSize}
              currentImage={currentImage}
              hasMask={hasMask}
              onLoadNext={loadNextImage}
              onAutoDetect={handleAutoDetect}
              onClearMask={handleClearMask}
              onProcess={handleProcess}
              onSave={handleSave}
              onSkip={handleSkip}
              loading={loading}
              processing={processing}
              autoMarkMode={imageConfig.auto_mark_cleaned}
            />
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ImageCleaningPage;

