// Migration: 029_create_default_system_roles.js
// Description: Create 5 default system roles with permissions
// Created: 2025-12-16

print('Starting migration: 029_create_default_system_roles');

// Switch to news database
db = db.getSiblingDB('news');

// Define system roles with their permissions
const systemRoles = [
    {
        role_id: 'role_super_admin',
        customer_id: null,
        role_name: 'Super Admin',
        slug: 'super_admin',
        description: 'Full system access - platform administrators only',
        permissions: [
            'news.view', 'news.create', 'news.edit', 'news.delete', 'news.manage_sources',
            'video.view', 'video.create', 'video.edit', 'video.delete', 'video.manage_configs', 'video.generate', 'video.recompute',
            'youtube.view', 'youtube.manage', 'youtube.upload',
            'user.view', 'user.create', 'user.edit', 'user.delete', 'user.manage_roles',
            'settings.view', 'settings.edit', 'settings.manage_audio',
            'customer.view', 'customer.create', 'customer.edit', 'customer.delete',
            'audit.view', 'audit.export'
        ],
        is_system_role: true,
        is_default: false,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: null,
        is_deleted: false
    },
    {
        role_id: 'role_customer_admin',
        customer_id: null,
        role_name: 'Customer Admin',
        slug: 'customer_admin',
        description: 'Full access within customer account',
        permissions: [
            'news.view', 'news.create', 'news.edit', 'news.delete', 'news.manage_sources',
            'video.view', 'video.create', 'video.edit', 'video.delete', 'video.manage_configs', 'video.generate', 'video.recompute',
            'youtube.view', 'youtube.manage', 'youtube.upload',
            'user.view', 'user.create', 'user.edit', 'user.delete', 'user.manage_roles',
            'settings.view', 'settings.edit', 'settings.manage_audio',
            'audit.view', 'audit.export'
        ],
        is_system_role: true,
        is_default: false,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: null,
        is_deleted: false
    },
    {
        role_id: 'role_editor',
        customer_id: null,
        role_name: 'Editor',
        slug: 'editor',
        description: 'Create and manage content - default role for new users',
        permissions: [
            'news.view', 'news.create', 'news.edit',
            'video.view', 'video.create', 'video.edit', 'video.manage_configs', 'video.generate', 'video.recompute',
            'youtube.view',
            'settings.view', 'settings.manage_audio'
        ],
        is_system_role: true,
        is_default: true,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: null,
        is_deleted: false
    },
    {
        role_id: 'role_publisher',
        customer_id: null,
        role_name: 'Publisher',
        slug: 'publisher',
        description: 'Create content and publish to YouTube',
        permissions: [
            'news.view', 'news.create',
            'video.view', 'video.create', 'video.generate',
            'youtube.view', 'youtube.upload',
            'settings.view'
        ],
        is_system_role: true,
        is_default: false,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: null,
        is_deleted: false
    },
    {
        role_id: 'role_viewer',
        customer_id: null,
        role_name: 'Viewer',
        slug: 'viewer',
        description: 'Read-only access to content',
        permissions: [
            'news.view',
            'video.view',
            'youtube.view',
            'settings.view'
        ],
        is_system_role: true,
        is_default: false,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: null,
        is_deleted: false
    }
];

// Insert system roles
db.roles.insertMany(systemRoles);
print('✓ Created ' + systemRoles.length + ' system roles:');
systemRoles.forEach(role => {
    print('  - ' + role.role_name + ' (' + role.permissions.length + ' permissions)');
});

print('✓ Migration 029_create_default_system_roles completed successfully');

