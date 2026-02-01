import React, { useState, useRef } from 'react';
import { useToast } from '../../../hooks/useToast';

/**
 * Images Panel
 * Features: Upload images, Stock images, Search
 */
const ImagesPanel = ({ onAddElement }) => {
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

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    
    files.forEach((file) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const newImage = {
            id: `upload-${Date.now()}-${Math.random()}`,
            url: e.target.result,
            title: file.name
          };
          setUploadedImages(prev => [...prev, newImage]);
          showToast('Image uploaded successfully', 'success');
        };
        reader.readAsDataURL(file);
      }
    });
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

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">📤 Upload Images</h3>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileUpload}
          className="hidden"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-2 shadow-sm"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Upload Image
        </button>
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

