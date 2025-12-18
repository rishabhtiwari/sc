// Migration: 022_create_roles_collection.js
// Description: Create roles collection for RBAC
// Created: 2025-12-16

print('Starting migration: 022_create_roles_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create roles collection
db.createCollection('roles');
print('✓ Created roles collection');

// Create indexes
db.roles.createIndex({ "role_id": 1 }, { unique: true, name: "idx_role_id" });
print('✓ Created index: role_id (unique)');

db.roles.createIndex({ "customer_id": 1, "slug": 1 }, { unique: true, name: "idx_customer_slug" });
print('✓ Created index: customer_id + slug (compound unique)');

db.roles.createIndex({ "role_type": 1 }, { name: "idx_role_type" });
print('✓ Created index: role_type');

db.roles.createIndex({ "customer_id": 1 }, { name: "idx_customer_id" });
print('✓ Created index: customer_id');

// Add schema validation
db.runCommand({
    collMod: 'roles',
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['role_id', 'role_name', 'slug', 'role_type', 'created_at'],
            properties: {
                role_id: {
                    bsonType: 'string',
                    description: 'Unique role identifier (UUID) - required'
                },
                customer_id: {
                    bsonType: ['string', 'null'],
                    description: 'Customer ID (null for system roles)'
                },
                role_name: {
                    bsonType: 'string',
                    minLength: 1,
                    maxLength: 100,
                    description: 'Role display name - required'
                },
                slug: {
                    bsonType: 'string',
                    pattern: '^[a-z0-9_-]+$',
                    minLength: 1,
                    maxLength: 50,
                    description: 'Role slug (lowercase, alphanumeric, underscores, hyphens) - required'
                },
                description: {
                    bsonType: ['string', 'null'],
                    maxLength: 500,
                    description: 'Role description'
                },
                permissions: {
                    bsonType: 'array',
                    items: {
                        bsonType: 'string'
                    },
                    description: 'Array of permission keys'
                },
                role_type: {
                    bsonType: 'string',
                    enum: ['system', 'custom'],
                    description: 'Role type: system or custom - required'
                },
                is_default: {
                    bsonType: 'bool',
                    description: 'Whether this is the default role for new users'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Creation timestamp - required'
                },
                updated_at: {
                    bsonType: 'date',
                    description: 'Last update timestamp'
                },
                created_by: {
                    bsonType: ['string', 'null'],
                    description: 'User ID who created this role'
                },
                is_deleted: {
                    bsonType: 'bool',
                    description: 'Soft delete flag'
                }
            }
        }
    },
    validationLevel: 'moderate',
    validationAction: 'warn'
});
print('✓ Added schema validation rules');

print('✓ Migration 022_create_roles_collection completed successfully');

