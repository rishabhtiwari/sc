import React, { useState } from 'react';
import Button from '../Button';
import ConfirmDialog from '../ConfirmDialog';

/**
 * OutputSchemaBuilder - Visual interface for defining output structure
 *
 * Allows users to define what fields they want in the AI's response
 * without needing to understand JSON schemas.
 */
const OutputSchemaBuilder = ({ fields = [], onChange }) => {
  const [editingIndex, setEditingIndex] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, index: null, field: null });
  const [editForm, setEditForm] = useState({
    name: '',
    type: 'text',
    description: '',
    required: true,
    minLength: '',
    maxLength: '',
    minItems: '',
    maxItems: '',
    min: '',
    max: ''
  });

  const fieldTypes = [
    { value: 'text', label: '📝 Text', description: 'Short text output', hasLength: true },
    { value: 'long_text', label: '📄 Long Text', description: 'Paragraph or multiple sentences', hasLength: true },
    { value: 'number', label: '🔢 Number', description: 'Numeric value', hasRange: true },
    { value: 'list', label: '📋 List', description: 'Multiple items (array)', hasList: true },
    { value: 'boolean', label: '✅ Yes/No', description: 'True or false value' }
  ];

  const handleAdd = () => {
    setEditingIndex(-1);
    setEditForm({
      name: '',
      type: 'text',
      description: '',
      required: true,
      minLength: '',
      maxLength: '',
      minItems: '',
      maxItems: '',
      min: '',
      max: ''
    });
  };

  const handleEdit = (index) => {
    setEditingIndex(index);
    setEditForm({ ...fields[index] });
  };

  const handleSave = () => {
    const newField = {
      ...editForm,
      name: editForm.name.toLowerCase().replace(/[^a-z0-9_]/g, '_')
    };

    let newFields;
    if (editingIndex === -1) {
      newFields = [...fields, newField];
    } else {
      newFields = [...fields];
      newFields[editingIndex] = newField;
    }

    onChange(newFields);
    setEditingIndex(null);
  };

  const handleDelete = (index) => {
    const field = fields[index];
    setDeleteDialog({ isOpen: true, index, field });
  };

  const confirmDelete = () => {
    const newFields = fields.filter((_, i) => i !== deleteDialog.index);
    onChange(newFields);
    setDeleteDialog({ isOpen: false, index: null, field: null });
  };

  const handleCancel = () => {
    setEditingIndex(null);
  };

  const getFieldTypeInfo = (type) => {
    return fieldTypes.find(t => t.value === type) || fieldTypes[0];
  };

  return (
    <div className="output-schema-builder">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-800">
          <strong>💡 What are Output Fields?</strong><br />
          These define what information the AI will generate for you. 
          For example: product description, key features, call-to-action, etc.
        </p>
      </div>

      {/* Field List */}
      {fields.length > 0 && (
        <div className="space-y-3 mb-6">
          {fields.map((field, index) => {
            const typeInfo = getFieldTypeInfo(field.type);
            return (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold text-gray-800">{field.name}</span>
                      <span className="text-xs text-gray-500">{typeInfo.label}</span>
                      {field.required && (
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                          Required
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{field.description}</p>
                    <div className="flex gap-4 text-xs text-gray-500">
                      {field.minLength && <span>Min: {field.minLength} chars</span>}
                      {field.maxLength && <span>Max: {field.maxLength} chars</span>}
                      {field.minItems && <span>Min: {field.minItems} items</span>}
                      {field.maxItems && <span>Max: {field.maxItems} items</span>}
                      {field.min && <span>Min: {field.min}</span>}
                      {field.max && <span>Max: {field.max}</span>}
                    </div>
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
            );
          })}
        </div>
      )}

      {/* Empty State */}
      {fields.length === 0 && editingIndex === null && (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-6">
          <p className="text-gray-500 mb-4">
            No output fields defined yet. Add fields to specify what the AI should generate.
          </p>
        </div>
      )}

      {/* Add Button */}
      {editingIndex === null && (
        <Button onClick={handleAdd} variant="primary">
          ➕ Add Output Field
        </Button>
      )}

      {/* Edit Form */}
      {editingIndex !== null && (
        <OutputFieldForm
          editForm={editForm}
          setEditForm={setEditForm}
          fieldTypes={fieldTypes}
          onSave={handleSave}
          onCancel={handleCancel}
          isNew={editingIndex === -1}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, index: null, field: null })}
        onConfirm={confirmDelete}
        title="Delete Output Field"
        message={
          deleteDialog.field
            ? `Are you sure you want to delete the "${deleteDialog.field.name}" field?`
            : 'Are you sure you want to delete this field?'
        }
      />
    </div>
  );
};

