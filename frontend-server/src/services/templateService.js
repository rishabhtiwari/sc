/**
 * Template Service
 * Handles API calls for template management
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';

/**
 * Get authentication headers
 */
const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

/**
 * List all templates
 * @param {string} category - Optional category filter (news, shorts, ecommerce)
 * @returns {Promise<Object>} Templates list
 */
const listTemplates = async (category = null) => {
  try {
    const url = new URL(`${API_BASE_URL}/templates`);
    if (category) {
      url.searchParams.append('category', category);
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch templates: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error listing templates:', error);
    throw error;
  }
};

/**
 * Get template by ID
 * @param {string} templateId - Template identifier
 * @returns {Promise<Object>} Template details
 */
const getTemplate = async (templateId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch template: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting template:', error);
    throw error;
  }
};

/**
 * Resolve template with variables
 * @param {Object} params - Resolution parameters
 * @param {string} params.customer_id - Customer ID
 * @param {string} params.template_type - Template type (long_video, shorts, product)
 * @param {string} params.template_id - Optional template ID override
 * @param {Object} params.variables - Template variables
 * @returns {Promise<Object>} Resolved template
 */
const resolveTemplate = async ({ customer_id, template_type, template_id, variables }) => {
  try {
    const response = await fetch(`${API_BASE_URL}/templates/resolve`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        customer_id,
        template_type,
        template_id,
        variables
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to resolve template: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error resolving template:', error);
    throw error;
  }
};

/**
 * Create or update template
 * @param {Object} template - Template definition
 * @returns {Promise<Object>} Created/updated template
 */
const saveTemplate = async (template) => {
  try {
    // This would call a create/update endpoint (to be implemented in template-service)
    const response = await fetch(`${API_BASE_URL}/templates`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(template)
    });

    if (!response.ok) {
      throw new Error(`Failed to save template: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error saving template:', error);
    throw error;
  }
};

/**
 * Delete template
 * @param {string} templateId - Template identifier
 * @returns {Promise<Object>} Deletion result
 */
const deleteTemplate = async (templateId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/templates/${templateId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to delete template: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error deleting template:', error);
    throw error;
  }
};

export const templateService = {
  listTemplates,
  getTemplate,
  resolveTemplate,
  saveTemplate,
  deleteTemplate
};

