/**
 * Migration: Create Prompt Templates Collection
 * Version: 041
 * Date: 2025-12-27
 * 
 * This migration creates a prompt_templates collection to store customizable
 * LLM prompts for product content generation with structured JSON output.
 */

print('🔄 Starting migration: 041_create_prompt_templates_collection');

// Switch to news database
db = db.getSiblingDB('news');

// Create prompt_templates collection
db.createCollection('prompt_templates', {
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
                    enum: ['ecommerce', 'social_media', 'news', 'marketing', 'product_summary', 'section_content', 'custom'],
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
print('✓ Created prompt_templates collection with schema validation');

// Create indexes
db.prompt_templates.createIndex(
    { template_id: 1, customer_id: 1 },
    { unique: true, name: 'idx_template_id_customer' }
);
print('✓ Created unique index on template_id + customer_id');

db.prompt_templates.createIndex(
    { customer_id: 1, category: 1, is_active: 1 },
    { name: 'idx_customer_category_active' }
);
print('✓ Created index on customer_id + category + is_active');

db.prompt_templates.createIndex(
    { customer_id: 1, is_system_default: 1 },
    { name: 'idx_customer_system_default' }
);
print('✓ Created index on customer_id + is_system_default');

// Insert default prompt templates
const now = new Date();

// Default Product Summary Template (Current format)
db.prompt_templates.insertOne({
    customer_id: 'customer_system',
    template_id: 'product_summary_default_v1',
    name: 'Default Product Summary',
    description: 'Standard product video narration script with 5 sections',
    category: 'ecommerce',
    prompt_text: `You are a professional product marketing copywriter creating a compelling video narration script for an e-commerce product video.

**Product Details:**
- Product Name: {product_name}
- Category: {category}
- Price Point: {price_info}
- Description: {description}

**Task:**
Create an engaging, persuasive video narration script that will be used for a 2-3 minute product video.

**CRITICAL OUTPUT FORMAT:**
You MUST return ONLY a valid JSON object with this exact structure (no markdown, no code blocks, just raw JSON):

{
  "opening_hook": "1-2 attention-grabbing sentences that immediately capture viewer interest",
  "product_introduction": "2-3 sentences introducing the product name and its primary purpose/benefit",
  "key_features": [
    {
      "feature_name": "Feature Name",
      "description": "Description of the feature and its benefit (2-3 sentences)"
    }
  ],
  "social_proof": "2-3 sentences adding credibility elements - quality assurance, customer satisfaction, unique selling points",
  "call_to_action": "2-3 sentences with a compelling reason to buy now and clear next steps"
}

**Style Guidelines:**
- Use conversational, friendly tone
- Keep sentences short and punchy for easy narration
- Use emotional triggers and sensory language
- Focus on benefits over features
- Create urgency without being pushy
- Make it sound natural when spoken aloud
- Include 4-6 features in the key_features array
- Aim for approximately 300-400 words total

Generate the JSON response now:`,
    output_schema: {
        type: 'object',
        required: ['opening_hook', 'product_introduction', 'key_features', 'social_proof', 'call_to_action'],
        properties: {
            opening_hook: { type: 'string', minLength: 20, maxLength: 500 },
            product_introduction: { type: 'string', minLength: 50, maxLength: 800 },
            key_features: {
                type: 'array',
                minItems: 3,
                maxItems: 8,
                items: {
                    type: 'object',
                    required: ['feature_name', 'description'],
                    properties: {
                        feature_name: { type: 'string', minLength: 3, maxLength: 100 },
                        description: { type: 'string', minLength: 20, maxLength: 500 }
                    }
                }
            },
            social_proof: { type: 'string', minLength: 30, maxLength: 600 },
            call_to_action: { type: 'string', minLength: 30, maxLength: 600 }
        }
    },
    variables: [
        { name: 'product_name', type: 'string', description: 'Name of the product', required: true, default: null },
        { name: 'category', type: 'string', description: 'Product category', required: true, default: null },
        { name: 'price_info', type: 'string', description: 'Price point or range', required: false, default: 'Premium quality' },
        { name: 'description', type: 'string', description: 'Product description', required: true, default: null }
    ],
    is_system_default: true,
    is_active: true,
    metadata: {
        author: 'System',
        tags: ['product', 'ecommerce', 'video', 'narration', 'default'],
        version: '1.0.0'
    },
    created_at: now,
    updated_at: now,
    created_by: 'system'
});
print('✓ Inserted template: product_summary_default_v1');

// Luxury Product Template
db.prompt_templates.insertOne({
    customer_id: 'customer_system',
    template_id: 'product_summary_luxury_v1',
    name: 'Luxury Product Summary',
    description: 'Premium, sophisticated narration for luxury products',
    category: 'ecommerce',
    prompt_text: `You are an elite luxury brand copywriter creating an exclusive video narration for a premium product.

**Product Details:**
- Product Name: {product_name}
- Category: {category}
- Price Point: {price_info}
- Description: {description}

**Task:**
Create a sophisticated, aspirational video narration that emphasizes exclusivity, craftsmanship, and prestige.

**CRITICAL OUTPUT FORMAT:**
Return ONLY a valid JSON object (no markdown, no code blocks):

{
  "opening_hook": "Captivating opening that evokes desire and exclusivity",
  "product_introduction": "Elegant introduction emphasizing heritage, craftsmanship, or uniqueness",
  "key_features": [
    {
      "feature_name": "Feature Name",
      "description": "Sophisticated description highlighting premium materials, artisanal quality, or innovative design"
    }
  ],
  "social_proof": "Emphasis on exclusivity, limited availability, celebrity endorsements, or prestigious awards",
  "call_to_action": "Refined call-to-action that maintains exclusivity while encouraging action"
}

**Style Guidelines:**
- Use sophisticated, refined language
- Emphasize quality, craftsmanship, and exclusivity
- Create aspiration and desire
- Avoid aggressive sales tactics
- Use sensory and emotional language
- Include 3-5 premium features
- Maintain an air of sophistication throughout

Generate the JSON response now:`,
    output_schema: {
        type: 'object',
        required: ['opening_hook', 'product_introduction', 'key_features', 'social_proof', 'call_to_action'],
        properties: {
            opening_hook: { type: 'string', minLength: 20, maxLength: 500 },
            product_introduction: { type: 'string', minLength: 50, maxLength: 800 },
            key_features: {
                type: 'array',
                minItems: 3,
                maxItems: 6,
                items: {
                    type: 'object',
                    required: ['feature_name', 'description'],
                    properties: {
                        feature_name: { type: 'string', minLength: 3, maxLength: 100 },
                        description: { type: 'string', minLength: 20, maxLength: 500 }
                    }
                }
            },
            social_proof: { type: 'string', minLength: 30, maxLength: 600 },
            call_to_action: { type: 'string', minLength: 30, maxLength: 600 }
        }
    },
    variables: [
        { name: 'product_name', type: 'string', description: 'Name of the product', required: true, default: null },
        { name: 'category', type: 'string', description: 'Product category', required: true, default: null },
        { name: 'price_info', type: 'string', description: 'Price point or range', required: false, default: 'Exclusive pricing' },
        { name: 'description', type: 'string', description: 'Product description', required: true, default: null }
    ],
    is_system_default: true,
    is_active: true,
    metadata: {
        author: 'System',
        tags: ['product', 'luxury', 'premium', 'sophisticated', 'exclusive'],
        version: '1.0.0'
    },
    created_at: now,
    updated_at: now,
    created_by: 'system'
});
print('✓ Inserted template: product_summary_luxury_v1');

// Tech/Gadget Product Template
db.prompt_templates.insertOne({
    customer_id: 'customer_system',
    template_id: 'product_summary_tech_v1',
    name: 'Tech & Gadget Summary',
    description: 'Technical, feature-focused narration for tech products and gadgets',
    category: 'ecommerce',
    prompt_text: `You are a tech product reviewer creating an informative and exciting video narration for a technology product or gadget.

**Product Details:**
- Product Name: {product_name}
- Category: {category}
- Price Point: {price_info}
- Description: {description}

**Task:**
Create an engaging, informative video narration that highlights technical specifications, innovative features, and practical benefits.

**CRITICAL OUTPUT FORMAT:**
Return ONLY a valid JSON object (no markdown, no code blocks):

{
  "opening_hook": "Exciting opening that highlights innovation or solves a tech problem",
  "product_introduction": "Clear introduction of the product with key specs and what makes it innovative",
  "key_features": [
    {
      "feature_name": "Feature/Spec Name",
      "description": "Technical details with practical benefits and real-world applications"
    }
  ],
  "social_proof": "Tech credentials, certifications, awards, compatibility, or user ratings",
  "call_to_action": "Clear CTA emphasizing value, early adopter benefits, or limited availability"
}

**Style Guidelines:**
- Balance technical accuracy with accessibility
- Explain specs in terms of real-world benefits
- Use enthusiastic but credible tone
- Highlight innovation and problem-solving
- Include compatibility and integration details
- Use tech-savvy language without jargon overload
- Include 4-7 technical features
- Emphasize what makes it better than alternatives

Generate the JSON response now:`,
    output_schema: {
        type: 'object',
        required: ['opening_hook', 'product_introduction', 'key_features', 'social_proof', 'call_to_action'],
        properties: {
            opening_hook: { type: 'string', minLength: 20, maxLength: 500 },
            product_introduction: { type: 'string', minLength: 50, maxLength: 800 },
            key_features: {
                type: 'array',
                minItems: 4,
                maxItems: 8,
                items: {
                    type: 'object',
                    required: ['feature_name', 'description'],
                    properties: {
                        feature_name: { type: 'string', minLength: 3, maxLength: 100 },
                        description: { type: 'string', minLength: 20, maxLength: 500 }
                    }
                }
            },
            social_proof: { type: 'string', minLength: 30, maxLength: 600 },
            call_to_action: { type: 'string', minLength: 30, maxLength: 600 }
        }
    },
    variables: [
        { name: 'product_name', type: 'string', description: 'Name of the product', required: true, default: null },
        { name: 'category', type: 'string', description: 'Product category', required: true, default: null },
        { name: 'price_info', type: 'string', description: 'Price point or range', required: false, default: 'Competitive pricing' },
        { name: 'description', type: 'string', description: 'Product description with specs', required: true, default: null }
    ],
    is_system_default: true,
    is_active: true,
    metadata: {
        author: 'System',
        tags: ['product', 'tech', 'gadget', 'technology', 'innovation'],
        version: '1.0.0'
    },
    created_at: now,
    updated_at: now,
    created_by: 'system'
});
print('✓ Inserted template: product_summary_tech_v1');

// 4. Fashion & Apparel Template
db.prompt_templates.insertOne({
    customer_id: 'customer_system',
    template_id: 'product_summary_fashion_v1',
    product_name: 'Fashion & Apparel Summary',
    name: 'Fashion & Apparel Summary',
    description: 'Stylish, trend-focused narration for fashion and clothing products',
    category: 'ecommerce',
    prompt_text: `You are a fashion stylist and copywriter creating an inspiring video narration for a fashion or apparel product.

**Product Details:**
- Product Name: {product_name}
- Category: {category}
- Price Point: {price_info}
- Description: {description}

**Task:**
Create a stylish, trend-focused video narration that emphasizes style, versatility, and fashion-forward design.

**CRITICAL OUTPUT FORMAT:**
Return ONLY a valid JSON object (no markdown, no code blocks):

{
  "opening_hook": "Fashion-forward opening that captures current trends or timeless style",
  "product_introduction": "Introduction highlighting design, style, and what makes it a must-have",
  "key_features": [
    {
      "feature_name": "Feature Name",
      "description": "Style details, materials, fit, versatility, and styling options"
    }
  ],
  "social_proof": "Fashion credentials, designer info, celebrity endorsements, or customer reviews",
  "call_to_action": "Stylish CTA emphasizing limited stock, seasonal relevance, or style versatility"
}

**Style Guidelines:**
- Use fashionable, aspirational language
- Emphasize style, fit, and versatility
- Highlight materials and craftsmanship
- Include styling suggestions
- Create desire and FOMO (fear of missing out)
- Use sensory descriptions (texture, drape, feel)
- Include 3-5 style features
- Mention occasions or styling versatility

Generate the JSON response now:`,
    output_schema: {
        type: 'object',
        required: ['opening_hook', 'product_introduction', 'key_features', 'social_proof', 'call_to_action'],
        properties: {
            opening_hook: { type: 'string', minLength: 20, maxLength: 500 },
            product_introduction: { type: 'string', minLength: 50, maxLength: 800 },
            key_features: {
                type: 'array',
                minItems: 3,
                maxItems: 6,
                items: {
                    type: 'object',
                    required: ['feature_name', 'description'],
                    properties: {
                        feature_name: { type: 'string', minLength: 3, maxLength: 100 },
                        description: { type: 'string', minLength: 20, maxLength: 500 }
                    }
                }
            },
            social_proof: { type: 'string', minLength: 30, maxLength: 600 },
            call_to_action: { type: 'string', minLength: 30, maxLength: 600 }
        }
    },
    variables: [
        { name: 'product_name', type: 'string', description: 'Name of the product', required: true, default: null },
        { name: 'category', type: 'string', description: 'Product category', required: true, default: null },
        { name: 'price_info', type: 'string', description: 'Price point or range', required: false, default: 'Affordable style' },
        { name: 'description', type: 'string', description: 'Product description', required: true, default: null }
    ],
    is_system_default: true,
    is_active: true,
    metadata: {
        author: 'System',
        tags: ['product', 'fashion', 'apparel', 'clothing', 'style'],
        version: '1.0.0'
    },
    created_at: now,
    updated_at: now,
    created_by: 'system'
});
print('✓ Inserted template: product_summary_fashion_v1');

// 5. Food & Beverage Template
db.prompt_templates.insertOne({
    customer_id: 'customer_system',
    template_id: 'product_summary_food_v1',
    product_name: 'Food & Beverage Summary',
    name: 'Food & Beverage Summary',
    description: 'Appetizing, sensory-rich narration for food and beverage products',
    category: 'ecommerce',
    prompt_text: `You are a food writer and culinary expert creating a mouth-watering video narration for a food or beverage product.

**Product Details:**
- Product Name: {product_name}
- Category: {category}
- Price Point: {price_info}
- Description: {description}

**Task:**
Create an appetizing, sensory-rich video narration that makes viewers crave the product.

**CRITICAL OUTPUT FORMAT:**
Return ONLY a valid JSON object (no markdown, no code blocks):

{
  "opening_hook": "Appetizing opening that triggers cravings or highlights unique taste experience",
  "product_introduction": "Introduction with sensory details, origin story, or what makes it special",
  "key_features": [
    {
      "feature_name": "Feature Name",
      "description": "Taste profile, ingredients, preparation, health benefits, or usage occasions"
    }
  ],
  "social_proof": "Quality certifications, awards, chef endorsements, customer reviews, or sourcing details",
  "call_to_action": "Compelling CTA emphasizing freshness, limited availability, or special offers"
}

**Style Guidelines:**
- Use rich sensory language (taste, aroma, texture, appearance)
- Emphasize freshness, quality ingredients, and authenticity
- Create cravings through vivid descriptions
- Highlight health benefits or dietary features
- Include origin story or artisanal details
- Mention pairing suggestions or usage occasions
- Include 3-5 taste/quality features
- Use warm, inviting tone

Generate the JSON response now:`,
    output_schema: {
        type: 'object',
        required: ['opening_hook', 'product_introduction', 'key_features', 'social_proof', 'call_to_action'],
        properties: {
            opening_hook: { type: 'string', minLength: 20, maxLength: 500 },
            product_introduction: { type: 'string', minLength: 50, maxLength: 800 },
            key_features: {
                type: 'array',
                minItems: 3,
                maxItems: 6,
                items: {
                    type: 'object',
                    required: ['feature_name', 'description'],
                    properties: {
                        feature_name: { type: 'string', minLength: 3, maxLength: 100 },
                        description: { type: 'string', minLength: 20, maxLength: 500 }
                    }
                }
            },
            social_proof: { type: 'string', minLength: 30, maxLength: 600 },
            call_to_action: { type: 'string', minLength: 30, maxLength: 600 }
        }
    },
    variables: [
        { name: 'product_name', type: 'string', description: 'Name of the product', required: true, default: null },
        { name: 'category', type: 'string', description: 'Product category', required: true, default: null },
        { name: 'price_info', type: 'string', description: 'Price point or range', required: false, default: 'Great value' },
        { name: 'description', type: 'string', description: 'Product description with ingredients/details', required: true, default: null }
    ],
    is_system_default: true,
    is_active: true,
    metadata: {
        author: 'System',
        tags: ['product', 'food', 'beverage', 'culinary', 'gourmet'],
        version: '1.0.0'
    },
    created_at: now,
    updated_at: now,
    created_by: 'system'
});
print('✓ Inserted template: product_summary_food_v1');

print('✓ Migration 041_create_prompt_templates_collection completed successfully');

