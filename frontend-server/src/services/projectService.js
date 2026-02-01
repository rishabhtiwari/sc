/**
 * Project Service
 * Handles design editor project save/load operations
 */
import api from './api';

// Use relative API path (proxied through frontend server)
const API_BASE_URL = '/api';

class ProjectService {
  /**
   * Save current project
   * @param {Object} projectData - Project data to save
   * @returns {Promise<Object>} Saved project
   */
  async saveProject(projectData) {
    try {
      const response = await api.post('/projects/', projectData);
      return response.data;
    } catch (error) {
      console.error('Error saving project:', error);
      throw error;
    }
  }

  /**
   * Update existing project
   * @param {string} projectId - Project ID
   * @param {Object} updateData - Data to update
   * @returns {Promise<Object>} Updated project
   */
  async updateProject(projectId, updateData) {
    try {
      const response = await api.put(`/projects/${projectId}`, updateData);
      return response.data;
    } catch (error) {
      console.error('Error updating project:', error);
      throw error;
    }
  }

  /**
   * Load project by ID
   * @param {string} projectId - Project ID
   * @returns {Promise<Object>} Project data
   */
  async loadProject(projectId) {
    try {
      const response = await api.get(`/projects/${projectId}`);
      return response.data;
    } catch (error) {
      console.error('Error loading project:', error);
      throw error;
    }
  }

  /**
   * List all projects
   * @param {Object} filters - Filter options (user_id, status, skip, limit)
   * @returns {Promise<Array>} List of projects
   */
  async listProjects(filters = {}) {
    try {
      const params = new URLSearchParams(filters).toString();
      const response = await api.get(`/projects/?${params}`);
      return response.data;
    } catch (error) {
      console.error('Error listing projects:', error);
      throw error;
    }
  }

  /**
   * Delete project
   * @param {string} projectId - Project ID
   * @param {boolean} hardDelete - If true, permanently delete
   * @returns {Promise<Object>} Delete result
   */
  async deleteProject(projectId, hardDelete = false) {
    try {
      const response = await api.delete(`/projects/${projectId}?hard=${hardDelete}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting project:', error);
      throw error;
    }
  }

  /**
   * Upload asset (audio/video/image) and get asset ID
   * @param {File} file - File to upload
   * @param {string} type - Asset type (audio, video, image)
   * @returns {Promise<Object>} Asset data with asset_id
   */
  async uploadAsset(file, type) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type', type);  // Changed from 'type' to 'asset_type'
      formData.append('name', file.name);

      const response = await api.post('/assets/upload', formData);
      return response.data.asset;
    } catch (error) {
      console.error('Error uploading asset:', error);
      throw error;
    }
  }
}

export default new ProjectService();

