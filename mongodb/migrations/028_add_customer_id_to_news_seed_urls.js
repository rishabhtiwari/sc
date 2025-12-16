// Migration: 028_add_customer_id_to_news_seed_urls.js
// Description: Add customer_id field to news_seed_urls collection
// Created: 2025-12-16

print('Starting migration: 028_add_customer_id_to_news_seed_urls');

// Switch to news database
db = db.getSiblingDB('news');

// Add customer_id field to all existing documents
const updateResult = db.news_seed_urls.updateMany(
    { customer_id: { $exists: false } },
    { $set: { customer_id: null } }
);
print('✓ Added customer_id field to ' + updateResult.modifiedCount + ' documents');

// Create indexes for multi-tenant queries
db.news_seed_urls.createIndex({ "customer_id": 1, "is_active": 1 }, { name: "idx_customer_active" });
print('✓ Created index: customer_id + is_active');

db.news_seed_urls.createIndex({ "customer_id": 1 }, { name: "idx_customer_id" });
print('✓ Created index: customer_id');

print('✓ Migration 028_add_customer_id_to_news_seed_urls completed successfully');

