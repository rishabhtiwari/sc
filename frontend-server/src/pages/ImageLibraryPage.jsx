import React, { useState, useEffect } from 'react';
import { Button } from '../components/common';
import { useToast } from '../hooks/useToast';
import { imageLibrary } from '../services/assetLibraryService';
import AuthenticatedImage from '../components/common/AuthenticatedImage';
import ConfirmDialog from '../components/common/ConfirmDialog';

/**
 * Image Library Page - Full page view of all images with modern, appealing design
 */
const ImageLibraryPage = () => {
  const { showToast } = useToast();
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, image: null });

  // Load images on mount
  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    setLoading(true);
    try {
      const response = await imageLibrary.list();
      if (response.success) {
        setImages(response.images || []);
      }
    } catch (error) {
      console.error('Failed to fetch images:', error);
      showToast('Failed to load image library', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (image) => {
    setDeleteDialog({ isOpen: true, image });
  };

  const confirmDelete = async () => {
    if (!deleteDialog.image) return;

    try {
      await imageLibrary.delete(deleteDialog.image.image_id);
      showToast('Image deleted successfully', 'success');
      setDeleteDialog({ isOpen: false, image: null });
      fetchImages(); // Refresh list
    } catch (error) {
      console.error('Failed to delete image:', error);
      showToast('Failed to delete image', 'error');
      setDeleteDialog({ isOpen: false, image: null });
    }
  };

  // Filter images based on search query
  const filteredImages = images.filter(image =>
    image.name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="w-16 h-16 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">🖼️</span>
            </div>
          </div>
          <p className="text-gray-700">Loading your image library...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Content */}
      <div className="space-y-6 p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🖼️</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Image Library
                </h1>
                <p className="text-gray-600 text-sm mt-1">
                  Browse and manage your image collection
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-gray-50 px-4 py-2 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-700">
                  <span className="font-semibold text-gray-900">{filteredImages.length}</span>
                  <span className="text-gray-500 mx-1">/</span>
                  <span className="font-semibold text-gray-900">{images.length}</span>
                  <span className="text-gray-600 ml-1">images</span>
                </p>
              </div>
              <Button
                onClick={() => window.location.href = '/design-editor'}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                🎨 Design Editor
              </Button>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
          <div className="relative">
            <input
              type="text"
              placeholder="🔍 Search images..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            />
          </div>
        </div>

        {/* Images Grid */}
        {filteredImages.length === 0 ? (
          <div className="bg-white rounded-lg shadow border border-gray-200 p-16">
            <div className="text-center">
              <div className="text-6xl mb-4 opacity-40">🖼️</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {images.length === 0 ? 'No Images Yet' : 'No Matching Images'}
              </h3>
              <p className="text-gray-600 mb-4">
                {images.length === 0
                  ? 'Upload images from the Design Editor to see them here'
                  : 'Try adjusting your search query'}
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredImages.map((image, index) => (
              <div
                key={image.image_id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-all overflow-hidden group border border-gray-200"
              >
                {/* Image Preview */}
                <div className="aspect-square bg-gray-100 relative overflow-hidden">
                  <AuthenticatedImage
                    src={image.url}
                    alt={image.name}
                    className="w-full h-full object-cover"
                  />
                  {/* Delete Button Overlay */}
                  <button
                    onClick={() => handleDeleteClick(image)}
                    className="absolute top-2 right-2 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-all shadow flex items-center justify-center"
                    title="Delete image"
                  >
                    ✕
                  </button>
                </div>

                {/* Image Info */}
                <div className="p-3">
                  <h3 className="font-medium text-gray-900 truncate mb-1">
                    {image.name || 'Untitled Image'}
                  </h3>
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span className="flex items-center gap-1">
                      📏 {image.width || 0} × {image.height || 0}
                    </span>
                    <span className="text-gray-500">
                      {new Date(image.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, image: null })}
        onConfirm={confirmDelete}
        title="Delete Image"
        description="This action cannot be undone"
        message={`Are you sure you want to delete "${deleteDialog.image?.name || 'this image'}"?`}
        confirmText="Delete Image"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default ImageLibraryPage;

