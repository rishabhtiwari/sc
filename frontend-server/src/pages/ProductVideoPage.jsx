import React, { useState, useEffect } from 'react';
import { Card, Button } from '../components/common';
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
  const { showToast } = useToast();

  // Fetch products on mount
  useEffect(() => {
    fetchProducts();
    fetchStats();
  }, []);

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

  const handleEdit = (product) => {
    setSelectedProduct(product);
    setShowWizard(true);
  };

  const handleDelete = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }

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
                <div className="flex gap-2">
                  <Button size="sm" variant="primary" onClick={() => handleEdit(product)}>
                    ✏️ Edit
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => handleDelete(product._id)}>
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
    </div>
  );
};

export default ProductVideoPage;

