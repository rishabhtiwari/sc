import React, { useState, useRef } from 'react';
import { useToast } from '../../../hooks/useToast';
import { imageLibrary } from '../../../services/assetLibraryService';

/**
 * Images Panel
 * Features: Upload images, Stock images, Search
 */
const ImagesPanel = ({ onAddElement, onOpenImageLibrary }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadedImages, setUploadedImages] = useState([]);
  const fileInputRef = useRef(null);
  const { showToast } = useToast();

  // Sample stock images (replace with actual stock image API)
  const stockImages = [
    { id: 1, url: 'https://via.placeholder.com/300x200/3B82F6/FFFFFF?text=Sample+1', title: 'Sample 1' },
    { id: 2, url: 'https://via.placeholder.com/300x200/10B981/FFFFFF?text=Sample+2', title: 'Sample 2' },
    { id: 3, url: 'https://via.placeholder.com/300x200/F59E0B/FFFFFF?text=Sample+3', title: 'Sample 3' },
    { id: 4, url: 'https://via.placeholder.com/300x200/EF4444/FFFFFF?text=Sample+4', title: 'Sample 4' },
  ];

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);

    for (const file of files) {
      if (file.type.startsWith('image/')) {
        try {
          console.log('📤 Uploading image to library:', file.name);

          // Upload to image library
          const libraryResponse = await imageLibrary.upload(file, file.name);

          if (libraryResponse.success && libraryResponse.image) {
            console.log('✅ Image uploaded to library:', libraryResponse.image);

            const newImage = {
              id: libraryResponse.image.image_id,
              url: libraryResponse.image.url, // Use library URL (starts with /api/)
              title: libraryResponse.image.name,
              libraryId: libraryResponse.image.image_id, // Track library ID for deletion
              // No file property - it's in library now
            };

            setUploadedImages(prev => [...prev, newImage]);
            showToast('Image uploaded to library', 'success');
          }
        } catch (error) {
          console.error('❌ Error uploading image to library:', error);

          // Fallback: Add with data URL (old behavior)
          const reader = new FileReader();
          reader.onload = (e) => {
            const newImage = {
              id: `upload-${Date.now()}-${Math.random()}`,
              url: e.target.result,
              title: file.name
            };
            setUploadedImages(prev => [...prev, newImage]);
            showToast('Image uploaded (not saved to library)', 'warning');
          };
          reader.readAsDataURL(file);
        }
      }
    }
  };

  const handleAddImage = (imageUrl) => {
    onAddElement({
      type: 'image',
      src: imageUrl,
      width: 300,
      height: 200
    });
    showToast('Image added to canvas', 'success');
  };

  const handleDeleteImage = async (image, event) => {
    event.stopPropagation(); // Prevent triggering handleAddImage

    try {
      // Delete from backend library if it has a libraryId
      if (image.libraryId) {
        console.log(`🗑️ Deleting image from library: ${image.libraryId}`);
        await imageLibrary.delete(image.libraryId);
        console.log('✅ Deleted from library');
      }

      // Remove from UI state
      setUploadedImages(prev => prev.filter(img => img.id !== image.id));
      showToast('Image deleted', 'success');
    } catch (error) {
      console.error('❌ Error deleting image:', error);
      showToast('Failed to delete image from library', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">🖼️ Images</h3>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileUpload}
          className="hidden"
        />
        {/* Upload and Library buttons side-by-side */}
        <div className="flex gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 px-3 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-1.5 shadow-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Upload
          </button>
          {onOpenImageLibrary && (
            <button
              onClick={onOpenImageLibrary}
              className="flex-1 px-3 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-1.5 shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
              </svg>
              Library
            </button>
          )}
        </div>
        <p className="text-xs text-gray-500 text-center">PNG, JPG, GIF up to 10MB</p>
      </div>

      {/* Uploaded Images */}
      {uploadedImages.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-900">Your Uploads</h3>
          <div className="grid grid-cols-2 gap-3">
            {uploadedImages.map((image) => (
              <div
                key={image.id}
                className="relative group rounded-lg overflow-hidden border border-gray-200 hover:border-blue-500 transition-all"
              >
                <img
                  src={image.url}
                  alt={image.title}
                  className="w-full h-24 object-cover cursor-pointer"
                  onClick={() => handleAddImage(image.url)}
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center gap-2">
                  <button
                    onClick={() => handleAddImage(image.url)}
                    className="px-2 py-1 bg-blue-600 text-white rounded text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    Add
                  </button>
                  <button
                    onClick={(e) => handleDeleteImage(image, e)}
                    className="px-2 py-1 bg-red-600 text-white rounded text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search Stock Images */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Stock Images</h3>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search images..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Stock Images Grid */}
      <div className="grid grid-cols-2 gap-3">
        {stockImages.map((image) => (
          <div
            key={image.id}
            onClick={() => handleAddImage(image.url)}
            className="relative group cursor-pointer rounded-lg overflow-hidden border border-gray-200 hover:border-blue-500 transition-all"
          >
            <img
              src={image.url}
              alt={image.title}
              className="w-full h-24 object-cover"
            />
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center">
              <span className="text-white opacity-0 group-hover:opacity-100 text-sm font-medium">
                Add to canvas
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ImagesPanel;

