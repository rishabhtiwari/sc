import React, { useState, useEffect } from 'react';
import { Card } from '../components/common';
import { useToast } from '../hooks/useToast';
import { imageService } from '../services';
import StatsDisplay from '../components/ImageCleaning/StatsDisplay';
import ImageCanvas from '../components/ImageCleaning/ImageCanvas';
import ControlPanel from '../components/ImageCleaning/ControlPanel';
import ReplaceImageModal from '../components/ImageCleaning/ReplaceImageModal';

/**
 * Image Processing Page - Remove watermarks from news images and view all images
 */
const ImageProcessingPage = () => {
  const [activeTab, setActiveTab] = useState('editor'); // 'editor' or 'gallery'
  const [stats, setStats] = useState({ total: 0, cleaned: 0, skipped: 0, pending: 0 });
  const [statsLoading, setStatsLoading] = useState(false);

  // Editor state
  const [currentImage, setCurrentImage] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [brushSize, setBrushSize] = useState(30);
  const [hasMask, setHasMask] = useState(false);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [clearMaskTrigger, setClearMaskTrigger] = useState(0);
  const [autoDetectTrigger, setAutoDetectTrigger] = useState(0);

  // Gallery state
  const [images, setImages] = useState([]);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalImages, setTotalImages] = useState(0);
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'pending', 'cleaned', 'skipped'
  const [limit] = useState(20);

  // Replace image modal state
  const [showReplaceModal, setShowReplaceModal] = useState(false);

  const { showToast } = useToast();

  // Load stats
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

  // Load images for gallery
  const loadImages = async () => {
    setGalleryLoading(true);
    try {
      const response = await imageService.listImages({
        page: currentPage,
        limit: limit,
        status: statusFilter,
      });
      const data = response.data?.data || response.data;
      setImages(data.images || []);
      setTotalPages(data.total_pages || 0);
      setTotalImages(data.total || 0);
    } catch (error) {
      console.error('Failed to load images:', error);
      showToast('Failed to load images', 'error');
    } finally {
      setGalleryLoading(false);
    }
  };

  // Load next image for editor
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
        originalUrl: data.original_image_url || '',
      });

      // Load image into canvas
      if (data.image_url) {
        // Fetch image with authentication headers
        const token = localStorage.getItem('auth_token');
        const headers = {};
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        fetch(data.image_url, { headers })
          .then(response => {
            if (!response.ok) {
              throw new Error(`Failed to fetch image: ${response.status}`);
            }
            return response.blob();
          })
          .then(blob => {
            const img = new Image();
            img.onload = () => {
              try {
                console.log('Loading image from URL:', data.image_url);
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                const dataUrl = canvas.toDataURL('image/png');
                console.log('Image loaded successfully, dimensions:', img.width, 'x', img.height);
                console.log('Canvas data URL created, length:', dataUrl.length);
                setImageData(dataUrl);
                setHasMask(false);
                setClearMaskTrigger(prev => prev + 1);
                // Clean up blob URL
                URL.revokeObjectURL(img.src);
              } catch (err) {
                console.error('Error converting image to canvas:', err);
                showToast('Failed to process image: ' + err.message, 'error');
              }
            };
            img.onerror = (err) => {
              console.error('Image load error:', err);
              showToast('Failed to load image', 'error');
              URL.revokeObjectURL(img.src);
            };
            img.src = URL.createObjectURL(blob);
          })
          .catch(err => {
            console.error('Failed to fetch image:', err);
            showToast('Failed to fetch image: ' + err.message, 'error');
          });
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

  // Save cleaned image
  const handleSave = async () => {
    if (!currentImage) {
      showToast('No image to save', 'warning');
      return;
    }

    setLoading(true);
    try {
      console.log('[Save] Getting canvas data...');
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
      
      await loadStats();
      await loadNextImage();
      
      // Reload gallery if on gallery tab
      if (activeTab === 'gallery') {
        await loadImages();
      }
    } catch (error) {
      console.error('[Save] Failed to save image:', error);
      console.error('[Save] Error response:', error.response?.data);
      showToast(error.response?.data?.error || 'Failed to save image', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Replace image URL - Open modal
  const handleReplaceImage = () => {
    if (!currentImage) {
      showToast('No image loaded', 'warning');
      return;
    }
    setShowReplaceModal(true);
  };

  // Handle replace image submission from modal
  const handleReplaceImageSubmit = async (newImageUrl) => {
    setShowReplaceModal(false);
    setLoading(true);

    try {
      const response = await imageService.replaceImage({
        doc_id: currentImage.id,
        image_url: newImageUrl,
      });

      showToast('Image URL replaced successfully!', 'success');

      // Reload the current image to show the new one
      await loadStats();

      // Update current image with new URL
      const data = response.data?.data || response.data;
      const newProxyUrl = data.image_url || `/api/proxy-image/${currentImage.id}`;

      setCurrentImage({
        ...currentImage,
        url: newProxyUrl,
        originalUrl: newImageUrl,
      });

      // Load the new image into canvas
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        try {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0);
          const dataUrl = canvas.toDataURL('image/png');
          setImageData(dataUrl);
          setHasMask(false);
          setClearMaskTrigger(prev => prev + 1);
        } catch (err) {
          console.error('Error converting image to canvas:', err);
          showToast('Failed to process new image: ' + err.message, 'error');
        }
      };
      img.onerror = (err) => {
        console.error('New image load error:', err);
        showToast('Failed to load new image', 'error');
      };
      img.src = newProxyUrl;

      // Reload gallery if on gallery tab
      if (activeTab === 'gallery') {
        await loadImages();
      }
    } catch (error) {
      console.error('Failed to replace image:', error);
      showToast(error.response?.data?.error || 'Failed to replace image URL', 'error');
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

    setLoading(true);
    try {
      await imageService.skipImage(currentImage.id);
      showToast('Image skipped', 'info');

      await loadStats();
      await loadNextImage();

      // Reload gallery if on gallery tab
      if (activeTab === 'gallery') {
        await loadImages();
      }
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

  // Load images when gallery tab is active or filters change
  useEffect(() => {
    if (activeTab === 'gallery') {
      loadImages();
    }
  }, [activeTab, currentPage, statusFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">🎨 Image Processing</h1>
        <p className="text-gray-600">Remove watermarks from news images using AI-powered inpainting</p>
      </div>

      {/* Statistics */}
      <StatsDisplay stats={stats} loading={statsLoading} />

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('editor')}
            className={`${
              activeTab === 'editor'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
          >
            🖼️ Editor
          </button>
          <button
            onClick={() => setActiveTab('gallery')}
            className={`${
              activeTab === 'gallery'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
          >
            📁 Gallery
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'editor' ? (
        // Editor Tab
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
                onReplaceImage={handleReplaceImage}
                onSkip={handleSkip}
                loading={loading}
                processing={processing}
              />
            </Card>
          </div>
        </div>
      ) : (
        // Gallery Tab
        <div className="space-y-4">
          {/* Filters */}
          <Card title="Filters">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700">Status:</label>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Images ({stats.total})</option>
                <option value="pending">Pending ({stats.pending})</option>
                <option value="cleaned">Cleaned ({stats.cleaned})</option>
                <option value="skipped">Skipped</option>
              </select>

              <div className="ml-auto text-sm text-gray-600">
                Showing {images.length} of {totalImages} images
              </div>
            </div>
          </Card>

          {/* Image Grid */}
          <Card title="Images">
            {galleryLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                  <p className="text-gray-700 font-semibold">Loading images...</p>
                </div>
              </div>
            ) : images.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🖼️</div>
                <p className="text-lg text-gray-600">No images found</p>
                <p className="text-sm text-gray-500 mt-2">Try changing the filter or add more articles</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {images.map((image) => (
                    <div
                      key={image.id}
                      className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
                    >
                      {/* Image */}
                      <div className="relative aspect-video bg-gray-100">
                        <img
                          src={image.status === 'cleaned' && image.cleaned_image_url ? image.cleaned_image_url : image.image_url}
                          alt={image.title}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        {/* Status Badge */}
                        <div className="absolute top-2 right-2">
                          <span
                            className={`px-2 py-1 text-xs font-semibold rounded-full ${
                              image.status === 'cleaned'
                                ? 'bg-green-100 text-green-800'
                                : image.status === 'skipped'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-blue-100 text-blue-800'
                            }`}
                          >
                            {image.status === 'cleaned' ? '✓ Cleaned' : image.status === 'skipped' ? '⊘ Skipped' : '⏳ Pending'}
                          </span>
                        </div>
                      </div>

                      {/* Info */}
                      <div className="p-3">
                        <h3 className="text-sm font-medium text-gray-900 truncate" title={image.title}>
                          {image.title}
                        </h3>
                        <p className="text-xs text-gray-500 mt-1">
                          {image.created_at ? new Date(image.created_at).toLocaleDateString() : 'N/A'}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      ← Previous
                    </button>

                    <span className="text-sm text-gray-700">
                      Page {currentPage} of {totalPages}
                    </span>

                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </Card>
        </div>
      )}

      {/* Replace Image Modal */}
      <ReplaceImageModal
        isOpen={showReplaceModal}
        onClose={() => setShowReplaceModal(false)}
        currentUrl={currentImage?.originalUrl || ''}
        onReplace={handleReplaceImageSubmit}
      />
    </div>
  );
};

export default ImageProcessingPage;

