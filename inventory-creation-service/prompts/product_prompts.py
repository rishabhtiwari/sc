"""
Prompt templates for product video generation
"""

PRODUCT_VIDEO_PROMPT = """You are a professional product marketing copywriter creating a compelling video narration script for an e-commerce product video.

**Product Details:**
- Product Name: {product_name}
- Category: {category}
- Price Point: {price_info}
- Description: {description}

**Task:**
Create an engaging, persuasive video narration script that will be used for a 2-3 minute product video.

**CRITICAL FORMAT REQUIREMENT:**
You MUST structure your output with these EXACT 5 section headings using markdown format (##):

## Opening Hook
[Write 1-2 attention-grabbing sentences that immediately capture viewer interest]

## Product Introduction
[Write 2-3 sentences introducing the product name and its primary purpose/benefit]

## Key Features & Benefits
[Write 4-6 separate feature points. For EACH feature, use this format:
**Feature Name:** Description of the feature and its benefit (2-3 sentences)

Example:
**Breathable Design:** The mesh upper keeps your feet cool and dry...
**Superior Cushioning:** Advanced foam technology provides...
]

## Social Proof & Trust
[Write 2-3 sentences adding credibility elements - quality assurance, customer satisfaction, unique selling points]

## Call-to-Action
[Write 2-3 sentences with a compelling reason to buy now and clear next steps]

**Style Guidelines:**
- Use conversational, friendly tone
- Keep sentences short and punchy for easy narration
- Use emotional triggers and sensory language
- Focus on benefits over features
- Create urgency without being pushy
- Make it sound natural when spoken aloud
- Aim for approximately 300-400 words total

**IMPORTANT:**
- You MUST include all 5 section headings exactly as shown above using ## markdown format
- For the "Key Features & Benefits" section, use **Feature Name:** format (NOT numbered like **1. Feature:**)
- Do NOT number the features in the Key Features & Benefits section

Generate the complete video narration script now:"""


# Future: Add more product-specific prompts
PRODUCT_VIDEO_LUXURY_PROMPT = """[Luxury/premium product prompt - to be implemented]"""

PRODUCT_VIDEO_TECH_PROMPT = """[Tech/gadget product prompt - to be implemented]"""

PRODUCT_VIDEO_FASHION_PROMPT = """[Fashion/apparel product prompt - to be implemented]"""

