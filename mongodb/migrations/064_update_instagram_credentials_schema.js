// Migration: Update instagram_credentials schema for master app integration
// Description: Add master_app_id reference and update encryption for access tokens
// Date: 2026-02-07

print('Running migration: 064_update_instagram_credentials_schema.js');

// Switch to news database
db = db.getSiblingDB('news');

// Get instagram_credentials collection
const instagramCreds = db.getCollection('instagram_credentials');

// Add new indexes for master_app_id
instagramCreds.createIndex({ "master_app_id": 1 }, { name: "master_app_idx" });
instagramCreds.createIndex(
    { "customer_id": 1, "user_id": 1, "instagram_user_id": 1 },
    { name: "customer_user_instagram_idx" }
);

print('✓ Created new indexes for instagram_credentials collection');

// Update existing documents to add new fields (if any exist)
const existingCount = instagramCreds.countDocuments();
print(`Found ${existingCount} existing Instagram credentials`);

if (existingCount > 0) {
    print('⚠️  WARNING: Existing Instagram credentials found!');
    print('⚠️  These credentials need to be migrated to use master apps.');
    print('⚠️  Steps required:');
    print('   1. Create a master app for each customer using their existing app_id/app_secret');
    print('   2. Update each credential to reference the master_app_id');
    print('   3. Re-encrypt access_token using customer-specific encryption key');
    print('   4. Remove app_id and app_secret fields from credentials (now in master app)');
    print('');
    print('⚠️  Run migration script: 065_migrate_instagram_to_master_apps.js');
}

// Updated schema structure for instagram_credentials collection:
// {
//     "_id": "ObjectId",
//     "customer_id": "string (customer ID for multi-tenancy)",
//     "user_id": "string (user ID who connected this account)",
//     "master_app_id": "ObjectId (reference to social_media_master_apps)",  // NEW
//     
//     // Instagram account information
//     "instagram_user_id": "string (Instagram Business/Creator Account ID)",
//     "instagram_username": "string (Instagram username)",
//     "instagram_account_type": "string (BUSINESS or CREATOR)",
//     "profile_picture_url": "string (Instagram profile picture URL)",
//     
//     // Facebook Page connection (required for Instagram Graph API)
//     "facebook_page_id": "string (Connected Facebook Page ID)",
//     "facebook_page_name": "string (Connected Facebook Page name)",
//     
//     // OAuth credentials (ENCRYPTED with customer's encryption key)
//     "access_token": "string (ENCRYPTED - OAuth access token)",  // UPDATED: Now encrypted
//     "token_expiry": "Date (when the access token expires)",
//     
//     // REMOVED FIELDS (now in master app):
//     // - app_id (moved to social_media_master_apps)
//     // - app_secret (moved to social_media_master_apps)
//     // - scopes (moved to social_media_master_apps)
//     
//     // Status and metadata
//     "is_active": "boolean (whether this credential is currently active)",
//     "is_authenticated": "boolean (whether OAuth flow is complete)",
//     "last_used_at": "Date (last time this credential was used)",
//     
//     // Audit fields
//     "created_at": "Date (when credential was created)",
//     "updated_at": "Date (when credential was last updated)",
//     "created_by": "string (user ID who created this credential)",
//     "updated_by": "string (user ID who last updated this credential)"
// }

print('✓ Migration 064_update_instagram_credentials_schema.js completed successfully');

