// Migration: Create projects collection for Design Editor
// Description: Creates projects collection with indexes for storing design editor projects
// Date: 2026-02-01

print('🎨 Starting migration: 056_create_projects_collection');

// Switch to ichat_db database (where assets are stored)
db = db.getSiblingDB('ichat_db');

print('📦 Creating projects collection...');

// Create the projects collection
db.createCollection('projects', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["project_id", "customer_id", "user_id", "name", "created_at", "updated_at"],
            properties: {
                project_id: {
                    bsonType: "string",
                    description: "Unique project identifier (required)"
                },
                customer_id: {
                    bsonType: "string",
                    description: "Customer ID who owns the project (required)"
                },
                user_id: {
                    bsonType: "string",
                    description: "User ID who created the project (required)"
                },
                name: {
                    bsonType: "string",
                    description: "Project name (required)"
                },
                description: {
                    bsonType: ["string", "null"],
                    description: "Project description (optional)"
                },
                thumbnail: {
                    bsonType: ["string", "null"],
                    description: "Project thumbnail URL (optional)"
                },
                settings: {
                    bsonType: "object",
                    description: "Project settings (canvas, duration, fps, quality)"
                },
                pages: {
                    bsonType: "array",
                    description: "Array of pages/slides in the project"
                },
                audioTracks: {
                    bsonType: "array",
                    description: "Array of audio tracks on timeline"
                },
                videoTracks: {
                    bsonType: "array",
                    description: "Array of video tracks on timeline"
                },
                assetReferences: {
                    bsonType: "array",
                    description: "Array of asset IDs referenced in the project"
                },
                version: {
                    bsonType: "int",
                    description: "Project version number"
                },
                status: {
                    bsonType: "string",
                    enum: ["draft", "published", "archived"],
                    description: "Project status"
                },
                tags: {
                    bsonType: "array",
                    description: "Array of tags for categorization"
                },
                created_at: {
                    bsonType: "date",
                    description: "Project creation timestamp (required)"
                },
                updated_at: {
                    bsonType: "date",
                    description: "Project last update timestamp (required)"
                },
                last_opened_at: {
                    bsonType: ["date", "null"],
                    description: "Last time project was opened (optional)"
                },
                deleted_at: {
                    bsonType: ["date", "null"],
                    description: "Soft delete timestamp (optional)"
                }
            }
        }
    }
});

print('✅ Projects collection created with schema validation');

print('📇 Creating indexes for projects collection...');

// Unique compound index on project_id and customer_id
db.projects.createIndex(
    { "project_id": 1, "customer_id": 1 },
    { 
        unique: true,
        name: "project_id_customer_id_unique"
    }
);
print('  ✓ Created unique index: project_id + customer_id');

// Index for listing projects by customer and user
db.projects.createIndex(
    { "customer_id": 1, "user_id": 1 },
    { name: "customer_user_index" }
);
print('  ✓ Created index: customer_id + user_id');

// Index for filtering by status
db.projects.createIndex(
    { "customer_id": 1, "status": 1 },
    { name: "customer_status_index" }
);
print('  ✓ Created index: customer_id + status');

// Index for sorting by updated_at (most recent first)
db.projects.createIndex(
    { "customer_id": 1, "updated_at": -1 },
    { name: "customer_updated_index" }
);
print('  ✓ Created index: customer_id + updated_at (descending)');

// Index for soft delete queries
db.projects.createIndex(
    { "deleted_at": 1 },
    { name: "deleted_at_index" }
);
print('  ✓ Created index: deleted_at');

// Index for asset reference lookups
db.projects.createIndex(
    { "assetReferences": 1 },
    { name: "asset_references_index" }
);
print('  ✓ Created index: assetReferences');

print('');
print('📊 Migration Summary:');
print('   - Collection: projects');
print('   - Database: ichat_db');
print('   - Indexes created: 6');
print('   - Schema validation: enabled');
print('');

print('✅ Migration 056_create_projects_collection completed successfully');

