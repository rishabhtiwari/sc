// Migration: 023_create_permissions_collection.js
// Description: Create permissions collection and seed with default permissions
// Created: 2025-12-16

print('Starting migration: 023_create_permissions_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create permissions collection
db.createCollection('permissions');
print('✓ Created permissions collection');

// Create indexes
db.permissions.createIndex({ "permission_id": 1 }, { unique: true, name: "idx_permission_id" });
print('✓ Created index: permission_id (unique)');

db.permissions.createIndex({ "permission_key": 1 }, { unique: true, name: "idx_permission_key" });
print('✓ Created index: permission_key (unique)');

db.permissions.createIndex({ "category": 1 }, { name: "idx_category" });
print('✓ Created index: category');

// Add schema validation
db.runCommand({
    collMod: 'permissions',
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['permission_id', 'permission_key', 'category', 'description'],
            properties: {
                permission_id: {
                    bsonType: 'string',
                    description: 'Unique permission identifier - required'
                },
                permission_key: {
                    bsonType: 'string',
                    pattern: '^[a-z_]+\\.[a-z_]+$',
                    description: 'Permission key (category.action) - required'
                },
                category: {
                    bsonType: 'string',
                    description: 'Permission category - required'
                },
                description: {
                    bsonType: 'string',
                    description: 'Permission description - required'
                }
            }
        }
    },
    validationLevel: 'moderate',
    validationAction: 'warn'
});
print('✓ Added schema validation rules');

// Seed default permissions
const permissions = [
    // News permissions
    { permission_id: 'perm_news_view', permission_key: 'news.view', category: 'news', description: 'View news articles' },
    { permission_id: 'perm_news_create', permission_key: 'news.create', category: 'news', description: 'Create news articles' },
    { permission_id: 'perm_news_edit', permission_key: 'news.edit', category: 'news', description: 'Edit news articles' },
    { permission_id: 'perm_news_delete', permission_key: 'news.delete', category: 'news', description: 'Delete news articles' },
    { permission_id: 'perm_news_manage_sources', permission_key: 'news.manage_sources', category: 'news', description: 'Manage news sources/feeds' },
    
    // Video permissions
    { permission_id: 'perm_video_view', permission_key: 'video.view', category: 'video', description: 'View videos' },
    { permission_id: 'perm_video_create', permission_key: 'video.create', category: 'video', description: 'Create videos' },
    { permission_id: 'perm_video_edit', permission_key: 'video.edit', category: 'video', description: 'Edit videos' },
    { permission_id: 'perm_video_delete', permission_key: 'video.delete', category: 'video', description: 'Delete videos' },
    { permission_id: 'perm_video_manage_configs', permission_key: 'video.manage_configs', category: 'video', description: 'Manage video configurations' },
    { permission_id: 'perm_video_generate', permission_key: 'video.generate', category: 'video', description: 'Generate videos' },
    { permission_id: 'perm_video_recompute', permission_key: 'video.recompute', category: 'video', description: 'Recompute/regenerate videos' },
    
    // YouTube permissions
    { permission_id: 'perm_youtube_view', permission_key: 'youtube.view', category: 'youtube', description: 'View YouTube credentials' },
    { permission_id: 'perm_youtube_manage', permission_key: 'youtube.manage', category: 'youtube', description: 'Manage YouTube credentials' },
    { permission_id: 'perm_youtube_upload', permission_key: 'youtube.upload', category: 'youtube', description: 'Upload videos to YouTube' },
    
    // User management permissions
    { permission_id: 'perm_user_view', permission_key: 'user.view', category: 'user', description: 'View users' },
    { permission_id: 'perm_user_create', permission_key: 'user.create', category: 'user', description: 'Create users' },
    { permission_id: 'perm_user_edit', permission_key: 'user.edit', category: 'user', description: 'Edit users' },
    { permission_id: 'perm_user_delete', permission_key: 'user.delete', category: 'user', description: 'Delete users' },
    { permission_id: 'perm_user_manage_roles', permission_key: 'user.manage_roles', category: 'user', description: 'Manage user roles' },
    
    // Settings permissions
    { permission_id: 'perm_settings_view', permission_key: 'settings.view', category: 'settings', description: 'View settings' },
    { permission_id: 'perm_settings_edit', permission_key: 'settings.edit', category: 'settings', description: 'Edit settings' },
    { permission_id: 'perm_settings_manage_audio', permission_key: 'settings.manage_audio', category: 'settings', description: 'Manage background audio library' },
    
    // Customer management permissions (Super Admin only)
    { permission_id: 'perm_customer_view', permission_key: 'customer.view', category: 'customer', description: 'View customers' },
    { permission_id: 'perm_customer_create', permission_key: 'customer.create', category: 'customer', description: 'Create customers' },
    { permission_id: 'perm_customer_edit', permission_key: 'customer.edit', category: 'customer', description: 'Edit customers' },
    { permission_id: 'perm_customer_delete', permission_key: 'customer.delete', category: 'customer', description: 'Delete customers' },
    
    // Audit permissions
    { permission_id: 'perm_audit_view', permission_key: 'audit.view', category: 'audit', description: 'View audit logs' },
    { permission_id: 'perm_audit_export', permission_key: 'audit.export', category: 'audit', description: 'Export audit logs' }
];

db.permissions.insertMany(permissions);
print('✓ Seeded ' + permissions.length + ' default permissions');

print('✓ Migration 023_create_permissions_collection completed successfully');

