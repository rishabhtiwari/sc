// Migration: Migrate existing Instagram credentials to master app system
// Description: Create master apps from existing credentials and update references
// Date: 2026-02-07
// WARNING: This migration requires the cryptography library to be available
// Run this migration AFTER deploying the new code with master app support

print('Running migration: 065_migrate_instagram_to_master_apps.js');

// Switch to news database
db = db.getSiblingDB('news');

const instagramCreds = db.getCollection('instagram_credentials');
const masterApps = db.getCollection('social_media_master_apps');
const encryptionKeys = db.getCollection('customer_encryption_keys');

// Get all existing Instagram credentials
const credentials = instagramCreds.find({}).toArray();

if (credentials.length === 0) {
    print('✓ No existing Instagram credentials to migrate');
    print('✓ Migration 065_migrate_instagram_to_master_apps.js completed successfully');
} else {
    print(`Found ${credentials.length} Instagram credentials to migrate`);
    print('');
    print('⚠️  MANUAL MIGRATION REQUIRED');
    print('⚠️  This migration cannot be run automatically because:');
    print('   1. Encryption keys need to be generated per customer');
    print('   2. Access tokens need to be re-encrypted with customer-specific keys');
    print('   3. App secrets need to be encrypted and moved to master apps');
    print('');
    print('📋 MIGRATION STEPS:');
    print('');
    print('For each customer with Instagram credentials:');
    print('');
    print('1. Generate encryption key for customer (if not exists):');
    print('   POST /api/social-media/master-apps (will auto-generate key)');
    print('');
    print('2. Create master app using existing app_id/app_secret:');
    print('   POST /api/social-media/master-apps');
    print('   {');
    print('     "platform": "instagram",');
    print('     "app_name": "Migrated Instagram App",');
    print('     "app_id": "<from existing credential>",');
    print('     "app_secret": "<from existing credential>",');
    print('     "redirect_uri": "http://localhost:8080/api/social-media/instagram/oauth/callback",');
    print('     "scopes": ["instagram_basic", "instagram_content_publish", "pages_read_engagement"],');
    print('     "is_active": true');
    print('   }');
    print('');
    print('3. Users need to reconnect their Instagram accounts:');
    print('   - Old credentials will continue to work temporarily');
    print('   - Users should disconnect and reconnect to use new master app');
    print('   - Old credentials can be deleted after reconnection');
    print('');
    print('📊 Credentials by customer:');
    
    // Group credentials by customer
    const credsByCustomer = {};
    credentials.forEach(cred => {
        const customerId = cred.customer_id || 'unknown';
        if (!credsByCustomer[customerId]) {
            credsByCustomer[customerId] = [];
        }
        credsByCustomer[customerId].push(cred);
    });
    
    Object.keys(credsByCustomer).forEach(customerId => {
        const creds = credsByCustomer[customerId];
        print(`\n  Customer: ${customerId}`);
        print(`  Credentials: ${creds.length}`);
        
        // Get unique app_id/app_secret combinations
        const uniqueApps = {};
        creds.forEach(cred => {
            const appId = cred.app_id || 'not_set';
            if (!uniqueApps[appId]) {
                uniqueApps[appId] = {
                    app_id: cred.app_id,
                    app_secret: cred.app_secret ? '***' : 'not_set',
                    count: 0
                };
            }
            uniqueApps[appId].count++;
        });
        
        Object.values(uniqueApps).forEach(app => {
            print(`    - App ID: ${app.app_id}, Secret: ${app.app_secret}, Used by: ${app.count} credential(s)`);
        });
    });
    
    print('');
    print('⚠️  IMPORTANT: Do not delete old credentials until users have reconnected!');
    print('');
    print('✓ Migration 065_migrate_instagram_to_master_apps.js analysis completed');
    print('  Manual migration steps documented above');
}

