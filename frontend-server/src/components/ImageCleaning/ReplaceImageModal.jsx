import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import Button from '../common/Button';

/**
 * ReplaceImageModal - Modal for replacing image URL
 */
const ReplaceImageModal = ({ isOpen, onClose, currentUrl, onReplace }) => {
  const [newUrl, setNewUrl] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setNewUrl(currentUrl || '');
      setError('');
    }
  }, [isOpen, currentUrl]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate URL
    if (!newUrl || newUrl.trim() === '') {
      setError('Please enter a valid URL');
      return;
    }

    if (newUrl.trim() === currentUrl) {
      setError('New URL is the same as current URL');
      return;
    }

    // Call the replace handler
    onReplace(newUrl.trim());
  };

  const handleCancel = () => {
    setNewUrl('');
    setError('');
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleCancel} title="Replace Image URL" size="lg">
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          {/* Current URL Display */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Current Image URL
            </label>
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <p className="text-sm text-gray-600 break-all">
                {currentUrl || 'No URL available'}
              </p>
            </div>
          </div>

          {/* New URL Input */}
          <div>
            <label htmlFor="newImageUrl" className="block text-sm font-medium text-gray-700 mb-2">
              New Image URL <span className="text-red-500">*</span>
            </label>
            <input
              id="newImageUrl"
              type="url"
              value={newUrl}
              onChange={(e) => {
                setNewUrl(e.target.value);
                setError('');
              }}
              placeholder="https://example.com/image.jpg"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoFocus
            />
            {error && (
              <p className="mt-2 text-sm text-red-600">{error}</p>
            )}
          </div>

          {/* Info Message */}
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              ℹ️ This will replace the original image URL in the database. You can manually clean the new image later if needed.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={handleCancel}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
            >
              Replace Image
            </Button>
          </div>
        </div>
      </form>
    </Modal>
  );
};

export default ReplaceImageModal;

