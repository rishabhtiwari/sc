// Migration: 000_create_ichat_database.js
// Description: Create ichat_db database with migration tracking table
// Created: 2025-10-19

print('Starting migration: 000_create_ichat_database');

// Switch to ichat_db database (will create it if it doesn't exist)
use ichat_db;

// Create _migrations collection for tracking migrations
db.createCollection('_migrations');

// Create indexes for the _migrations collection
db.getCollection('_migrations').createIndex({ "migration_id": 1 }, { unique: true }); // Unique migration ID
db.getCollection('_migrations').createIndex({ "executed_at": 1 }); // Sort by execution time

print('✓ Created _migrations collection with indexes');

// Schema structure for _migrations collection:
// {
//     "migration_id": "string (unique migration identifier)",
//     "migration_file": "string (path to migration file)",
//     "executed_at": "Date (when migration was executed)",
//     "status": "string (completed, failed)"
// }

print('✓ ichat_db database and migration tracking system created');
print('Migration 000_create_ichat_database completed successfully');
