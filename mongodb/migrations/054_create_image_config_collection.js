// Migration: Create image_config collection with multi-tenancy support
// Description: Creates image_config collection to store image cleaning configuration per customer
// Date: 2026-01-20

db = db.getSiblingDB('news');

print('🎨 Creating image_config collection with multi-tenancy support...');

// Create image_config collection if it doesn't exist
if (!db.getCollectionNames().includes('image_config')) {
    db.createCollection('image_config');
    print('✅ image_config collection created');
} else {
    print('ℹ️  image_config collection already exists');
}

// Create indexes for image_config
print('📑 Creating indexes for image_config...');

// Unique index on customer_id (each customer has one image config)
db.image_config.createIndex(
    { customer_id: 1 },
    { 
        unique: true,
        name: 'idx_image_config_customer_id_unique'
    }
);
print('✅ Created unique index on customer_id');

// Index on created_at for sorting
db.image_config.createIndex(
    { created_at: -1 },
    { name: 'idx_image_config_created_at' }
);
print('✅ Created index on created_at');

// Index on updated_at for sorting
db.image_config.createIndex(
    { updated_at: -1 },
    { name: 'idx_image_config_updated_at' }
);
print('✅ Created index on updated_at');

print('✅ Migration 054_create_image_config_collection completed successfully');

