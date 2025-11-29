import React from 'react';
import { Card, Button } from '../common';

/**
 * Shorts Grid Component - Display YouTube Shorts ready for upload
 */
const ShortsGrid = ({ shorts, onUpload, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <Card key={i}>
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  if (!shorts || shorts.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-6xl mb-4">✅</div>
        <p className="text-gray-600 text-lg">No shorts pending upload. All caught up!</p>
      </div>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {shorts.map((short) => (
        <Card key={short.id} className="hover:shadow-lg transition-shadow duration-200">
          <div className="space-y-3">
            {/* Title */}
            <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 min-h-[2.5rem]">
              {short.title}
            </h3>

            {/* Metadata */}
            <div className="text-xs text-gray-600 space-y-1">
              {short.publishedAt && (
                <p>📅 {formatDate(short.publishedAt)}</p>
              )}
              {short.short_summary && (
                <p className="line-clamp-2">📝 {short.short_summary}</p>
              )}
            </div>

            {/* Upload Button */}
            <Button
              variant="danger"
              icon="⬆️"
              onClick={() => onUpload(short.id)}
              fullWidth
              size="sm"
            >
              Upload to YouTube
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default ShortsGrid;

