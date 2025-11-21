// Migration: 011_load_seed_urls_from_file.js
// Description: Load news seed URLs from JSON file and insert into MongoDB
// Created: 2025-11-21

print('Starting migration: 011_load_seed_urls_from_file');

// Switch to news database
db = db.getSiblingDB('news');

print("Loading seed URLs from JSON file...");

// Read the JSON file
const fs = require('fs');
const seedDataPath = '/app/seed-data/news_seed_urls.json';

let seedUrls = [];

try {
    // Check if file exists
    if (!fs.existsSync(seedDataPath)) {
        print(`⚠️  Seed data file not found at: ${seedDataPath}`);
        print('Migration will skip loading seed URLs from file.');
        quit(0);
    }

    // Read and parse the JSON file
    const fileContent = fs.readFileSync(seedDataPath, 'utf8');
    seedUrls = JSON.parse(fileContent);
    
    print(`✓ Successfully loaded ${seedUrls.length} seed URLs from file`);
} catch (error) {
    print(`❌ Error reading seed data file: ${error.message}`);
    print('Migration will skip loading seed URLs from file.');
    quit(0);
}

// Process and insert each seed URL
let insertedCount = 0;
let updatedCount = 0;
let skippedCount = 0;

seedUrls.forEach(function(seedUrl) {
    try {
        // Add timestamps if not present
        if (!seedUrl.created_at) {
            seedUrl.created_at = new Date();
        }
        if (!seedUrl.updated_at) {
            seedUrl.updated_at = new Date();
        }
        
        // Add default fields if not present
        if (seedUrl.last_fetched_at === undefined) {
            seedUrl.last_fetched_at = null;
        }
        if (seedUrl.fetch_count === undefined) {
            seedUrl.fetch_count = 0;
        }
        if (seedUrl.success_count === undefined) {
            seedUrl.success_count = 0;
        }
        if (seedUrl.error_count === undefined) {
            seedUrl.error_count = 0;
        }
        if (seedUrl.last_error === undefined) {
            seedUrl.last_error = null;
        }
        
        // Check if seed URL already exists by partner_id
        const existing = db.news_seed_urls.findOne({
            partner_id: seedUrl.partner_id
        });
        
        if (!existing) {
            // Insert new seed URL
            const result = db.news_seed_urls.insertOne(seedUrl);
            if (result.acknowledged) {
                insertedCount++;
                print(`✓ Inserted: ${seedUrl.name} (${seedUrl.partner_id})`);
                print(`  Category: ${seedUrl.category}, Language: ${seedUrl.language}, Country: ${seedUrl.country}`);
            }
        } else {
            // Update existing seed URL (preserve fetch statistics)
            const updateDoc = {
                $set: {
                    url: seedUrl.url,
                    partner_name: seedUrl.partner_name,
                    name: seedUrl.name,
                    provider: seedUrl.provider,
                    category: seedUrl.category,
                    country: seedUrl.country,
                    language: seedUrl.language,
                    frequency_minutes: seedUrl.frequency_minutes,
                    frequency_hours: seedUrl.frequency_hours,
                    is_active: seedUrl.is_active,
                    parameters: seedUrl.parameters,
                    metadata: seedUrl.metadata,
                    updated_at: new Date()
                }
            };
            
            const result = db.news_seed_urls.updateOne(
                { partner_id: seedUrl.partner_id },
                updateDoc
            );
            
            if (result.modifiedCount > 0) {
                updatedCount++;
                print(`↻ Updated: ${seedUrl.name} (${seedUrl.partner_id})`);
            } else {
                skippedCount++;
                print(`- Skipped (no changes): ${seedUrl.name} (${seedUrl.partner_id})`);
            }
        }
    } catch (error) {
        print(`❌ Error processing seed URL ${seedUrl.name}: ${error.message}`);
    }
});

print("\n" + "=".repeat(60));
print("✅ Seed URLs migration completed!");
print("=".repeat(60));
print(`📊 Summary:`);
print(`   Total seed URLs in file: ${seedUrls.length}`);
print(`   Inserted: ${insertedCount}`);
print(`   Updated: ${updatedCount}`);
print(`   Skipped: ${skippedCount}`);

// Display current database state
const totalSeedUrls = db.news_seed_urls.countDocuments();
const activeSeedUrls = db.news_seed_urls.countDocuments({ is_active: true });

print(`\n📈 Database State:`);
print(`   Total seed URLs in database: ${totalSeedUrls}`);
print(`   Active seed URLs: ${activeSeedUrls}`);

// Display all seed URLs grouped by category
print(`\n📋 Seed URLs by Category:`);
const categories = db.news_seed_urls.distinct("category");
categories.forEach(function(category) {
    const count = db.news_seed_urls.countDocuments({ category: category, is_active: true });
    print(`   ${category}: ${count} active URLs`);
});

// Display all seed URLs grouped by language
print(`\n🌍 Seed URLs by Language:`);
const languages = db.news_seed_urls.distinct("language");
languages.forEach(function(language) {
    const count = db.news_seed_urls.countDocuments({ language: language, is_active: true });
    print(`   ${language}: ${count} active URLs`);
});

print("\n✅ Migration 011_load_seed_urls_from_file completed successfully!");

