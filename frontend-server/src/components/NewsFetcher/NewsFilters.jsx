import React from 'react';

/**
 * News Filters Component - Filter controls for news articles
 */
const NewsFilters = ({ 
  filters, 
  categories, 
  languages, 
  countries, 
  onFilterChange,
  loading 
}) => {
  const handleChange = (e) => {
    const { name, value } = e.target;
    onFilterChange({ ...filters, [name]: value });
  };

  return (
    <div className="flex flex-wrap gap-4 mb-6">
      <div className="flex flex-col gap-1">
        <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
          Category
        </label>
        <select
          name="category"
          value={filters.category || ''}
          onChange={handleChange}
          disabled={loading}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">All Categories</option>
          {Object.entries(categories || {}).map(([cat, count]) => (
            <option key={cat} value={cat}>
              {cat} ({count})
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
          Language
        </label>
        <select
          name="language"
          value={filters.language || ''}
          onChange={handleChange}
          disabled={loading}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">All Languages</option>
          {Object.entries(languages || {}).map(([lang, count]) => (
            <option key={lang} value={lang}>
              {lang.toUpperCase()} ({count})
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
          Country
        </label>
        <select
          name="country"
          value={filters.country || ''}
          onChange={handleChange}
          disabled={loading}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="">All Countries</option>
          {Object.entries(countries || {}).map(([country, count]) => (
            <option key={country} value={country}>
              {country.toUpperCase()} ({count})
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
          Page Size
        </label>
        <select
          name="pageSize"
          value={filters.pageSize || 25}
          onChange={handleChange}
          disabled={loading}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value="10">10</option>
          <option value="25">25</option>
          <option value="50">50</option>
          <option value="100">100</option>
        </select>
      </div>
    </div>
  );
};

export default NewsFilters;

