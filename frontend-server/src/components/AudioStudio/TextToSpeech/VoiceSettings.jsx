import React from 'react';
import { Card } from '../../common';

/**
 * Voice Settings Component
 * Controls for adjusting voice parameters
 */
const VoiceSettings = ({ settings, onSettingsChange }) => {
  const handleChange = (key, value) => {
    onSettingsChange({
      ...settings,
      [key]: value
    });
  };

  return (
    <Card title="⚙️ Voice Settings">
      <div className="space-y-6">
        {/* Speed Control */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">
              Speed
            </label>
            <span className="text-sm font-semibold text-blue-600">
              {settings.speed.toFixed(2)}x
            </span>
          </div>
          <input
            type="range"
            min="0.5"
            max="2.0"
            step="0.1"
            value={settings.speed}
            onChange={(e) => handleChange('speed', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0.5x (Slow)</span>
            <span>1.0x (Normal)</span>
            <span>2.0x (Fast)</span>
          </div>
        </div>

        {/* Pitch Control - Coming Soon */}
        <div className="opacity-50">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">
              Pitch
              <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                Coming Soon
              </span>
            </label>
            <span className="text-sm font-semibold text-gray-600">
              {settings.pitch > 0 ? '+' : ''}{settings.pitch}
            </span>
          </div>
          <input
            type="range"
            min="-12"
            max="12"
            step="1"
            value={settings.pitch}
            onChange={(e) => handleChange('pitch', parseInt(e.target.value))}
            disabled
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>-12 (Lower)</span>
            <span>0 (Normal)</span>
            <span>+12 (Higher)</span>
          </div>
        </div>

        {/* Stability Control - Coming Soon */}
        <div className="opacity-50">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">
              Stability
              <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                Coming Soon
              </span>
            </label>
            <span className="text-sm font-semibold text-gray-600">
              {(settings.stability * 100).toFixed(0)}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={settings.stability}
            onChange={(e) => handleChange('stability', parseFloat(e.target.value))}
            disabled
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>More Variable</span>
            <span>More Stable</span>
          </div>
        </div>

        {/* Clarity Control - Coming Soon */}
        <div className="opacity-50">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">
              Clarity
              <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                Coming Soon
              </span>
            </label>
            <span className="text-sm font-semibold text-gray-600">
              {(settings.clarity * 100).toFixed(0)}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={settings.clarity}
            onChange={(e) => handleChange('clarity', parseFloat(e.target.value))}
            disabled
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>More Similar</span>
            <span>More Clear</span>
          </div>
        </div>

        {/* Info Note */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-xs text-blue-800">
            <strong>Note:</strong> Currently, only Speed control is supported by Kokoro-82m.
            Pitch, Stability, and Clarity controls will be available with ElevenLabs integration.
          </p>
        </div>
      </div>
    </Card>
  );
};

export default VoiceSettings;

