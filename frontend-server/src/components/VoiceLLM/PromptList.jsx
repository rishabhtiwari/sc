import React from 'react';
import { Card, Button, Badge } from '../common';

/**
 * Prompt List Component - Display list of configured prompts
 */
const PromptList = ({ prompts, onEdit, onDelete, onTest, loading }) => {
  const getTypeColor = (type) => {
    const colors = {
      summary: 'blue',
      title: 'green',
      description: 'purple',
      tags: 'orange',
    };
    return colors[type] || 'gray';
  };

  const getTypeLabel = (type) => {
    const labels = {
      summary: 'News Summary',
      title: 'Title Generation',
      description: 'Description Generation',
      tags: 'Tags Generation',
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3 mb-4"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </Card>
        ))}
      </div>
    );
  }

  if (!prompts || prompts.length === 0) {
    return (
      <Card className="text-center py-12">
        <div className="text-gray-400 mb-4">
          <svg
            className="mx-auto h-12 w-12"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Prompts Configured</h3>
        <p className="text-gray-500 mb-4">
          Get started by creating your first LLM prompt template
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {prompts.map((prompt) => (
        <Card key={prompt._id || prompt.id} className="hover:shadow-lg transition-shadow">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="text-lg font-semibold text-gray-900">{prompt.name}</h3>
                <Badge color={getTypeColor(prompt.type)}>
                  {getTypeLabel(prompt.type)}
                </Badge>
              </div>
              {prompt.description && (
                <p className="text-sm text-gray-600">{prompt.description}</p>
              )}
            </div>
          </div>

          {/* Template Preview */}
          <div className="bg-gray-50 rounded-lg p-3 mb-3">
            <p className="text-xs font-medium text-gray-500 mb-1">Template:</p>
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono overflow-x-auto">
              {prompt.template.length > 200
                ? prompt.template.substring(0, 200) + '...'
                : prompt.template}
            </pre>
          </div>

          {/* Parameters */}
          <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
            <div className="flex items-center gap-1">
              <span className="font-medium">Max Tokens:</span>
              <span>{prompt.maxTokens || 150}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="font-medium">Temperature:</span>
              <span>{prompt.temperature || 0.7}</span>
            </div>
            {prompt.updatedAt && (
              <div className="flex items-center gap-1 ml-auto">
                <span className="text-gray-400">Updated:</span>
                <span>{new Date(prompt.updatedAt).toLocaleDateString()}</span>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-3 border-t">
            <Button
              variant="primary"
              size="sm"
              onClick={() => onTest(prompt)}
            >
              Test
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onEdit(prompt)}
            >
              Edit
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => onDelete(prompt)}
            >
              Delete
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default PromptList;

