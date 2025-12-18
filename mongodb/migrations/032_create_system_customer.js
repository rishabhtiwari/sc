// Migration: 032_create_system_customer.js
// Description: Create system customer for system-level operations (migrations, system jobs, etc.)
// Created: 2025-12-17

print('Starting migration: 032_create_system_customer');

// Switch to news database
db = db.getSiblingDB('news');

// Check if system customer already exists
const existingSystemCustomer = db.customers.findOne({ customer_id: 'customer_system' });

if (existingSystemCustomer) {
    print('⚠️  System customer already exists, skipping creation');
} else {
    // Create system customer
    const systemCustomer = {
        customer_id: 'customer_system',
        company_name: 'System',
        slug: 'system',
        status: 'active',
        subscription: {
            plan_type: 'system',
            status: 'active',
            trial_ends_at: null,
            started_at: new Date(),
            ends_at: null
        },
        limits: {
            max_users: 999999,
            max_videos_per_month: 999999,
            max_storage_gb: 999999
        },
        features: [
            'news_fetching',
            'video_generation',
            'youtube_upload',
            'background_audio',
            'custom_branding',
            'analytics',
            'api_access',
            'system_operations'
        ],
        billing: {
            email: 'system@newsautomation.internal',
            address: {}
        },
        created_at: new Date(),
        updated_at: new Date(),
        created_by: null,
        is_deleted: false
    };

    db.customers.insertOne(systemCustomer);
    print('✓ Created system customer: customer_system');
}

// Verify system customer exists
const systemCustomer = db.customers.findOne({ customer_id: 'customer_system' });
if (systemCustomer) {
    print('✓ System customer verified:');
    print('  - customer_id: ' + systemCustomer.customer_id);
    print('  - company_name: ' + systemCustomer.company_name);
    print('  - status: ' + systemCustomer.status);
} else {
    print('❌ ERROR: System customer not found after migration!');
}

print('✓ Migration 032_create_system_customer completed successfully');

