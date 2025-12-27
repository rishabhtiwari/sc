import { useState, useCallback } from 'react';
import api from '../services/api';

/**
 * Generic hook for AI content generation
 * Works with any content type (product summaries, news articles, social posts, etc.)
 */
export const useContentGeneration = () => {
  const [generating, setGenerating] = useState(false);
  const [content, setContent] = useState(null);
  const [error, setError] = useState(null);

  /**
   * Generate content using LLM service
   * @param {Object} options - Generation options
   * @param {string} options.endpoint - API endpoint to call
   * @param {Object} options.data - Data to send to the endpoint
   * @param {Function} options.onSuccess - Callback on success
   * @param {Function} options.onError - Callback on error
   */
  const generate = useCallback(async (options) => {
    const { endpoint, data, onSuccess, onError } = options;

    setGenerating(true);
    setError(null);

    try {
      const response = await api.post(endpoint, data);

      if (response.data.status === 'success') {
        // Backend now sends 'content_text' (formatted text) and 'content' (raw JSON)
        // Prefer content_text for display, fallback to other fields for backward compatibility
        const generatedContent = response.data.content_text || response.data.ai_summary || response.data.content || response.data.result;
        setContent(generatedContent);

        if (onSuccess) {
          onSuccess(generatedContent, response.data);
        }

        return { success: true, content: generatedContent, data: response.data };
      } else {
        const errorMsg = response.data.message || 'Content generation failed';
        setError(errorMsg);
        
        if (onError) {
          onError(errorMsg);
        }

        return { success: false, error: errorMsg };
      }
    } catch (err) {
      console.error('Content generation error:', err);
      const errorMsg = err.response?.data?.message || err.message || 'Failed to generate content';
      setError(errorMsg);
      
      if (onError) {
        onError(errorMsg);
      }

      return { success: false, error: errorMsg };
    } finally {
      setGenerating(false);
    }
  }, []);

  /**
   * Generate content directly using LLM service
   * @param {Object} options - Generation options
   * @param {string} options.prompt - The prompt to send to LLM
   * @param {string} options.model - LLM model to use (optional)
   * @param {boolean} options.useRag - Whether to use RAG (optional)
   * @param {Function} options.onSuccess - Callback on success
   * @param {Function} options.onError - Callback on error
   */
  const generateWithLLM = useCallback(async (options) => {
    const { prompt, model = 'gpt-4', useRag = false, onSuccess, onError } = options;

    return generate({
      endpoint: '/api/llm/generate',
      data: {
        query: prompt,
        model,
        use_rag: useRag
      },
      onSuccess: (content, data) => {
        if (onSuccess) {
          onSuccess(data.response || content, data);
        }
      },
      onError
    });
  }, [generate]);

  /**
   * Reset the hook state
   */
  const reset = useCallback(() => {
    setGenerating(false);
    setContent(null);
    setError(null);
  }, []);

  return {
    generating,
    content,
    error,
    generate,
    generateWithLLM,
    reset,
    setContent
  };
};

