import { useState, useCallback } from 'react';
import api from '../services/api';

/**
 * Custom hook for API calls with loading and error states
 * @param {Function} apiFunction - API function to call
 * @returns {Object} { data, loading, error, execute, reset }
 */
export const useApi = (apiFunction) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(
    async (...args) => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiFunction(...args);
        setData(response.data);
        return response.data;
      } catch (err) {
        const errorMessage = err.response?.data?.error || err.message || 'An error occurred';
        setError(errorMessage);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
};

/**
 * Custom hook for fetching data on mount
 * @param {Function} apiFunction - API function to call
 * @param {Array} dependencies - Dependencies array
 * @returns {Object} { data, loading, error, refetch }
 */
export const useFetch = (apiFunction, dependencies = []) => {
  const { data, loading, error, execute } = useApi(apiFunction);

  const refetch = useCallback(() => {
    execute();
  }, [execute]);

  // Auto-fetch on mount and when dependencies change
  useState(() => {
    execute();
  }, dependencies);

  return { data, loading, error, refetch };
};

