import React from 'react';
import { Table, Badge, Button } from '../common';
import { formatDate } from '../../utils/formatters';

/**
 * Seed URLs Table Component - Display and manage seed URLs
 */
const SeedUrlsTable = ({ seedUrls, loading, onEdit, onToggleStatus, onDelete }) => {
  const columns = [
    {
      key: 'partner_name',
      label: 'Partner Name',
      render: (value) => <span className="font-semibold">{value}</span>,
    },
    {
      key: 'partner_id',
      label: 'Partner ID',
      render: (value) => <span className="text-sm text-gray-600">{value}</span>,
    },
    {
      key: 'category',
      label: 'Categories',
      render: (value) => {
        if (Array.isArray(value)) {
          return (
            <div className="flex flex-wrap gap-1">
              {value.map((cat, idx) => (
                <Badge key={idx} variant="success">{cat}</Badge>
              ))}
            </div>
          );
        }
        return <Badge variant="success">{value || 'general'}</Badge>;
      },
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (value) => (
        <Badge variant={value ? 'success' : 'error'}>
          {value ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'frequency_minutes',
      label: 'Frequency',
      render: (value) => `${value || 60} min`,
    },
    {
      key: 'last_run',
      label: 'Last Run',
      render: (value) => value ? formatDate(value) : 'Never',
    },
    {
      key: 'is_due',
      label: 'Due',
      render: (value) => (
        <Badge variant={value ? 'warning' : 'success'}>
          {value ? 'Due' : 'Not Due'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="primary"
            onClick={() => onEdit(row)}
          >
            Edit
          </Button>
          <Button
            size="sm"
            variant={row.is_active ? 'warning' : 'success'}
            onClick={() => onToggleStatus(row.partner_id, !row.is_active)}
          >
            {row.is_active ? 'Disable' : 'Enable'}
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={() => onDelete(row.partner_id)}
          >
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      data={seedUrls}
      loading={loading}
      emptyMessage="No seed URLs configured"
    />
  );
};

export default SeedUrlsTable;

