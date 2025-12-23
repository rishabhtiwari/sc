import React, { useState, useRef } from 'react';
import { Button } from '../../common';
import { productService } from '../../../services';
import { useToast } from '../../../hooks/useToast';

/**
 * Step 3: Media Upload
 */
const Step3_MediaUpload = ({ formData, onComplete, onUpdate }) => {
  const [mediaFiles, setMediaFiles] = useState(formData.media_files || []);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const { showToast } = useToast();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  const handleFiles = async (files) => {
    if (!formData.product_id) {
      showToast('Product ID not found', 'error');
      return;
    }

    // Validate file types
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/quicktime'];
    const invalidFiles = Array.from(files).filter(file => !validTypes.includes(file.type));
    
    if (invalidFiles.length > 0) {
      showToast('Only images (JPG, PNG, GIF) and videos (MP4, MOV) are allowed', 'error');
      return;
    }

    // Check total file count
    if (mediaFiles.length + files.length > 10) {
      showToast('Maximum 10 files allowed', 'error');
      return;
    }

    try {
      setUploading(true);
      const response = await productService.uploadMedia(formData.product_id, files);
      
      if (response.data.status === 'success') {
        const newFiles = response.data.media_files;
        setMediaFiles([...mediaFiles, ...newFiles]);
        showToast(`${newFiles.length} file(s) uploaded successfully`, 'success');
      }
    } catch (error) {
      console.error('Error uploading media:', error);
      showToast('Failed to upload media files', 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleRemove = (index) => {
    const newFiles = mediaFiles.filter((_, i) => i !== index);
    setMediaFiles(newFiles);
  };

  const handleNext = () => {
    if (mediaFiles.length === 0) {
      showToast('Please upload at least one media file', 'error');
      return;
    }

    onComplete({ media_files: mediaFiles });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">🖼️ Media Upload</h3>
        <p className="text-gray-600">Upload images or videos for your product</p>
      </div>

      {/* Drag & Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-gray-300 hover:border-indigo-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,video/*"
          onChange={handleFileInput}
          className="hidden"
        />

        <div className="text-6xl mb-4">📤</div>
        <h4 className="text-lg font-semibold text-gray-900 mb-2">
          Drag & drop files here
        </h4>
        <p className="text-gray-600 mb-4">or</p>
        <Button
          variant="primary"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          loading={uploading}
        >
          Browse Files
        </Button>
        <p className="text-sm text-gray-500 mt-4">
          Supported: JPG, PNG, GIF, MP4, MOV (Max 10 files)
        </p>
      </div>

      {/* Uploaded Files Grid */}
      {mediaFiles.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 mb-3">
            Uploaded Files ({mediaFiles.length}/10)
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {mediaFiles.map((file, index) => (
              <div key={index} className="relative group">
                <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                  {file.type === 'image' ? (
                    <img
                      src={file.url}
                      alt={file.filename}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <span className="text-4xl">🎥</span>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => handleRemove(index)}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  ✕
                </button>
                <p className="text-xs text-gray-600 mt-1 truncate">{file.filename}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleNext}
          disabled={mediaFiles.length === 0}
        >
          Next: Select Audio →
        </Button>
      </div>
    </div>
  );
};

export default Step3_MediaUpload;

