import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Input, Button } from '../../common';
import { productService } from '../../../services';
import { useToast } from '../../../hooks/useToast';

/**
 * Step 1: Product Description
 */
const Step1_ProductDescription = forwardRef(({ formData, onComplete }, ref) => {
  const [productName, setProductName] = useState(formData.product_name || '');
  const [description, setDescription] = useState(formData.description || '');
  const [category, setCategory] = useState(formData.category || 'General');
  const [price, setPrice] = useState(formData.price || '');
  const [currency, setCurrency] = useState(formData.currency || 'USD');
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  const categories = [
    'General',
    'Electronics',
    'Clothing',
    'Shoes',
    'Accessories',
    'Home & Garden',
    'Sports',
    'Beauty',
    'Food & Beverage',
    'Books',
    'Toys',
    'Other'
  ];

  const currencies = ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'CNY'];

  // Expose handleNext to parent via ref
  useImperativeHandle(ref, () => ({
    handleNext
  }));

  const handleNext = async () => {
    // Validation
    if (!productName.trim()) {
      showToast('⚠️ Product name is required', 'error', 4000);
      return;
    }
    if (!description.trim()) {
      showToast('⚠️ Product description is required', 'error', 4000);
      return;
    }

    // Validate price if provided
    if (price && (isNaN(parseFloat(price)) || parseFloat(price) < 0)) {
      showToast('⚠️ Please enter a valid price', 'error', 4000);
      return;
    }

    try {
      setLoading(true);

      const data = {
        product_name: productName,
        description: description,
        category: category,
        price: price ? parseFloat(price) : null,
        currency: currency
      };

      // Create or update product
      let productId = formData.product_id;

      if (productId) {
        // Update existing product
        await productService.updateProduct(productId, data);
        showToast('✅ Product updated successfully', 'success');
      } else {
        // Create new product
        const response = await productService.createProduct(data);
        if (response.data.status === 'success') {
          productId = response.data.product_id;
          showToast('✅ Product created successfully', 'success');
        } else {
          throw new Error(response.data.message || 'Failed to create product');
        }
      }

      // Pass data to next step
      onComplete({
        ...data,
        product_id: productId
      });

    } catch (error) {
      console.error('❌ Error saving product:', error);

      // Provide more specific error messages
      let errorMessage = 'Failed to save product. Please try again.';

      if (error.response) {
        const status = error.response.status;
        const data = error.response.data;

        if (status === 401) {
          errorMessage = '🔒 Session expired. Please log in again.';
        } else if (status === 400) {
          errorMessage = `⚠️ ${data?.message || 'Invalid product data'}`;
        } else if (status === 500) {
          errorMessage = '⚠️ Server error. Please try again later.';
        } else if (data?.message) {
          errorMessage = `❌ ${data.message}`;
        }
      } else if (error.request) {
        errorMessage = '🌐 Network error. Please check your connection.';
      } else if (error.message) {
        errorMessage = `❌ ${error.message}`;
      }

      showToast(errorMessage, 'error', 6000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">📝 Product Information</h3>
        <p className="text-gray-600">Enter the basic details about your product</p>
      </div>

      <div className="space-y-4">
        <Input
          label="Product Name *"
          type="text"
          placeholder="e.g., Nike Air Max 2024"
          value={productName}
          onChange={(e) => setProductName(e.target.value)}
          helperText="Enter a clear, descriptive product name"
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Product Description *
          </label>
          <textarea
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            rows="6"
            placeholder="Describe your product in detail. Include key features, benefits, and what makes it special..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <p className="mt-1 text-sm text-gray-500">
            {description.length} characters
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Input
              label="Price"
              type="number"
              placeholder="149.99"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              step="0.01"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Currency
              </label>
              <select
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
              >
                {currencies.map((curr) => (
                  <option key={curr} value={curr}>{curr}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

Step1_ProductDescription.displayName = 'Step1_ProductDescription';

export default Step1_ProductDescription;

