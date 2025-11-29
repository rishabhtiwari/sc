import api from './api';

/**
 * LLM Service - API calls for LLM/prompt operations
 */

/**
 * Get all LLM prompts
 * @returns {Promise} API response
 */
export const getPrompts = async () => {
  const response = await api.get('/llm/prompts');
  return response.data;
};

/**
 * Get prompt by ID
 * @param {string} id - Prompt ID
 * @returns {Promise} API response
 */
export const getPromptById = async (id) => {
  const response = await api.get(`/llm/prompts/${id}`);
  return response.data;
};

/**
 * Get prompt by type
 * @param {string} type - Prompt type (summary, title, description, tags)
 * @returns {Promise} API response
 */
export const getPromptByType = async (type) => {
  const response = await api.get(`/llm/prompts/type/${type}`);
  return response.data;
};

/**
 * Create new prompt
 * @param {Object} data - Prompt data
 * @returns {Promise} API response
 */
export const createPrompt = async (data) => {
  const response = await api.post('/llm/prompts', data);
  return response.data;
};

/**
 * Update existing prompt
 * @param {string} id - Prompt ID
 * @param {Object} data - Prompt data
 * @returns {Promise} API response
 */
export const updatePrompt = async (id, data) => {
  const response = await api.put(`/llm/prompts/${id}`, data);
  return response.data;
};

/**
 * Delete prompt
 * @param {string} id - Prompt ID
 * @returns {Promise} API response
 */
export const deletePrompt = async (id) => {
  const response = await api.delete(`/llm/prompts/${id}`);
  return response.data;
};

/**
 * Test prompt with sample data
 * @param {Object} data - { promptId, template, sampleData, maxTokens, temperature }
 * @returns {Promise} API response
 */
export const testPrompt = async (data) => {
  const response = await api.post('/llm/prompts/test', data);
  return response.data;
};

/**
 * Get LLM configuration
 * @returns {Promise} API response
 */
export const getLLMConfig = async () => {
  const response = await api.get('/llm/config');
  return response.data;
};

/**
 * Update LLM configuration
 * @param {Object} data - Configuration data
 * @returns {Promise} API response
 */
export const updateLLMConfig = async (data) => {
  const response = await api.put('/llm/config', data);
  return response.data;
};

export default {
  getPrompts,
  getPromptById,
  getPromptByType,
  createPrompt,
  updatePrompt,
  deletePrompt,
  testPrompt,
  getLLMConfig,
  updateLLMConfig,
};

