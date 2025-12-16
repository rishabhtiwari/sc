// Migration: 025_add_customer_id_to_news_document.js
// Description: Add customer_id field to news_document collection
// Created: 2025-12-16

print('Starting migration: 025_add_customer_id_to_news_document');

// Switch to news database
db = db.getSiblingDB('news');

// Add customer_id field to all existing documents (set to null initially)
const updateResult = db.news_document.updateMany(
    { customer_id: { $exists: false } },
    { $set: { customer_id: null } }
);
print('✓ Added customer_id field to ' + updateResult.modifiedCount + ' documents');

// Create indexes for multi-tenant queries
db.news_document.createIndex({ "customer_id": 1, "publishedAt": -1 }, { name: "idx_customer_published" });
print('✓ Created index: customer_id + publishedAt');

db.news_document.createIndex({ "customer_id": 1, "status": 1 }, { name: "idx_customer_status" });
print('✓ Created index: customer_id + status');

db.news_document.createIndex({ "customer_id": 1, "id": 1 }, { name: "idx_customer_id" });
print('✓ Created index: customer_id + id');

print('✓ Migration 025_add_customer_id_to_news_document completed successfully');

