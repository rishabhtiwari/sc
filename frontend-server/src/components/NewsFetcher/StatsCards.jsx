import React from 'react';
import { Card } from '../common';

/**
 * Stats Cards Component - Display news statistics
 */
const StatsCards = ({ stats, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
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
      title: 'Total Articles',
      value: stats?.total_articles || 0,
      icon: '📰',
      color: 'blue',
    },
    {
      title: 'Enriched',
      value: stats?.enriched_articles || 0,
      icon: '✅',
      color: 'green',
    },
    {
      title: 'Pending Enrichment',
      value: stats?.pending_enrichment || 0,
      icon: '⏳',
      color: 'yellow',
    },
    {
      title: 'Failed',
      value: stats?.failed_articles || 0,
      icon: '❌',
      color: 'red',
    },
  ];

  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statCards.map((stat, index) => (
        <Card key={index}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 uppercase tracking-wide mb-1">
                {stat.title}
              </p>
              <p className={`text-3xl font-bold ${colorClasses[stat.color]}`}>
                {stat.value.toLocaleString()}
              </p>
            </div>
            <div className="text-4xl">{stat.icon}</div>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default StatsCards;

