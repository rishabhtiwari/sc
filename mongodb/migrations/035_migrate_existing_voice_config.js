// Migration: Migrate existing voice_config to multi-tenant structure
// Description: Adds customer_id to existing voice_config documents and creates default configs
// Date: 2025-12-18

db = db.getSiblingDB('news');

print('🎤 Migrating existing voice_config to multi-tenant structure...');

// Get system customer ID
const defaultCustomer = db.getSiblingDB('ichat').customers.findOne({ name: 'System Customer' });
const defaultCustomerId = defaultCustomer ? defaultCustomer.customer_id : 'customer_system';

print(`ℹ️  Default customer ID: ${defaultCustomerId}`);

// Check if there's an existing voice_config without customer_id
const existingConfig = db.voice_config.findOne({ customer_id: { $exists: false } });

if (existingConfig) {
    print('📝 Found existing voice_config without customer_id, migrating...');
    
    // Add customer_id to existing config
    db.voice_config.updateOne(
        { _id: existingConfig._id },
        {
            $set: {
                customer_id: defaultCustomerId,
                created_by: 'migration_script',
                updated_by: 'migration_script',
                created_at: existingConfig.createdAt || new Date(),
                updated_at: existingConfig.updatedAt || new Date(),
                is_deleted: false
            },
            $unset: {
                type: "",
                createdAt: "",
                updatedAt: ""
            }
        }
    );
    print(`✅ Migrated existing config to customer: ${defaultCustomerId}`);
} else {
    print('ℹ️  No existing voice_config found without customer_id');
}

// Create default voice config for default customer if it doesn't exist
const defaultConfig = db.voice_config.findOne({ customer_id: defaultCustomerId });

if (!defaultConfig) {
    print('📝 Creating default voice config for default customer...');
    
    db.voice_config.insertOne({
        customer_id: defaultCustomerId,
        defaultVoice: 'am_adam',
        enableAlternation: true,
        language: 'en',
        maleVoices: ['am_adam', 'am_michael'],
        femaleVoices: ['af_bella', 'af_sarah'],
        created_by: 'migration_script',
        updated_by: 'migration_script',
        created_at: new Date(),
        updated_at: new Date(),
        is_deleted: false
    });
    
    print('✅ Created default voice config for default customer');
} else {
    print('ℹ️  Default voice config already exists for default customer');
}

// Create default voice config for system customer
const systemCustomerId = 'customer_system';
const systemConfig = db.voice_config.findOne({ customer_id: systemCustomerId });

if (!systemConfig) {
    print('📝 Creating default voice config for system customer...');
    
    db.voice_config.insertOne({
        customer_id: systemCustomerId,
        defaultVoice: 'am_adam',
        enableAlternation: true,
        language: 'en',
        maleVoices: ['am_adam', 'am_michael'],
        femaleVoices: ['af_bella', 'af_sarah'],
        created_by: 'migration_script',
        updated_by: 'migration_script',
        created_at: new Date(),
        updated_at: new Date(),
        is_deleted: false
    });
    
    print('✅ Created default voice config for system customer');
} else {
    print('ℹ️  Default voice config already exists for system customer');
}

// Remove any old configs with type='default'
const oldConfigs = db.voice_config.find({ type: 'default', customer_id: { $exists: true } });
const oldConfigCount = oldConfigs.count();

if (oldConfigCount > 0) {
    print(`📝 Found ${oldConfigCount} old configs with type='default', cleaning up...`);
    db.voice_config.updateMany(
        { type: 'default' },
        { $unset: { type: "" } }
    );
    print('✅ Cleaned up old type field');
}

print('✅ Migration 035_migrate_existing_voice_config completed successfully');

