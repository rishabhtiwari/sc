import { useState, useEffect, useCallback } from 'react';
import { templateService } from '../services';

/**
 * Hook for managing templates
 * Fetches and manages template selection
 */
export const useTemplates = (initialTemplateId = null) => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(initialTemplateId);
  const [selectedTemplateDetails, setSelectedTemplateDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetch all templates
   */
  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await templateService.getTemplates();
      
      if (response.data.status === 'success') {
        setTemplates(response.data.templates || []);
      } else {
        setError(response.data.message || 'Failed to load templates');
      }
    } catch (err) {
      console.error('Error fetching templates:', err);
      setError(err.response?.data?.message || err.message || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch template details by ID
   */
  const fetchTemplateDetails = useCallback(async (templateId) => {
    if (!templateId) {
      setSelectedTemplateDetails(null);
      return;
    }

    try {
      const response = await templateService.getTemplate(templateId);
      
      if (response.data.status === 'success') {
        setSelectedTemplateDetails(response.data.template);
        return response.data.template;
      } else {
        setError(response.data.message || 'Failed to load template details');
        return null;
      }
    } catch (err) {
      console.error('Error fetching template details:', err);
      setError(err.response?.data?.message || err.message || 'Failed to load template details');
      return null;
    }
  }, []);

  /**
   * Select a template and fetch its details
   */
  const selectTemplate = useCallback(async (templateId) => {
    setSelectedTemplate(templateId);
    return await fetchTemplateDetails(templateId);
  }, [fetchTemplateDetails]);

  /**
   * Get template variables from template details
   */
  const getTemplateVariables = useCallback(() => {
    if (!selectedTemplateDetails) return [];
    return selectedTemplateDetails.variables || [];
  }, [selectedTemplateDetails]);

  /**
   * Get template sections from template details
   */
  const getTemplateSections = useCallback(() => {
    if (!selectedTemplateDetails) return [];
    return selectedTemplateDetails.sections || [];
  }, [selectedTemplateDetails]);

  // Load templates on mount
  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  // Load template details when selectedTemplate changes
  useEffect(() => {
    if (selectedTemplate) {
      fetchTemplateDetails(selectedTemplate);
    }
  }, [selectedTemplate, fetchTemplateDetails]);

  return {
    templates,
    selectedTemplate,
    selectedTemplateDetails,
    loading,
    error,
    fetchTemplates,
    fetchTemplateDetails,
    selectTemplate,
    setSelectedTemplate,
    getTemplateVariables,
    getTemplateSections
  };
};

