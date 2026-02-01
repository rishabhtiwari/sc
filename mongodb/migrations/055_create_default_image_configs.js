// Migration: Create default image configs for all existing customers
// Description: Initializes image_config for all customers with auto_mark_cleaned=false (manual mode)
// Date: 2026-01-20

db = db.getSiblingDB('news');

print('🎨 Creating default image configs for all existing customers...');

// Get all unique customer IDs from news_document collection
const customerIds = db.news_document.distinct('customer_id');
print(`ℹ️  Found ${customerIds.length} unique customers in news_document collection`);

let createdCount = 0;
let skippedCount = 0;

// Create default image config for each customer
customerIds.forEach(customerId => {
    if (!customerId) {
        print('⚠️  Skipping null/undefined customer_id');
        skippedCount++;
        return;
    }
    
    // Check if config already exists
    const existingConfig = db.image_config.findOne({ customer_id: customerId });
    
    if (existingConfig) {
        print(`ℹ️  Image config already exists for customer: ${customerId}`);
        skippedCount++;
        return;
    }
    
    // Create default config with auto_mark_cleaned=false (manual mode)
    db.image_config.insertOne({
        customer_id: customerId,
        auto_mark_cleaned: false,  // Default to manual cleaning mode
        created_at: new Date(),
        updated_at: new Date()
    });
    
    print(`✅ Created default image config for customer: ${customerId}`);
    createdCount++;
});

print('');
print('📊 Migration Summary:');
print(`   - Total customers found: ${customerIds.length}`);
print(`   - Configs created: ${createdCount}`);
print(`   - Configs skipped (already exist): ${skippedCount}`);
print('');

// Verify the migration
const totalConfigs = db.image_config.countDocuments();
print(`✅ Total image configs in database: ${totalConfigs}`);

// Show sample configs
print('');
print('📋 Sample image configs:');
db.image_config.find().limit(5).forEach(config => {
    print(`   - Customer: ${config.customer_id}, Auto-mark: ${config.auto_mark_cleaned}`);
});

print('');
print('✅ Migration 055_create_default_image_configs completed successfully');

