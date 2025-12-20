// Migration: 031_assign_existing_data_to_default_customer.js
// Description: Assign all existing data to the default customer
// Created: 2025-12-16

print('Starting migration: 031_assign_existing_data_to_default_customer');

// Switch to news database
db = db.getSiblingDB('news');

const defaultCustomerId = 'customer_system';

print('Assigning existing data to customer: ' + defaultCustomerId);
print('');

// Update news_document collection
const newsResult = db.news_document.updateMany(
    { customer_id: null },
    { $set: { customer_id: defaultCustomerId } }
);
print('✓ Assigned ' + newsResult.modifiedCount + ' news documents to default customer');

// Update long_video_configs collection
const configsResult = db.long_video_configs.updateMany(
    { customer_id: null },
    { $set: { customer_id: defaultCustomerId, created_by: 'user_super_admin' } }
);
print('✓ Assigned ' + configsResult.modifiedCount + ' video configs to default customer');

// Update youtube_credentials collection
const credentialsResult = db.youtube_credentials.updateMany(
    { customer_id: null },
    { $set: { customer_id: defaultCustomerId } }
);
print('✓ Assigned ' + credentialsResult.modifiedCount + ' YouTube credentials to default customer');

// Update news_seed_urls collection
const seedUrlsResult = db.news_seed_urls.updateMany(
    { customer_id: null },
    { $set: { customer_id: defaultCustomerId } }
);
print('✓ Assigned ' + seedUrlsResult.modifiedCount + ' news seed URLs to default customer');

print('');
print('='.repeat(60));
print('DATA MIGRATION SUMMARY:');
print('  News Documents: ' + newsResult.modifiedCount);
print('  Video Configs: ' + configsResult.modifiedCount);
print('  YouTube Credentials: ' + credentialsResult.modifiedCount);
print('  News Seed URLs: ' + seedUrlsResult.modifiedCount);
print('  Total Records Migrated: ' + (newsResult.modifiedCount + configsResult.modifiedCount + credentialsResult.modifiedCount + seedUrlsResult.modifiedCount));
print('='.repeat(60));

print('✓ Migration 031_assign_existing_data_to_default_customer completed successfully');

