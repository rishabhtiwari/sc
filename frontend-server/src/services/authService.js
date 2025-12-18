/**
 * Authentication Service
 * Handles all authentication-related API calls
 */

import api from './api';

const AUTH_BASE_URL = '/auth';

/**
 * Login user
 */
export const login = async (email, password) => {
  const response = await api.post(`${AUTH_BASE_URL}/login`, {
    email,
    password
  });
  
  if (response.data.success && response.data.token) {
    // Store token and user info
    localStorage.setItem('auth_token', response.data.token);
    localStorage.setItem('user_info', JSON.stringify(response.data.user));
  }
  
  return response.data;
};

/**
 * Logout user
 */
export const logout = async () => {
  try {
    await api.post(`${AUTH_BASE_URL}/logout`);
  } finally {
    // Clear local storage regardless of API response
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  }
};

/**
 * Verify token
 */
export const verifyToken = async () => {
  const response = await api.post(`${AUTH_BASE_URL}/verify`);
  return response.data;
};

/**
 * Get current user from local storage
 */
export const getCurrentUser = () => {
  const userInfo = localStorage.getItem('user_info');
  return userInfo ? JSON.parse(userInfo) : null;
};

/**
 * Get auth token from local storage
 */
export const getAuthToken = () => {
  return localStorage.getItem('auth_token');
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  return !!getAuthToken();
};

/**
 * Check if user has specific permission
 */
export const hasPermission = (permission) => {
  const user = getCurrentUser();
  return user?.permissions?.includes(permission) || false;
};

/**
 * Check if user has any of the specified permissions
 */
export const hasAnyPermission = (permissions) => {
  const user = getCurrentUser();
  return permissions.some(permission => user?.permissions?.includes(permission));
};

/**
 * Check if user has all of the specified permissions
 */
export const hasAllPermissions = (permissions) => {
  const user = getCurrentUser();
  return permissions.every(permission => user?.permissions?.includes(permission));
};

/**
 * Forgot password
 */
export const forgotPassword = async (email) => {
  const response = await api.post(`${AUTH_BASE_URL}/forgot-password`, { email });
  return response.data;
};

/**
 * Reset password
 */
export const resetPassword = async (token, newPassword) => {
  const response = await api.post(`${AUTH_BASE_URL}/reset-password`, {
    token,
    new_password: newPassword
  });
  return response.data;
};

// Customer Management APIs

/**
 * Register new customer (Public - no authentication required)
 */
export const registerCustomer = async (customerData) => {
  const response = await api.post(`${AUTH_BASE_URL}/customers/register`, customerData);
  return response.data;
};

/**
 * Get all customers (Super Admin only)
 */
export const getCustomers = async (params = {}) => {
  const response = await api.get(`${AUTH_BASE_URL}/customers`, { params });
  return response.data;
};

/**
 * Create customer (Super Admin only)
 */
export const createCustomer = async (customerData) => {
  const response = await api.post(`${AUTH_BASE_URL}/customers`, customerData);
  return response.data;
};

/**
 * Get customer details
 */
export const getCustomer = async (customerId) => {
  const response = await api.get(`${AUTH_BASE_URL}/customers/${customerId}`);
  return response.data;
};

/**
 * Update customer
 */
export const updateCustomer = async (customerId, customerData) => {
  const response = await api.put(`${AUTH_BASE_URL}/customers/${customerId}`, customerData);
  return response.data;
};

/**
 * Delete customer (Super Admin only)
 */
export const deleteCustomer = async (customerId) => {
  const response = await api.delete(`${AUTH_BASE_URL}/customers/${customerId}`);
  return response.data;
};

// User Management APIs

/**
 * Get all users (filtered by customer)
 */
export const getUsers = async (params = {}) => {
  const response = await api.get(`${AUTH_BASE_URL}/users`, { params });
  return response.data;
};

/**
 * Create user
 */
export const createUser = async (userData) => {
  const response = await api.post(`${AUTH_BASE_URL}/users`, userData);
  return response.data;
};

/**
 * Get user details
 */
export const getUser = async (userId) => {
  const response = await api.get(`${AUTH_BASE_URL}/users/${userId}`);
  return response.data;
};

/**
 * Update user
 */
export const updateUser = async (userId, userData) => {
  const response = await api.put(`${AUTH_BASE_URL}/users/${userId}`, userData);
  return response.data;
};

/**
 * Delete user
 */
export const deleteUser = async (userId) => {
  const response = await api.delete(`${AUTH_BASE_URL}/users/${userId}`);
  return response.data;
};

/**
 * Reset user password
 */
export const resetUserPassword = async (userId, newPassword) => {
  const response = await api.post(`${AUTH_BASE_URL}/users/${userId}/reset-password`, {
    new_password: newPassword
  });
  return response.data;
};

/**
 * Deactivate user
 */
export const deactivateUser = async (userId) => {
  const response = await api.post(`${AUTH_BASE_URL}/users/${userId}/deactivate`);
  return response.data;
};

// Role Management APIs

/**
 * Get all roles
 */
export const getRoles = async () => {
  const response = await api.get(`${AUTH_BASE_URL}/roles`);
  return response.data;
};

/**
 * Get role details
 */
export const getRole = async (roleId) => {
  const response = await api.get(`${AUTH_BASE_URL}/roles/${roleId}`);
  return response.data;
};

/**
 * Get all permissions
 */
export const getPermissions = async () => {
  const response = await api.get(`${AUTH_BASE_URL}/permissions`);
  return response.data;
};

// Audit Log APIs

/**
 * Get audit logs (filtered by customer)
 */
export const getAuditLogs = async (params = {}) => {
  const response = await api.get(`${AUTH_BASE_URL}/audit-logs`, { params });
  return response.data;
};

/**
 * Get audit log details
 */
export const getAuditLog = async (logId) => {
  const response = await api.get(`${AUTH_BASE_URL}/audit-logs/${logId}`);
  return response.data;
};

export default {
  login,
  logout,
  verifyToken,
  getCurrentUser,
  getAuthToken,
  isAuthenticated,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  forgotPassword,
  resetPassword,
  registerCustomer,
  getCustomers,
  createCustomer,
  getCustomer,
  updateCustomer,
  deleteCustomer,
  getUsers,
  createUser,
  getUser,
  updateUser,
  deleteUser,
  resetUserPassword,
  deactivateUser,
  getRoles,
  getRole,
  getPermissions,
  getAuditLogs,
  getAuditLog
};

