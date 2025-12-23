"""
Product Service - Backend service for e-commerce product management
Handles all product CRUD operations, AI summary generation, and video generation orchestration
"""

import logging
import os
import re
import io
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import requests
from pydub import AudioSegment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB Configuration
MONGO_URI = os.getenv('MONGODB_URL', 'mongodb://ichat_app:ichat_app_password_2024@ichat-mongodb:27017/news?authSource=admin')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['news']
products_collection = db['products']

# Service URLs
LLM_SERVICE_URL = os.getenv('LLM_SERVICE_URL', 'http://ichat-llm-service:8083')
VIDEO_GENERATOR_URL = os.getenv('VIDEO_GENERATOR_URL', 'http://ichat-video-generator:8095')
AUDIO_GENERATION_URL = os.getenv('AUDIO_GENERATION_URL', 'http://audio-generation-factory:3000')
TEMPLATE_SERVICE_URL = os.getenv('TEMPLATE_SERVICE_URL', 'http://ichat-template-service:5010')
API_SERVER_URL = os.getenv('API_SERVER_EXTERNAL_URL', 'http://localhost:8080')


def convert_audio_url_to_proxy(audio_url):
    """Convert internal audio-generation-factory URL to API server proxy URL

    Args:
        audio_url: Internal URL like http://audio-generation-factory:3000/temp/file.wav

    Returns:
        Proxy URL like http://localhost:8080/api/audio/proxy/temp/file.wav
    """
    if not audio_url:
        return audio_url

    # Extract the path after the audio-generation-factory domain
    # e.g., http://audio-generation-factory:3000/temp/file.wav -> temp/file.wav
    if AUDIO_GENERATION_URL in audio_url:
        relative_path = audio_url.replace(AUDIO_GENERATION_URL, '').lstrip('/')
        proxy_url = f"{API_SERVER_URL}/api/audio/proxy/{relative_path}"
        logger.debug(f"Converted audio URL: {audio_url} -> {proxy_url}")
        return proxy_url

    # If it's already a proxy URL or some other format, return as-is
    return audio_url


def serialize_product(product):
    """Convert MongoDB document to JSON-serializable dict"""
    if product:
        product['_id'] = str(product['_id'])
        if 'created_at' in product and isinstance(product['created_at'], datetime):
            product['created_at'] = product['created_at'].isoformat()
        if 'updated_at' in product and isinstance(product['updated_at'], datetime):
            product['updated_at'] = product['updated_at'].isoformat()
        # Backward compatibility: provide both 'name' and 'product_name'
        if 'name' in product:
            product['product_name'] = product['name']
    return product


def strip_markdown_for_tts(text):
    """
    Strip markdown syntax from text for TTS (Text-to-Speech)
    Removes:
    - ### headings
    - ** bold markers
    - * italic markers
    - Other markdown syntax that shouldn't be spoken
    """
    if not text:
        return text

    # Remove markdown headings (###, ##, #)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold markers (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # Remove italic markers (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

    # Remove inline code `code` -> code
    text = re.sub(r'`(.+?)`', r'\1', text)

    return text.strip()


