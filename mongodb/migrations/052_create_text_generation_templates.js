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
        prompt_text: `Generate a catchy, attention-grabbing headline about: {topic}

Topic/Subject: {topic}
Target Audience: {audience}

Requirements:
- Keep it short and impactful (5-10 words)
- Make it memorable and engaging
- Use powerful action words
- Avoid clichés
- Tailor to the target audience

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
        variables: [
            {
                name: 'topic',
                type: 'text',
                description: 'What is the headline about?',
                required: true,
                default: 'Summer Sale - Up to 50% Off'
            },
            {
                name: 'audience',
                type: 'text',
                description: 'Who is the target audience?',
                required: false,
                default: 'Young professionals'
            }
        ],
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
        prompt_text: `Generate a memorable brand tagline for: {brand_name}

Brand Name: {brand_name}
What the brand does: {brand_description}

Requirements:
- Keep it concise (3-7 words)
- Make it unique and memorable
- Reflect the brand personality
- Easy to remember and pronounce
- Emotionally resonant

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
        variables: [
            {
                name: 'brand_name',
                type: 'text',
                description: 'What is the brand name?',
                required: true,
                default: 'TechFlow'
            },
            {
                name: 'brand_description',
                type: 'textarea',
                description: 'Brief description of what the brand does',
                required: false,
                default: 'A modern productivity app for remote teams'
            }
        ],
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
        prompt_text: `Generate an engaging social media caption about: {topic}

Topic/Content: {topic}
Target Audience: {audience}

Requirements:
- Keep it conversational and friendly
- Include a call-to-action
- Use emojis appropriately
- Tailor to the target audience
- Keep it engaging and shareable

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
        variables: [
            {
                name: 'topic',
                type: 'textarea',
                description: 'What is the post about?',
                required: true,
                default: 'Launching our new eco-friendly product line'
            },
            {
                name: 'audience',
                type: 'text',
                description: 'Who is the target audience?',
                required: false,
                default: 'Environmentally conscious millennials'
            }
        ],
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
        prompt_text: `Generate an inspirational quote about: {topic}

Topic/Theme: {topic}
Target Audience: {audience}

Requirements:
- Make it motivational and uplifting
- Keep it concise (10-20 words)
- Use powerful, positive language
- Make it relatable to the audience
- Focus on the specified theme

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
        variables: [
            {
                name: 'topic',
                type: 'text',
                description: 'What theme or topic?',
                required: true,
                default: 'Success and perseverance'
            },
            {
                name: 'audience',
                type: 'text',
                description: 'Who is the target audience?',
                required: false,
                default: 'Entrepreneurs and dreamers'
            }
        ],
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

// Insert or replace templates (upsert)
print('Inserting/updating text generation templates...');
textTemplates.forEach(template => {
    const result = db.prompt_templates.replaceOne(
        {
            template_id: template.template_id,
            customer_id: template.customer_id
        },
        template,
        { upsert: true }
    );

    if (result.matchedCount > 0) {
        print(`  ✓ Updated template: ${template.name}`);
    } else {
        print(`  ✓ Created template: ${template.name}`);
    }
});

print('✓ Migration 052_create_text_generation_templates completed successfully');

