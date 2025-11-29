import React, { useState, useEffect } from 'react';
import { Card, Button, Modal } from '../components/common';
import { PromptEditor, PromptList, PromptTester, VoiceConfig } from '../components/VoiceLLM';
import { llmService, voiceService } from '../services';
import { useToast } from '../hooks/useToast';

/**
 * Voice & LLM Configuration Page
 */
const VoiceLLMPage = () => {
  const [activeTab, setActiveTab] = useState('prompts'); // prompts, voice
  const [prompts, setPrompts] = useState([]);
  const [voiceConfig, setVoiceConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showEditor, setShowEditor] = useState(false);
  const [showTester, setShowTester] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const { showToast } = useToast();

  // Load prompts on mount
  useEffect(() => {
    if (activeTab === 'prompts') {
      loadPrompts();
    } else if (activeTab === 'voice') {
      loadVoiceConfig();
    }
  }, [activeTab]);

  const loadPrompts = async () => {
    setLoading(true);
    try {
      const data = await llmService.getPrompts();
      setPrompts(data);
    } catch (error) {
      showToast('Failed to load prompts', 'error');
      console.error('Error loading prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadVoiceConfig = async () => {
    setLoading(true);
    try {
      const data = await voiceService.getConfig();
      setVoiceConfig(data);
    } catch (error) {
      showToast('Failed to load voice configuration', 'error');
      console.error('Error loading voice config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePrompt = () => {
    setSelectedPrompt(null);
    setShowEditor(true);
  };

  const handleEditPrompt = (prompt) => {
    setSelectedPrompt(prompt);
    setShowEditor(true);
  };

  const handleSavePrompt = async (promptData) => {
    setLoading(true);
    try {
      if (selectedPrompt) {
        // Update existing prompt
        await llmService.updatePrompt(selectedPrompt._id || selectedPrompt.id, promptData);
        showToast('Prompt updated successfully', 'success');
      } else {
        // Create new prompt
        await llmService.createPrompt(promptData);
        showToast('Prompt created successfully', 'success');
      }
      setShowEditor(false);
      setSelectedPrompt(null);
      loadPrompts();
    } catch (error) {
      showToast('Failed to save prompt', 'error');
      console.error('Error saving prompt:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePrompt = async (prompt) => {
    if (!window.confirm(`Are you sure you want to delete "${prompt.name}"?`)) {
      return;
    }

    setLoading(true);
    try {
      await llmService.deletePrompt(prompt._id || prompt.id);
      showToast('Prompt deleted successfully', 'success');
      loadPrompts();
    } catch (error) {
      showToast('Failed to delete prompt', 'error');
      console.error('Error deleting prompt:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTestPrompt = (prompt) => {
    setSelectedPrompt(prompt);
    setShowTester(true);
  };

  const handleRunTest = async (prompt, sampleData) => {
    try {
      const result = await llmService.testPrompt({
        promptId: prompt._id || prompt.id,
        template: prompt.template,
        sampleData,
        maxTokens: prompt.maxTokens,
        temperature: prompt.temperature,
      });
      return result;
    } catch (error) {
      throw new Error(error.message || 'Failed to test prompt');
    }
  };

  const handleSaveVoiceConfig = async (configData) => {
    setLoading(true);
    try {
      await voiceService.updateConfig(configData);
      showToast('Voice configuration saved successfully', 'success');
      loadVoiceConfig();
    } catch (error) {
      showToast('Failed to save voice configuration', 'error');
      console.error('Error saving voice config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVoicePreview = async (voiceId, text) => {
    try {
      const audioUrl = await voiceService.preview(voiceId, text);
      return audioUrl;
    } catch (error) {
      showToast('Failed to preview voice', 'error');
      throw error;
    }
  };

  const tabs = [
    { id: 'prompts', label: 'LLM Prompts', icon: '📝' },
    { id: 'voice', label: 'Voice Settings', icon: '🎙️' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Voice & LLM Configuration</h1>
          <p className="text-gray-600 mt-2">
            Configure LLM prompts and voice settings for news automation
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div>
          {activeTab === 'prompts' && (
            <div>
              {/* Action Bar */}
              <div className="mb-6 flex justify-between items-center">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">LLM Prompts</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Manage prompt templates for different content generation tasks
                  </p>
                </div>
                <Button variant="primary" onClick={handleCreatePrompt}>
                  + Create Prompt
                </Button>
              </div>

              {/* Prompt List */}
              <PromptList
                prompts={prompts}
                onEdit={handleEditPrompt}
                onDelete={handleDeletePrompt}
                onTest={handleTestPrompt}
                loading={loading}
              />
            </div>
          )}

          {activeTab === 'voice' && (
            <div>
              {/* Voice Configuration */}
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Voice Settings</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Configure voice settings for audio generation
                </p>
              </div>

              {voiceConfig ? (
                <VoiceConfig
                  config={voiceConfig}
                  onSave={handleSaveVoiceConfig}
                  onPreview={handleVoicePreview}
                  loading={loading}
                />
              ) : (
                <Card>
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="text-gray-600 mt-4">Loading voice configuration...</p>
                  </div>
                </Card>
              )}
            </div>
          )}
        </div>

        {/* Modals */}
        {showEditor && (
          <Modal
            isOpen={showEditor}
            onClose={() => {
              setShowEditor(false);
              setSelectedPrompt(null);
            }}
            title={selectedPrompt ? 'Edit Prompt' : 'Create New Prompt'}
            size="large"
          >
            <PromptEditor
              prompt={selectedPrompt}
              onSave={handleSavePrompt}
              onCancel={() => {
                setShowEditor(false);
                setSelectedPrompt(null);
              }}
              loading={loading}
            />
          </Modal>
        )}

        {showTester && selectedPrompt && (
          <Modal
            isOpen={showTester}
            onClose={() => {
              setShowTester(false);
              setSelectedPrompt(null);
            }}
            title="Test Prompt"
            size="large"
          >
            <PromptTester
              prompt={selectedPrompt}
              onClose={() => {
                setShowTester(false);
                setSelectedPrompt(null);
              }}
              onTest={handleRunTest}
            />
          </Modal>
        )}
      </div>
    </div>
  );
};

export default VoiceLLMPage;

