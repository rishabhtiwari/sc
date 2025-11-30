import React from 'react';
import { Card, Button } from '../common';

/**
 * Shorts Grid Component - Display YouTube Shorts ready for upload with pagination
 */
const ShortsGrid = ({
  shorts,
  onUpload,
  loading,
  pagination,
  onPageChange
}) => {
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

  // Get video URL for a short
  const getVideoUrl = (short) => {
    if (!short.shorts_video_path) return null;

    // Extract article_id and filename from shorts_video_path
    // Path format: /public/article_id/short.mp4 or article_id/short.mp4
    const pathParts = short.shorts_video_path.replace('/public/', '').split('/');
    if (pathParts.length >= 2) {
      const articleId = pathParts[0];
      const filename = pathParts[1];
      // Route through API server instead of directly to video-generator
      return `/api/news/videos/shorts/${articleId}/${filename}`;
    }
    return null;
  };

  return (
    <div className="space-y-4">
      {/* Pagination Info */}
      {pagination && (
        <div className="flex justify-between items-center text-sm text-gray-600">
          <div>
            Showing {shorts.length} of {pagination.total} shorts
          </div>
          <div>
            Page {pagination.page} of {pagination.total_pages}
          </div>
        </div>
      )}

      {/* Shorts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {shorts.map((short) => {
          const videoUrl = getVideoUrl(short);

          return (
            <Card key={short.id} className="hover:shadow-lg transition-shadow duration-200">
              <div className="space-y-3">
                {/* Video Preview */}
                {videoUrl ? (
                  <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '9/16', maxHeight: '400px' }}>
                    <video
                      src={videoUrl}
                      controls
                      className="w-full h-full object-contain"
                      preload="metadata"
                    >
                      Your browser does not support the video tag.
                    </video>
                  </div>
                ) : (
                  <div className="relative bg-gray-100 rounded-lg flex items-center justify-center" style={{ aspectRatio: '9/16', maxHeight: '400px' }}>
                    <p className="text-gray-500 text-sm">📹 Video not available</p>
                  </div>
                )}

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
          );
        })}
      </div>

      {/* Pagination Controls */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex justify-center items-center gap-2 mt-6">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(pagination.page - 1)}
            disabled={!pagination.has_prev}
          >
            ← Previous
          </Button>

          <div className="flex gap-1">
            {Array.from({ length: pagination.total_pages }, (_, i) => i + 1).map((pageNum) => (
              <button
                key={pageNum}
                onClick={() => onPageChange(pageNum)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  pageNum === pagination.page
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {pageNum}
              </button>
            ))}
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(pagination.page + 1)}
            disabled={!pagination.has_next}
          >
            Next →
          </Button>
        </div>
      )}
    </div>
  );
};

export default ShortsGrid;

