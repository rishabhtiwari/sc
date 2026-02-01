/**
 * Migration: Add speed field to voice_config
 * Version: 053
 * Date: 2026-01-11
 * 
 * This migration adds the 'speed' field to all existing voice_config documents.
 * Default speed is set to 1.2 (20% faster than normal) which is optimal for news narration.
 */

print('🔄 Starting migration: 053_add_speed_to_voice_config');

// Switch to news database
db = db.getSiblingDB('news');

try {
    // Check if voice_config collection exists
    if (!db.getCollectionNames().includes('voice_config')) {
        print('⚠️  voice_config collection does not exist, skipping migration');
        print('✓ Migration 053_add_speed_to_voice_config completed (skipped)');
    } else {
        // Count existing configs
        const totalConfigs = db.voice_config.countDocuments({});
        print(`📊 Found ${totalConfigs} voice configuration(s)`);
        
        if (totalConfigs === 0) {
            print('ℹ️  No voice configs found, nothing to migrate');
        } else {
            // Update all voice_config documents that don't have speed field
            const result = db.voice_config.updateMany(
                {
                    speed: { $exists: false }
                },
                {
                    $set: {
                        speed: 1.2,  // Default: 1.2x speed (20% faster for news)
                        updated_by: 'migration_053',
                        updated_at: new Date()
                    }
                }
            );
            
            print(`✅ Updated ${result.modifiedCount} voice configuration(s) with speed: 1.2`);
            
            // Show summary of all configs
            print('\n📋 Voice Config Summary:');
            db.voice_config.find({}).forEach(config => {
                const speed = config.speed || 'not set';
                print(`  - Customer: ${config.customer_id}, Speed: ${speed}x, Language: ${config.language || 'en'}`);
            });
        }
        
        print('\n✓ Migration 053_add_speed_to_voice_config completed successfully');
    }
} catch (error) {
    print(`❌ Migration 053_add_speed_to_voice_config failed: ${error}`);
    throw error;
}

