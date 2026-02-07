import React, { useState, useEffect } from 'react';
import { Modal, Button } from '../common';
import { SOCIAL_PLATFORMS } from '../../services/socialMediaService';

/**
 * Master App Form Component
 * Modal form for creating/editing master apps
 */
const MasterAppForm = ({ isOpen, onClose, onSave, masterApp, platformId }) => {
  const [formData, setFormData] = useState({
    platform: platformId || 'instagram',
    app_name: '',
    app_id: '',
    app_secret: '',
    redirect_uri: 'http://localhost:8080/api/social-media/instagram/oauth/callback',
    scopes: [],
    is_active: true,
    metadata: {
      environment: 'production',
      description: '',
      notes: ''
    }
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (masterApp) {
      // Edit mode - populate form with existing data
      setFormData({
        platform: masterApp.platform,
        app_name: masterApp.app_name,
        app_id: masterApp.app_id,
        app_secret: '', // Don't populate secret for security
        redirect_uri: masterApp.redirect_uri,
        scopes: masterApp.scopes || [],
        is_active: masterApp.is_active,
        metadata: masterApp.metadata || { environment: 'production', description: '', notes: '' }
      });
    } else if (platformId) {
      // Create mode - set defaults for platform
      const platform = SOCIAL_PLATFORMS[platformId];
      setFormData(prev => ({
        ...prev,
        platform: platformId,
        scopes: platform?.defaultScopes || [],
        redirect_uri: `http://localhost:8080/api/social-media/${platformId}/oauth/callback`
      }));
    }
  }, [masterApp, platformId]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleMetadataChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      metadata: { ...prev.metadata, [field]: value }
    }));
  };

  const handleScopeToggle = (scope) => {
    setFormData(prev => ({
      ...prev,
      scopes: prev.scopes.includes(scope)
        ? prev.scopes.filter(s => s !== scope)
        : [...prev.scopes, scope]
    }));
  };

  const validate = () => {
    const newErrors = {};
    
    if (!formData.app_name.trim()) {
      newErrors.app_name = 'App name is required';
    }
    
    if (!formData.app_id.trim()) {
      newErrors.app_id = 'App ID is required';
    }
    
    if (!masterApp && !formData.app_secret.trim()) {
      newErrors.app_secret = 'App secret is required';
    }
    
    if (!formData.redirect_uri.trim()) {
      newErrors.redirect_uri = 'Redirect URI is required';
    }
    
    if (formData.scopes.length === 0) {
      newErrors.scopes = 'At least one scope is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }
    
    setLoading(true);
    try {
      // Don't send empty app_secret in edit mode
      const dataToSend = { ...formData };
      if (masterApp && !dataToSend.app_secret) {
        delete dataToSend.app_secret;
      }
      
      await onSave(dataToSend);
      onClose();
    } catch (error) {
      console.error('Error saving master app:', error);
      setErrors({ submit: error.response?.data?.error || 'Failed to save master app' });
    } finally {
      setLoading(false);
    }
  };

  const platform = SOCIAL_PLATFORMS[formData.platform];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={masterApp ? `Edit ${platform?.name} App` : `Create ${platform?.name} Master App`}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* App Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            App Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.app_name}
            onChange={(e) => handleChange('app_name', e.target.value)}
            placeholder="e.g., Production Instagram App"
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
              errors.app_name ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.app_name && <p className="text-red-500 text-xs mt-1">{errors.app_name}</p>}
        </div>

        {/* App ID */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {platform?.name} App ID <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.app_id}
            onChange={(e) => handleChange('app_id', e.target.value)}
            placeholder={platform?.id === 'instagram' ? 'Facebook App ID' : 'App ID'}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm ${
              errors.app_id ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.app_id && <p className="text-red-500 text-xs mt-1">{errors.app_id}</p>}
        </div>

        {/* App Secret */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {platform?.name} App Secret {!masterApp && <span className="text-red-500">*</span>}
          </label>
          <input
            type="password"
            value={formData.app_secret}
            onChange={(e) => handleChange('app_secret', e.target.value)}
            placeholder={masterApp ? 'Leave blank to keep existing secret' : 'App Secret'}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm ${
              errors.app_secret ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.app_secret && <p className="text-red-500 text-xs mt-1">{errors.app_secret}</p>}
          {masterApp && (
            <p className="text-xs text-gray-500 mt-1">
              Leave blank to keep the existing secret. Enter a new value to update it.
            </p>
          )}
        </div>

        {/* Redirect URI */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            OAuth Redirect URI <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.redirect_uri}
            onChange={(e) => handleChange('redirect_uri', e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-xs ${
              errors.redirect_uri ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.redirect_uri && <p className="text-red-500 text-xs mt-1">{errors.redirect_uri}</p>}
        </div>

        {/* Scopes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            OAuth Scopes <span className="text-red-500">*</span>
          </label>
          <div className="space-y-2 max-h-40 overflow-y-auto border border-gray-200 rounded-lg p-3">
            {platform?.defaultScopes.map((scope) => (
              <label key={scope} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.scopes.includes(scope)}
                  onChange={() => handleScopeToggle(scope)}
                  className="rounded text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{scope}</span>
              </label>
            ))}
          </div>
          {errors.scopes && <p className="text-red-500 text-xs mt-1">{errors.scopes}</p>}
        </div>

        {/* Environment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Environment
          </label>
          <select
            value={formData.metadata.environment}
            onChange={(e) => handleMetadataChange('environment', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="production">Production</option>
            <option value="staging">Staging</option>
            <option value="development">Development</option>
          </select>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={formData.metadata.description}
            onChange={(e) => handleMetadataChange('description', e.target.value)}
            placeholder="Optional description for this app"
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Active Status */}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_active"
            checked={formData.is_active}
            onChange={(e) => handleChange('is_active', e.target.checked)}
            className="rounded text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="is_active" className="text-sm text-gray-700">
            Set as active app (will deactivate other apps for this platform)
          </label>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <span className="text-blue-600">ℹ️</span>
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Encryption & Security</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>App secret will be encrypted automatically using your customer-specific encryption key</li>
                <li>Encryption key is auto-generated if this is your first master app</li>
                <li>All user access tokens will be encrypted with the same key</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {errors.submit && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
            {errors.submit}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : masterApp ? 'Update App' : 'Create App'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default MasterAppForm;

