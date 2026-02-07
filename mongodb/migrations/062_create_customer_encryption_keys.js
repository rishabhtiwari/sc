// Migration: Create customer_encryption_keys collection
// Description: Store per-customer encryption keys for securing social media app secrets and access tokens
// Date: 2026-02-07

print('Running migration: 062_create_customer_encryption_keys.js');

// Switch to news database
db = db.getSiblingDB('news');

// Create customer_encryption_keys collection
db.createCollection('customer_encryption_keys');
print('✓ Created customer_encryption_keys collection');

// Create indexes
db.getCollection('customer_encryption_keys').createIndex(
    { "customer_id": 1 }, 
    { unique: true, name: "customer_encryption_key_idx" }
);
db.getCollection('customer_encryption_keys').createIndex({ "created_at": -1 });
print('✓ Created indexes for customer_encryption_keys collection');

// Schema structure for customer_encryption_keys collection:
// {
//     "_id": "ObjectId",
//     "customer_id": "string (unique - one encryption key per customer)",
//     "encryption_key": "string (Fernet encryption key - base64 encoded, auto-generated)",
//     "created_at": "Date (when key was generated)",
//     "updated_at": "Date (when key was last rotated/updated)",
//     "key_version": "number (for key rotation support - default: 1)",
//     "previous_keys": ["array of previous keys for decrypting old data during rotation"]
// }

// Note: Encryption keys are automatically generated when a customer creates their first master app
// Each customer has their own encryption key for maximum security isolation

print('✓ Migration 062_create_customer_encryption_keys.js completed successfully');

