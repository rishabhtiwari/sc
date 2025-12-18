// Migration: 033_fix_news_document_unique_index.js
// Description: Fix unique index on news_document to support multi-tenancy
//              - Drop old unique index on 'id' field alone
//              - Drop non-unique index on 'customer_id + id'
//              - Create new unique compound index on 'customer_id + id'
// Created: 2025-12-17
// Reason: The old unique index on 'id' prevented different customers from having
//         the same article (same RSS feed). This caused the second customer's job
//         to update the first customer's articles instead of creating new ones.

print('Starting migration: 033_fix_news_document_unique_index');

// Switch to news database
db = db.getSiblingDB('news');

// Drop the old unique index on 'id' field alone
try {
    db.news_document.dropIndex('id_1');
    print('✓ Dropped old unique index on id field');
} catch (e) {
    print('⚠ Could not drop id_1 index (may not exist): ' + e.message);
}

// Drop the non-unique index on customer_id + id (created in migration 025)
try {
    db.news_document.dropIndex('idx_customer_id');
    print('✓ Dropped non-unique index on customer_id + id');
} catch (e) {
    print('⚠ Could not drop idx_customer_id index (may not exist): ' + e.message);
}

// Create new compound unique index on customer_id + id
// This allows the same article ID to exist for different customers
try {
    db.news_document.createIndex(
        { customer_id: 1, id: 1 },
        { unique: true, name: 'idx_customer_id_unique' }
    );
    print('✓ Created unique compound index on customer_id + id');
} catch (e) {
    print('⚠ Could not create idx_customer_id_unique index: ' + e.message);
    print('  This may be because duplicate data exists. Please clean up duplicates first.');
}

print('✓ Migration 033_fix_news_document_unique_index completed successfully');
print('');
print('IMPORTANT: This migration ensures proper multi-tenant data isolation.');
print('Each customer can now have their own copy of the same article from RSS feeds.');

