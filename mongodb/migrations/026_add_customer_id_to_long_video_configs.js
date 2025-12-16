// Migration: 026_add_customer_id_to_long_video_configs.js
// Description: Add customer_id and created_by fields to long_video_configs collection
// Created: 2025-12-16

print('Starting migration: 026_add_customer_id_to_long_video_configs');

// Switch to news database
db = db.getSiblingDB('news');

// Add customer_id and created_by fields to all existing documents
const updateResult = db.long_video_configs.updateMany(
    { $or: [{ customer_id: { $exists: false } }, { created_by: { $exists: false } }] },
    { $set: { customer_id: null, created_by: null } }
);
print('✓ Added customer_id and created_by fields to ' + updateResult.modifiedCount + ' documents');

// Create indexes for multi-tenant queries
db.long_video_configs.createIndex({ "customer_id": 1, "status": 1 }, { name: "idx_customer_status" });
print('✓ Created index: customer_id + status');

db.long_video_configs.createIndex({ "customer_id": 1, "nextRunTime": 1 }, { name: "idx_customer_next_run" });
print('✓ Created index: customer_id + nextRunTime');

db.long_video_configs.createIndex({ "customer_id": 1 }, { name: "idx_customer_id" });
print('✓ Created index: customer_id');

print('✓ Migration 026_add_customer_id_to_long_video_configs completed successfully');

