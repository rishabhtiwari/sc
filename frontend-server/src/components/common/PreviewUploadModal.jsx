import React, { useState, useEffect } from 'react';
import { Modal } from './index';
import { PLATFORMS, getConnectedAccounts, uploadToPlatform } from '../../services/uploadService';
import { useToast } from '../../hooks/useToast';

/**
 * Preview and Upload Modal
 * Multi-step modal for previewing content and uploading to social media platforms
 * 
 * Steps:
 * 1. Preview - Show video/image preview
 * 2. Platform Selection - Choose platform and account
 * 3. Upload - Configure metadata and upload
 */
const PreviewUploadModal = ({ isOpen, onClose, asset }) => {
  const { showToast } = useToast();
  const [step, setStep] = useState(1); // 1: Preview, 2: Platform Selection, 3: Upload
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Upload form data
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    tags: [],
    caption: '',
    privacy: 'public',
    category: '22' // Default: People & Blogs
  });

  useEffect(() => {
    if (isOpen && asset) {
      // Reset state when modal opens
      setStep(1);
      setSelectedPlatform(null);
      setSelectedAccount(null);
      setFormData({
        title: asset.name || asset.title || '',
        description: asset.description || '',
        tags: asset.tags || [],
        caption: '',
        privacy: 'public',
        category: '22'
      });
    }
  }, [isOpen, asset]);

  const handlePlatformSelect = async (platform) => {
    setSelectedPlatform(platform);
    setLoading(true);
    
    try {
      const connectedAccounts = await getConnectedAccounts(platform.id);
      setAccounts(connectedAccounts);
      
      if (connectedAccounts.length === 0) {
        showToast(`No ${platform.name} accounts connected. Please connect an account first.`, 'warning');
        return;
      }
      
      // Auto-select first account if only one
      if (connectedAccounts.length === 1) {
        setSelectedAccount(connectedAccounts[0]);
      }
      
      setStep(3); // Go to upload step
    } catch (error) {
      console.error('Failed to load accounts:', error);
      showToast(`Failed to load ${platform.name} accounts`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedAccount) {
      showToast('Please select an account', 'warning');
      return;
    }

    setLoading(true);
    setUploadProgress(0);

    try {
      const uploadParams = {
        credentialId: selectedAccount.credential_id || selectedAccount._id,
        ...formData
      };

      // Add platform-specific fields
      if (selectedPlatform.id === 'youtube') {
        uploadParams.videoPath = asset.url || asset.video_url;
        uploadParams.categoryId = formData.category;
        uploadParams.privacyStatus = formData.privacy;
      } else if (selectedPlatform.id === 'instagram') {
        uploadParams.mediaUrl = asset.url || asset.video_url;
        uploadParams.caption = formData.caption;
        uploadParams.mediaType = asset.type === 'video' ? 'VIDEO' : 'IMAGE';
      }

      // Simulate progress (in real implementation, use upload progress events)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const result = await uploadToPlatform(selectedPlatform.id, uploadParams);

      clearInterval(progressInterval);
      setUploadProgress(100);

      showToast(`Successfully uploaded to ${selectedPlatform.name}!`, 'success');
      
      // Close modal after short delay
      setTimeout(() => {
        onClose();
      }, 1500);

    } catch (error) {
      console.error('Upload failed:', error);
      showToast(error.message || 'Upload failed', 'error');
      setUploadProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (step === 3) {
      setStep(2);
      setSelectedAccount(null);
    } else if (step === 2) {
      setStep(1);
      setSelectedPlatform(null);
    }
  };

  if (!asset) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={step === 1 ? 'Preview' : step === 2 ? 'Select Platform' : `Upload to ${selectedPlatform?.name}`}
      size="large"
    >
      {/* Step 1: Preview */}
      {step === 1 && (
        <div className="space-y-4">
          {/* Preview Area */}
          <div className="bg-black rounded-lg overflow-hidden aspect-video flex items-center justify-center">
            {asset.preview_url || asset.url || asset.video_url ? (
              asset.type === 'video' || asset.video_url ? (
                <video
                  src={asset.preview_url || asset.url || asset.video_url}
                  controls
                  className="w-full h-full"
                />
              ) : (
                <img
                  src={asset.preview_url || asset.url}
                  alt={asset.name}
                  className="w-full h-full object-contain"
                />
              )
            ) : (
              <div className="text-white text-center">
                <p className="text-lg">No preview available</p>
              </div>
            )}
          </div>

          {/* Asset Info */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">{asset.name || asset.title || 'Untitled'}</h3>
            {asset.description && (
              <p className="text-sm text-gray-600">{asset.description}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => setStep(2)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <span>Upload to Platform</span>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Platform Selection */}
      {step === 2 && (
        <div className="space-y-4">
          <p className="text-gray-600 mb-4">Choose a platform to upload your content</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.values(PLATFORMS).map((platform) => (
              <button
                key={platform.id}
                onClick={() => handlePlatformSelect(platform)}
                disabled={loading}
                className={`p-6 border-2 rounded-xl hover:border-blue-500 hover:shadow-lg transition-all text-left group ${
                  loading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-16 h-16 rounded-xl bg-gradient-to-br ${platform.color} flex items-center justify-center text-3xl shadow-lg`}>
                    {platform.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                      {platform.name}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      Upload to {platform.name}
                    </p>
                  </div>
                  <svg className="w-6 h-6 text-gray-400 group-hover:text-blue-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            ))}
          </div>

          <div className="flex justify-between pt-4">
            <button
              onClick={handleBack}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Upload Configuration */}
      {step === 3 && selectedPlatform && (
        <div className="space-y-4">
          {/* Account Selection */}
          {accounts.length > 1 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Account
              </label>
              <select
                value={selectedAccount?._id || selectedAccount?.credential_id || ''}
                onChange={(e) => {
                  const account = accounts.find(a => (a._id || a.credential_id) === e.target.value);
                  setSelectedAccount(account);
                }}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Choose an account...</option>
                {accounts.map((account) => (
                  <option key={account._id || account.credential_id} value={account._id || account.credential_id}>
                    {account.channel_title || account.account_name || account.email || 'Account'}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* YouTube-specific fields */}
          {selectedPlatform.id === 'youtube' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  maxLength={100}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter video title"
                />
                <p className="text-xs text-gray-500 mt-1">{formData.title.length}/100 characters</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  maxLength={5000}
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter video description"
                />
                <p className="text-xs text-gray-500 mt-1">{formData.description.length}/5000 characters</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Privacy
                  </label>
                  <select
                    value={formData.privacy}
                    onChange={(e) => setFormData({ ...formData, privacy: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="public">Public</option>
                    <option value="unlisted">Unlisted</option>
                    <option value="private">Private</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="22">People & Blogs</option>
                    <option value="25">News & Politics</option>
                    <option value="24">Entertainment</option>
                    <option value="10">Music</option>
                    <option value="17">Sports</option>
                    <option value="20">Gaming</option>
                    <option value="28">Science & Technology</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {/* Instagram-specific fields */}
          {selectedPlatform.id === 'instagram' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Caption
              </label>
              <textarea
                value={formData.caption}
                onChange={(e) => setFormData({ ...formData, caption: e.target.value })}
                maxLength={2200}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Write a caption..."
              />
              <p className="text-xs text-gray-500 mt-1">{formData.caption.length}/2200 characters</p>
            </div>
          )}

          {/* Upload Progress */}
          {loading && uploadProgress > 0 && (
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-blue-900">Uploading...</span>
                <span className="text-sm font-medium text-blue-900">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between pt-4">
            <button
              onClick={handleBack}
              disabled={loading}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back
            </button>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                disabled={loading}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={loading || !selectedAccount || (selectedPlatform.id === 'youtube' && !formData.title)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Uploading...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <span>Upload</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default PreviewUploadModal;

