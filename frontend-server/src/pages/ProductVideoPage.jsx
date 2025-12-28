import React, { useState, useEffect } from 'react';
import { Card, Button, ConfirmDialog, Table } from '../components/common';
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
  const [viewMode, setViewMode] = useState('card'); // 'card' or 'table'
  const [selectedCategory, setSelectedCategory] = useState('all');
  const { showToast } = useToast();

  // Product categories
  const categories = {
    all: { label: 'All Products', icon: '📦', color: 'gray' },
    electronics: { label: 'Electronics', icon: '💻', color: 'blue' },
    clothing: { label: 'Clothing', icon: '👕', color: 'purple' },
    shoes: { label: 'Shoes', icon: '👟', color: 'red' },
    accessories: { label: 'Accessories', icon: '⌚', color: 'pink' },
    home: { label: 'Home & Garden', icon: '🏡', color: 'green' },
    sports: { label: 'Sports', icon: '⚽', color: 'orange' },
    beauty: { label: 'Beauty', icon: '💄', color: 'rose' },
    food: { label: 'Food & Beverage', icon: '🍔', color: 'yellow' },
    books: { label: 'Books', icon: '📚', color: 'indigo' },
    toys: { label: 'Toys', icon: '🧸', color: 'cyan' },
    general: { label: 'General', icon: '📦', color: 'gray' },
    other: { label: 'Other', icon: '🎁', color: 'slate' }
  };

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

    // Poll every 15 seconds
    const pollInterval = setInterval(() => {
      fetchProducts();
      fetchStats();
    }, 15000);

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

  // Filter products by category
  const filteredProducts = selectedCategory === 'all'
    ? products
    : products.filter(p => {
        const productCategory = (p.category || 'general').toLowerCase().replace(/\s+&\s+/g, '').replace(/\s+/g, '');
        return productCategory === selectedCategory;
      });

  // Get category info for a product
  const getCategoryInfo = (categoryName) => {
    const normalized = (categoryName || 'general').toLowerCase().replace(/\s+&\s+/g, '').replace(/\s+/g, '');
    return categories[normalized] || categories.general;
  };

  // Get status badge color
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'green';
      case 'processing': return 'blue';
      case 'failed': return 'red';
      default: return 'yellow';
    }
  };

  // Table columns configuration
  const tableColumns = [
    {
      key: 'product_name',
      label: 'Product Name',
      render: (value, product) => {
        const categoryInfo = getCategoryInfo(product.category);
        return (
          <div className="flex items-center gap-2">
            <span className="text-xl">{categoryInfo.icon}</span>
            <span className="font-medium">{value}</span>
          </div>
        );
      }
    },
    {
      key: 'category',
      label: 'Category',
      render: (value) => {
        const cat = getCategoryInfo(value);
        return (
          <span className={`px-2 py-1 rounded text-xs font-medium bg-${cat.color}-100 text-${cat.color}-700`}>
            {cat.label}
          </span>
        );
      }
    },
    {
      key: 'description',
      label: 'Description',
      render: (value) => (
        <span className="text-sm text-gray-600 line-clamp-2">{value || 'No description'}</span>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (_, product) => {
        const status = product.generated_video?.status || 'pending';
        const color = getStatusColor(status);
        return (
          <span className={`px-2 py-1 rounded text-xs font-medium bg-${color}-100 text-${color}-700`}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        );
      }
    },
    {
      key: 'price',
      label: 'Price',
      render: (value, product) => {
        if (!value) return <span className="text-gray-400">-</span>;
        return <span className="font-medium">{product.currency || 'USD'} {value}</span>;
      }
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, product) => (
        <TableRowActions
          product={product}
          onEdit={() => handleEdit(product)}
          onPreview={() => handlePreview(product)}
          onRecompute={() => handleRecomputeVideo(product)}
          onDelete={() => handleDelete(product)}
          isProcessing={recomputingProductId === product._id || product.generated_video?.status === 'processing'}
        />
      )
    }
  ];

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

  // Product Card Component
  const ProductCard = ({ product, onEdit, onPreview, onRecompute, onDelete, isProcessing }) => {
    const categoryInfo = getCategoryInfo(product.category);
    const status = product.generated_video?.status || 'pending';
    const statusColor = getStatusColor(status);
    const hasVideo = product.video_url || product.generated_video?.video_url;

    return (
      <div className="bg-white border-2 border-gray-200 rounded-lg overflow-hidden hover:shadow-lg hover:border-gray-300 transition-all duration-200">
        {/* Preview/Thumbnail Section - Compact */}
        <div className="relative h-32 bg-gradient-to-br from-blue-50 via-blue-100 to-blue-50 flex items-center justify-center overflow-hidden group">
          {hasVideo ? (
            <div className="absolute inset-0">
              <video
                src={product.video_url || product.generated_video?.video_url}
                className="w-full h-full object-cover"
                muted
              />
            </div>
          ) : (
            <div className="text-5xl opacity-30">{categoryInfo.icon}</div>
          )}

          {/* Category badge - Compact */}
          <div className="absolute top-1.5 left-1.5">
            <span className={`px-1.5 py-0.5 rounded text-xs font-semibold shadow-md backdrop-blur-sm bg-${categoryInfo.color}-100 text-${categoryInfo.color}-700`}>
              {categoryInfo.icon} {categoryInfo.label}
            </span>
          </div>

          {/* Status badge - Compact */}
          <div className="absolute top-1.5 right-1.5">
            <span className={`px-1.5 py-0.5 rounded text-xs font-semibold shadow-md backdrop-blur-sm bg-${statusColor}-100 text-${statusColor}-700`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
          </div>

          {/* Play button - Compact */}
          {hasVideo && (
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 shadow-2xl transform group-hover:scale-110 cursor-pointer z-10"
              onClick={onPreview}
            >
              <svg className="w-6 h-6 text-indigo-600 ml-1" fill="currentColor" viewBox="0 0 20 20">
                <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
              </svg>
            </div>
          )}
        </div>

        {/* Content Section - Compact */}
        <div className="p-3">
          {/* Header - Compact */}
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <span className="text-xl">{categoryInfo.icon}</span>
              <div>
                <h3 className="font-semibold text-gray-900 text-base leading-tight">
                  {product.product_name}
                </h3>
              </div>
            </div>
          </div>

          {/* Description - Compact */}
          <p className="text-xs text-gray-600 mb-2 line-clamp-2 min-h-[32px]">
            {product.description || 'No description provided'}
          </p>

          {/* Product Info - Compact */}
          <div className="flex items-center gap-3 mb-2 text-xs text-gray-500 border-t border-gray-100 pt-2">
            {product.price && (
              <div className="flex items-center gap-1">
                <span>💰</span>
                <span>{product.currency || 'USD'} {product.price}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <span>📊</span>
              <span className={`text-${statusColor}-600 font-medium`}>{status}</span>
            </div>
          </div>

          {/* Actions - All in one line - Compact */}
          <div className="flex gap-1.5">
            <Button
              size="sm"
              onClick={onPreview}
              disabled={isProcessing || !hasVideo}
              className="flex-1 text-xs py-1"
            >
              {hasVideo ? 'Preview' : '⏳'}
            </Button>
            <Button
              size="sm"
              onClick={onRecompute}
              disabled={isProcessing}
              className="flex-1 text-xs py-1"
            >
              {isProcessing ? '⏳' : 'Recompute'}
            </Button>
            <Button
              size="sm"
              onClick={onEdit}
              disabled={isProcessing}
              className="flex-1 text-xs py-1"
            >
              Edit
            </Button>
            <Button
              size="sm"
              variant="danger"
              onClick={onDelete}
              disabled={isProcessing}
              className="px-2 text-xs py-1"
            >
              🗑️
            </Button>
          </div>
        </div>
      </div>
    );
  };

  // Table Row Actions Component
  const TableRowActions = ({ product, onEdit, onPreview, onRecompute, onDelete, isProcessing }) => {
    const hasVideo = product.video_url || product.generated_video?.video_url;

    return (
      <div className="flex gap-1.5">
        <Button
          size="sm"
          onClick={onPreview}
          disabled={isProcessing || !hasVideo}
          className="px-2 py-1"
        >
          {hasVideo ? 'Preview' : '⏳'}
        </Button>
        <Button
          size="sm"
          onClick={onRecompute}
          disabled={isProcessing}
          className="px-2 py-1"
        >
          {isProcessing ? '⏳' : 'Recompute'}
        </Button>
        <Button
          size="sm"
          onClick={onEdit}
          disabled={isProcessing}
          className="px-2 py-1"
        >
          Edit
        </Button>
        <Button
          size="sm"
          variant="danger"
          onClick={onDelete}
          disabled={isProcessing}
          className="px-2 py-1"
        >
          🗑️
        </Button>
      </div>
    );
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

      {/* Products Section */}
      <Card className="bg-white">
        {/* Category Filters and View Toggle */}
        <div className="border-b border-gray-200 pb-4 mb-4">
          {/* Category Filter Pills */}
          <div className="flex flex-wrap gap-2 mb-4">
            {Object.entries(categories).map(([key, cat]) => (
              <button
                key={key}
                onClick={() => setSelectedCategory(key)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                  selectedCategory === key
                    ? `bg-${cat.color}-100 text-${cat.color}-700 ring-2 ring-${cat.color}-500`
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {cat.icon} {cat.label}
              </button>
            ))}
          </div>

          {/* View Toggle and Create Button */}
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={() => setViewMode('card')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                viewMode === 'card'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
                Cards
              </span>
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                viewMode === 'table'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Table
              </span>
            </button>
            <Button variant="primary" onClick={handleCreateNew}>
              + Create Product
            </Button>
          </div>
        </div>

        {/* Loading State */}
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
          <>
            {/* Table View */}
            {viewMode === 'table' && (
              <Table
                columns={tableColumns}
                data={filteredProducts}
                emptyMessage={`No ${selectedCategory === 'all' ? '' : categories[selectedCategory]?.label.toLowerCase()} products found. Create your first product!`}
              />
            )}

            {/* Card View */}
            {viewMode === 'card' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredProducts.map((product) => (
                  <ProductCard
                    key={product._id}
                    product={product}
                    onEdit={() => handleEdit(product)}
                    onPreview={() => handlePreview(product)}
                    onRecompute={() => handleRecomputeVideo(product)}
                    onDelete={() => handleDelete(product)}
                    isProcessing={recomputingProductId === product._id || product.generated_video?.status === 'processing'}
                  />
                ))}
              </div>
            )}
          </>
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

