/**
 * Migration: Add text_generation category to prompt_templates schema
 * Version: 051
 * Date: 2026-01-10
 * 
 * This migration updates the prompt_templates collection validator to include
 * the 'text_generation' category in the allowed enum values.
 */

print('🔄 Starting migration: 051_add_text_generation_category');

// Switch to news database
db = db.getSiblingDB('news');

// Get current validator
const currentValidator = db.getCollectionInfos({ name: 'prompt_templates' })[0].options.validator;

// Update the validator to include 'text_generation' category
db.runCommand({
    collMod: 'prompt_templates',
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['template_id', 'name', 'category', 'prompt_text', 'output_schema', 'customer_id'],
            properties: {
                customer_id: {
                    bsonType: 'string',
                    description: 'Customer ID for multi-tenancy (use "customer_system" for system templates)'
                },
                template_id: {
                    bsonType: 'string',
                    description: 'Unique template identifier'
                },
                name: {
                    bsonType: 'string',
                    description: 'Template display name'
                },
                description: {
                    bsonType: 'string',
                    description: 'Template description'
                },
                category: {
                    bsonType: 'string',
                    enum: ['ecommerce', 'social_media', 'news', 'marketing', 'product_summary', 'section_content', 'text_generation', 'custom'],
                    description: 'Template category/use case'
                },
                prompt_text: {
                    bsonType: 'string',
                    description: 'Prompt template with placeholders like {product_name}, {features}'
                },
                output_schema: {
                    bsonType: 'object',
                    description: 'JSON schema for validating LLM output'
                },
                variables: {
                    bsonType: 'array',
                    description: 'List of variable placeholders used in prompt',
                    items: {
                        bsonType: 'object',
                        required: ['name', 'type'],
                        properties: {
                            name: { bsonType: 'string' },
                            type: { bsonType: 'string' },
                            description: { bsonType: 'string' },
                            required: { bsonType: 'bool' },
                            default: { bsonType: ['string', 'null'] }
                        }
                    }
                },
                is_system_default: {
                    bsonType: 'bool',
                    description: 'Whether this is a system-provided template'
                },
                is_active: {
                    bsonType: 'bool',
                    description: 'Whether template is active'
                },
                metadata: {
                    bsonType: 'object',
                    description: 'Additional metadata (tags, author, etc.)'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Creation timestamp'
                },
                updated_at: {
                    bsonType: 'date',
                    description: 'Last update timestamp'
                },
                created_by: {
                    bsonType: 'string',
                    description: 'User who created the template'
                }
            }
        }
    }
});

print('✓ Updated prompt_templates validator to include text_generation category');

print('✓ Migration 051_add_text_generation_category completed successfully');

