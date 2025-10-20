// Migration: 002_create_news_seed_urls.js
// Description: Create seed URLs collection for news information sources
// Created: 2025-10-19

print('Starting migration: 002_create_news_seed_urls');

// Switch to news database
use news;

// Create news_seed_urls collection
db.createCollection('news_seed_urls');

// Create indexes for the news_seed_urls collection
db.getCollection('news_seed_urls').createIndex({ "partner_id": 1 }, { unique: true }); // Unique partner ID
db.getCollection('news_seed_urls').createIndex({ "url": 1 }, { unique: true }); // Unique URL
db.getCollection('news_seed_urls').createIndex({ "partner_name": 1 }); // Filter by partner
db.getCollection('news_seed_urls').createIndex({ "is_active": 1 }); // Filter by active status
db.getCollection('news_seed_urls').createIndex({ "frequency_minutes": 1 }); // Sort by frequency
db.getCollection('news_seed_urls').createIndex({ "last_run": 1 }); // Sort by last run time

print('✓ Created news_seed_urls collection with indexes');

// Insert GNews seed URL
db.getCollection('news_seed_urls').insertOne({
    partner_id: "gnews_001",
    url: "https://gnews.io/api/v4/top-headlines?category={category}&apikey={api_key}&lang={lang}&country={country}",
    partner_name: "GNews",
    frequency_minutes: 60,
    is_active: true,
    last_run: null,
    parameters: {
        category: {
            type: "string",
            required: false,
            description: "News category (general, world, nation, business, technology, entertainment, sports, science, health)",
            default: "general"
        },
        api_key: {
            type: "string",
            required: true,
            description: "GNews API key"
        },
        lang: {
            type: "string",
            required: false,
            description: "Language code (en, es, fr, de, it, pt, ru, etc.)",
            default: "en"
        },
        country: {
            type: "string",
            required: false,
            description: "Country code (us, gb, ca, au, in, etc.)",
            default: "in"
        }
    },
    created_at: new Date(),
    updated_at: new Date()
});

print('✓ Inserted GNews seed URL');

// Schema structure for news_seed_urls collection:
// {
//     "partner_id": "string (unique identifier for the partner)",
//     "url": "string (API endpoint URL with parameter placeholders)",
//     "partner_name": "string (news provider name)",
//     "frequency_minutes": "number (how often to fetch in minutes)",
//     "is_active": "boolean (whether this seed URL is active)",
//     "last_run": "Date (timestamp of last successful fetch, null if never run)",
//     "parameters": {
//         "param_name": {
//             "type": "string (parameter data type)",
//             "required": "boolean (whether parameter is required)",
//             "description": "string (parameter description)",
//             "default": "any (default value if not provided)"
//         }
//     },
//     "created_at": "Date (record creation timestamp)",
//     "updated_at": "Date (record update timestamp)"
// }

print('✓ News seed URLs collection created with GNews configuration');
print('Migration 002_create_news_seed_urls completed successfully');
