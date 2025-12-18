// Migration: Fix seed URLs unique index for multi-tenancy
// Date: 2025-12-17
// Description: Change unique index from 'url' to compound 'customer_id + url' to allow
//              multiple customers to use the same seed URL template

print('=== Migration 026: Fix seed URLs unique index for multi-tenancy ===');

const db = db.getSiblingDB('news');

print('\n1. Checking current indexes on news_seed_urls collection...');
const currentIndexes = db.news_seed_urls.getIndexes();
currentIndexes.forEach(idx => {
    print('  - ' + JSON.stringify(idx.key) + ' (unique: ' + (idx.unique || false) + ')');
});

print('\n2. Dropping old url_1 unique index...');
try {
    db.news_seed_urls.dropIndex('url_1');
    print('  ✅ Dropped url_1 index');
} catch (e) {
    print('  ⚠️  Index url_1 not found or already dropped: ' + e.message);
}

print('\n3. Adding customer_id field to existing seed URLs (set to null for system-wide seeds)...');
const updateResult = db.news_seed_urls.updateMany(
    { customer_id: { $exists: false } },
    { $set: { customer_id: null } }
);
print('  ✅ Updated ' + updateResult.modifiedCount + ' seed URLs with customer_id field');

print('\n4. Creating new compound unique index on customer_id + url...');
db.news_seed_urls.createIndex(
    { customer_id: 1, url: 1 },
    { 
        name: 'customer_url_unique_idx',
        unique: true,
        background: true
    }
);
print('  ✅ Created compound unique index: customer_id + url');

print('\n5. Creating index on customer_id + is_active for efficient queries...');
db.news_seed_urls.createIndex(
    { customer_id: 1, is_active: 1 },
    { 
        name: 'customer_active_idx',
        background: true
    }
);
print('  ✅ Created index: customer_id + is_active');

print('\n6. Creating index on customer_id + partner_id for lookups...');
db.news_seed_urls.createIndex(
    { customer_id: 1, partner_id: 1 },
    { 
        name: 'customer_partner_idx',
        background: true
    }
);
print('  ✅ Created index: customer_id + partner_id');

print('\n7. Verifying new indexes...');
const newIndexes = db.news_seed_urls.getIndexes();
print('Current indexes on news_seed_urls:');
newIndexes.forEach(idx => {
    const partial = idx.partialFilterExpression ? ' (partial)' : '';
    print('  - ' + JSON.stringify(idx.key) + ' (unique: ' + (idx.unique || false) + ')' + partial);
});

print('\n8. Checking seed URLs data...');
const totalSeeds = db.news_seed_urls.countDocuments({});
const seedsWithCustomer = db.news_seed_urls.countDocuments({ customer_id: { $ne: null } });
const seedsWithoutCustomer = db.news_seed_urls.countDocuments({ customer_id: null });
print('  Total seed URLs: ' + totalSeeds);
print('  Seed URLs with customer_id: ' + seedsWithCustomer);
print('  System-wide seed URLs (customer_id=null): ' + seedsWithoutCustomer);

print('\n✅ Migration 026 completed successfully!');
print('   - Dropped old url_1 unique index');
print('   - Added customer_id field to all seed URLs');
print('   - Created compound unique index: customer_id + url');
print('   - Created supporting indexes for multi-tenant queries');
print('   - Same URL template can now be used by multiple customers');

