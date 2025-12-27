import React, { useState, useEffect } from 'react';
import { Card, Button, ConfirmDialog } from '../common';
import { useToast } from '../../hooks/useToast';
import api from '../../services/api';

/**
 * Credentials Manager Component - Manage YouTube OAuth credentials
 */
const CredentialsManager = () => {
  const [credentials, setCredentials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authCode, setAuthCode] = useState('');
  const [authenticatingCredentialId, setAuthenticatingCredentialId] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, credential: null });
  const { showToast } = useToast();

  const [formData, setFormData] = useState({
    name: '',
    client_id: '',
    client_secret: '',
    project_id: '',
    channel_id: '',
    channel_name: '',
    is_active: false,
    notes: ''
  });

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    try {
      setLoading(true);
      const response = await api.get('/youtube/credentials');
      const data = response.data;

      if (data.status === 'success') {
        setCredentials(data.data || []);
      } else {
        showToast('Failed to load credentials', 'error');
      }
    } catch (error) {
      console.error('Error loading credentials:', error);
      showToast('Error loading credentials', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate required fields
    if (!formData.name || !formData.client_id || !formData.client_secret || !formData.project_id) {
      showToast('Please fill in all required fields', 'error');
      return;
    }

    try {
      const response = editingId
        ? await api.put(`/youtube/credentials/${editingId}`, formData)
        : await api.post('/youtube/credentials', formData);

      const data = response.data;

      if (data.status === 'success') {
        showToast(editingId ? 'Credential updated successfully' : 'Credential created successfully', 'success');
        setShowForm(false);
        setEditingId(null);
        resetForm();
        loadCredentials();
      } else {
        showToast(data.error || 'Operation failed', 'error');
      }
    } catch (error) {
      console.error('Error saving credential:', error);
      showToast('Error saving credential', 'error');
    }
  };

  const handleEdit = (credential) => {
    setFormData({
      name: credential.name || '',
      client_id: credential.client_id || '',
      client_secret: '', // Don't populate for security
      project_id: credential.project_id || '',
      channel_id: credential.channel_id || '',
      channel_name: credential.channel_name || '',
      is_active: credential.is_active || false,
      notes: credential.notes || ''
    });
    setEditingId(credential.credential_id);
    setShowForm(true);
  };

  const handleAuthenticate = async (credentialId) => {
    try {
      // Start OAuth flow
      const response = await api.post('/youtube/auth/start', { credential_id: credentialId });
      const data = response.data;

      if (data.status === 'success') {
        // Open OAuth URL in new tab
        window.open(data.auth_url, '_blank');

        // Show modal for entering auth code
        setAuthenticatingCredentialId(credentialId);
        setAuthCode('');
        setShowAuthModal(true);
      } else {
        showToast(data.error || 'Failed to start authentication', 'error');
      }
    } catch (error) {
      console.error('Error authenticating credential:', error);
      showToast('Error authenticating credential', 'error');
    }
  };

  const handleSubmitAuthCode = async () => {
    if (!authCode.trim()) {
      showToast('Please enter the authorization code', 'error');
      return;
    }

    try {
      const callbackResponse = await api.post('/youtube/oauth-callback', {
        code: authCode.trim(),
        credential_id: authenticatingCredentialId
      });

      const callbackData = callbackResponse.data;

      if (callbackData.status === 'success') {
        showToast('✅ Authentication successful!', 'success');
        setShowAuthModal(false);
        setAuthCode('');
        setAuthenticatingCredentialId(null);
        loadCredentials();
      } else {
        showToast(callbackData.error || 'Authentication failed', 'error');
      }
    } catch (error) {
      console.error('Error completing authentication:', error);
      showToast('Error completing authentication', 'error');
    }
  };

  const handleCancelAuth = () => {
    setShowAuthModal(false);
    setAuthCode('');
    setAuthenticatingCredentialId(null);
    showToast('Authentication cancelled', 'info');
  };

  const handleDelete = (credential) => {
    setDeleteDialog({ isOpen: true, credential });
  };

  const confirmDelete = async () => {
    const credential = deleteDialog.credential;
    setDeleteDialog({ isOpen: false, credential: null });

    try {
      const response = await api.delete(`/youtube/credentials/${credential._id}`);
      const data = response.data;

      if (data.status === 'success') {
        showToast('Credential deleted successfully', 'success');
        loadCredentials();
      } else {
        showToast(data.error || 'Delete failed', 'error');
      }
    } catch (error) {
      console.error('Error deleting credential:', error);
      showToast('Error deleting credential', 'error');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      client_id: '',
      client_secret: '',
      project_id: '',
      channel_id: '',
      channel_name: '',
      is_active: false,
      notes: ''
    });
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingId(null);
    resetForm();
  };

  if (loading) {
    return (
      <Card>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">YouTube Credentials</h2>
          <p className="text-gray-600 mt-1">Manage OAuth credentials for YouTube uploads</p>
        </div>
        {!showForm && (
          <Button
            variant="primary"
            icon="➕"
            onClick={() => setShowForm(true)}
          >
            Add Credential
          </Button>
        )}
      </div>

      {/* Form */}
      {showForm && (
        <Card>
          <form onSubmit={handleSubmit} className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {editingId ? 'Edit Credential' : 'Add New Credential'}
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="e.g., Main Channel"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Project ID <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="project_id"
                  value={formData.project_id}
                  onChange={handleInputChange}
                  placeholder="Google Cloud Project ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Client ID <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="client_id"
                  value={formData.client_id}
                  onChange={handleInputChange}
                  placeholder="OAuth 2.0 Client ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Client Secret <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  name="client_secret"
                  value={formData.client_secret}
                  onChange={handleInputChange}
                  placeholder={editingId ? "Leave blank to keep current" : "OAuth 2.0 Client Secret"}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required={!editingId}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Channel ID
                </label>
                <input
                  type="text"
                  name="channel_id"
                  value={formData.channel_id}
                  onChange={handleInputChange}
                  placeholder="YouTube Channel ID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Channel Name
                </label>
                <input
                  type="text"
                  name="channel_name"
                  value={formData.channel_name}
                  onChange={handleInputChange}
                  placeholder="YouTube Channel Name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                placeholder="Optional notes about this credential"
                rows="3"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleInputChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-700">
                Set as active credential (will be used for uploads)
              </label>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" variant="primary">
                {editingId ? 'Update' : 'Create'} Credential
              </Button>
              <Button type="button" variant="secondary" onClick={handleCancel}>
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Credentials List */}
      <div className="space-y-4">
        {credentials.length === 0 ? (
          <Card>
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔑</div>
              <p className="text-gray-600 text-lg">No credentials configured yet</p>
              <p className="text-gray-500 text-sm mt-2">Add your first YouTube OAuth credential to get started</p>
            </div>
          </Card>
        ) : (
          credentials.map((cred) => (
            <Card key={cred.credential_id}>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{cred.name}</h3>
                    {cred.is_active && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                        Active
                      </span>
                    )}
                    {cred.is_authenticated && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                        ✓ Authenticated
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600">
                    <div>
                      <span className="font-medium">Project ID:</span> {cred.project_id}
                    </div>
                    <div>
                      <span className="font-medium">Client ID:</span> {cred.client_id?.substring(0, 20)}...
                    </div>
                    {cred.channel_name && (
                      <div>
                        <span className="font-medium">Channel:</span> {cred.channel_name}
                      </div>
                    )}
                    {cred.created_at && (
                      <div>
                        <span className="font-medium">Created:</span> {new Date(cred.created_at).toLocaleDateString()}
                      </div>
                    )}
                    {cred.token_expiry && (
                      <div>
                        <span className="font-medium">Token Expiry:</span>{' '}
                        <span className={new Date(cred.token_expiry) < new Date() ? 'text-red-600 font-semibold' : 'text-green-600'}>
                          {new Date(cred.token_expiry).toLocaleString()}
                          {new Date(cred.token_expiry) < new Date() && ' (Expired)'}
                        </span>
                      </div>
                    )}
                  </div>

                  {cred.notes && (
                    <p className="text-sm text-gray-500 mt-2">{cred.notes}</p>
                  )}
                </div>

                <div className="flex gap-2 ml-4">
                  {!cred.is_authenticated && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleAuthenticate(cred.credential_id)}
                    >
                      🔐 Authenticate
                    </Button>
                  )}
                  {cred.is_authenticated && (
                    <Button
                      variant="success"
                      size="sm"
                      onClick={() => handleAuthenticate(cred.credential_id)}
                    >
                      🔄 Re-authenticate
                    </Button>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleEdit(cred)}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleDelete(cred)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Auth Code Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">Enter Authorization Code</h3>

            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded">
              <p className="text-sm text-blue-800 mb-2">
                <strong>✅ Authorization page opened in a new tab</strong>
              </p>
              <ol className="text-sm text-blue-700 list-decimal list-inside space-y-1">
                <li>Switch to the new tab and authorize the application</li>
                <li>After authorization, you will receive an authorization code</li>
                <li>Copy the authorization code</li>
                <li>Paste it in the field below</li>
              </ol>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Authorization Code
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="3"
                placeholder="Paste your authorization code here..."
                value={authCode}
                onChange={(e) => setAuthCode(e.target.value)}
                autoFocus
              />
            </div>

            <div className="flex gap-2 justify-end">
              <Button
                variant="secondary"
                onClick={handleCancelAuth}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSubmitAuthCode}
                disabled={!authCode.trim()}
              >
                Submit
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, credential: null })}
        onConfirm={confirmDelete}
        title="Delete Credential"
        description="This action cannot be undone"
        message={
          deleteDialog.credential
            ? `Are you sure you want to delete the credential "${deleteDialog.credential.name}"?`
            : ''
        }
        warningMessage="This will permanently delete the YouTube credential. You will need to re-authenticate if you want to use this account again."
        confirmText="Delete Credential"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default CredentialsManager;

