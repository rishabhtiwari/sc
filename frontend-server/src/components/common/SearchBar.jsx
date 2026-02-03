import React from 'react';

/**
 * Generic Search Bar Component
 * Reusable search input with clear button and customizable styling
 *
 * @param {string} value - Current search value
 * @param {function} onChange - Change handler
 * @param {string} placeholder - Placeholder text
 * @param {string} className - Additional CSS classes
 * @param {boolean} compact - Use compact width (25% of normal width)
 */
const SearchBar = ({
  value = '',
  onChange,
  placeholder = '🔍 Search...',
  className = '',
  compact = false
}) => {
  const handleClear = () => {
    if (onChange) {
      onChange({ target: { value: '' } });
    }
  };

  return (
    <div className={`relative ${compact ? 'w-1/4' : 'w-full'} ${className}`}>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder-gray-400 text-gray-900"
      />
      {value && (
        <button
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors text-lg"
          title="Clear search"
        >
          ✕
        </button>
      )}
    </div>
  );
};

export default SearchBar;

