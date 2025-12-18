// Migration: 021_create_users_collection.js
// Description: Create users collection with indexes and validation
// Created: 2025-12-16

print('Starting migration: 021_create_users_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create users collection with schema validation
db.createCollection('users', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['user_id', 'customer_id', 'email', 'password_hash', 'role_id', 'status', 'created_at'],
            properties: {
                user_id: {
                    bsonType: 'string',
                    description: 'Unique user identifier'
                },
                customer_id: {
                    bsonType: 'string',
                    description: 'Customer ID this user belongs to'
                },
                email: {
                    bsonType: 'string',
                    pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
                    description: 'User email address'
                },
                password_hash: {
                    bsonType: 'string',
                    description: 'Bcrypt hashed password'
                },
                first_name: {
                    bsonType: 'string',
                    description: 'User first name'
                },
                last_name: {
                    bsonType: 'string',
                    description: 'User last name'
                },
                role_id: {
                    bsonType: 'string',
                    description: 'Role ID assigned to user'
                },
                status: {
                    enum: ['active', 'inactive', 'suspended'],
                    description: 'User account status'
                },
                email_verified: {
                    bsonType: 'bool',
                    description: 'Whether email is verified'
                },
                email_verification_token: {
                    bsonType: ['string', 'null'],
                    description: 'Token for email verification'
                },
                email_verification_expires_at: {
                    bsonType: ['date', 'null'],
                    description: 'Email verification token expiry'
                },
                password_reset_token: {
                    bsonType: ['string', 'null'],
                    description: 'Token for password reset'
                },
                password_reset_expires_at: {
                    bsonType: ['date', 'null'],
                    description: 'Password reset token expiry'
                },
                last_login_at: {
                    bsonType: ['date', 'null'],
                    description: 'Last login timestamp'
                },
                login_count: {
                    bsonType: 'int',
                    minimum: 0,
                    description: 'Total number of logins'
                },
                failed_login_attempts: {
                    bsonType: 'int',
                    minimum: 0,
                    description: 'Failed login attempt count'
                },
                account_locked_until: {
                    bsonType: ['date', 'null'],
                    description: 'Account lockout expiry time'
                },
                preferences: {
                    bsonType: 'object',
                    description: 'User preferences'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Creation timestamp'
                },
                updated_at: {
                    bsonType: 'date',
                    description: 'Last update timestamp'
                },
                created_by: {
                    bsonType: ['string', 'null'],
                    description: 'User ID who created this user'
                },
                updated_by: {
                    bsonType: ['string', 'null'],
                    description: 'User ID who last updated this user'
                },
                is_deleted: {
                    bsonType: 'bool',
                    description: 'Soft delete flag'
                }
            }
        }
    }
});

print('✓ Created users collection with schema validation');

// Create indexes
db.users.createIndex({ user_id: 1 }, { unique: true });
print('✓ Created unique index on user_id');

db.users.createIndex({ email: 1 }, { unique: true, partialFilterExpression: { is_deleted: false } });
print('✓ Created unique index on email (globally unique, excluding deleted users)');

db.users.createIndex({ customer_id: 1, email: 1 });
print('✓ Created compound index on customer_id + email');

db.users.createIndex({ customer_id: 1, status: 1 });
print('✓ Created compound index on customer_id + status');

db.users.createIndex({ role_id: 1 });
print('✓ Created index on role_id');

db.users.createIndex({ created_at: -1 });
print('✓ Created index on created_at (descending)');

db.users.createIndex({ is_deleted: 1 });
print('✓ Created index on is_deleted');

db.users.createIndex({ email_verification_token: 1 }, { sparse: true });
print('✓ Created sparse index on email_verification_token');

db.users.createIndex({ password_reset_token: 1 }, { sparse: true });
print('✓ Created sparse index on password_reset_token');

print('✓ Migration 021_create_users_collection completed successfully');

