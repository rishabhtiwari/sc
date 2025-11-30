import React, { useState, useEffect } from 'react';
import { formatDate } from '../../utils/formatters';
import newsService from '../../services/newsService';

/**
 * Article Detail Modal Component - Display and edit article details
 */
const ArticleDetailModal = ({ article, isOpen, onClose, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [editedArticle, setEditedArticle] = useState({
    title: '',
    description: '',
    short_summary: '',
    content: '',
    status: 'completed',
  });

  // Initialize edited article when article changes
  useEffect(() => {
    if (article) {
      setEditedArticle({
        title: article.title || '',
        description: article.description || '',
        short_summary: article.short_summary || '',
        content: article.content || '',
        status: article.status || 'completed',
      });
    }
  }, [article]);

  if (!isOpen || !article) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    // Reset to original values
    setEditedArticle({
      title: article.title || '',
      description: article.description || '',
      short_summary: article.short_summary || '',
      content: article.content || '',
      status: article.status || 'completed',
    });
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      const response = await newsService.updateArticle(article.id, editedArticle);

      if (response.data?.status === 'success') {
        setIsEditing(false);
        // Call onUpdate callback if provided
        if (onUpdate) {
          onUpdate(response.data.article);
        }
        // Show success message (you can add a toast here)
        alert('Article updated successfully!');
      } else {
        alert('Failed to update article: ' + (response.data?.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error updating article:', error);
      alert('Error updating article: ' + (error.response?.data?.error || error.message));
    } finally {
      setIsSaving(false);
    }
  };

  const handleInputChange = (field, value) => {
    setEditedArticle(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-start">
          <div className="flex-1 pr-4">
            {isEditing ? (
              <input
                type="text"
                value={editedArticle.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                className="w-full text-2xl font-bold text-gray-900 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Article title"
              />
            ) : (
              <h2 className="text-2xl font-bold text-gray-900">{article.title}</h2>
            )}
            <div className="flex flex-wrap gap-3 mt-2 text-sm text-gray-600">
              <span>
                <strong>Source:</strong> {article.source?.name || 'Unknown'}
              </span>
              <span>•</span>
              <span>
                <strong>Published:</strong> {formatDate(article.publishedAt)}
              </span>
              {article.author && (
                <>
                  <span>•</span>
                  <span>
                    <strong>Author:</strong> {article.author}
                  </span>
                </>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Categories */}
          {article.category && (
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Categories</h3>
              <div className="flex flex-wrap gap-2">
                {Array.isArray(article.category) ? (
                  article.category.map((cat, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                    >
                      {cat}
                    </span>
                  ))
                ) : (
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    {article.category}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Image */}
          {article.urlToImage && (
            <div className="mb-4">
              <img
                src={article.urlToImage}
                alt={article.title}
                className="w-full rounded-lg"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            </div>
          )}

          {/* Description */}
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Description</h3>
            {isEditing ? (
              <textarea
                value={editedArticle.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-gray-800 leading-relaxed focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="3"
                placeholder="Article description"
              />
            ) : (
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{article.description || 'N/A'}</p>
            )}
          </div>

          {/* Short Summary */}
          {(article.short_summary || isEditing) && (
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Short Summary</h3>
              {isEditing ? (
                <textarea
                  value={editedArticle.short_summary}
                  onChange={(e) => handleInputChange('short_summary', e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-gray-800 leading-relaxed focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="4"
                  placeholder="Short summary"
                />
              ) : (
                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{article.short_summary || 'N/A'}</p>
              )}
            </div>
          )}

          {/* Content */}
          {(article.content || isEditing) && (
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Content</h3>
              {isEditing ? (
                <textarea
                  value={editedArticle.content}
                  onChange={(e) => handleInputChange('content', e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-gray-800 leading-relaxed focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="8"
                  placeholder="Article content"
                />
              ) : (
                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{article.content || 'N/A'}</p>
              )}
            </div>
          )}

          {/* Additional Info */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Additional Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Status:</span>
                {isEditing ? (
                  <select
                    value={editedArticle.status}
                    onChange={(e) => handleInputChange('status', e.target.value)}
                    className="ml-2 border border-gray-300 rounded px-2 py-1 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                    <option value="dont_process">Don't Process</option>
                  </select>
                ) : (
                  <span className="ml-2 font-medium text-gray-900">
                    {article.status || 'Unknown'}
                  </span>
                )}
              </div>
              <div>
                <span className="text-gray-600">Language:</span>
                <span className="ml-2 font-medium text-gray-900">
                  {article.lang || 'N/A'}
                </span>
              </div>
              {article.source?.country && (
                <div>
                  <span className="text-gray-600">Country:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {article.source.country}
                  </span>
                </div>
              )}
              {article._id && (
                <div>
                  <span className="text-gray-600">Article ID:</span>
                  <span className="ml-2 font-mono text-xs text-gray-900">
                    {article._id}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Original URL */}
          {article.url && (
            <div className="mt-4">
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                View Original Article
                <svg
                  className="w-4 h-4 ml-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </a>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          {isEditing ? (
            <>
              <button
                onClick={handleCancel}
                disabled={isSaving}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleEdit}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Edit Article
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArticleDetailModal;

