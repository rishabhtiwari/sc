import React from 'react';
import { Card } from '../common';

/**
 * Stats Cards Component - Display YouTube upload statistics
 */
const StatsCards = ({ stats, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i}>
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-3/4"></div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  const statCards = [
    {
      title: 'Ready to Upload',
      value: stats?.ready_to_upload || 0,
      icon: '📤',
      color: 'blue',
    },
    {
      title: 'Already Uploaded',
      value: stats?.already_uploaded || 0,
      icon: '✅',
      color: 'green',
    },
    {
      title: 'Total Videos',
      value: stats?.total_videos || 0,
      icon: '🎬',
      color: 'purple',
    },
    {
      title: 'Shorts Ready',
      value: stats?.shorts_ready_to_upload || 0,
      icon: '📱',
      color: 'orange',
    },
    {
      title: 'Shorts Uploaded',
      value: stats?.shorts_already_uploaded || 0,
      icon: '✨',
      color: 'teal',
    },
    {
      title: 'Total Shorts',
      value: stats?.total_shorts || 0,
      icon: '🎥',
      color: 'indigo',
    },
  ];

  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    purple: 'text-purple-600',
    orange: 'text-orange-600',
    teal: 'text-teal-600',
    indigo: 'text-indigo-600',
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      {statCards.map((stat, index) => (
        <Card key={index}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-600 uppercase tracking-wide mb-1">
                {stat.title}
              </p>
              <p className={`text-2xl font-bold ${colorClasses[stat.color]}`}>
                {stat.value.toLocaleString()}
              </p>
            </div>
            <div className="text-3xl">{stat.icon}</div>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default StatsCards;

