/**
 * Migration: Restructure Product AI Summary to JSON Format
 * Version: 040
 * Date: 2025-12-23
 * 
 * This migration converts the ai_summary field from plain text to a structured JSON format
 * with separate sections, and adds audio_path and video_path fields for each section.
 * 
 * New Schema:
 * {
 *     "ai_summary": {
 *         "sections": [
 *             {
 *                 "title": "Opening Hook",
 *                 "content": "...",
 *                 "order": 1,
 *                 "audio_path": null,
 *                 "video_path": null,
 *                 "audio_config": {
 *                     "speed": 1.0,
 *                     "voice": "am_adam",
 *                     "duration": 0
 *                 }
 *             },
 *             ...
 *         ],
 *         "full_text": "...",  // Original full text for backward compatibility
 *         "generated_at": ISODate("..."),
 *         "version": "2.0"
 *     }
 * }
 */

db = db.getSiblingDB('news');

/**
 * Parse AI summary text into structured sections
 */
function parseAiSummaryToSections(aiSummaryText) {
    if (!aiSummaryText || typeof aiSummaryText !== 'string') {
        return [];
    }
    
    const sections = [];
    
    // Split by markdown headings (## Section Name)
    const parts = aiSummaryText.split(/\n##\s+/);
    
    // Remove first part if it's empty or doesn't start with ##
    let startIndex = 0;
    if (parts[0].trim() && !parts[0].startsWith('##')) {
        startIndex = 1;
    }
    
    let order = 1;
    for (let i = startIndex; i < parts.length; i++) {
        const part = parts[i].trim();
        if (!part) continue;
        
        // Split into title and content
        const lines = part.split('\n');
        const title = lines[0].trim();
        const content = lines.slice(1).join('\n').trim();
        
        sections.push({
            title: title,
            content: content,
            order: order,
            audio_path: null,
            video_path: null,
            audio_config: {
                speed: 1.0,  // Default speed, will be updated during audio generation
                voice: null,
                duration: 0
            }
        });
        order++;
    }
    
    return sections;
}

print('🔄 Starting migration: Restructure Product AI Summary');
print('📊 Database: news');
print('📦 Collection: products');

// Find all products with ai_summary field (old format - string)
const productsToMigrate = db.products.find({
    'ai_summary': { $type: 'string', $ne: '' }
});

let migratedCount = 0;
let skippedCount = 0;
let errorCount = 0;

productsToMigrate.forEach(function(product) {
    try {
        const productId = product._id;
        const oldSummary = product.ai_summary || '';
        
        // Parse into sections
        const sections = parseAiSummaryToSections(oldSummary);
        
        if (sections.length === 0) {
            print('⚠️  Product ' + productId + ': No sections found, skipping');
            skippedCount++;
            return;
        }
        
        // Create new structured format
        const newAiSummary = {
            sections: sections,
            full_text: oldSummary,  // Keep original for backward compatibility
            generated_at: product.updated_at || new Date(),
            version: '2.0'
        };
        
        // Update product
        db.products.updateOne(
            { _id: productId },
            {
                $set: {
                    ai_summary: newAiSummary,
                    migration_version: '040',
                    migrated_at: new Date()
                }
            }
        );
        
        migratedCount++;
        print('✅ Product ' + productId + ': Migrated ' + sections.length + ' sections');
        
    } catch (e) {
        errorCount++;
        print('❌ Product ' + product._id + ': Error - ' + e.message);
    }
});

print('');
print('============================================================');
print('✅ Migration completed!');
print('📊 Migrated: ' + migratedCount);
print('⚠️  Skipped: ' + skippedCount);
print('❌ Errors: ' + errorCount);
print('============================================================');

