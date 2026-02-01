import React from 'react';
import { Button } from '../common';

/**
 * Control Panel Component - Controls for image cleaning operations
 */
const ControlPanel = ({
  brushSize,
  onBrushSizeChange,
  currentImage,
  hasMask,
  onLoadNext,
  onAutoDetect,
  onClearMask,
  onProcess,
  onSave,
  onSkip,
  onReplaceImage,
  loading,
  processing,
  autoMarkMode = false,
}) => {
  return (
    <div className="space-y-4">
      {/* Image Info */}
      {currentImage && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm font-semibold text-blue-900 mb-1">Current Image:</p>
          <p className="text-sm text-blue-700">{currentImage.title || 'Untitled'}</p>
          {currentImage.source && (
            <p className="text-xs text-blue-600 mt-1">Source: {currentImage.source}</p>
          )}
        </div>
      )}

      {/* Instructions */}
      {currentImage && !autoMarkMode && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm font-semibold text-blue-900 mb-2">📝 Instructions:</p>
          <ul className="text-xs text-blue-700 space-y-1">
            <li>• <strong>No watermark?</strong> Click "Save & Mark Done" directly</li>
            <li>• <strong>Has watermark?</strong> Paint over it, then click "Remove Watermark"</li>
            <li>• Use brush size slider or "Auto-detect" button</li>
          </ul>
        </div>
      )}

      {/* Auto-Mark Mode Instructions */}
      {currentImage && autoMarkMode && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm font-semibold text-green-900 mb-2">✅ Auto-Mark Mode:</p>
          <p className="text-xs text-green-700">
            Images are automatically marked as cleaned. Click "Save & Next" to mark this image and load the next one.
          </p>
        </div>
      )}

      {/* Brush Size Control - Only show in manual mode */}
      {!autoMarkMode && (
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-gray-700">
            Brush Size: {brushSize}px
        </label>
        <input
          type="range"
          min="5"
          max="100"
          value={brushSize}
          onChange={(e) => onBrushSizeChange(parseInt(e.target.value))}
          disabled={!currentImage || loading}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            background: `linear-gradient(to right, #667eea 0%, #667eea ${((brushSize - 5) / 95) * 100}%, #e5e7eb ${((brushSize - 5) / 95) * 100}%, #e5e7eb 100%)`
          }}
        />
      </div>

      )}

      {/* Action Buttons */}
      <div className="space-y-3">
        {/* Load Image */}
        <div>
          <Button
            variant="primary"
            icon="📥"
            onClick={onLoadNext}
            loading={loading}
            size="sm"
            className="w-full shadow-sm hover:shadow-md"
          >
            Load Next Image
          </Button>
        </div>

        {/* Mask Tools - Only show in manual mode */}
        {!autoMarkMode && (
          <div className="border-t pt-3">
            <p className="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">Mask Tools</p>
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="info"
                icon="🔍"
                onClick={onAutoDetect}
                disabled={!currentImage || loading}
                size="sm"
                className="shadow-sm hover:shadow-md"
              >
                Auto-detect
              </Button>

              <Button
                variant="secondary"
                icon="🗑️"
                onClick={onClearMask}
                disabled={!currentImage || !hasMask || loading}
                size="sm"
                className="shadow-sm hover:shadow-md"
              >
                Clear Mask
              </Button>
            </div>
          </div>
        )}

        {/* Processing - Only show in manual mode */}
        {!autoMarkMode && (
          <div className="border-t pt-3">
            <p className="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">Processing</p>
            <Button
              variant="primary"
              icon="✨"
              onClick={onProcess}
              disabled={!currentImage || !hasMask || loading}
              loading={processing}
              size="sm"
              className="w-full shadow-sm hover:shadow-md"
            >
              Remove Watermark
            </Button>
          </div>
        )}

        {/* Actions */}
        <div className="border-t pt-3">
          <p className="text-xs font-semibold text-gray-600 mb-2 uppercase tracking-wide">Actions</p>
          <div className="space-y-2">
            <Button
              variant="success"
              icon={autoMarkMode ? "✅" : "💾"}
              onClick={onSave}
              disabled={!currentImage || loading}
              size="sm"
              className="w-full shadow-sm hover:shadow-md"
            >
              {autoMarkMode ? "Save & Next" : "Save & Mark Done"}
            </Button>

            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="warning"
                icon="🔄"
                onClick={onReplaceImage}
                disabled={!currentImage || loading}
                size="sm"
                className="shadow-sm hover:shadow-md"
              >
                Replace URL
              </Button>

              <Button
                variant="danger"
                icon="⏭️"
                onClick={onSkip}
                disabled={!currentImage || loading}
                size="sm"
                className="shadow-sm hover:shadow-md"
              >
                Skip Image
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;