def parse_ai_summary_to_sections(ai_summary_text):
    """
    Parse AI summary text into structured sections

    Expected format:
    ## Opening Hook
    Content here...

    ## Product Introduction
    Content here...

    ## Key Features & Benefits
    **Feature 1:** Description
    **Feature 2:** Description

    ## Social Proof & Trust
    Content here...

    ## Call-to-Action
    Content here...

    Returns:
        list: List of section dictionaries with title, content, order, etc.
    """
    if not ai_summary_text:
        return []

    sections = []

    # Split by markdown headings (## Section Name)
    parts = re.split(r'\n##\s+', ai_summary_text)

    # First part might not have a heading if text starts without ##
    if parts[0].strip() and not parts[0].startswith('##'):
        # This is content before any heading - skip or treat as intro
        parts = parts[1:]

    order = 1
    for part in parts:
        if not part.strip():
            continue

        # Split into title and content
        lines = part.strip().split('\n', 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""

        sections.append({
            "title": title,
            "content": content,
            "order": order,
            "audio_path": None,
            "video_path": None,
            "audio_config": {
                "speed": 1.0,  # Default speed, will be updated during audio generation
                "voice": None,
                "duration": 0
            }
        })
        order += 1

    return sections


def get_smart_audio_config(section_title, section_index, total_sections):
    """
    Get intelligent audio configuration for a section to create engaging storytelling

    This creates a natural narrative arc:
    - Opening: Energetic and attention-grabbing
    - Middle: Clear, informative, slightly varied
    - Closing: Confident and motivating

    Args:
        section_title: Title of the section
        section_index: 0-based index of the section
        total_sections: Total number of sections

    Returns:
        dict: Audio configuration with speed and description
    """
    section_lower = section_title.lower()

    # Default configuration
    config = {
        'speed': 1.0,
        'description': 'Standard narration'
    }

    # 1. OPENING HOOK - Fast, energetic, attention-grabbing
    if 'hook' in section_lower or 'opening' in section_lower or section_index == 0:
        config.update({
            'speed': 1.1,
            'description': '⚡ Energetic opening to grab attention'
        })

    # 2. PRODUCT INTRODUCTION - Warm, welcoming, clear
    elif 'introduction' in section_lower or 'intro' in section_lower or section_index == 1:
        config.update({
            'speed': 1.0,
            'description': '👋 Warm and welcoming introduction'
        })

    # 3. KEY FEATURES & BENEFITS - Slower, clear, informative
    elif 'feature' in section_lower or 'benefit' in section_lower:
        config.update({
            'speed': 0.95,
            'description': '📋 Clear and informative feature presentation'
        })

    # 4. SOCIAL PROOF & TRUST - Confident, steady
    elif 'proof' in section_lower or 'trust' in section_lower or 'testimonial' in section_lower:
        config.update({
            'speed': 1.0,
            'description': '✅ Confident and trustworthy tone'
        })

    # 5. CALL-TO-ACTION - Energetic, urgent, motivating
    elif 'action' in section_lower or 'cta' in section_lower or 'call' in section_lower or section_index == total_sections - 1:
        config.update({
            'speed': 1.05,
            'description': '🎯 Energetic and motivating call-to-action'
        })

    # Default for any other sections
    else:
        config.update({
            'speed': 1.0,
            'description': '📝 Standard narration pace'
        })

    return config


def get_section_speed(section_title, section_pitches, section_index=0, total_sections=5):
    """
    Get speed for a section based on user preferences or smart defaults

    Uses intelligent defaults that create a natural storytelling arc:
    - Opening Hook: 1.1x (energetic)
    - Product Introduction: 1.0x (welcoming)
    - Key Features: 0.95x (clear, informative)
    - Social Proof: 1.0x (confident)
    - Call-to-Action: 1.05x (motivating)

    User can override with custom pitch settings.

    Args:
        section_title (str): Title of the section
        section_pitches (dict): Dictionary mapping section titles to pitch values (user overrides)
        section_index (int): Index of the section (for smart defaults)
        total_sections (int): Total number of sections (for smart defaults)

    Returns:
        float: Speed value for TTS (0.85 to 1.15)
    """
    # Check if user has set a custom pitch for this section (OVERRIDE)
    if section_pitches and section_title in section_pitches:
        pitch = section_pitches.get(section_title, 'normal')

        speed_map = {
            'low': 0.85,
            'normal': 1.0,
            'high': 1.15
        }

        return speed_map.get(pitch, 1.0)

    # Use smart defaults based on section type and position
    smart_config = get_smart_audio_config(section_title, section_index, total_sections)
    return smart_config['speed']


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'product-service'}), 200


@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products for a customer"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')
        
        logger.info(f"📦 Fetching products for customer: {customer_id}, user: {user_id}")
        
        products = list(products_collection.find({
            'customer_id': customer_id,
            'user_id': user_id
        }).sort('created_at', -1))
        
        products = [serialize_product(p) for p in products]
        
        logger.info(f"✅ Found {len(products)} products")
        return jsonify({
            'status': 'success',
            'products': products,
            'count': len(products)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error fetching products: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')
        
        product = products_collection.find_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })
        
        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'product': serialize_product(product)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error fetching product: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products', methods=['POST'])