/**
 * OutputFieldForm - Form for editing output field
 */
const OutputFieldForm = ({ editForm, setEditForm, fieldTypes, onSave, onCancel, isNew }) => {
  const selectedType = fieldTypes.find(t => t.value === editForm.type) || fieldTypes[0];

  return (
    <div className="border border-blue-300 rounded-lg p-6 bg-blue-50 mt-6">
      <h3 className="text-lg font-semibold mb-4">
        {isNew ? '➕ Add New Output Field' : '✏️ Edit Output Field'}
      </h3>

      <div className="space-y-4">
        {/* Field Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Field Name <span className="text-red-500">*</span>
            <span className="text-gray-500 text-xs ml-2">
              (Will be: {editForm.name.toLowerCase().replace(/[^a-z0-9_]/g, '_') || 'field_name'})
            </span>
          </label>
          <input
            type="text"
            value={editForm.name}
            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
            placeholder="e.g., Product Description"
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
            {fieldTypes.map(type => (
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
            <span className="text-gray-500 text-xs ml-2">(What should the AI generate here?)</span>
          </label>
          <textarea
            value={editForm.description}
            onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
            placeholder="e.g., A compelling product description highlighting benefits"
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        {/* Required Checkbox */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="output-required"
            checked={editForm.required}
            onChange={(e) => setEditForm({ ...editForm, required: e.target.checked })}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <label htmlFor="output-required" className="ml-2 text-sm text-gray-700">
            This field is required in the output
          </label>
        </div>

        {/* Length Constraints (for text) */}
        {selectedType.hasLength && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Length (characters)
              </label>
              <input
                type="number"
                value={editForm.minLength}
                onChange={(e) => setEditForm({ ...editForm, minLength: e.target.value })}
                placeholder="e.g., 50"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Length (characters)
              </label>
              <input
                type="number"
                value={editForm.maxLength}
                onChange={(e) => setEditForm({ ...editForm, maxLength: e.target.value })}
                placeholder="e.g., 500"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}

        {/* List Constraints */}
        {selectedType.hasList && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Items
              </label>
              <input
                type="number"
                value={editForm.minItems}
                onChange={(e) => setEditForm({ ...editForm, minItems: e.target.value })}
                placeholder="e.g., 3"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Items
              </label>
              <input
                type="number"
                value={editForm.maxItems}
                onChange={(e) => setEditForm({ ...editForm, maxItems: e.target.value })}
                placeholder="e.g., 8"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}

        {/* Number Range */}
        {selectedType.hasRange && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Value
              </label>
              <input
                type="number"
                value={editForm.min}
                onChange={(e) => setEditForm({ ...editForm, min: e.target.value })}
                placeholder="e.g., 0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Value
              </label>
              <input
                type="number"
                value={editForm.max}
                onChange={(e) => setEditForm({ ...editForm, max: e.target.value })}
                placeholder="e.g., 100"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          <Button onClick={onSave} variant="primary">
            ✅ Save Field
          </Button>
          <Button onClick={onCancel} variant="secondary">
            ❌ Cancel
          </Button>
        </div>
      </div>
    </div>
  );
};

export default OutputSchemaBuilder;

