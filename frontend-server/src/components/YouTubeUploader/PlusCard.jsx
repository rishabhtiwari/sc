import React from 'react';

/**
 * Plus Card Component - Create new video configuration
 */
const PlusCard = ({ onClick }) => {
  return (
    <button
      onClick={onClick}
      className="bg-white border-2 border-dashed border-gray-300 rounded-lg shadow-sm hover:shadow-md hover:border-red-400 transition-all h-full min-h-[200px] flex flex-col items-center justify-center gap-3 p-6 group"
    >
      <div className="w-16 h-16 rounded-full bg-gray-100 group-hover:bg-red-50 flex items-center justify-center transition-colors">
        <svg
          className="w-8 h-8 text-gray-400 group-hover:text-red-600 transition-colors"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4v16m8-8H4"
          />
        </svg>
      </div>
      <div className="text-center">
        <p className="text-lg font-semibold text-gray-700 group-hover:text-red-600 transition-colors">
          Create New Configuration
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Click to add a new video configuration
        </p>
      </div>
    </button>
  );
};

export default PlusCard;

