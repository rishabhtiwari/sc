import React, { useState, useEffect } from 'react';
import { Button, Badge } from '../common';
import { formatDate } from '../../utils/formatters';

/**
 * News Selector Component - Select and order news articles for video merging
 */
const NewsSelector = ({ config, onSelectionChange, onClose, embedded = false }) => {
  const [availableNews, setAvailableNews] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState(null);

  useEffect(() => {
    loadAvailableNews();
  }, [config]);

  const loadAvailableNews = async () => {
    setLoading(true);
    try {
      // Build query parameters
      const params = new URLSearchParams();
      params.append('limit', '100');
      
      if (config.categories && config.categories.length > 0) {
        config.categories.forEach(cat => params.append('categories', cat));
      }
      if (config.country) {
        params.append('country', config.country);
      }
      if (config.language) {
        params.append('language', config.language);
      }

      const response = await fetch(`/api/videos/available-news?${params.toString()}`);
      const data = await response.json();

      if (data.status === 'success') {
        setAvailableNews(data.articles || []);
      } else {
        console.error('Failed to load news:', data.error);
      }
    } catch (error) {
      console.error('Error loading news:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSelect = (articleId) => {
    setSelectedIds(prev => {
      let newSelectedIds;
      if (prev.includes(articleId)) {
        newSelectedIds = prev.filter(id => id !== articleId);
      } else {
        // Check if we've reached the limit
        const maxCount = config.videoCount || 20;
        if (prev.length >= maxCount) {
          alert(`You can only select up to ${maxCount} articles as per the configuration.`);
          return prev;
        }
        newSelectedIds = [...prev, articleId];
      }

      // Notify parent component of selection change (for embedded mode)
      if (onSelectionChange) {
        onSelectionChange(newSelectedIds);
      }

      return newSelectedIds;
    });
  };

  const handleSelectAll = () => {
    let newSelectedIds;
    if (selectedIds.length === availableNews.length) {
      newSelectedIds = [];
    } else {
      // Respect the videoCount limit
      const maxCount = config.videoCount || 20;
      newSelectedIds = availableNews.slice(0, maxCount).map(article => article.id);

      if (availableNews.length > maxCount) {
        alert(`Only the first ${maxCount} articles will be selected as per the configuration limit.`);
      }
    }

    setSelectedIds(newSelectedIds);

    // Notify parent component of selection change (for embedded mode)
    if (onSelectionChange) {
      onSelectionChange(newSelectedIds);
    }
  };

  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    const newSelectedIds = [...selectedIds];
    const draggedId = newSelectedIds[draggedIndex];
    newSelectedIds.splice(draggedIndex, 1);
    newSelectedIds.splice(index, 0, draggedId);

    setSelectedIds(newSelectedIds);
    setDraggedIndex(index);

    // Notify parent component of selection change (for embedded mode)
    if (onSelectionChange) {
      onSelectionChange(newSelectedIds);
    }
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const handleMoveUp = (index) => {
    if (index === 0) return;
    const newSelectedIds = [...selectedIds];
    [newSelectedIds[index - 1], newSelectedIds[index]] = [newSelectedIds[index], newSelectedIds[index - 1]];
    setSelectedIds(newSelectedIds);

    // Notify parent component of selection change (for embedded mode)
    if (onSelectionChange) {
      onSelectionChange(newSelectedIds);
    }
  };

  const handleMoveDown = (index) => {
    if (index === selectedIds.length - 1) return;
    const newSelectedIds = [...selectedIds];
    [newSelectedIds[index], newSelectedIds[index + 1]] = [newSelectedIds[index + 1], newSelectedIds[index]];
    setSelectedIds(newSelectedIds);

    // Notify parent component of selection change (for embedded mode)
    if (onSelectionChange) {
      onSelectionChange(newSelectedIds);
    }
  };

  const handleSave = () => {
    onSelectionChange(selectedIds);
    onClose();
  };

  const getSelectedArticles = () => {
    return selectedIds.map(id => availableNews.find(article => article.id === id)).filter(Boolean);
  };

  const getVoiceBadge = (voice) => {
    const isMale = ['am_adam', 'am_michael', 'bm_george', 'bm_lewis', 'male'].includes(voice);
    const isFemale = ['af_bella', 'af_nicole', 'af_sarah', 'af_sky', 'bf_emma', 'bf_isabella', 'female'].includes(voice);
    
    if (isMale) return <Badge variant="info">🎙️ Male</Badge>;
    if (isFemale) return <Badge variant="success">🎙️ Female</Badge>;
    return <Badge variant="default">🎙️ Unknown</Badge>;
  };

  const containerClass = embedded
    ? "w-full h-full flex flex-col"
    : "fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4";

  const innerClass = embedded
    ? "w-full h-full flex flex-col"
    : "bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[90vh] overflow-hidden flex flex-col";

  return (
    <div className={containerClass}>
      <div className={innerClass}>
        {/* Header */}
        {!embedded && (
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Select News Articles</h2>
              <p className="text-sm text-gray-600 mt-1">
                Choose articles and drag to reorder. Selected: {selectedIds.length}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Available News List */}
          <div className="w-1/2 border-r border-gray-200 flex flex-col">
            <div className="px-6 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h3 className="font-semibold text-gray-900">Available News ({availableNews.length})</h3>
                <p className="text-xs text-gray-600 mt-0.5">
                  Limit: {selectedIds.length}/{config.videoCount || 20} articles
                </p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleSelectAll}
              >
                {selectedIds.length === availableNews.length ? 'Deselect All' : 'Select All'}
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {loading ? (
                <div className="flex justify-center items-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="space-y-2">
                  {availableNews.map((article) => (
                    <div
                      key={article.id}
                      onClick={() => handleToggleSelect(article.id)}
                      className={`p-3 border rounded-lg cursor-pointer transition-all ${
                        selectedIds.includes(article.id)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(article.id)}
                          onChange={() => {}}
                          className="mt-1"
                        />
                        {article.thumbnail && (
                          <img
                            src={`/api/proxy-image/${article.id}`}
                            alt={article.title}
                            className="w-16 h-16 object-cover rounded"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm text-gray-900 line-clamp-2">
                            {article.title}
                          </p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {article.category && (
                              <Badge variant="info">{Array.isArray(article.category) ? article.category[0] : article.category}</Badge>
                            )}
                            {article.voice && getVoiceBadge(article.voice)}
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {formatDate(article.publishedAt || article.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Selected News List (Ordered) */}
          <div className="w-1/2 flex flex-col">
            <div className="px-6 py-3 bg-blue-50 border-b border-blue-200">
              <h3 className="font-semibold text-blue-900">Selected & Ordered ({selectedIds.length})</h3>
              <p className="text-xs text-blue-700 mt-1">Drag to reorder or use arrow buttons</p>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {selectedIds.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-4xl mb-2">📋</div>
                  <p>No articles selected</p>
                  <p className="text-sm mt-1">Select articles from the left panel</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {getSelectedArticles().map((article, index) => (
                    <div
                      key={article.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, index)}
                      onDragOver={(e) => handleDragOver(e, index)}
                      onDragEnd={handleDragEnd}
                      className={`p-3 border border-blue-200 rounded-lg bg-white cursor-move transition-all ${
                        draggedIndex === index ? 'opacity-50' : ''
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex flex-col gap-1">
                          <span className="text-xs font-bold text-blue-600 bg-blue-100 px-2 py-1 rounded">
                            #{index + 1}
                          </span>
                          <button
                            onClick={() => handleMoveUp(index)}
                            disabled={index === 0}
                            className="text-xs px-1 py-0.5 bg-gray-100 rounded disabled:opacity-30"
                          >
                            ▲
                          </button>
                          <button
                            onClick={() => handleMoveDown(index)}
                            disabled={index === selectedIds.length - 1}
                            className="text-xs px-1 py-0.5 bg-gray-100 rounded disabled:opacity-30"
                          >
                            ▼
                          </button>
                        </div>
                        {article.thumbnail && (
                          <img
                            src={`/api/proxy-image/${article.id}`}
                            alt={article.title}
                            className="w-16 h-16 object-cover rounded"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm text-gray-900 line-clamp-2">
                            {article.title}
                          </p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {article.category && (
                              <Badge variant="info">{Array.isArray(article.category) ? article.category[0] : article.category}</Badge>
                            )}
                            {article.voice && getVoiceBadge(article.voice)}
                          </div>
                        </div>
                        <button
                          onClick={() => handleToggleSelect(article.id)}
                          className="text-red-500 hover:text-red-700 font-bold"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        {!embedded && (
          <div className="px-6 py-4 border-t border-gray-200 flex justify-between items-center bg-gray-50">
            <p className="text-sm text-gray-600">
              {selectedIds.length} article{selectedIds.length !== 1 ? 's' : ''} selected
            </p>
            <div className="flex gap-3">
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleSave}
                disabled={selectedIds.length === 0}
              >
                Use Selected Articles ({selectedIds.length})
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NewsSelector;

