import React, { useState, useEffect } from 'react';
import { Card, Button, ConfirmDialog } from '../components/common';
import { useToast } from '../hooks/useToast';
import { productService } from '../services';
import ProductVideoWizard from '../components/ProductVideo/ProductVideoWizard';

/**
 * Product Video Page - E-commerce product video creation and management
 * @param {boolean} embedded - Whether the page is embedded in another page (hides header)
 */
const ProductVideoPage = ({ embedded = false }) => {
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0
  });
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewProduct, setPreviewProduct] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, product: null });
  const [recomputeDialog, setRecomputeDialog] = useState({ isOpen: false, product: null });
  const [recomputingProductId, setRecomputingProductId] = useState(null);
  const { showToast } = useToast();

  // Fetch products on mount
  useEffect(() => {
    fetchProducts();
    fetchStats();
  }, []);

  // Poll for product status updates when there are processing products
  useEffect(() => {
    const hasProcessingProducts = products.some(
      p => p.generated_video?.status === 'processing' || recomputingProductId === p._id
    );

    if (!hasProcessingProducts) {
      return;
    }

    // Poll every 3 seconds
    const pollInterval = setInterval(() => {
      fetchProducts();
      fetchStats();
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [products, recomputingProductId]);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await productService.getProducts();
      if (response.data.status === 'success') {
        setProducts(response.data.products || []);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
      // Don't show error toast if it's just empty - set empty array
      setProducts([]);
      // Only show error if it's not a 404 or empty response
      if (error.response && error.response.status !== 404) {
        showToast('Failed to fetch products', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await productService.getProductStats();
      if (response.data.status === 'success') {
        setStats(response.data.stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
      // Don't show error for stats - just keep default values
    }
  };

  const handleCreateNew = () => {
    setSelectedProduct(null);
    setShowWizard(true);
  };

  const handleEdit = async (product) => {
    // Fetch the latest product data from the API to ensure we have fresh media_urls
    try {
      const response = await productService.getProduct(product._id);
      if (response.data.status === 'success') {
        setSelectedProduct(response.data.product);
        setShowWizard(true);
      } else {
        showToast('Failed to load product data', 'error');
      }
    } catch (error) {
      console.error('Error fetching product:', error);
      showToast('Failed to load product data', 'error');
    }
  };

  const handleDelete = (product) => {
    setDeleteDialog({ isOpen: true, product });
  };

  const confirmDelete = async () => {
    const productId = deleteDialog.product._id;
    setDeleteDialog({ isOpen: false, product: null });

    try {
      await productService.deleteProduct(productId);
      showToast('Product deleted successfully', 'success');
      fetchProducts();
      fetchStats();
    } catch (error) {
      console.error('Error deleting product:', error);
      showToast('Failed to delete product', 'error');
    }
  };

  const handleWizardClose = () => {
    setShowWizard(false);
    setSelectedProduct(null);
    fetchProducts();
    fetchStats();
  };

  const handlePreview = (product) => {
    setPreviewProduct(product);
    setShowPreview(true);
  };

  const handlePreviewClose = () => {
    setShowPreview(false);
    setPreviewProduct(null);
  };

  const handleRecomputeVideo = (product) => {
    setRecomputeDialog({ isOpen: true, product });
  };

  const confirmRecompute = async () => {
    const product = recomputeDialog.product;
    setRecomputeDialog({ isOpen: false, product: null });
    setRecomputingProductId(product._id);

    try {
      showToast('Starting video regeneration...', 'info');

      // Call the generate video API
      // Don't send any data - backend will fetch everything from the database
      const response = await productService.generateVideo(product._id, {});

      if (response.data.status === 'success') {
        showToast('Video regeneration started successfully', 'success');
        await fetchProducts();
        fetchStats();
      } else {
        showToast(response.data.message || 'Failed to start video regeneration', 'error');
      }
    } catch (error) {
      console.error('Error recomputing video:', error);
      showToast(error.response?.data?.message || 'Failed to recompute video', 'error');
    } finally {
      setRecomputingProductId(null);
    }
  };

  return (
    <div className={embedded ? "h-full bg-gray-50 p-6" : "min-h-screen bg-gray-50 p-6"}>
      {/* Header - Only show if not embedded */}
      {!embedded && (
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">📦 Product Videos</h1>
          <p className="text-gray-600 mt-1">Create engaging product videos for your e-commerce store</p>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <Card className="bg-white">
          <div className="text-center">
            <div className="text-3xl mb-2">📹</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600">Total Videos</div>
          </div>
        </Card>
        
        <Card className="bg-white">
          <div className="text-center">
            <div className="text-3xl mb-2">⏳</div>
            <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
            <div className="text-sm text-gray-600">Pending</div>
          </div>
        </Card>
        
        <Card className="bg-white">
          <div className="text-center">
            <div className="text-3xl mb-2">⚙️</div>
            <div className="text-2xl font-bold text-blue-600">{stats.processing}</div>
            <div className="text-sm text-gray-600">Processing</div>
          </div>
        </Card>
        
        <Card className="bg-white">
          <div className="text-center">
            <div className="text-3xl mb-2">✅</div>
            <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
            <div className="text-sm text-gray-600">Completed</div>
          </div>
        </Card>
        
        <Card className="bg-white">
          <div className="text-center">
            <div className="text-3xl mb-2">❌</div>
            <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
            <div className="text-sm text-gray-600">Failed</div>
          </div>
        </Card>
      </div>

      {/* Products Grid */}
      <Card title="Product Videos" className="bg-white">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <p className="ml-3 text-gray-600">Loading products...</p>
          </div>
        ) : products.length === 0 ? (
          // Empty state - no products yet
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📦</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Product Videos Yet</h3>
            <p className="text-gray-600 mb-6">Get started by creating your first product video</p>
            <Button onClick={handleCreateNew} variant="primary" size="lg">
              ➕ Create Your First Video
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Existing Products */}
            {products.map((product) => (
              <div key={product._id} className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                <h3 className="font-semibold text-gray-900 mb-2">{product.product_name}</h3>
                <p className="text-sm text-gray-600 mb-2 line-clamp-2">{product.description}</p>
                <div className="text-xs text-gray-500 mb-3">
                  Category: {product.category} | Status: {product.generated_video?.status || 'pending'}
                </div>
                <div className="flex gap-2 flex-wrap">
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => handleEdit(product)}
                    disabled={recomputingProductId === product._id || product.generated_video?.status === 'processing'}
                  >
                    ✏️ Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handlePreview(product)}
                    disabled={recomputingProductId === product._id || product.generated_video?.status === 'processing' || (!product.video_url && !product.generated_video?.video_url)}
                  >
                    {(product.video_url || product.generated_video?.video_url) ? '👁️ Preview' : '⏳ No Video'}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleRecomputeVideo(product)}
                    disabled={recomputingProductId === product._id || product.generated_video?.status === 'processing'}
                  >
                    {(recomputingProductId === product._id || product.generated_video?.status === 'processing') ? '⏳ Processing...' : '🔄 Recompute'}
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => handleDelete(product)}
                    disabled={recomputingProductId === product._id || product.generated_video?.status === 'processing'}
                  >
                    🗑️ Delete
                  </Button>
                </div>
              </div>
            ))}

            {/* Create New Card */}
            <button
              onClick={handleCreateNew}
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 hover:border-indigo-500 hover:bg-indigo-50 transition-colors flex flex-col items-center justify-center min-h-[200px]"
            >
              <div className="text-5xl mb-2">➕</div>
              <div className="text-lg font-semibold text-gray-700">Create New Video</div>
            </button>
          </div>
        )}
      </Card>

      {/* Wizard Modal */}
      {showWizard && (
        <ProductVideoWizard
          product={selectedProduct}
          onClose={handleWizardClose}
          onComplete={handleWizardClose}
        />
      )}

      {/* Video Preview Modal */}
      {showPreview && previewProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-gray-900">{previewProduct.product_name}</h2>
                <p className="text-sm text-gray-600 mt-1">Video Preview</p>
              </div>
              <button
                onClick={handlePreviewClose}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6">
              {/* Video Player */}
              <div className="mb-6">
                <div className="bg-black rounded-lg overflow-hidden aspect-video">
                  <video
                    controls
                    autoPlay
                    className="w-full h-full"
                    src={previewProduct.video_url || previewProduct.generated_video?.video_url}
                    onError={(e) => {
                      console.error('Video playback error:', e);
                      console.error('Video URL:', previewProduct.video_url || previewProduct.generated_video?.video_url);
                    }}
                    onLoadedMetadata={() => {
                      console.log('Video metadata loaded successfully');
                    }}
                  >
                    Your browser does not support the video tag.
                  </video>
                </div>
                {/* Debug info */}
                <div className="mt-2 text-xs text-gray-500">
                  Video URL: {previewProduct.video_url || previewProduct.generated_video?.video_url}
                </div>
              </div>

              {/* Product Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Product Information</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-600">Name:</span>
                      <span className="ml-2 font-medium">{previewProduct.product_name}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Category:</span>
                      <span className="ml-2 font-medium">{previewProduct.category}</span>
                    </div>
                    {previewProduct.price && (
                      <div>
                        <span className="text-gray-600">Price:</span>
                        <span className="ml-2 font-medium">
                          {previewProduct.currency || '$'} {previewProduct.price}
                        </span>
                      </div>
                    )}
                    {previewProduct.description && (
                      <div>
                        <span className="text-gray-600">Description:</span>
                        <p className="mt-1 text-gray-900">{previewProduct.description}</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Video Information</h3>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-600">Status:</span>
                      <span className="ml-2 font-medium">
                        {previewProduct.generated_video?.status || 'N/A'}
                      </span>
                    </div>
                    {previewProduct.template_id && (
                      <div>
                        <span className="text-gray-600">Template:</span>
                        <span className="ml-2 font-medium">{previewProduct.template_id}</span>
                      </div>
                    )}
                    {previewProduct.duration && (
                      <div>
                        <span className="text-gray-600">Duration:</span>
                        <span className="ml-2 font-medium">{previewProduct.duration}s</span>
                      </div>
                    )}
                    {(previewProduct.video_url || previewProduct.generated_video?.video_url) && (
                      <div>
                        <span className="text-gray-600">Video URL:</span>
                        <a
                          href={previewProduct.video_url || previewProduct.generated_video?.video_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 text-blue-600 hover:underline text-xs break-all"
                        >
                          {(previewProduct.video_url || previewProduct.generated_video?.video_url).substring(0, 50)}...
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex gap-3 justify-end">
                <Button variant="outline" onClick={handlePreviewClose}>
                  Close
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    handleRecomputeVideo(previewProduct);
                    handlePreviewClose();
                  }}
                  disabled={previewProduct.generated_video?.status === 'processing'}
                >
                  {previewProduct.generated_video?.status === 'processing' ? '⏳ Processing...' : '🔄 Recompute Video'}
                </Button>
                <Button variant="primary" onClick={() => {
                  handlePreviewClose();
                  handleEdit(previewProduct);
                }}>
                  ✏️ Edit Product
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, product: null })}
        onConfirm={confirmDelete}
        title="Delete Product"
        description="This action cannot be undone"
        message={
          deleteDialog.product
            ? `Are you sure you want to delete "${deleteDialog.product.product_name}"?`
            : ''
        }
        warningMessage="This will permanently delete the product and all associated data including videos. This action cannot be undone."
        confirmText="Delete Product"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Recompute Video Confirmation Dialog */}
      <ConfirmDialog
        isOpen={recomputeDialog.isOpen}
        onClose={() => setRecomputeDialog({ isOpen: false, product: null })}
        onConfirm={confirmRecompute}
        title="Recompute Video"
        description="Regenerate product video"
        message={
          recomputeDialog.product
            ? `Are you sure you want to recompute the video for "${recomputeDialog.product.product_name}"?`
            : ''
        }
        warningMessage="This will regenerate the video using the current product data. The existing video will be replaced."
        confirmText="Recompute Video"
        cancelText="Cancel"
        variant="warning"
      />
    </div>
  );
};

export default ProductVideoPage;

