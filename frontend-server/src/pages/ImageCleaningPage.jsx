import React, { useState, useEffect } from 'react';
import { Card } from '../components/common';
import { useToast } from '../hooks/useToast';
import { imageService } from '../services';
import StatsDisplay from '../components/ImageCleaning/StatsDisplay';
import ImageCanvas from '../components/ImageCleaning/ImageCanvas';
import ControlPanel from '../components/ImageCleaning/ControlPanel';

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

  const { showToast } = useToast();

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
      });

      // Load image as base64
      if (data.image_url) {
        console.log('Loading image from URL:', data.image_url);
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
          console.log('Image loaded successfully, dimensions:', img.width, 'x', img.height);
          try {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            const dataUrl = canvas.toDataURL('image/png');
            console.log('Canvas data URL created, length:', dataUrl.length);
            setImageData(dataUrl);
            setHasMask(false);
            showToast('Image loaded successfully', 'success');
          } catch (err) {
            console.error('Error converting image to canvas:', err);
            showToast('Failed to process image: ' + err.message, 'error');
          }
        };
        img.onerror = (err) => {
          console.error('Image load error:', err);
          showToast('Failed to load image', 'error');
        };
        img.src = data.image_url;
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
      const response = await imageService.processImage({
        doc_id: currentImage.id,
        image_data: canvasData.imageData,
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
      console.log('[Save] Getting canvas data...');
      // Get current image data
      const canvasData = window.getImageCanvasData?.();
      console.log('[Save] Canvas data:', canvasData ? 'present' : 'null');
      if (!canvasData) {
        throw new Error('Failed to get canvas data');
      }

      console.log('[Save] Saving image for doc_id:', currentImage.id);
      console.log('[Save] Image data length:', canvasData.imageData?.length);

      const response = await imageService.saveImage({
        doc_id: currentImage.id,
        image_data: canvasData.imageData,
      });

      console.log('[Save] Save response:', response.data);
      showToast('Image saved and marked as done!', 'success');

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
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">🎨 Image Cleaning</h1>
        <p className="text-gray-600">Remove watermarks from news images using AI-powered inpainting</p>
      </div>

      {/* Statistics */}
      <StatsDisplay stats={stats} loading={statsLoading} />

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Canvas Area */}
        <div className="lg:col-span-2">
          <Card title="Image Editor">
            <div className="relative" style={{ height: '600px' }}>
              <ImageCanvas
                image={imageData}
                brushSize={brushSize}
                onMaskChange={setHasMask}
                clearMask={clearMaskTrigger}
                autoDetect={autoDetectTrigger}
              />
              
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
            />
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ImageCleaningPage;

