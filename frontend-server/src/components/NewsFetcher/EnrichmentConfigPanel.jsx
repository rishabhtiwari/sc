import React, { useState, useEffect } from 'react';
import { Card, Button, ConfirmDialog } from '../common';
import { useToast } from '../../hooks/useToast';
import { newsService } from '../../services';

/**
 * Enrichment Configuration Panel - Manage enrichment prompt settings
 */
const EnrichmentConfigPanel = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [editedConfig, setEditedConfig] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [resetDialog, setResetDialog] = useState({ isOpen: false });

  const { showToast } = useToast();

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const response = await newsService.getEnrichmentConfig();

      if (response.data?.status === 'success' && response.data?.config) {
        setConfig(response.data.config);
        setEditedConfig(response.data.config);
      } else {
        showToast('Failed to load configuration', 'error');
      }
    } catch (error) {
      console.error('Error loading config:', error);
      showToast('Error loading configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field, value) => {
    setEditedConfig(prev => ({
      ...prev,
      [field]: value
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      // Only send changed fields
      const updates = {};
      Object.keys(editedConfig).forEach(key => {
        if (editedConfig[key] !== config[key] && key !== 'config_type' && key !== 'created_at' && key !== 'updated_at') {
          updates[key] = editedConfig[key];
        }
      });

      const response = await newsService.updateEnrichmentConfig(updates);

      if (response.data?.status === 'success') {
        showToast('Configuration saved successfully', 'success');
        setConfig(response.data.config);
        setEditedConfig(response.data.config);
        setHasChanges(false);
      } else {
        showToast(response.data?.error || 'Failed to save configuration', 'error');
      }
    } catch (error) {
      console.error('Error saving config:', error);
      showToast('Error saving configuration', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setResetDialog({ isOpen: true });
  };

  const confirmReset = async () => {
    setResetDialog({ isOpen: false });

    try {
      setResetting(true);
      const response = await newsService.resetEnrichmentConfig();

      if (response.data?.status === 'success') {
        showToast('Configuration reset to defaults', 'success');
        setConfig(response.data.config);
        setEditedConfig(response.data.config);
        setHasChanges(false);
      } else {
        showToast(response.data?.error || 'Failed to reset configuration', 'error');
      }
    } catch (error) {
      console.error('Error resetting config:', error);
      showToast('Error resetting configuration', 'error');
    } finally {
      setResetting(false);
    }
  };

  const handleCancel = () => {
    setEditedConfig(config);
    setHasChanges(false);
  };

  if (loading) {
    return (
      <Card title="⚙️ Enrichment Configuration">
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Card>
    );
  }

  if (!editedConfig) {
    return (
      <Card title="⚙️ Enrichment Configuration">
        <div className="text-center py-12 text-gray-500">
          Failed to load configuration
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card title="⚙️ Enrichment Configuration">
        <div className="space-y-6">
          {/* Header with actions */}
          <div className="flex justify-between items-center pb-4 border-b">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Prompt & Parameters</h3>
              <p className="text-sm text-gray-500 mt-1">
                Configure how news articles are enriched with AI-generated summaries
              </p>
            </div>
            <div className="flex gap-2">
              {hasChanges && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCancel}
                >
                  Cancel
                </Button>
              )}
              <Button
                variant="primary"
                size="sm"
                onClick={handleSave}
                loading={saving}
                disabled={!hasChanges}
              >
                💾 Save Changes
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleReset}
                loading={resetting}
              >
                🔄 Reset to Defaults
              </Button>
            </div>
          </div>

          {/* Prompt Template */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Primary Prompt Template
              <span className="text-gray-500 font-normal ml-2">(First attempt)</span>
            </label>
            <textarea
              value={editedConfig.prompt_template || ''}
              onChange={(e) => handleFieldChange('prompt_template', e.target.value)}
              rows={12}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              placeholder="Enter the prompt template for generating summaries..."
            />
            <p className="text-xs text-gray-500 mt-1">
              Use <code className="bg-gray-100 px-1 rounded">{`{content}`}</code> as placeholder for article content
            </p>
          </div>

          {/* Retry Prompt Template */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Retry Prompt Template
              <span className="text-gray-500 font-normal ml-2">(Used on retry attempts)</span>
            </label>
            <textarea
              value={editedConfig.retry_prompt_template || ''}
              onChange={(e) => handleFieldChange('retry_prompt_template', e.target.value)}
              rows={10}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              placeholder="Enter the retry prompt template..."
            />
          </div>

          {/* Parameters Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4 border-t">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Min Words
              </label>
              <input
                type="number"
                value={editedConfig.target_min_words || 40}
                onChange={(e) => handleFieldChange('target_min_words', parseInt(e.target.value))}
                min="20"
                max="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Target minimum word count</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Max Words
              </label>
              <input
                type="number"
                value={editedConfig.target_max_words || 75}
                onChange={(e) => handleFieldChange('target_max_words', parseInt(e.target.value))}
                min="30"
                max="150"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Target maximum word count</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Min Word Count (Validation)
              </label>
              <input
                type="number"
                value={editedConfig.min_word_count || 30}
                onChange={(e) => handleFieldChange('min_word_count', parseInt(e.target.value))}
                min="10"
                max="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Reject if below this count</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Word Count (Validation)
              </label>
              <input
                type="number"
                value={editedConfig.max_word_count || 100}
                onChange={(e) => handleFieldChange('max_word_count', parseInt(e.target.value))}
                min="50"
                max="200"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Reject if above this count</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Retries
              </label>
              <input
                type="number"
                value={editedConfig.max_retries || 2}
                onChange={(e) => handleFieldChange('max_retries', parseInt(e.target.value))}
                min="1"
                max="5"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Number of retry attempts</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature
              </label>
              <input
                type="number"
                step="0.1"
                value={editedConfig.temperature || 0.6}
                onChange={(e) => handleFieldChange('temperature', parseFloat(e.target.value))}
                min="0"
                max="2"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">LLM temperature (0-2)</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Retry Temperature
              </label>
              <input
                type="number"
                step="0.1"
                value={editedConfig.retry_temperature || 0.7}
                onChange={(e) => handleFieldChange('retry_temperature', parseFloat(e.target.value))}
                min="0"
                max="2"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Temperature for retries</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Tokens
              </label>
              <input
                type="number"
                value={editedConfig.max_tokens || 200}
                onChange={(e) => handleFieldChange('max_tokens', parseInt(e.target.value))}
                min="50"
                max="500"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Max tokens to generate</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Content Max Chars
              </label>
              <input
                type="number"
                value={editedConfig.content_max_chars || 2000}
                onChange={(e) => handleFieldChange('content_max_chars', parseInt(e.target.value))}
                min="500"
                max="5000"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Max chars from article</p>
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">ℹ️ Configuration Tips</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• The prompt template should include clear instructions for word count and content quality</li>
              <li>• Use <code className="bg-blue-100 px-1 rounded">{'{content}'}</code> placeholder where article content should be inserted</li>
              <li>• Target word counts guide the LLM, validation counts reject unsuitable summaries</li>
              <li>• Higher temperature (0.7-1.0) = more creative, Lower (0.3-0.6) = more focused</li>
              <li>• Changes take effect immediately for new enrichment tasks</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Reset Confirmation Dialog */}
      <ConfirmDialog
        isOpen={resetDialog.isOpen}
        onClose={() => setResetDialog({ isOpen: false })}
        onConfirm={confirmReset}
        title="Reset to Default Configuration"
        description="Restore default enrichment settings"
        message="Are you sure you want to reset to default configuration?"
        warningMessage="This will overwrite all custom settings with the default configuration. This action cannot be undone."
        confirmText="Reset to Defaults"
        cancelText="Cancel"
        variant="warning"
      />
    </div>
  );
};

export default EnrichmentConfigPanel;

