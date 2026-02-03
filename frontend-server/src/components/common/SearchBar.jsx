import React from 'react';

/**
 * Generic Search Bar Component
 * Reusable search input with clear button and customizable styling
 * 
 * @param {string} value - Current search value
 * @param {function} onChange - Change handler
 * @param {string} placeholder - Placeholder text
 * @param {string} className - Additional CSS classes
 * @param {boolean} compact - Use compact size (25% of normal)
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
    <div className={`relative ${className}`}>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className={`
          w-full bg-white border border-gray-300 rounded-lg 
          focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 
          transition-all placeholder-gray-400 text-gray-900
          ${compact ? 'px-3 py-1.5 text-sm' : 'px-4 py-2'}
        `}
      />
      {value && (
        <button
          onClick={handleClear}
          className={`
            absolute right-3 top-1/2 -translate-y-1/2 
            text-gray-400 hover:text-gray-600 transition-colors
            ${compact ? 'text-sm' : 'text-lg'}
          `}
          title="Clear search"
        >
          ✕
        </button>
      )}
    </div>
  );
};

export default SearchBar;

