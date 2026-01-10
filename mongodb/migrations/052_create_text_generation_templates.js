/**
 * Migration: Create default text generation prompt templates
 * Version: 052
 * Date: 2026-01-10
 *
 * This migration adds default text generation templates to the prompt_templates collection.
 * Requires migration 051 to be run first (adds text_generation category to schema).
 */

print('🔄 Starting migration: 052_create_text_generation_templates');

// Use the news database (same as all other prompt templates)
db = db.getSiblingDB('news');

// Text generation templates
const textTemplates = [
    {
        customer_id: 'customer_system',
        template_id: 'text_gen_headline',
        name: 'Catchy Headline',
        description: 'Generate attention-grabbing headlines for your designs',
        category: 'text_generation',
        prompt_text: `Generate a catchy, attention-grabbing headline for a design project.

Requirements:
- Keep it short and impactful (5-10 words)
- Make it memorable and engaging
- Use powerful action words
- Avoid clichés

Generate ONLY the headline text, nothing else.`,
        output_schema: {
            type: 'object',
            properties: {
                content: {
                    type: 'string',
                    description: 'The generated headline'
                }
            },
            required: ['content']
        },
        variables: [],
        is_system_default: true,
        is_active: true,
        metadata: {
            tags: ['headline', 'text', 'design'],
            author: 'system'
        },
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'system'
    },
    {
        customer_id: 'customer_system',
        template_id: 'text_gen_tagline',
        name: 'Brand Tagline',
        description: 'Create memorable brand taglines',
        category: 'text_generation',
        prompt_text: `Generate a memorable brand tagline.

Requirements:
- Keep it concise (3-7 words)
- Make it unique and memorable
- Reflect brand values
- Easy to remember

Generate ONLY the tagline text, nothing else.`,
        output_schema: {
            type: 'object',
            properties: {
                content: {
                    type: 'string',
                    description: 'The generated tagline'
                }
            },
            required: ['content']
        },
        variables: [],
        is_system_default: true,
        is_active: true,
        metadata: {
            tags: ['tagline', 'branding', 'text'],
            author: 'system'
        },
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'system'
    },
    {
        customer_id: 'customer_system',
        template_id: 'text_gen_social_caption',
        name: 'Social Media Caption',
        description: 'Generate engaging social media captions',
        category: 'text_generation',
        prompt_text: `Generate an engaging social media caption.

Requirements:
- Keep it conversational and friendly
- Include a call-to-action
- Use emojis appropriately
- Keep it under 150 characters

Generate ONLY the caption text, nothing else.`,
        output_schema: {
            type: 'object',
            properties: {
                content: {
                    type: 'string',
                    description: 'The generated caption'
                }
            },
            required: ['content']
        },
        variables: [],
        is_system_default: true,
        is_active: true,
        metadata: {
            tags: ['social-media', 'caption', 'text'],
            author: 'system'
        },
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'system'
    },
    {
        customer_id: 'customer_system',
        template_id: 'text_gen_quote',
        name: 'Inspirational Quote',
        description: 'Generate inspirational quotes for designs',
        category: 'text_generation',
        prompt_text: `Generate an inspirational quote.

Requirements:
- Make it motivational and uplifting
- Keep it concise (10-20 words)
- Use powerful, positive language
- Make it relatable

Generate ONLY the quote text, nothing else.`,
        output_schema: {
            type: 'object',
            properties: {
                content: {
                    type: 'string',
                    description: 'The generated quote'
                }
            },
            required: ['content']
        },
        variables: [],
        is_system_default: true,
        is_active: true,
        metadata: {
            tags: ['quote', 'inspiration', 'text'],
            author: 'system'
        },
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'system'
    }
];

// Insert templates
print('Inserting text generation templates...');
textTemplates.forEach(template => {
    const existing = db.prompt_templates.findOne({
        template_id: template.template_id,
        customer_id: template.customer_id
    });
    
    if (existing) {
        print(`  ⚠ Template ${template.template_id} already exists, skipping`);
    } else {
        db.prompt_templates.insertOne(template);
        print(`  ✓ Created template: ${template.name}`);
    }
});

print('✓ Migration 052_create_text_generation_templates completed successfully');

