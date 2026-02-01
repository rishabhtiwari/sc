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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="w-20 h-20 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-3xl">🖼️</span>
            </div>
          </div>
          <p className="text-lg font-semibold text-gray-700">Loading your image library...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      {/* Content */}
      <div className="relative space-y-6 p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/50 p-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 via-pink-500 to-blue-500 rounded-2xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform">
                <span className="text-4xl">🖼️</span>
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 bg-clip-text text-transparent">
                  Image Library
                </h1>
                <p className="text-gray-600 mt-1 font-medium">
                  Browse and manage your image collection
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-gradient-to-r from-purple-100 to-pink-100 px-6 py-3 rounded-xl border border-purple-200">
                <p className="text-sm font-semibold text-gray-700">
                  <span className="text-purple-600 text-xl">{filteredImages.length}</span>
                  <span className="text-gray-500 mx-1">/</span>
                  <span className="text-pink-600 text-xl">{images.length}</span>
                  <span className="text-gray-600 ml-2">images</span>
                </p>
              </div>
              <Button
                onClick={() => window.location.href = '/design-editor'}
                className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-xl hover:shadow-xl transition-all transform hover:scale-105 font-semibold"
              >
                🎨 Design Editor
              </Button>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-lg border border-white/50 p-6">
          <div className="relative">
            <input
              type="text"
              placeholder="🔍 Search images..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-6 py-4 bg-white border-2 border-purple-200 rounded-xl focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all text-lg"
            />
          </div>
        </div>

        {/* Images Grid */}
        {filteredImages.length === 0 ? (
          <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/50 p-16">
            <div className="text-center">
              <div className="text-8xl mb-6 opacity-50">🖼️</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                {images.length === 0 ? 'No Images Yet' : 'No Matching Images'}
              </h3>
              <p className="text-gray-600 text-lg mb-6">
                {images.length === 0
                  ? 'Upload images from the Design Editor to see them here'
                  : 'Try adjusting your search query'}
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredImages.map((image, index) => (
              <div
                key={image.image_id}
                className="transform transition-all duration-300 hover:scale-105"
                style={{
                  animation: `fadeInUp 0.5s ease-out ${index * 0.05}s both`
                }}
              >
                <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl transition-all overflow-hidden group border border-purple-100">
                  {/* Image Preview */}
                  <div className="aspect-square bg-gradient-to-br from-purple-100 to-pink-100 relative overflow-hidden">
                    <AuthenticatedImage
                      src={image.url}
                      alt={image.name}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                    />
                    {/* Delete Button Overlay */}
                    <button
                      onClick={() => handleDeleteClick(image)}
                      className="absolute top-3 right-3 w-10 h-10 bg-red-500 hover:bg-red-600 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all shadow-lg flex items-center justify-center transform hover:scale-110"
                      title="Delete image"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Image Info */}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 truncate text-lg mb-2">
                      {image.name || 'Untitled Image'}
                    </h3>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        📏 {image.width || 0} × {image.height || 0}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(image.created_at).toLocaleDateString()}
                      </span>
                    </div>
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

      {/* Animations */}
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
};

export default ImageLibraryPage;

