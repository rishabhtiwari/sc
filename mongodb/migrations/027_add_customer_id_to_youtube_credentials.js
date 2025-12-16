// Migration: 027_add_customer_id_to_youtube_credentials.js
// Description: Add customer_id field to youtube_credentials collection
// Created: 2025-12-16

print('Starting migration: 027_add_customer_id_to_youtube_credentials');

// Switch to news database
db = db.getSiblingDB('news');

// Add customer_id field to all existing documents
const updateResult = db.youtube_credentials.updateMany(
    { customer_id: { $exists: false } },
    { $set: { customer_id: null } }
);
print('✓ Added customer_id field to ' + updateResult.modifiedCount + ' documents');

// Create indexes for multi-tenant queries
db.youtube_credentials.createIndex({ "customer_id": 1, "is_active": 1 }, { name: "idx_customer_active" });
print('✓ Created index: customer_id + is_active');

db.youtube_credentials.createIndex({ "customer_id": 1, "credential_id": 1 }, { name: "idx_customer_credential" });
print('✓ Created index: customer_id + credential_id');

db.youtube_credentials.createIndex({ "customer_id": 1 }, { name: "idx_customer_id" });
print('✓ Created index: customer_id');

print('✓ Migration 027_add_customer_id_to_youtube_credentials completed successfully');

