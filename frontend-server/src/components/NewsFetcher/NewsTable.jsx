import React from 'react';
import { Table, Badge } from '../common';
import { formatDate } from '../../utils/formatters';

/**
 * News Table Component - Display news articles in a table
 */
const NewsTable = ({ articles, loading, onViewArticle }) => {
  const getStatusBadge = (status) => {
    const statusMap = {
      completed: { variant: 'success', label: 'Completed' },
      enriched: { variant: 'success', label: 'Enriched' },
      progress: { variant: 'warning', label: 'In Progress' },
      pending: { variant: 'warning', label: 'Pending' },
      failed: { variant: 'error', label: 'Failed' },
    };

    const statusInfo = statusMap[status?.toLowerCase()] || { variant: 'default', label: status || 'Unknown' };
    return <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>;
  };

  const columns = [
    {
      key: 'title',
      label: 'Title',
      render: (value, row) => (
        <div className="max-w-md">
          <p className="font-semibold text-gray-900 truncate">{value || 'N/A'}</p>
          {row.description && (
            <p className="text-sm text-gray-500 truncate mt-1">{row.description}</p>
          )}
        </div>
      ),
    },
    {
      key: 'category',
      label: 'Category',
      render: (value) => {
        // Handle array of categories
        const categoryText = Array.isArray(value)
          ? value.join(', ')
          : (value || 'general');
        return <Badge variant="info">{categoryText}</Badge>;
      },
    },
    {
      key: 'source',
      label: 'Source',
      render: (value) => value?.name || 'Unknown',
    },
    {
      key: 'publishedAt',
      label: 'Published',
      render: (value) => formatDate(value),
    },
    {
      key: 'status',
      label: 'Status',
      render: (value) => getStatusBadge(value),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <button
          onClick={() => onViewArticle(row)}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          View
        </button>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      data={articles}
      loading={loading}
      emptyMessage="No news articles found"
    />
  );
};

export default NewsTable;

