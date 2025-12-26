import React, { useState, useCallback } from 'react';
import { Button, AuthenticatedImage, AuthenticatedVideo } from '../';
import { useToast } from '../../../hooks/useToast';
import api from '../../../services/api';

/**
 * Generic Media Uploader Component
 * Handles image and video uploads with preview
 * 
 * @param {Object} props
 * @param {Array} props.initialFiles - Initial media files [{type: 'image'|'video', url: '...'}]
 * @param {Function} props.onFilesChange - Callback when files change
 * @param {string} props.uploadEndpoint - API endpoint for file upload
 * @param {Array} props.acceptedTypes - Accepted file types ['image', 'video']
 * @param {number} props.maxFiles - Maximum number of files
 * @param {number} props.maxFileSize - Maximum file size in MB
 * @param {boolean} props.showPreview - Show file previews
 * @param {string} props.className - Additional CSS classes
 */
const MediaUploader = ({
  initialFiles = [],
  onFilesChange,
  uploadEndpoint = '/api/upload',
  acceptedTypes = ['image', 'video'],
  maxFiles = 10,
  maxFileSize = 100, // MB
  showPreview = true,
  className = ''
}) => {
  const [files, setFiles] = useState(initialFiles);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [deletingIndices, setDeletingIndices] = useState(new Set());
  const { showToast } = useToast();

  /**
   * Handle file selection
   */
  const handleFileSelect = async (event) => {
    const selectedFiles = Array.from(event.target.files);
    
    // Validate file count
    if (files.length + selectedFiles.length > maxFiles) {
      showToast(`Maximum ${maxFiles} files allowed`, 'error');
      return;
    }

    // Validate file sizes
    const oversizedFiles = selectedFiles.filter(
      file => file.size > maxFileSize * 1024 * 1024
    );
    
    if (oversizedFiles.length > 0) {
      showToast(`Some files exceed ${maxFileSize}MB limit`, 'error');
      return;
    }

    // Upload files
    setUploading(true);
    const uploadedFiles = [];

    for (const file of selectedFiles) {
      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post(uploadEndpoint, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(prev => ({
              ...prev,
              [file.name]: progress
            }));
          }
        });

        if (response.data.status === 'success') {
          const fileType = file.type.startsWith('image/') ? 'image' : 'video';
          uploadedFiles.push({
            type: fileType,
            url: response.data.url || response.data.file_url,
            name: file.name,
            size: file.size
          });
        }
      } catch (error) {
        console.error('Upload error:', error);
        showToast(`Failed to upload ${file.name}`, 'error');
      }
    }

    // Update files
    const newFiles = [...files, ...uploadedFiles];
    setFiles(newFiles);
    
    if (onFilesChange) {
      onFilesChange(newFiles);
    }

    setUploading(false);
    setUploadProgress({});
    
    if (uploadedFiles.length > 0) {
      showToast(`${uploadedFiles.length} file(s) uploaded successfully`, 'success');
    }
  };

  /**
   * Handle file deletion
   */
  const handleFileDelete = (index) => {
    setDeletingIndices(prev => new Set(prev).add(index));
    
    setTimeout(() => {
      const newFiles = files.filter((_, i) => i !== index);
      setFiles(newFiles);
      
      if (onFilesChange) {
        onFilesChange(newFiles);
      }
      
      setDeletingIndices(prev => {
        const next = new Set(prev);
        next.delete(index);
        return next;
      });
    }, 300);
  };

  /**
   * Get accept attribute for file input
   */
  const getAcceptAttribute = () => {
    const types = [];
    if (acceptedTypes.includes('image')) {
      types.push('image/*');
    }
    if (acceptedTypes.includes('video')) {
      types.push('video/*');
    }
    return types.join(',');
  };

  return (
    <div className={`media-uploader ${className}`}>
      {/* Upload Button */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Media Files ({files.length}/{maxFiles})
        </label>
        
        <input
          type="file"
          multiple
          accept={getAcceptAttribute()}
          onChange={handleFileSelect}
          disabled={uploading || files.length >= maxFiles}
          className="hidden"
          id="media-upload-input"
        />
        
        <label
          htmlFor="media-upload-input"
          className={`inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg cursor-pointer ${
            uploading || files.length >= maxFiles
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          <span className="mr-2">📁</span>
          {uploading ? 'Uploading...' : 'Upload Files'}
        </label>
        
        <p className="text-xs text-gray-500 mt-1">
          Accepted: {acceptedTypes.join(', ')} • Max size: {maxFileSize}MB
        </p>
      </div>

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="mb-4 space-y-2">
          {Object.entries(uploadProgress).map(([filename, progress]) => (
            <div key={filename} className="flex items-center gap-2">
              <span className="text-sm text-gray-600 flex-1 truncate">{filename}</span>
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-indigo-600 h-2 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-sm text-gray-600">{progress}%</span>
            </div>
          ))}
        </div>
      )}

      {/* File Preview Grid */}
      {showPreview && files.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {files.map((file, index) => (
            <div
              key={index}
              className={`relative border border-gray-300 rounded-lg overflow-hidden transition-all ${
                deletingIndices.has(index) ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
              }`}
            >
              {/* Preview */}
              <div className="aspect-square bg-gray-100">
                {file.type === 'image' ? (
                  <AuthenticatedImage
                    src={file.url}
                    alt={file.name || `Image ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <AuthenticatedVideo
                    src={file.url}
                    className="w-full h-full object-cover"
                  />
                )}
              </div>
              
              {/* Delete Button */}
              <button
                onClick={() => handleFileDelete(index)}
                className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600 transition-colors"
                title="Delete"
              >
                ×
              </button>
              
              {/* File Type Badge */}
              <div className="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
                {file.type}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {files.length === 0 && !uploading && (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-500">
          <div className="text-4xl mb-2">📁</div>
          <p>No files uploaded yet</p>
          <p className="text-sm">Click "Upload Files" to add media</p>
        </div>
      )}
    </div>
  );
};

export default MediaUploader;

