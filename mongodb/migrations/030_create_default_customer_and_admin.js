// Migration: 030_create_default_customer_and_admin.js
// Description: Create default customer account and super admin user
// Created: 2025-12-16

print('Starting migration: 030_create_default_customer_and_admin');

// Switch to news database
db = db.getSiblingDB('news');

// Create default customer
const defaultCustomer = {
    customer_id: 'customer_default',
    company_name: 'Default Customer',
    slug: 'default',
    status: 'active',
    subscription: {
        plan_type: 'enterprise',
        status: 'active',
        trial_ends_at: null,
        started_at: new Date(),
        ends_at: null
    },
    limits: {
        max_users: 100,
        max_videos_per_month: 10000,
        max_storage_gb: 1000
    },
    features: [
        'news_fetching',
        'video_generation',
        'youtube_upload',
        'background_audio',
        'custom_branding',
        'analytics',
        'api_access'
    ],
    billing: {
        email: 'billing@newsautomation.com',
        address: {}
    },
    created_at: new Date(),
    updated_at: new Date(),
    created_by: null,
    is_deleted: false
};

db.customers.insertOne(defaultCustomer);
print('✓ Created default customer: ' + defaultCustomer.company_name);
print('  - Customer ID: ' + defaultCustomer.customer_id);
print('  - Plan: ' + defaultCustomer.subscription.plan_type);
print('  - Status: ' + defaultCustomer.status);

// Create super admin user
// Password: admin123
// Password: admin123
// Hash generated with Python: bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt(rounds=12))
const superAdminUser = {
    user_id: 'user_super_admin',
    customer_id: 'customer_default',
    email: 'admin@newsautomation.com',
    password_hash: '$2b$12$qc62sgy/WnsXW8WPBe5YG.aM5TroVSJowo8hejli06gEXFvDPgul.',
    first_name: 'Super',
    last_name: 'Admin',
    role_id: 'role_super_admin',
    status: 'active',
    email_verified: true,
    email_verification_token: null,
    email_verification_expires_at: null,
    password_reset_token: null,
    password_reset_expires_at: null,
    last_login_at: null,
    login_count: 0,
    failed_login_attempts: 0,
    account_locked_until: null,
    preferences: {
        language: 'en',
        timezone: 'UTC',
        theme: 'light',
        notifications: {
            email: true,
            browser: true
        }
    },
    created_at: new Date(),
    updated_at: new Date(),
    created_by: null,
    is_deleted: false
};

db.users.insertOne(superAdminUser);
print('✓ Created super admin user:');
print('  - Email: ' + superAdminUser.email);
print('  - Password: admin123');
print('  - Role: Super Admin');
print('  - User ID: ' + superAdminUser.user_id);

print('');
print('='.repeat(60));
print('DEFAULT LOGIN CREDENTIALS:');
print('  Email: admin@newsautomation.com');
print('  Password: admin123');
print('  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!');
print('='.repeat(60));

print('✓ Migration 030_create_default_customer_and_admin completed successfully');

