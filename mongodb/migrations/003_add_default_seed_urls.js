// Migration: Add default seed URLs for news fetcher
// This migration adds default seed URLs to the news_seed_urls collection

// Switch to news database
db = db.getSiblingDB('news');

print("Adding default seed URLs for news fetcher...");

// Default seed URLs that will be called by the news-fetcher service
const defaultSeedUrls = [
    {
        url: "https://gnews.io/api/v4/top-headlines",
        name: "GNews Top Headlines - General",
        provider: "gnews",
        category: "general",
        country: "in", 
        language: "en",
        frequency_hours: 1,
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        last_fetched_at: null,
        fetch_count: 0,
        success_count: 0,
        error_count: 0,
        last_error: null,
        metadata: {
            description: "Top headlines from GNews API - General category",
            actual_url_called: "https://gnews.io/api/v4/top-headlines?category=general&country=in&lang=en&token={API_KEY}",
            max_articles: 100,
            api_params: {
                category: "general",
                country: "in",
                lang: "en"
            }
        }
    },
    {
        url: "https://gnews.io/api/v4/top-headlines", 
        name: "GNews Top Headlines - Technology",
        provider: "gnews",
        category: "technology",
        country: "in",
        language: "en", 
        frequency_hours: 2,
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        last_fetched_at: null,
        fetch_count: 0,
        success_count: 0,
        error_count: 0,
        last_error: null,
        metadata: {
            description: "Top headlines from GNews API - Technology category",
            actual_url_called: "https://gnews.io/api/v4/top-headlines?category=technology&country=in&lang=en&token={API_KEY}",
            max_articles: 50,
            api_params: {
                category: "technology",
                country: "in",
                lang: "en"
            }
        }
    },
    {
        url: "https://gnews.io/api/v4/search",
        name: "GNews Search - India News", 
        provider: "gnews",
        category: "general",
        country: "in",
        language: "en",
        frequency_hours: 4,
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        last_fetched_at: null,
        fetch_count: 0,
        success_count: 0,
        error_count: 0,
        last_error: null,
        metadata: {
            description: "Search for India-specific news from GNews API",
            actual_url_called: "https://gnews.io/api/v4/search?q=India&country=in&lang=en&sortby=publishedAt&token={API_KEY}",
            max_articles: 75,
            api_params: {
                q: "India",
                country: "in",
                lang: "en",
                sortby: "publishedAt"
            }
        }
    }
];

// Insert default seed URLs (only if they don't already exist)
defaultSeedUrls.forEach(function(seedUrl) {
    const existing = db.news_seed_urls.findOne({
        url: seedUrl.url,
        "metadata.api_params.category": seedUrl.metadata.api_params.category || seedUrl.metadata.api_params.q
    });
    
    if (!existing) {
        const result = db.news_seed_urls.insertOne(seedUrl);
        print(`✓ Inserted seed URL: ${seedUrl.name}`);
        print(`  Actual URL called: ${seedUrl.metadata.actual_url_called}`);
    } else {
        print(`- Seed URL already exists: ${seedUrl.name}`);
    }
});

// Create indexes for efficient querying
print("Creating indexes for news_seed_urls collection...");

// Index for active seed URLs
db.news_seed_urls.createIndex({ "is_active": 1 });

// Index for fetching due URLs
db.news_seed_urls.createIndex({ 
    "is_active": 1, 
    "last_fetched_at": 1, 
    "frequency_hours": 1 
});

// Index for provider and category
db.news_seed_urls.createIndex({ "provider": 1, "category": 1 });

// Index for URL uniqueness
db.news_seed_urls.createIndex({ "url": 1, "metadata.api_params": 1 }, { unique: true });

print("✅ Default seed URLs migration completed successfully!");

// Display summary
const totalSeedUrls = db.news_seed_urls.countDocuments();
const activeSeedUrls = db.news_seed_urls.countDocuments({ is_active: true });

print(`📊 Summary:`);
print(`   Total seed URLs in database: ${totalSeedUrls}`);
print(`   Active seed URLs: ${activeSeedUrls}`);
print(`   Default URLs that will be called:`);
print(`   1. https://gnews.io/api/v4/top-headlines?category=general&country=in&lang=en&token={API_KEY}`);
print(`   2. https://gnews.io/api/v4/top-headlines?category=technology&country=in&lang=en&token={API_KEY}`);
print(`   3. https://gnews.io/api/v4/search?q=India&country=in&lang=en&sortby=publishedAt&token={API_KEY}`);
