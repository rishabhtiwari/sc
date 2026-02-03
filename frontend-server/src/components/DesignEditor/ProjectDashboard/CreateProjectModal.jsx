/**
 * Create Project Modal - Veed/Canva Style
 * Template selection and project settings
 */
import React, { useState } from 'react';

const TEMPLATES = [
  {
    id: 'blank',
    name: 'Blank Project',
    description: 'Start from scratch',
    icon: '📄',
    settings: {
      canvas: { width: 1920, height: 1080, backgroundColor: '#ffffff' },
      duration: 30,
      fps: 30,
      quality: 'high'
    }
  },
  {
    id: 'youtube',
    name: 'YouTube Video',
    description: '16:9 landscape format',
    icon: '🎥',
    settings: {
      canvas: { width: 1920, height: 1080, backgroundColor: '#000000' },
      duration: 60,
      fps: 30,
      quality: 'high'
    }
  },
  {
    id: 'instagram',
    name: 'Instagram Story',
    description: '9:16 vertical format',
    icon: '📱',
    settings: {
      canvas: { width: 1080, height: 1920, backgroundColor: '#ffffff' },
      duration: 15,
      fps: 30,
      quality: 'high'
    }
  },
  {
    id: 'square',
    name: 'Square Video',
    description: '1:1 for social media',
    icon: '⬜',
    settings: {
      canvas: { width: 1080, height: 1080, backgroundColor: '#ffffff' },
      duration: 30,
      fps: 30,
      quality: 'high'
    }
  },
  {
    id: 'presentation',
    name: 'Presentation',
    description: 'Slide-based format',
    icon: '📊',
    settings: {
      canvas: { width: 1920, height: 1080, backgroundColor: '#f3f4f6' },
      duration: 120,
      fps: 30,
      quality: 'high'
    }
  },
  {
    id: 'tiktok',
    name: 'TikTok Video',
    description: '9:16 short format',
    icon: '🎵',
    settings: {
      canvas: { width: 1080, height: 1920, backgroundColor: '#000000' },
      duration: 60,
      fps: 30,
      quality: 'high'
    }
  }
];

const CreateProjectModal = ({ onClose, onCreate }) => {
  const [step, setStep] = useState(1); // 1: template, 2: details
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setProjectName(template.name);
    setStep(2);
  };

  const handleCreate = () => {
    const projectData = {
      name: projectName || 'Untitled Project',
      description: projectDescription,
      settings: selectedTemplate.settings,
      pages: [],
      audioTracks: [],
      videoTracks: [],
      status: 'draft',
      tags: []
    };
    onCreate(projectData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">
            {step === 1 ? 'Choose a Template' : 'Project Details'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {step === 1 ? (
            <>
              <p className="text-gray-600 mb-6">
                Select a template to get started quickly, or start from scratch
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {TEMPLATES.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template)}
                    className="group relative p-6 border-2 border-gray-200 rounded-xl hover:border-purple-500 hover:shadow-lg transition-all duration-200 text-left"
                  >
                    <div className="text-4xl mb-3">{template.icon}</div>
                    <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-purple-600">
                      {template.name}
                    </h3>
                    <p className="text-sm text-gray-500">{template.description}</p>
                    <div className="mt-3 text-xs text-gray-400">
                      {template.settings.canvas.width} × {template.settings.canvas.height}
                    </div>
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div className="max-w-xl mx-auto">
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Name *
                </label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  autoFocus
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={projectDescription}
                  onChange={(e) => setProjectDescription(e.target.value)}
                  placeholder="Add a description for your project"
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Template Preview */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h4 className="font-medium text-gray-900 mb-3">Template Settings</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500">Dimensions:</span>
                    <span className="ml-2 font-medium">
                      {selectedTemplate.settings.canvas.width} × {selectedTemplate.settings.canvas.height}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Duration:</span>
                    <span className="ml-2 font-medium">{selectedTemplate.settings.duration}s</span>
                  </div>
                  <div>
                    <span className="text-gray-500">FPS:</span>
                    <span className="ml-2 font-medium">{selectedTemplate.settings.fps}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Quality:</span>
                    <span className="ml-2 font-medium capitalize">{selectedTemplate.settings.quality}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
          <button
            onClick={step === 1 ? onClose : () => setStep(1)}
            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
          >
            {step === 1 ? 'Cancel' : 'Back'}
          </button>
          {step === 2 && (
            <button
              onClick={handleCreate}
              disabled={!projectName.trim()}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              Create Project
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default CreateProjectModal;

