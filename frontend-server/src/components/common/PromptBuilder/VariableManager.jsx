import React, { useState } from 'react';
import Button from '../Button';
import ConfirmDialog from '../ConfirmDialog';

/**
 * VariableManager - Visual interface for managing prompt variables
 *
 * Allows users to define input fields that will be filled when using the template.
 * Non-technical users can think of these as "form fields" they need to fill.
 */
const VariableManager = ({ variables = [], onChange }) => {
  const [editingIndex, setEditingIndex] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, index: null, variable: null });
  const [editForm, setEditForm] = useState({
    name: '',
    type: 'text',
    description: '',
    required: true,
    default: ''
  });

  const variableTypes = [
    { value: 'text', label: '📝 Text', description: 'Short text input' },
    { value: 'long_text', label: '📄 Long Text', description: 'Multi-line text' },
    { value: 'number', label: '🔢 Number', description: 'Numeric value' },
    { value: 'url', label: '🔗 URL', description: 'Web link' },
    { value: 'list', label: '📋 List', description: 'Multiple items' }
  ];

  const handleAdd = () => {
    setEditingIndex(-1); // -1 means adding new
    setEditForm({
      name: '',
      type: 'text',
      description: '',
      required: true,
      default: ''
    });
  };

  const handleEdit = (index) => {
    setEditingIndex(index);
    setEditForm({ ...variables[index] });
  };

  const handleSave = () => {
    const newVariable = {
      ...editForm,
      name: editForm.name.toLowerCase().replace(/[^a-z0-9_]/g, '_')
    };

    let newVariables;
    if (editingIndex === -1) {
      // Adding new
      newVariables = [...variables, newVariable];
    } else {
      // Editing existing
      newVariables = [...variables];
      newVariables[editingIndex] = newVariable;
    }

    onChange(newVariables);
    setEditingIndex(null);
  };

  const handleDelete = (index) => {
    const variable = variables[index];
    setDeleteDialog({ isOpen: true, index, variable });
  };

  const confirmDelete = () => {
    const newVariables = variables.filter((_, i) => i !== deleteDialog.index);
    onChange(newVariables);
    setDeleteDialog({ isOpen: false, index: null, variable: null });
  };

  const handleCancel = () => {
    setEditingIndex(null);
  };

  return (
    <div className="variable-manager">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-800">
          <strong>💡 What are Input Fields?</strong><br />
          These are the pieces of information you'll need to provide when using this template.
          For example: product name, price, features, etc.
        </p>
      </div>

      {/* Variable List */}
      {variables.length > 0 && (
        <div className="space-y-3 mb-6">
          {variables.map((variable, index) => (
            <div
              key={index}
              className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                      {`{${variable.name}}`}
                    </span>
                    <span className="text-xs text-gray-500">
                      {variableTypes.find(t => t.value === variable.type)?.label || variable.type}
                    </span>
                    {variable.required && (
                      <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                        Required
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700">{variable.description}</p>
                  {variable.default && (
                    <p className="text-xs text-gray-500 mt-1">
                      Default: {variable.default}
                    </p>
                  )}
                </div>
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handleEdit(index)}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    ✏️ Edit
                  </button>
                  <button
                    onClick={() => handleDelete(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {variables.length === 0 && editingIndex === null && (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6">
          <p className="text-gray-500 mb-4">
            No input fields defined yet. Add fields that users will fill when using this template.
          </p>
        </div>
      )}

      {/* Add Button */}
      {editingIndex === null && (
        <Button onClick={handleAdd} variant="primary">
          ➕ Add Input Field
        </Button>
      )}

      {/* Edit Form */}
      {editingIndex !== null && (
        <div className="border border-blue-300 rounded-lg p-6 bg-blue-50 mt-6">
          <h3 className="text-lg font-semibold mb-4">
            {editingIndex === -1 ? '➕ Add New Input Field' : '✏️ Edit Input Field'}
          </h3>

          <div className="space-y-4">
            {/* Field Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Field Name <span className="text-red-500">*</span>
                <span className="text-gray-500 text-xs ml-2">
                  (Will be converted to: {editForm.name.toLowerCase().replace(/[^a-z0-9_]/g, '_') || 'field_name'})
                </span>
              </label>
              <input
                type="text"
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                placeholder="e.g., Product Name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {/* Field Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Field Type <span className="text-red-500">*</span>
              </label>
              <select
                value={editForm.type}
                onChange={(e) => setEditForm({ ...editForm, type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                {variableTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label} - {type.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description <span className="text-red-500">*</span>
                <span className="text-gray-500 text-xs ml-2">(What should the user enter here?)</span>
              </label>
              <textarea
                value={editForm.description}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                placeholder="e.g., Enter the name of your product"
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {/* Required Checkbox */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="required"
                checked={editForm.required}
                onChange={(e) => setEditForm({ ...editForm, required: e.target.checked })}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="required" className="ml-2 text-sm text-gray-700">
                This field is required
              </label>
            </div>

            {/* Default Value */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Value
                <span className="text-gray-500 text-xs ml-2">(Optional - used if user doesn't provide a value)</span>
              </label>
              <input
                type="text"
                value={editForm.default}
                onChange={(e) => setEditForm({ ...editForm, default: e.target.value })}
                placeholder="e.g., Amazing Product"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button onClick={handleSave} variant="primary">
                ✅ Save Field
              </Button>
              <Button onClick={handleCancel} variant="secondary">
                ❌ Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, index: null, variable: null })}
        onConfirm={confirmDelete}
        title="Delete Input Field"
        description="Remove variable from template"
        message={
          deleteDialog.variable
            ? `Are you sure you want to delete the "${deleteDialog.variable.name}" input field?`
            : ''
        }
        warningMessage="This will remove the variable from the template. You will no longer be able to use this field when generating content."
        confirmText="Delete Field"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default VariableManager;

