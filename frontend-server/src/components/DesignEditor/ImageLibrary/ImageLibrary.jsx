import React, { useState, useEffect } from 'react';
import { useToast } from '../../../hooks/useToast';
import { imageLibrary } from '../../../services/assetLibraryService';
import AuthenticatedImage from '../../common/AuthenticatedImage';
import ConfirmDialog from '../../common/ConfirmDialog';

/**
 * Image Library Modal - Full-screen modal for browsing image library
 */
const ImageLibrary = ({ isOpen, onClose, onAddToCanvas }) => {
  const { showToast } = useToast();
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, image: null });

  useEffect(() => {
    if (isOpen) {
      fetchImages();
    }
  }, [isOpen]);

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

  const handleAddToCanvas = (image) => {
    if (onAddToCanvas) {
      onAddToCanvas({
        type: 'image',
        src: image.url,
        name: image.name,
        libraryId: image.image_id
      });
      showToast('Image added to canvas', 'success');
      onClose();
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-2xl w-[95%] h-[95%] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🖼️</span>
              <h1 className="text-2xl font-bold text-gray-900">Image Library</h1>
            </div>
            <button
              onClick={onClose}
              className="text-gray-600 hover:text-gray-900 text-2xl font-bold transition-colors"
            >
              ✕
            </button>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Browse and add images from your library to the canvas
          </p>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading images...</p>
              </div>
            </div>
          ) : images.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <span className="text-6xl">🖼️</span>
                <p className="mt-4 text-gray-600">No images in library</p>
                <p className="text-sm text-gray-500 mt-2">Upload images from the Images panel to see them here</p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {images.map((image) => (
                <div
                  key={image.image_id}
                  className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden group"
                >
                  <div className="aspect-square bg-gray-100 relative overflow-hidden">
                    <AuthenticatedImage
                      src={image.url}
                      alt={image.name}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all flex items-center justify-center gap-2">
                      <button
                        onClick={() => handleAddToCanvas(image)}
                        className="px-3 py-1.5 bg-blue-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity text-sm font-medium"
                      >
                        Add to Canvas
                      </button>
                      <button
                        onClick={() => handleDeleteClick(image)}
                        className="px-3 py-1.5 bg-red-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <div className="p-3">
                    <p className="text-sm font-medium text-gray-900 truncate">{image.name}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(image.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, image: null })}
        onConfirm={confirmDelete}
        title="Delete Image"
        description="This action cannot be undone"
        message={
          deleteDialog.image
            ? `Are you sure you want to delete "${deleteDialog.image.name}"?`
            : ''
        }
        warningMessage="This will permanently delete the image from your library. This action cannot be undone."
        confirmText="Delete Image"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default ImageLibrary;

