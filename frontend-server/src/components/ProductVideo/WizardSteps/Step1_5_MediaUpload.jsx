import React, { useState, useEffect } from 'react';
import { Button, AuthenticatedImage } from '../../common';
import { productService } from '../../../services';
import { useToast } from '../../../hooks/useToast';

/**
 * Step 1.5: Media Upload - Upload product images/videos
 */
const Step1_5_MediaUpload = ({ formData, onComplete, onUpdate }) => {
  console.log('📸 Step1_5_MediaUpload - formData:', formData);
  console.log('📸 Step1_5_MediaUpload - formData.media_files:', formData.media_files);

  const [mediaFiles, setMediaFiles] = useState(formData.media_files || []);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [urlInput, setUrlInput] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const { showToast } = useToast();

  console.log('📸 Initial mediaFiles state:', mediaFiles);

  // Cleanup blob URLs when component unmounts
  useEffect(() => {
    return () => {
      mediaFiles.forEach(file => {
        if (file?.url?.startsWith('blob:')) {
          try {
            URL.revokeObjectURL(file.url);
            console.log('🧹 Cleanup: Revoked blob URL on unmount:', file.url);
          } catch (error) {
            console.warn('Failed to revoke blob URL on unmount:', error);
          }
        }
      });
    };
  }, [mediaFiles]);

  const handleAddUrl = () => {
    if (!urlInput.trim()) {
      showToast('Please enter a valid URL', 'error');
      return;
    }

    // Basic URL validation
    try {
      new URL(urlInput);
    } catch (e) {
      showToast('Please enter a valid URL', 'error');
      return;
    }

    // Determine type from URL extension
    const url = urlInput.trim();
    const extension = url.split('.').pop().toLowerCase();
    const imageExtensions = ['jpg', 'jpeg', 'png', 'webp', 'gif'];
    const videoExtensions = ['mp4', 'webm', 'mov'];

    let type = 'image';
    if (videoExtensions.includes(extension)) {
      type = 'video';
    }

    const newFile = {
      url: url,
      type: type,
      name: url.split('/').pop()
    };

    const updatedMediaFiles = [...mediaFiles, newFile];
    setMediaFiles(updatedMediaFiles);
    onUpdate({ media_files: updatedMediaFiles });

    setUrlInput('');
    showToast('Media URL added successfully', 'success');
  };

  const handleFileSelect = async (event) => {
    const files = Array.from(event.target.files);

    if (files.length === 0) return;

    // Validate file types
    const validImageTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
    const validVideoTypes = ['video/mp4', 'video/webm', 'video/mov', 'video/quicktime'];
    const validTypes = [...validImageTypes, ...validVideoTypes];

    const invalidFiles = files.filter(file => !validTypes.includes(file.type));

    if (invalidFiles.length > 0) {
      showToast('Invalid file type. Please upload images (JPG, PNG, WEBP, GIF) or videos (MP4, WEBM, MOV)', 'error');
      return;
    }

    // Check total file count
    if (mediaFiles.length + files.length > 20) {
      showToast('Maximum 20 files allowed', 'error');
      return;
    }

    try {
      setUploading(true);

      // Create preview URLs and keep file references
      const newFiles = files.map(file => {
        const type = validImageTypes.includes(file.type) ? 'image' : 'video';
        return {
          url: URL.createObjectURL(file),
          type: type,
          name: file.name,
          file: file // Keep reference to actual file for upload
        };
      });

      const updatedMediaFiles = [...mediaFiles, ...newFiles];
      setMediaFiles(updatedMediaFiles);
      onUpdate({ media_files: updatedMediaFiles });

      showToast(`${files.length} file(s) added successfully`, 'success');
    } catch (error) {
      console.error('Error handling file upload:', error);
      showToast('Failed to add files', 'error');
    } finally {
      setUploading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  const handleRemoveFile = (index) => {
    const fileToRemove = mediaFiles[index];

    // If it's a blob URL (newly uploaded file), revoke it to free memory
    if (fileToRemove?.url?.startsWith('blob:')) {
      try {
        URL.revokeObjectURL(fileToRemove.url);
        console.log('🗑️ Revoked blob URL:', fileToRemove.url);
      } catch (error) {
        console.warn('Failed to revoke blob URL:', error);
      }
    }

    const updatedFiles = mediaFiles.filter((_, i) => i !== index);
    setMediaFiles(updatedFiles);
    onUpdate({ media_files: updatedFiles });
  };

  const handleReorder = (index, direction) => {
    const newFiles = [...mediaFiles];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (targetIndex < 0 || targetIndex >= newFiles.length) return;
    
    [newFiles[index], newFiles[targetIndex]] = [newFiles[targetIndex], newFiles[index]];
    setMediaFiles(newFiles);
    onUpdate({ media_files: newFiles });
  };

  const handleNext = async () => {
    if (mediaFiles.length === 0) {
      showToast('Please upload at least one product image or video', 'error');
      return;
    }

    try {
      setUploading(true);

      console.log('📤 handleNext - Total media files:', mediaFiles.length);
      console.log('📤 Media files structure:', mediaFiles);

      // Separate files with actual File objects from URL-only entries
      const filesWithObjects = mediaFiles.filter(f => f.file);
      const urlOnlyFiles = mediaFiles.filter(f => !f.file && f.url && !f.url.startsWith('blob:'));

      console.log('📤 Files with File objects:', filesWithObjects.length, filesWithObjects);
      console.log('📤 URL-only files:', urlOnlyFiles.length, urlOnlyFiles);

      let allServerUrls = [];

      // Upload actual files first and get server URLs
      if (filesWithObjects.length > 0) {
        const actualFiles = filesWithObjects.map(f => f.file);
        console.log('📤 Uploading actual files:', actualFiles);
        const response = await productService.uploadMedia(formData.product_id, actualFiles);
        if (response.data && response.data.all_media_urls) {
          allServerUrls = response.data.all_media_urls;
          console.log('✅ Got server URLs:', allServerUrls);
        }
      }

      // Then save URL-only entries (if any)
      if (urlOnlyFiles.length > 0) {
        const urls = urlOnlyFiles.map(f => f.url);
        console.log('📤 Uploading URL-only files:', urls);
        const response = await productService.uploadMedia(formData.product_id, urls);
        if (response.data && response.data.all_media_urls) {
          allServerUrls = response.data.all_media_urls;
          console.log('✅ Got server URLs:', allServerUrls);
        }
      }

      // Convert server URLs to media_files format
      const serverMediaFiles = allServerUrls.map((url, index) => {
        const extension = url.split('.').pop().toLowerCase().split('?')[0];
        const videoExtensions = ['mp4', 'webm', 'mov'];
        const type = videoExtensions.includes(extension) ? 'video' : 'image';

        return {
          url: url,
          type: type,
          name: url.split('/').pop().split('?')[0] || `media-${index + 1}`
        };
      });

      console.log('✅ Final media files with server URLs:', serverMediaFiles);

      showToast('Media saved successfully', 'success');
      onComplete({ media_files: serverMediaFiles });

    } catch (error) {
      console.error('Error saving media:', error);
      showToast('Failed to save media files', 'error');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">📸 Product Media</h3>
        <p className="text-gray-600">Upload images and videos of your product</p>
      </div>

      {/* Upload Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* File Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-indigo-500 transition-colors">
          <input
            type="file"
            id="media-upload"
            multiple
            accept="image/jpeg,image/jpg,image/png,image/webp,video/mp4,video/webm"
            onChange={handleFileSelect}
            className="hidden"
            disabled={uploading}
          />
          <label
            htmlFor="media-upload"
            className="cursor-pointer flex flex-col items-center"
          >
            <div className="text-5xl mb-3">📁</div>
            <p className="text-base font-medium text-gray-700 mb-1">
              Upload Files
            </p>
            <p className="text-xs text-gray-500">
              Click to browse
            </p>
          </label>
        </div>

        {/* URL Input */}
        <div className="border-2 border-dashed border-indigo-300 rounded-lg p-6 text-center hover:border-indigo-500 transition-colors bg-indigo-50">
          <div className="flex flex-col items-center">
            <div className="text-5xl mb-3">🔗</div>
            <p className="text-base font-medium text-gray-700 mb-3">
              Add from URL
            </p>
            <button
              onClick={() => setShowUrlInput(!showUrlInput)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
            >
              {showUrlInput ? 'Hide' : 'Add URL'}
            </button>
          </div>
        </div>
      </div>

      {/* URL Input Form */}
      {showUrlInput && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Image or Video URL
          </label>
          <div className="flex gap-2">
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddUrl()}
              placeholder="https://example.com/product-image.jpg"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <Button
              variant="primary"
              onClick={handleAddUrl}
              disabled={!urlInput.trim()}
            >
              Add
            </Button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            💡 Paste a direct link to an image (JPG, PNG, WEBP) or video (MP4, WEBM)
          </p>
        </div>
      )}

      {/* Upload Progress */}
      {uploading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="animate-spin text-2xl">⏳</div>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900">
                Uploading {uploadProgress.fileName}...
              </p>
              <p className="text-xs text-blue-700">
                File {uploadProgress.current} of {uploadProgress.total}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Uploaded Files */}
      {mediaFiles.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-gray-900">
              Uploaded Media ({mediaFiles.length})
            </h4>
            <p className="text-xs text-gray-500">
              💡 Drag to reorder - images will show in this order
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {mediaFiles.map((file, index) => (
              <div
                key={index}
                className="relative group border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
              >
                {/* Preview */}
                <div className="aspect-square bg-gray-100">
                  {file.type === 'image' ? (
                    <AuthenticatedImage
                      src={file.url}
                      alt={file.name || `Product ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gray-800 text-white">
                      <div className="text-center">
                        <div className="text-4xl mb-2">🎥</div>
                        <p className="text-xs">Video</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Order Badge */}
                <div className="absolute top-2 left-2 bg-indigo-600 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                  {index + 1}
                </div>

                {/* Actions */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
                  {/* Move Up */}
                  {index > 0 && (
                    <button
                      onClick={() => handleReorder(index, 'up')}
                      className="bg-white text-gray-700 rounded-full p-2 hover:bg-gray-100 transition-colors"
                      title="Move up"
                    >
                      ↑
                    </button>
                  )}

                  {/* Move Down */}
                  {index < mediaFiles.length - 1 && (
                    <button
                      onClick={() => handleReorder(index, 'down')}
                      className="bg-white text-gray-700 rounded-full p-2 hover:bg-gray-100 transition-colors"
                      title="Move down"
                    >
                      ↓
                    </button>
                  )}

                  {/* Remove */}
                  <button
                    onClick={() => handleRemoveFile(index)}
                    className="bg-red-500 text-white rounded-full p-2 hover:bg-red-600 transition-colors"
                    title="Remove"
                  >
                    ✕
                  </button>
                </div>

                {/* File Name */}
                <div className="p-2 bg-white">
                  <p className="text-xs text-gray-600 truncate" title={file.name}>
                    {file.name || `File ${index + 1}`}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">💡</span>
          <div className="flex-1 text-sm text-blue-900">
            <p className="font-medium mb-1">Tips for best results:</p>
            <ul className="list-disc list-inside space-y-1 text-blue-800">
              <li>Upload high-quality images (at least 1080p)</li>
              <li>Use images with good lighting and clear product visibility</li>
              <li>The order of images matters - they'll appear sequentially in your video</li>
              <li>First image will be used as the video thumbnail</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleNext}
          disabled={uploading || mediaFiles.length === 0}
        >
          Next: Generate AI Summary →
        </Button>
      </div>
    </div>
  );
};

export default Step1_5_MediaUpload;

