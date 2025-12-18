import React, { useState, useEffect } from 'react';
import { Modal, Input, Button } from '../common';
import newsService from '../../services/newsService';

/**
 * Seed URL Modal Component - Add/Edit seed URLs
 */
const SeedUrlModal = ({ isOpen, onClose, onSave, seedUrl }) => {
  const [formData, setFormData] = useState({
    partner_name: '',
    url: '',
    category: [],
    country: 'in',
    language: 'en',
    frequency_minutes: 60,
    is_active: true,
    api_key: '',
  });

  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [availableCategories, setAvailableCategories] = useState([]);

  // Fetch supported categories for seed URL configuration on mount
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await newsService.getSupportedCategories();
        if (response.data?.categories) {
          setAvailableCategories(response.data.categories);
        }
      } catch (error) {
        console.error('Failed to fetch supported categories:', error);
        // Fallback to default categories
        setAvailableCategories(['general', 'world', 'nation', 'business', 'technology', 'entertainment', 'sports', 'science', 'health']);
      }
    };
    fetchCategories();
  }, []);

  useEffect(() => {
    if (seedUrl) {
      setFormData({
        partner_name: seedUrl.partner_name || '',
        url: seedUrl.url || '',
        category: Array.isArray(seedUrl.category) ? seedUrl.category : (seedUrl.category ? [seedUrl.category] : []),
        country: seedUrl.country || 'in',
        language: seedUrl.language || 'en',
        frequency_minutes: seedUrl.frequency_minutes || 60,
        is_active: seedUrl.is_active !== undefined ? seedUrl.is_active : true,
        api_key: seedUrl.parameters?.api_key?.default || '',
      });
    } else {
      setFormData({
        partner_name: '',
        url: '',
        category: [],
        country: 'in',
        language: 'en',
        frequency_minutes: 60,
        is_active: true,
        api_key: '',
      });
    }
    setErrors({});
  }, [seedUrl, isOpen]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleCategoryToggle = (category) => {
    setFormData(prev => {
      const currentCategories = prev.category || [];
      const isSelected = currentCategories.includes(category);

      return {
        ...prev,
        category: isSelected
          ? currentCategories.filter(c => c !== category)
          : [...currentCategories, category]
      };
    });

    // Clear error for category field
    if (errors.category) {
      setErrors(prev => ({ ...prev, category: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    
    if (!formData.partner_name.trim()) {
      newErrors.partner_name = 'Partner name is required';
    }
    
    if (!formData.url.trim()) {
      newErrors.url = 'URL is required';
    } else if (!/^https?:\/\/.+/.test(formData.url)) {
      newErrors.url = 'Please enter a valid URL';
    }
    
    if (formData.frequency_minutes < 1) {
      newErrors.frequency_minutes = 'Frequency must be at least 1 minute';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setSaving(true);
    try {
      const dataToSave = {
        ...formData,
        category: formData.category.length === 1 ? formData.category[0] : formData.category,
        frequency_minutes: parseInt(formData.frequency_minutes, 10),
      };

      // Build parameters object if api_key is provided
      if (formData.api_key && formData.api_key.trim()) {
        dataToSave.parameters = {
          api_key: {
            type: 'string',
            required: true,
            description: 'API key for the news provider',
            default: formData.api_key.trim()
          }
        };
      }

      await onSave(dataToSave);
      onClose();
    } catch (error) {
      setErrors({ submit: error.message || 'Failed to save seed URL' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={seedUrl ? 'Edit Seed URL' : 'Add Seed URL'}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Partner Name"
          name="partner_name"
          value={formData.partner_name}
          onChange={handleChange}
          error={errors.partner_name}
          placeholder="e.g., Times of India"
          required
        />

        <Input
          label="URL"
          name="url"
          type="url"
          value={formData.url}
          onChange={handleChange}
          error={errors.url}
          placeholder="https://gnews.io/api/v4/top-headlines?category={category}&apikey={api_key}"
          required
        />

        <Input
          label="API Key (Optional)"
          name="api_key"
          type="text"
          value={formData.api_key}
          onChange={handleChange}
          error={errors.api_key}
          placeholder="Enter API key if URL contains {api_key} placeholder"
          helpText="Required only if your URL template uses {api_key} placeholder"
        />

        {/* Category Checkboxes */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Categories *
          </label>
          <div className="grid grid-cols-2 gap-2 p-3 border border-gray-300 rounded-lg bg-gray-50">
            {availableCategories.map((cat) => (
              <div key={cat} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id={`category-${cat}`}
                  checked={formData.category.includes(cat)}
                  onChange={() => handleCategoryToggle(cat)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label htmlFor={`category-${cat}`} className="text-sm text-gray-700 capitalize">
                  {cat}
                </label>
              </div>
            ))}
          </div>
          {errors.category && (
            <p className="text-sm text-red-600">{errors.category}</p>
          )}
        </div>

        {/* Country */}
        <div className="space-y-2">
          <label htmlFor="country" className="block text-sm font-medium text-gray-700">
            Country
          </label>
          <select
            id="country"
            name="country"
            value={formData.country}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="in">India (in)</option>
            <option value="us">United States (us)</option>
            <option value="gb">United Kingdom (gb)</option>
            <option value="au">Australia (au)</option>
            <option value="ca">Canada (ca)</option>
          </select>
        </div>

        {/* Language */}
        <div className="space-y-2">
          <label htmlFor="language" className="block text-sm font-medium text-gray-700">
            Language
          </label>
          <select
            id="language"
            name="language"
            value={formData.language}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="en">English (en)</option>
            <option value="hi">Hindi (hi)</option>
            <option value="es">Spanish (es)</option>
            <option value="fr">French (fr)</option>
            <option value="de">German (de)</option>
          </select>
        </div>

        <Input
          label="Fetch Frequency (minutes)"
          name="frequency_minutes"
          type="number"
          value={formData.frequency_minutes}
          onChange={handleChange}
          error={errors.frequency_minutes}
          min="1"
          required
        />

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_active"
            name="is_active"
            checked={formData.is_active}
            onChange={handleChange}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
            Active (enable fetching)
          </label>
        </div>

        {errors.submit && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {errors.submit}
          </div>
        )}

        <div className="flex gap-3 justify-end pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={saving}
          >
            {seedUrl ? 'Update' : 'Add'} Seed URL
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default SeedUrlModal;

