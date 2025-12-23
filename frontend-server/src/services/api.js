import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api',
  timeout: 600000, // 10 minutes for long-running operations like LLM generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add customer and user context headers
    const userInfo = localStorage.getItem('user_info');
    if (userInfo) {
      try {
        const user = JSON.parse(userInfo);
        if (user.customer_id) {
          config.headers['X-Customer-ID'] = user.customer_id;
        }
        if (user.user_id) {
          config.headers['X-User-ID'] = user.user_id;
        }
      } catch (e) {
        console.error('Failed to parse user info:', e);
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle errors globally
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;

      if (status === 401) {
        // Unauthorized - redirect to login
        console.error('Unauthorized - redirecting to login');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        window.location.href = '/login';
      } else if (status === 403) {
        // Forbidden - permission denied
        console.error('Permission denied:', error.response.data);
      } else {
        console.error('API Error:', status, error.response.data);
      }
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;

