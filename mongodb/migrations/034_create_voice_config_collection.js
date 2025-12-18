// Migration: Create voice_config collection with multi-tenancy support
// Description: Creates voice_config collection with customer_id field and indexes
// Date: 2025-12-18

db = db.getSiblingDB('news');

print('🎤 Creating voice_config collection with multi-tenancy support...');

// Create voice_config collection if it doesn't exist
if (!db.getCollectionNames().includes('voice_config')) {
    db.createCollection('voice_config');
    print('✅ voice_config collection created');
} else {
    print('ℹ️  voice_config collection already exists');
}

// Create indexes for voice_config
print('📑 Creating indexes for voice_config...');

// Unique index on customer_id (each customer has one voice config)
db.voice_config.createIndex(
    { customer_id: 1 },
    { 
        unique: true,
        name: 'idx_voice_config_customer_id_unique'
    }
);
print('✅ Created unique index on customer_id');

// Index on created_at for sorting
db.voice_config.createIndex(
    { created_at: -1 },
    { name: 'idx_voice_config_created_at' }
);
print('✅ Created index on created_at');

// Index on updated_at for sorting
db.voice_config.createIndex(
    { updated_at: -1 },
    { name: 'idx_voice_config_updated_at' }
);
print('✅ Created index on updated_at');

// Compound index for multi-tenant queries with soft delete
db.voice_config.createIndex(
    { customer_id: 1, is_deleted: 1 },
    { name: 'idx_voice_config_customer_deleted' }
);
print('✅ Created compound index on customer_id and is_deleted');

print('✅ Migration 034_create_voice_config_collection completed successfully');

