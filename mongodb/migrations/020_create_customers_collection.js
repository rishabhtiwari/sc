// Migration: 020_create_customers_collection.js
// Description: Create customers collection for multi-tenant support
// Created: 2025-12-16

print('Starting migration: 020_create_customers_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create customers collection
db.createCollection('customers');
print('✓ Created customers collection');

// Create indexes
db.customers.createIndex({ "customer_id": 1 }, { unique: true, name: "idx_customer_id" });
print('✓ Created index: customer_id (unique)');

db.customers.createIndex({ "slug": 1 }, { unique: true, sparse: true, name: "idx_slug" });
print('✓ Created index: slug (unique)');

db.customers.createIndex({ "status": 1 }, { name: "idx_status" });
print('✓ Created index: status');

db.customers.createIndex({ "subscription.status": 1 }, { name: "idx_subscription_status" });
print('✓ Created index: subscription.status');

db.customers.createIndex({ "created_at": -1 }, { name: "idx_created_at" });
print('✓ Created index: created_at');

// Add schema validation
db.runCommand({
    collMod: 'customers',
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['customer_id', 'company_name', 'status', 'created_at'],
            properties: {
                customer_id: {
                    bsonType: 'string',
                    description: 'Unique customer identifier (UUID) - required'
                },
                company_name: {
                    bsonType: 'string',
                    minLength: 1,
                    maxLength: 200,
                    description: 'Company/organization name - required'
                },
                slug: {
                    bsonType: ['string', 'null'],
                    pattern: '^[a-z0-9-]+$',
                    minLength: 3,
                    maxLength: 50,
                    description: 'Unique slug (lowercase, alphanumeric, hyphens only)'
                },
                status: {
                    enum: ['active', 'suspended', 'trial', 'cancelled'],
                    description: 'Customer account status - required'
                },
                subscription: {
                    bsonType: 'object',
                    properties: {
                        plan_type: {
                            enum: ['free', 'basic', 'premium', 'enterprise'],
                            description: 'Subscription plan type'
                        },
                        status: {
                            enum: ['active', 'inactive', 'trial', 'cancelled', 'past_due'],
                            description: 'Subscription status'
                        },
                        trial_ends_at: {
                            bsonType: ['date', 'null'],
                            description: 'Trial expiration date'
                        },
                        started_at: {
                            bsonType: ['date', 'null'],
                            description: 'Subscription start date'
                        },
                        ends_at: {
                            bsonType: ['date', 'null'],
                            description: 'Subscription end date'
                        }
                    }
                },
                limits: {
                    bsonType: 'object',
                    properties: {
                        max_users: {
                            bsonType: 'int',
                            minimum: 1,
                            description: 'Maximum users allowed'
                        },
                        max_videos_per_month: {
                            bsonType: 'int',
                            minimum: 0,
                            description: 'Maximum videos per month'
                        },
                        max_storage_gb: {
                            bsonType: 'int',
                            minimum: 1,
                            description: 'Maximum storage in GB'
                        }
                    }
                },
                features: {
                    bsonType: 'array',
                    items: {
                        bsonType: 'string'
                    },
                    description: 'Array of enabled feature flags'
                },
                billing: {
                    bsonType: 'object',
                    properties: {
                        email: {
                            bsonType: 'string',
                            description: 'Billing email address'
                        },
                        address: {
                            bsonType: 'object',
                            description: 'Billing address details'
                        }
                    }
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
                    description: 'User ID who created this customer'
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

print('✓ Migration 020_create_customers_collection completed successfully');

