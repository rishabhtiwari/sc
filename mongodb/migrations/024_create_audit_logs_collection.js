// Migration: 024_create_audit_logs_collection.js
// Description: Create audit_logs collection for tracking user actions
// Created: 2025-12-16

print('Starting migration: 024_create_audit_logs_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create audit_logs collection
db.createCollection('audit_logs');
print('✓ Created audit_logs collection');

// Create indexes
db.audit_logs.createIndex({ "customer_id": 1, "timestamp": -1 }, { name: "idx_customer_timestamp" });
print('✓ Created index: customer_id + timestamp');

db.audit_logs.createIndex({ "user_id": 1, "timestamp": -1 }, { name: "idx_user_timestamp" });
print('✓ Created index: user_id + timestamp');

db.audit_logs.createIndex({ "resource_type": 1, "resource_id": 1 }, { name: "idx_resource" });
print('✓ Created index: resource_type + resource_id');

db.audit_logs.createIndex({ "action": 1 }, { name: "idx_action" });
print('✓ Created index: action');

db.audit_logs.createIndex({ "timestamp": -1 }, { name: "idx_timestamp" });
print('✓ Created index: timestamp');

// Add schema validation
db.runCommand({
    collMod: 'audit_logs',
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['log_id', 'customer_id', 'user_id', 'action', 'resource_type', 'timestamp'],
            properties: {
                log_id: {
                    bsonType: 'string',
                    description: 'Unique log identifier (UUID) - required'
                },
                customer_id: {
                    bsonType: 'string',
                    description: 'Customer ID - required'
                },
                user_id: {
                    bsonType: 'string',
                    description: 'User ID who performed the action - required'
                },
                action: {
                    enum: ['create', 'read', 'update', 'delete', 'login', 'logout', 'upload', 'download', 'publish', 'generate'],
                    description: 'Action performed - required'
                },
                resource_type: {
                    bsonType: 'string',
                    description: 'Type of resource (e.g., news, video, user, config) - required'
                },
                resource_id: {
                    bsonType: ['string', 'null'],
                    description: 'ID of the affected resource'
                },
                changes: {
                    bsonType: 'object',
                    properties: {
                        before: {
                            bsonType: ['object', 'null'],
                            description: 'State before the change'
                        },
                        after: {
                            bsonType: ['object', 'null'],
                            description: 'State after the change'
                        }
                    },
                    description: 'Before/after state for updates'
                },
                metadata: {
                    bsonType: 'object',
                    properties: {
                        ip_address: {
                            bsonType: 'string',
                            description: 'IP address of the user'
                        },
                        user_agent: {
                            bsonType: 'string',
                            description: 'User agent string'
                        },
                        session_id: {
                            bsonType: 'string',
                            description: 'Session identifier'
                        }
                    },
                    description: 'Additional metadata about the action'
                },
                status: {
                    enum: ['success', 'failure', 'error'],
                    description: 'Status of the action'
                },
                error_message: {
                    bsonType: ['string', 'null'],
                    description: 'Error message if action failed'
                },
                timestamp: {
                    bsonType: 'date',
                    description: 'Timestamp of the action - required'
                }
            }
        }
    },
    validationLevel: 'moderate',
    validationAction: 'warn'
});
print('✓ Added schema validation rules');

print('✓ Migration 024_create_audit_logs_collection completed successfully');

