import React, { useState, useEffect } from 'react';
import { Modal, Input, Button } from '../common';

/**
 * Seed URL Modal Component - Add/Edit seed URLs
 */
const SeedUrlModal = ({ isOpen, onClose, onSave, seedUrl }) => {
  const [formData, setFormData] = useState({
    partner_name: '',
    url: '',
    category: '',
    frequency_minutes: 60,
    is_active: true,
  });

  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (seedUrl) {
      setFormData({
        partner_name: seedUrl.partner_name || '',
        url: seedUrl.url || '',
        category: Array.isArray(seedUrl.category) ? seedUrl.category.join(', ') : seedUrl.category || '',
        frequency_minutes: seedUrl.frequency_minutes || 60,
        is_active: seedUrl.is_active !== undefined ? seedUrl.is_active : true,
      });
    } else {
      setFormData({
        partner_name: '',
        url: '',
        category: '',
        frequency_minutes: 60,
        is_active: true,
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
      // Convert category string to array if it contains commas
      const categoryValue = formData.category.includes(',')
        ? formData.category.split(',').map(c => c.trim()).filter(Boolean)
        : formData.category.trim();

      const dataToSave = {
        ...formData,
        category: categoryValue,
        frequency_minutes: parseInt(formData.frequency_minutes, 10),
      };

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
          placeholder="https://example.com/rss"
          required
        />

        <Input
          label="Category"
          name="category"
          value={formData.category}
          onChange={handleChange}
          error={errors.category}
          placeholder="e.g., technology, sports (comma-separated for multiple)"
          helperText="Enter one or more categories separated by commas"
        />

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