def create_product():
    """Create a new product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')
        
        data = request.get_json()
        
        product = {
            'customer_id': customer_id,
            'user_id': user_id,
            'name': data.get('product_name') or data.get('name'),  # Support both field names
            'description': data.get('description'),
            'category': data.get('category', 'General'),
            'price': data.get('price'),
            'currency': data.get('currency', 'USD'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'draft'
        }
        
        result = products_collection.insert_one(product)
        product['_id'] = str(result.inserted_id)

        logger.info(f"✅ Created product: {product['_id']}")
        return jsonify({
            'status': 'success',
            'product_id': product['_id'],
            'product': serialize_product(product)
        }), 201

    except Exception as e:
        logger.error(f"❌ Error creating product: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        data = request.get_json()

        update_data = {
            'updated_at': datetime.utcnow()
        }

        # Update allowed fields
        allowed_fields = ['product_name', 'name', 'description', 'category', 'price', 'currency',
                         'ai_summary', 'media_files', 'audio_config', 'template_id',
                         'generated_video', 'status']

        for field in allowed_fields:
            if field in data:
                # Normalize product_name to name
                if field == 'product_name':
                    update_data['name'] = data[field]
                else:
                    update_data[field] = data[field]

        result = products_collection.update_one(
            {
                '_id': ObjectId(product_id),
                'customer_id': customer_id,
                'user_id': user_id
            },
            {'$set': update_data}
        )

        if result.matched_count == 0:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        logger.info(f"✅ Updated product: {product_id}")
        return jsonify({
            'status': 'success',
            'message': 'Product updated successfully'
        }), 200

    except Exception as e:
        logger.error(f"❌ Error updating product: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        result = products_collection.delete_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if result.deleted_count == 0:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        logger.info(f"✅ Deleted product: {product_id}")
        return jsonify({
            'status': 'success',
            'message': 'Product deleted successfully'
        }), 200

    except Exception as e:
        logger.error(f"❌ Error deleting product: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products/stats', methods=['GET'])
def get_product_stats():
    """Get product statistics"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        total = products_collection.count_documents({
            'customer_id': customer_id,
            'user_id': user_id
        })

        completed = products_collection.count_documents({
            'customer_id': customer_id,
            'user_id': user_id,
            'generated_video.status': 'completed'
        })

        in_progress = products_collection.count_documents({
            'customer_id': customer_id,
            'user_id': user_id,
            'generated_video.status': 'processing'
        })

        draft = products_collection.count_documents({
            'customer_id': customer_id,
            'user_id': user_id,
            'status': 'draft'
        })

        stats = {
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'draft': draft
        }

        logger.info(f"✅ Stats: {stats}")
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200

    except Exception as e:
        logger.error(f"❌ Error fetching stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products/<product_id>/generate-summary', methods=['POST'])
def generate_summary(product_id):
    """Generate AI summary for product description"""
    try:
        logger.info(f"📝 Generating summary for product {product_id}")
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')
        logger.info(f"🔐 Context: customer_id={customer_id}, user_id={user_id}")

        # Get product
        product = products_collection.find_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if not product:
            logger.warning(f"⚠️ Product {product_id} not found for customer {customer_id}")
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        logger.info(f"✅ Found product: {product.get('name', 'Unknown')}")

        # Get options
        data = request.get_json() or {}
        regenerate = data.get('regenerate', False)

        # Check if summary already exists
        if product.get('ai_summary') and not regenerate:
            logger.info(f"ℹ️ Summary already exists for product {product_id}")
            return jsonify({
                'status': 'success',
                'message': 'Summary already exists',
                'ai_summary': product['ai_summary']
            }), 200

        # Call LLM service to generate summary
        llm_service_url = os.getenv('LLM_SERVICE_URL', 'http://ichat-llm-service:8083')
        logger.info(f"🤖 Calling LLM service at {llm_service_url}")

        # Build comprehensive prompt for 2-3 minute video narration
        product_name = product.get('name', 'Unknown Product')
        product_description = product.get('description', 'No description provided')
        product_category = product.get('category', 'General')
        product_price = product.get('price', '')
        product_currency = product.get('currency', 'USD')

        price_info = f"${product_price} {product_currency}" if product_price else "Premium quality"

        prompt = f"""You are a professional product marketing copywriter creating a compelling video narration script for an e-commerce product video.

**Product Details:**
- Product Name: {product_name}
- Category: {product_category}
- Price Point: {price_info}
- Description: {product_description}

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

        try:
            response = requests.post(
                f"{llm_service_url}/llm/generate",
                json={'query': prompt, 'use_rag': False},
                timeout=600  # 10 minutes for LLM generation (model loading can take time)
            )
            logger.info(f"📡 LLM service response status: {response.status_code}")
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout calling LLM service")
            return jsonify({
                'status': 'error',
                'message': 'LLM service timeout'
            }), 504
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error to LLM service: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'LLM service unavailable: {str(e)}'
            }), 503

        if response.status_code != 200:
            error_msg = f"LLM service returned {response.status_code}: {response.text}"
            logger.error(f"❌ {error_msg}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate summary',
                'details': error_msg
            }), 500

        summary_text = response.json().get('response', '')
        logger.info(f"✅ Generated summary: {summary_text[:100]}...")

        # Parse summary into structured sections
        sections = parse_ai_summary_to_sections(summary_text)
        logger.info(f"📊 Parsed {len(sections)} sections from AI summary")

        # Create structured AI summary object
        structured_summary = {
            'sections': sections,
            'full_text': summary_text,  # Keep original for backward compatibility
            'generated_at': datetime.utcnow(),
            'version': '2.0'
        }

        # Update product with structured AI summary
        products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {
                '$set': {
                    'ai_summary': structured_summary,
                    'updated_at': datetime.utcnow()
                }
            }
        )

        logger.info(f"✅ Generated AI summary for product {product_id}")

        return jsonify({
            'status': 'success',
            'message': 'Summary generated successfully',
            'ai_summary': structured_summary
        }), 200

    except Exception as e:
        logger.error(f"❌ Error generating summary: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products/<product_id>/upload-media', methods=['POST'])
def upload_media(product_id):
    """Upload media files for product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        # Get product
        product = products_collection.find_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        # Get media URLs from request
        data = request.get_json() or {}
        media_urls = data.get('media_urls', [])

        # Update product with media URLs
        products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {
                '$set': {
                    'media_urls': media_urls,
                    'updated_at': datetime.utcnow()
                }
            }
        )

        logger.info(f"✅ Uploaded {len(media_urls)} media files for product {product_id}")

        return jsonify({
            'status': 'success',
            'message': f'Uploaded {len(media_urls)} media files',
            'media_urls': media_urls
        }), 200

    except Exception as e:
        logger.error(f"❌ Error uploading media: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products/<product_id>/generate-audio', methods=['POST'])
def generate_audio(product_id):
    """Generate audio from AI summary using TTS with section-based pitch control"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        # Get product
        product = products_collection.find_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        if not product.get('ai_summary'):
            return jsonify({
                'status': 'error',
                'message': 'No AI summary found. Generate summary first.'
            }), 400

        # Get options
        data = request.get_json() or {}
        voice = data.get('voice', 'am_adam')
        model = data.get('model', 'kokoro-82m')
        language = data.get('language', 'en')
        section_pitches = data.get('sectionPitches', {})

        logger.info(f"🎤 Generating section-based audio - Model: {model}, Voice: {voice}, Language: {language}")
        if section_pitches:
            logger.info(f"🎵 Section pitches: {section_pitches}")

        # Get AI summary (handle both old and new formats)
        ai_summary = product.get('ai_summary')

        # Check if it's the new structured format
        if isinstance(ai_summary, dict) and 'sections' in ai_summary:
            sections = ai_summary['sections']
            logger.info(f"📊 Found {len(sections)} sections in structured format")
        else:
            # Old format - plain text, need to parse
            logger.info(f"📝 Parsing AI summary from plain text format")
            sections = parse_ai_summary_to_sections(ai_summary if isinstance(ai_summary, str) else '')
            if not sections:
                return jsonify({
                    'status': 'error',
                    'message': 'Could not parse AI summary into sections'
                }), 400

        # Generate audio for each section
        section_audio_urls = []  # Proxy URLs for frontend
        section_internal_urls = []  # Internal URLs for backend processing
        total_duration = 0

        for idx, section in enumerate(sections):
            section_title = section.get('title', f'Section {idx + 1}')
            section_content = section.get('content', '')

            if not section_content:
                logger.warning(f"⚠️ Section '{section_title}' has no content, skipping")
                continue

            # Get smart audio configuration for this section
            smart_config = get_smart_audio_config(section_title, idx, len(sections))

            # Get speed (user override or smart default)
            speed = get_section_speed(section_title, section_pitches, idx, len(sections))

            # Create safe filename
            safe_title = re.sub(r'[^a-z0-9]+', '_', section_title.lower())
            filename = f'section_{idx + 1}_{safe_title}.wav'

            logger.info(f"🎙️ Section {idx + 1}/{len(sections)}: '{section_title}'")
            logger.info(f"   {smart_config['description']}")
            logger.info(f"   Speed: {speed}x")

            # Strip markdown syntax before sending to TTS
            clean_text = strip_markdown_for_tts(section_content)
            logger.debug(f"   Original text length: {len(section_content)}, Clean text length: {len(clean_text)}")

            # Call audio generation service for this section
            try:
                response = requests.post(
                    f"{AUDIO_GENERATION_URL}/tts",
                    json={
                        'text': clean_text,  # Use cleaned text without markdown
                        'voice': voice,
                        'model': model,
                        'speed': speed,
                        'product_id': product_id,  # Add product_id to save in product folder
                        'filename': filename
                    },
                    timeout=600  # Increased to 10 minutes for long sections
                )

                if response.status_code != 200:
                    logger.error(f"❌ Audio generation failed for section '{section_title}': {response.text}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to generate audio for section: {section_title}'
                    }), 500

                result = response.json()
                # Get internal URL from audio generation service
                internal_audio_url = f"{AUDIO_GENERATION_URL}{result.get('audio_url', '')}"
                # Convert to proxy URL for browser access
                section_audio_url = convert_audio_url_to_proxy(internal_audio_url)
                duration = result.get('audio_info', {}).get('duration', 0)

                section_audio_urls.append(section_audio_url)
                section_internal_urls.append(internal_audio_url)
                total_duration += duration

                # Update section with audio info (use proxy URL)
                section['audio_path'] = section_audio_url
                section['audio_config'] = {
                    'speed': speed,
                    'voice': voice,
                    'duration': duration
                }

                logger.info(f"✅ Generated audio for '{section_title}': {duration:.2f}s")

            except requests.exceptions.Timeout:
                logger.error(f"❌ Timeout generating audio for section '{section_title}'")
                return jsonify({
                    'status': 'error',
                    'message': f'Timeout generating audio for section: {section_title}'
                }), 504
            except Exception as e:
                logger.error(f"❌ Error generating audio for section '{section_title}': {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Error generating audio for section {section_title}: {str(e)}'
                }), 500

        logger.info(f"✅ Generated {len(section_audio_urls)} section audio files, total duration: {total_duration:.2f}s")

        # Concatenate all section audio files into one combined file
        combined_audio_url = None
        if section_audio_urls:
            try:
                logger.info(f"🔗 Concatenating {len(section_audio_urls)} audio files...")

                # Download and concatenate all section audio files
                combined_audio = AudioSegment.empty()

                # Use internal URLs for downloading (backend-to-backend communication)
                for idx, internal_url in enumerate(section_internal_urls):
                    logger.info(f"📥 Downloading section {idx + 1}/{len(section_internal_urls)}: {internal_url}")

                    # Download audio file using internal URL
                    audio_response = requests.get(internal_url, timeout=30)
                    if audio_response.status_code != 200:
                        logger.error(f"❌ Failed to download audio from {internal_url}")
                        continue

                    # Load into AudioSegment
                    section_audio = AudioSegment.from_wav(io.BytesIO(audio_response.content))
                    combined_audio += section_audio

                    logger.info(f"✅ Added section {idx + 1} to combined audio")

                # Save combined audio to temporary file
                combined_filename = f'audio_combined.wav'

                # Create temp file and export
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                    combined_audio.export(temp_path, format='wav')
                    logger.info(f"💾 Exported combined audio to temp file: {temp_path}")

                # Upload combined audio to audio generation service with product_id
                try:
                    with open(temp_path, 'rb') as audio_file:
                        files = {'file': (combined_filename, audio_file, 'audio/wav')}
                        # Pass product_id as form data to save in product folder
                        data = {'product_id': product_id}
                        upload_response = requests.post(
                            f"{AUDIO_GENERATION_URL}/upload",
                            files=files,
                            data=data,
                            timeout=60
                        )

                        if upload_response.status_code == 200:
                            upload_result = upload_response.json()
                            # Get internal URL and convert to proxy URL
                            internal_combined_url = f"{AUDIO_GENERATION_URL}{upload_result.get('audio_url', '')}"
                            combined_audio_url = convert_audio_url_to_proxy(internal_combined_url)
                            logger.info(f"✅ Uploaded combined audio: {combined_audio_url}")
                        else:
                            logger.error(f"❌ Failed to upload combined audio: {upload_response.text}")
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        logger.info(f"🗑️ Cleaned up temp file: {temp_path}")

            except Exception as e:
                logger.error(f"❌ Error concatenating audio files: {str(e)}", exc_info=True)
                # Continue without combined audio - individual sections are still available

        # Update product with structured AI summary and audio info
        updated_ai_summary = {
            'version': '2.0',
            'generated_at': ai_summary.get('generated_at') if isinstance(ai_summary, dict) else datetime.utcnow(),
            'full_text': ai_summary.get('full_text') if isinstance(ai_summary, dict) else ai_summary,
            'sections': sections
        }

        update_data = {
            'ai_summary': updated_ai_summary,
            'audio_config': {
                'voice': voice,
                'model': model,
                'language': language,
                'total_duration': total_duration,
                'section_count': len(section_audio_urls)
            },
            'updated_at': datetime.utcnow()
        }

        # Add combined audio URL if available
        if combined_audio_url:
            update_data['audio_url'] = combined_audio_url
            logger.info(f"📝 Storing combined audio URL in product: {combined_audio_url}")

        products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': update_data}
        )

        logger.info(f"✅ Generated section-based audio for product {product_id}")

        response_data = {
            'status': 'success',
            'message': f'Audio generated successfully for {len(section_audio_urls)} sections',
            'section_audio_urls': section_audio_urls,
            'total_duration': total_duration,
            'audio_config': {
                'voice': voice,
                'model': model,
                'language': language,
                'section_count': len(section_audio_urls)
            }
        }

        # Add combined audio URL to response if available
        if combined_audio_url:
            response_data['audio_url'] = combined_audio_url
            response_data['combined_audio_url'] = combined_audio_url
            response_data['message'] = f'Audio generated successfully for {len(section_audio_urls)} sections and combined into one file'

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"❌ Error generating audio: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products/<product_id>/generate-video', methods=['POST'])
def generate_video(product_id):
    """Generate final product video"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        # Get product
        product = products_collection.find_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if not product:
            return jsonify({
                'status': 'error',
                'message': 'Product not found'
            }), 404

        # Validate required fields
        if not product.get('ai_summary'):
            return jsonify({
                'status': 'error',
                'message': 'No AI summary found. Generate summary first.'
            }), 400

        if not product.get('audio_url'):
            return jsonify({
                'status': 'error',
                'message': 'No audio found. Generate audio first.'
            }), 400

        # Get options
        data = request.get_json() or {}
        template_id = data.get('template_id', 'default')

        # Call video generator service
        video_service_url = os.getenv('VIDEO_GENERATOR_URL', 'http://ichat-video-generator:8095')

        response = requests.post(
            f"{video_service_url}/api/video/generate",
            json={
                'product_id': product_id,
                'template_id': template_id,
                'audio_url': product['audio_url'],
                'media_urls': product.get('media_urls', []),
                'text': product['ai_summary']
            },
            timeout=120
        )

        if response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate video'
            }), 500

        video_url = response.json().get('video_url', '')

        # Update product with video URL and status
        products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {
                '$set': {
                    'video_url': video_url,
                    'status': 'completed',
                    'updated_at': datetime.utcnow()
                }
            }
        )

        logger.info(f"✅ Generated video for product {product_id}")

        return jsonify({
            'status': 'success',
            'message': 'Video generated successfully',
            'video_url': video_url
        }), 200

    except Exception as e:
        logger.error(f"❌ Error generating video: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 8099))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    logger.info(f"🚀 Starting Product Service on {host}:{port}")
    app.run(host=host, port=port, debug=False)

