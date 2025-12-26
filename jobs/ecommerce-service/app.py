"""
Product Service - Backend service for e-commerce product management
Handles all product CRUD operations, AI summary generation, and video generation orchestration
"""

import logging
import os
import re
import io
import tempfile
import uuid
from flask import Flask, request, jsonify, send_from_directory
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
TEMPLATE_SERVICE_URL = os.getenv('TEMPLATE_SERVICE_URL', 'http://ichat-template-service:5000')
# External URL for frontend/browser access
API_SERVER_URL = os.getenv('API_SERVER_EXTERNAL_URL', 'http://localhost:8080')
# Internal URL for container-to-container communication
API_SERVER_INTERNAL_URL = os.getenv('API_SERVER_INTERNAL_URL', 'http://ichat-api-server:8080')


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

        products_raw = list(products_collection.find({
            'customer_id': customer_id,
            'user_id': user_id
        }).sort('created_at', -1))

        # Log media_urls for each product before serialization
        for p in products_raw:
            if p.get('media_urls'):
                # Filter out blob URLs before returning
                valid_urls = [url for url in p.get('media_urls', []) if not url.startswith('blob:')]
                if len(valid_urls) != len(p.get('media_urls', [])):
                    logger.warning(f"⚠️ Product {p['_id']} had {len(p.get('media_urls', [])) - len(valid_urls)} blob URLs, filtering them out")
                    p['media_urls'] = valid_urls
                logger.info(f"📸 Product {p['_id']} has {len(p.get('media_urls', []))} media URLs: {p.get('media_urls', [])[:2]}...")

        products = [serialize_product(p) for p in products_raw]

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

        # Filter out blob URLs before returning
        if product.get('media_urls'):
            valid_urls = [url for url in product.get('media_urls', []) if not url.startswith('blob:')]
            if len(valid_urls) != len(product.get('media_urls', [])):
                logger.warning(f"⚠️ Product {product_id} had {len(product.get('media_urls', [])) - len(valid_urls)} blob URLs, filtering them out")
                product['media_urls'] = valid_urls

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
                         'ai_summary', 'audio_config', 'template_id',
                         'generated_video', 'status', 'distribution_mode', 'template_variables',
                         'section_mapping']

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

        logger.info(f"📤 Upload media request - Content-Type: {request.content_type}")
        logger.info(f"📤 Request files: {list(request.files.keys())}")
        logger.info(f"📤 Request form: {list(request.form.keys())}")

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

        # Check if this is a file upload or URL submission
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle actual file uploads
            if 'files' not in request.files:
                return jsonify({
                    'status': 'error',
                    'message': 'No files provided'
                }), 400

            files = request.files.getlist('files')
            if not files:
                return jsonify({
                    'status': 'error',
                    'message': 'No files provided'
                }), 400

            uploaded_urls = []  # Just track URLs

            for file in files:
                if file.filename == '':
                    continue

                # Determine if file is video or image based on mimetype (for folder organization only)
                is_video = file.content_type and file.content_type.startswith('video/')
                media_type = 'videos' if is_video else 'images'

                # Create upload directory for this product in public folder
                upload_dir = os.path.join('/app/public/product', product_id, media_type)
                os.makedirs(upload_dir, exist_ok=True)

                # Generate unique filename
                file_ext = os.path.splitext(file.filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                file_path = os.path.join(upload_dir, unique_filename)

                # Save file
                file.save(file_path)
                logger.info(f"💾 Saved {media_type[:-1]} file: {file_path} (type: {file.content_type})")

                # Generate accessible URL
                file_url = f"{API_SERVER_URL}/api/ecommerce/public/product/{product_id}/{media_type}/{unique_filename}"
                uploaded_urls.append(file_url)

            # Don't save to product document - media will be stored in template_variables
            # Just update the timestamp
            products_collection.update_one(
                {'_id': ObjectId(product_id)},
                {
                    '$set': {
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            logger.info(f"✅ Uploaded {len(uploaded_urls)} files for product {product_id}")
            logger.info(f"📤 Returning URLs: {uploaded_urls}")

            return jsonify({
                'status': 'success',
                'message': f'Uploaded {len(uploaded_urls)} files',
                'urls': uploaded_urls
            }), 200

        else:
            # No file upload - invalid request
            return jsonify({
                'status': 'error',
                'message': 'No files provided. Use multipart/form-data to upload files.'
            }), 400

    except Exception as e:
        logger.error(f"❌ Error uploading media: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/ecommerce/public/product/<product_id>/images/<filename>', methods=['GET'])
def serve_product_images(product_id, filename):
    """Serve uploaded image files for a product"""
    try:
        images_dir = os.path.join('/app/public/product', product_id, 'images')
        return send_from_directory(images_dir, filename)
    except Exception as e:
        logger.error(f"❌ Error serving image file: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'File not found'
        }), 404


@app.route('/api/ecommerce/public/product/<product_id>/videos/<filename>', methods=['GET'])
def serve_product_videos(product_id, filename):
    """Serve uploaded video files for a product"""
    try:
        videos_dir = os.path.join('/app/public/product', product_id, 'videos')
        logger.info(f"🎥 Serving video file: {videos_dir}/{filename}")
        return send_from_directory(videos_dir, filename)
    except Exception as e:
        logger.error(f"❌ Error serving video file: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'File not found'
        }), 404


@app.route('/api/ecommerce/public/product/<product_id>/videos/<filename>', methods=['DELETE'])
def delete_product_video(product_id, filename):
    """Delete a specific video file from a product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        logger.info(f"🗑️ Deleting video file: {product_id}/videos/{filename}")

        # Verify product exists and belongs to user
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

        # Delete the physical file
        videos_dir = os.path.join('/app/public/product', product_id, 'videos')
        file_path = os.path.join(videos_dir, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"✅ Deleted video file: {file_path}")
        else:
            logger.warning(f"⚠️ Video file not found: {file_path}")

        # Update template_variables.dynamic_videos
        template_variables = product.get('template_variables', {})
        video_url = f"/api/ecommerce/public/product/{product_id}/videos/{filename}"
        full_video_url = f"{API_SERVER_URL}/api/ecommerce/public/product/{product_id}/videos/{filename}"

        logger.info(f"🗑️ Cleaning up template_variables.dynamic_videos")
        logger.info(f"  - Before: {template_variables.get('dynamic_videos', [])}")

        # Find which index was removed
        original_videos = template_variables.get('dynamic_videos', [])
        removed_index = None
        for i, url in enumerate(original_videos):
            if url == video_url or url == full_video_url:
                removed_index = i
                break

        # Filter out the deleted video
        updated_dynamic_videos = [
            url for url in original_videos
            if url != video_url and url != full_video_url
        ]
        template_variables['dynamic_videos'] = updated_dynamic_videos

        # Also update timings array if it exists
        if removed_index is not None and 'dynamic_videos_timings' in template_variables:
            timings = template_variables.get('dynamic_videos_timings', [])
            if removed_index < len(timings):
                timings.pop(removed_index)
                template_variables['dynamic_videos_timings'] = timings
                logger.info(f"  - Removed timing at index {removed_index}")

        logger.info(f"  - After: {updated_dynamic_videos}")

        # Update product in database
        products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {
                'template_variables': template_variables,
                'updated_at': datetime.utcnow()
            }}
        )

        logger.info(f"✅ Removed video from template_variables.dynamic_videos: {filename}")
        logger.info(f"✅ Updated dynamic_videos count: {len(updated_dynamic_videos)}")
        logger.info(f"✅ Updated dynamic_videos: {updated_dynamic_videos}")

        return jsonify({
            'status': 'success',
            'message': 'Video deleted successfully',
            'template_variables': template_variables
        }), 200

    except Exception as e:
        logger.error(f"❌ Error deleting video file: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/ecommerce/public/product/<product_id>/images/<filename>', methods=['DELETE'])
def delete_product_image(product_id, filename):
    """Delete a specific image file from a product"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        logger.info(f"🗑️ Deleting image file: {product_id}/images/{filename}")

        # Verify product exists and belongs to user
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

        # Delete the physical file
        images_dir = os.path.join('/app/public/product', product_id, 'images')
        file_path = os.path.join(images_dir, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"✅ Deleted image file: {file_path}")
        else:
            logger.warning(f"⚠️ Image file not found: {file_path}")

        # Update template_variables.dynamic_images
        template_variables = product.get('template_variables', {})
        image_url = f"/api/ecommerce/public/product/{product_id}/images/{filename}"
        full_image_url = f"{API_SERVER_URL}/api/ecommerce/public/product/{product_id}/images/{filename}"

        logger.info(f"🗑️ Cleaning up template_variables.dynamic_images")
        logger.info(f"  - Before: {template_variables.get('dynamic_images', [])}")

        # Filter out the deleted image
        original_images = template_variables.get('dynamic_images', [])
        updated_dynamic_images = [
            url for url in original_images
            if url != image_url and url != full_image_url
        ]
        template_variables['dynamic_images'] = updated_dynamic_images

        logger.info(f"  - After: {updated_dynamic_images}")

        # Update product in database
        products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {
                'template_variables': template_variables,
                'updated_at': datetime.utcnow()
            }}
        )

        logger.info(f"✅ Removed image from template_variables.dynamic_images: {filename}")
        logger.info(f"✅ Updated dynamic_images count: {len(updated_dynamic_images)}")
        logger.info(f"✅ Updated dynamic_images: {updated_dynamic_images}")

        return jsonify({
            'status': 'success',
            'message': 'Image deleted successfully',
            'template_variables': template_variables
        }), 200

    except Exception as e:
        logger.error(f"❌ Error deleting image file: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/ecommerce/public/product/<product_id>/<filename>', methods=['GET'])
def serve_product_files(product_id, filename):
    """Serve audio/video files for a product"""
    try:
        product_dir = os.path.join('/app/public/product', product_id)
        return send_from_directory(product_dir, filename)
    except Exception as e:
        logger.error(f"❌ Error serving product file: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'File not found'
        }), 404


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

                # Save combined audio directly to product's public folder
                combined_filename = f'audio_combined.wav'

                # Create product directory in public folder
                product_dir = os.path.join('/app/public/product', product_id)
                os.makedirs(product_dir, exist_ok=True)

                # Save combined audio file
                audio_path = os.path.join(product_dir, combined_filename)
                combined_audio.export(audio_path, format='wav')
                logger.info(f"💾 Saved combined audio to: {audio_path}")

                # Generate accessible URLs (external for frontend, internal for services)
                combined_audio_url = f"{API_SERVER_URL}/api/ecommerce/public/product/{product_id}/{combined_filename}"
                combined_audio_url_internal = f"{API_SERVER_INTERNAL_URL}/api/ecommerce/public/product/{product_id}/{combined_filename}"
                logger.info(f"✅ Combined audio URL: {combined_audio_url}")
                logger.info(f"✅ Combined audio URL (internal): {combined_audio_url_internal}")

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

        # Add combined audio URLs if available
        if combined_audio_url:
            update_data['audio_url'] = combined_audio_url  # External URL for frontend
            update_data['audio_url_internal'] = combined_audio_url_internal  # Internal URL for services
            logger.info(f"📝 Storing combined audio URL in product: {combined_audio_url}")
            logger.info(f"📝 Storing internal audio URL in product: {combined_audio_url_internal}")

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


def distribute_media_across_sections(media_files, sections, distribution_mode='auto', section_mapping=None):
    """
    Distribute media (images and videos) across AI summary sections.
    Each asset gets a duration based on the section it belongs to.

    Args:
        media_files: List of media file dicts with 'url', 'type' ('image' or 'video')
        sections: List of AI summary sections with audio_config
        distribution_mode: 'auto' or 'manual'
        section_mapping: Dict mapping section title to list of media objects (for manual mode)
                        Example: {"opening_hook": [{"type": "video", "url": "..."}, {"type": "image", "url": "..."}]}

    Returns:
        Dict with:
        - section_media: Dict mapping section titles to lists of media dicts
        - media_list: List of dicts with 'url', 'duration', 'type' (NO start_time)
        - images_list: List of image URLs in sequence
        - videos_list: List of video URLs in sequence
    """
    if not sections:
        return {
            'section_media': {},
            'media_timings': [],
            'images_list': [],
            'videos_list': []
        }

    section_media = {section['title']: [] for section in sections}

    if distribution_mode == 'manual' and section_mapping:
        # Manual mode: assign media based on section-to-media mapping
        # section_mapping format: {"section_title": [{"type": "video", "url": "..."}, ...]}

        # Normalize section titles (convert to lowercase with underscores for matching)
        def normalize_title(title):
            # Remove markdown heading prefix (##) and strip whitespace
            normalized = title.strip()
            if normalized.startswith('##'):
                normalized = normalized[2:].strip()
            # Convert to lowercase, replace spaces with underscores, & with 'and'
            return normalized.lower().replace(' ', '_').replace('&', 'and')

        # Create a mapping of normalized titles to original titles
        normalized_to_original = {normalize_title(section['title']): section['title'] for section in sections}

        # Assign media according to the mapping
        for section_key, media_list in section_mapping.items():
            # Try to match the section key (could be normalized or original)
            normalized_key = normalize_title(section_key)
            original_title = normalized_to_original.get(normalized_key, section_key)

            if original_title in section_media and isinstance(media_list, list):
                for media_item in media_list:
                    if isinstance(media_item, dict) and 'url' in media_item and 'type' in media_item:
                        section_media[original_title].append(media_item)

        # If no media was assigned via mapping and we have media_files, auto-distribute
        total_assigned = sum(len(media) for media in section_media.values())
        if total_assigned == 0 and media_files:
            # Auto mode: distribute evenly across sections
            for idx, media in enumerate(media_files):
                section = sections[idx % len(sections)]
                section_media[section['title']].append(media)
    else:
        # Auto mode: distribute evenly across sections
        if media_files:
            for idx, media in enumerate(media_files):
                section = sections[idx % len(sections)]
                section_media[section['title']].append(media)

    # Create media list with duration for each asset
    # Each media item in a section gets equal duration
    # (section_duration / num_media)
    # NO start_time - template service will concatenate sequentially
    media_list = []
    images_list = []
    videos_list = []

    for section in sections:
        section_duration = section.get('audio_config', {}).get('duration', 5.0)
        section_title = section['title']
        media_in_section = section_media.get(section_title, [])

        if media_in_section:
            # Divide section duration equally among all media
            # Example: 30s section with 5 media = 6s per media
            media_duration = section_duration / len(media_in_section)

            for media in media_in_section:
                media_url = media.get('url') if isinstance(media, dict) else media
                media_type = media.get('type', 'image') if isinstance(media, dict) else 'image'

                # Only send URL, duration, and type
                # Template service will create clips and concatenate
                media_item = {
                    'url': media_url,
                    'duration': media_duration,
                    'type': media_type
                }
                media_list.append(media_item)

                # Add to type-specific lists (in order they appear)
                if media_type == 'image':
                    images_list.append(media_url)
                elif media_type == 'video':
                    videos_list.append(media_url)

    return {
        'section_media': section_media,
        'media_list': media_list,
        'images_list': images_list,
        'videos_list': videos_list
    }





@app.route('/api/products/<product_id>/generate-video', methods=['POST'])
def generate_video(product_id):
    """Generate final product video"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        logger.info(f"🎬 Generating video for product {product_id}")

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
        template_variables = data.get('template_variables', {})
        distribution_mode = data.get('distribution_mode', 'auto')
        section_mapping = data.get('section_mapping', {})

        logger.info(f"🎨 Template ID: {template_id}")
        logger.info(f"🔧 Template variables from request: {list(template_variables.keys())}")
        logger.info(f"🎯 Distribution mode: {distribution_mode}")

        # Log what media arrays we have
        for key in template_variables.keys():
            if 'image' in key.lower() or 'video' in key.lower():
                value = template_variables[key]
                if isinstance(value, list):
                    logger.info(f"  {key}: {len(value)} items")

        # Media is now stored in template_variables, not in product.media_files
        # Extract media from template_variables for distribution logic
        media_files = []
        for key, value in template_variables.items():
            # Skip timing arrays and other metadata
            if key.endswith('_timings') or not isinstance(value, list) or len(value) == 0:
                continue

            # Check if this is an image or video array (must be array of strings)
            if key.endswith('_images') or 'image' in key.lower():
                media_files.extend([{'url': url, 'type': 'image'} for url in value if isinstance(url, str)])
            elif key.endswith('_videos') or 'video' in key.lower():
                media_files.extend([{'url': url, 'type': 'video'} for url in value if isinstance(url, str)])

        logger.info(f"📦 Extracted {len(media_files)} media files from template_variables")
        for idx, media in enumerate(media_files):
            logger.info(f"  [{idx}] {media.get('type')}: {media.get('url')}")

        # Get AI summary sections for media distribution
        ai_summary = product.get('ai_summary', {})
        sections = []
        if isinstance(ai_summary, dict) and 'sections' in ai_summary:
            sections = ai_summary['sections']

        # Initialize variables
        product_images = []
        media_data_for_template = {}

        # Calculate media durations on-the-fly (don't store in DB)
        if media_files and sections and distribution_mode:
            logger.info(f"🎬 Calculating timings for {len(media_files)} media files across {len(sections)} sections")

            result = distribute_media_across_sections(
                media_files,
                sections,
                distribution_mode,
                section_mapping
            )

            media_list = result['media_list']
            images_list = result['images_list']
            videos_list = result['videos_list']

            # Log media sequence
            logger.info(f"⏱️ Media sequence:")
            for i, item in enumerate(media_list):
                media_type_icon = '🖼️' if item.get('type') == 'image' else '🎥'
                logger.info(f"  {media_type_icon} Media {i+1}: {item['duration']:.2f}s ({item['type']})")

            # Send as dynamic_media (single merged array)
            # Template service will create clips and concatenate
            media_data_for_template = {
                'dynamic_media': media_list
            }

            product_images = images_list

            logger.info(f"✅ Prepared {len(media_list)} media items for template service")
        else:
            logger.info(f"ℹ️ Skipping timing calculation (media: {len(media_files)}, sections: {len(sections)})")

        # Fetch template to check for dynamic layers
        template_response = requests.get(
            f"{TEMPLATE_SERVICE_URL}/api/templates/{template_id}",
            headers={'X-Customer-ID': customer_id}
        )

        if template_response.status_code != 200:
            logger.warning(f"⚠️ Could not fetch template {template_id}, using legacy video generation")
            # Fall back to old video generator
            video_service_url = os.getenv('VIDEO_GENERATOR_URL', 'http://ichat-video-generator:8095')
            response = requests.post(
                f"{video_service_url}/api/video/generate",
                json={
                    'product_id': product_id,
                    'template_id': template_id,
                    'audio_url': product['audio_url'],
                    'media_urls': product_images,
                    'text': product['ai_summary']
                },
                timeout=120
            )
        else:
            # Use template service with variable resolution
            template = template_response.json().get('template', {})

            # Auto-populate dynamic layer variables with product images
            for layer in template.get('layers', []):
                if layer.get('is_dynamic') and layer.get('variable_name'):
                    var_name = layer['variable_name']
                    # Only auto-populate if not already provided
                    if var_name not in template_variables:
                        template_variables[var_name] = product_images
                        logger.info(f"✅ Auto-populated '{var_name}' with {len(product_images)} product images")

            # Add other common variables
            if 'product_name' not in template_variables:
                template_variables['product_name'] = product.get('name', 'Product')

            # Merge media data with template_variables
            # (media list is calculated on-the-fly, not stored in DB)
            sample_data_with_media = {**template_variables, **media_data_for_template}

            # Call template service preview endpoint
            # Use internal audio URL for container-to-container communication
            audio_url_for_service = product.get('audio_url_internal', product.get('audio_url'))
            logger.info(f"🎵 Using audio URL for template service: {audio_url_for_service}")
            logger.info(f"🔧 Template variables: {list(template_variables.keys())}")
            logger.info(f"📊 Media data: {list(media_data_for_template.keys())}")

            response = requests.post(
                f"{TEMPLATE_SERVICE_URL}/api/templates/preview",
                json={
                    'template': template,
                    'sample_data': sample_data_with_media,
                    'is_initial': False,
                    'audio_url': audio_url_for_service,
                    'output_path': f"videos/product_{product_id}.mp4"
                },
                timeout=300
            )

        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"❌ Video generation failed: {response.status_code} - {error_detail}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate video',
                'details': error_detail
            }), 500

        # Template service preview endpoint returns 'preview_url', not 'video_url'
        response_data = response.json()
        video_url = response_data.get('preview_url') or response_data.get('video_url', '')
        logger.info(f"📹 Received video URL from template service: {video_url}")

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

        # Serialize product before returning
        updated_product = products_collection.find_one({'_id': ObjectId(product_id)})

        return jsonify({
            'status': 'success',
            'message': 'Video generated successfully',
            'video_url': video_url,
            'product': serialize_product(updated_product) if updated_product else None
        }), 200

    except Exception as e:
        logger.error(f"❌ Error generating video: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/products/<product_id>/generate-video-dynamic', methods=['POST'])
def generate_video_dynamic(product_id):
    """
    Generate product video with dynamic number of images using template system

    This endpoint leverages the existing template variable resolution system to:
    1. Extract images and sections from product data
    2. Calculate timing based on TTS audio durations
    3. Pass variables to template service for resolution
    4. Generate video with dynamically expanded layers

    Request body:
        {
            "template_id": "my_product_template",  // Customer's template with sources array
            "use_section_images": true  // If true, use images from AI summary sections
        }
    """
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')

        logger.info(f"🎬 Generating dynamic video for product {product_id}")

        # Get product
        product = products_collection.find_one({
            '_id': ObjectId(product_id),
            'customer_id': customer_id,
            'user_id': user_id
        })

        if not product:
            return jsonify({'status': 'error', 'message': 'Product not found'}), 404

        # Validate required data
        ai_summary = product.get('ai_summary')
        if not ai_summary or 'sections' not in ai_summary:
            return jsonify({'status': 'error', 'message': 'No AI summary sections found. Generate summary first.'}), 400

        sections = ai_summary['sections']

        # Get request options
        data = request.get_json() or {}
        template_id = data.get('template_id')
        use_section_images = data.get('use_section_images', False)

        if not template_id:
            return jsonify({'status': 'error', 'message': 'template_id is required'}), 400

        # Extract data from sections
        product_images = []
        section_durations = []
        combined_audio_url = product.get('audio_url')  # Combined audio file

        for section in sections:
            # Get audio duration for this section
            audio_config = section.get('audio_config', {})
            duration = audio_config.get('duration', 5.0)
            section_durations.append(duration)

            # Get images for this section if use_section_images is true
            if use_section_images:
                section_images = section.get('images', [])
                if section_images:
                    product_images.extend(section_images)

        # If no section-specific images or not using them, use product media_urls
        if not product_images:
            product_images = product.get('media_urls', [])

        if not product_images:
            return jsonify({'status': 'error', 'message': 'No product images found. Upload images first.'}), 400

        if not combined_audio_url:
            return jsonify({'status': 'error', 'message': 'No audio found. Generate audio first.'}), 400

        # Calculate total duration and duration per image
        total_duration = sum(section_durations) if section_durations else len(product_images) * 5.0
        duration_per_image = total_duration / len(product_images) if product_images else 5.0

        logger.info(f"📊 Dynamic video stats:")
        logger.info(f"   Images: {len(product_images)}")
        logger.info(f"   Sections: {len(sections)}")
        logger.info(f"   Total duration: {total_duration:.2f}s")
        logger.info(f"   Duration per image: {duration_per_image:.2f}s")
        logger.info(f"   Template: {template_id}")

        # Get the template from template service
        logger.info(f"📥 Fetching template {template_id} from template service")
        template_response = requests.get(
            f"{TEMPLATE_SERVICE_URL}/api/templates/{template_id}",
            headers={'X-Customer-ID': customer_id, 'X-User-ID': user_id},
            timeout=30
        )

        if template_response.status_code != 200:
            logger.error(f"Failed to fetch template: {template_response.text}")
            return jsonify({'status': 'error', 'message': f'Failed to fetch template: {template_id}'}), 500

        template = template_response.json().get('template', {})

        # Prepare variables for template resolution
        template_variables = {
            'product_name': product.get('name', 'Product'),
            'brand_color': data.get('brand_color', '#3B82F6'),
            'total_duration': total_duration
        }

        # Find dynamic layers and add their variables
        # Dynamic layers have is_dynamic=true and variable_name set
        dynamic_layers_found = []
        for layer in template.get('layers', []):
            if layer.get('is_dynamic') and layer.get('variable_name'):
                var_name = layer['variable_name']
                # Add the product images array to variables
                template_variables[var_name] = product_images
                dynamic_layers_found.append(var_name)
                logger.info(f"✅ Found dynamic layer with variable '{var_name}', adding {len(product_images)} images")

                # Create timing metadata for this dynamic layer
                # Distribute images across sections based on audio durations
                image_timings = []
                current_time = 0.0
                images_per_section = max(1, len(product_images) // len(sections))

                for section_idx, section in enumerate(sections):
                    section_duration = section_durations[section_idx]
                    # Calculate how many images for this section
                    if section_idx == len(sections) - 1:
                        # Last section gets remaining images
                        section_image_count = len(product_images) - len(image_timings)
                    else:
                        section_image_count = images_per_section

                    # Distribute section duration across images in this section
                    if section_image_count > 0:
                        image_duration = section_duration / section_image_count
                        for i in range(section_image_count):
                            image_timings.append({
                                'start_time': current_time,
                                'duration': image_duration,
                                'section': section.get('title', f'Section {section_idx + 1}')
                            })
                            current_time += image_duration

                # Add timing metadata to template variables
                timing_var_name = f"{var_name}_timings"
                template_variables[timing_var_name] = image_timings
                logger.info(f"✅ Created {len(image_timings)} timing entries for '{var_name}'")

        # Also handle old-style templates with sources array (backward compatibility)
        for layer in template.get('layers', []):
            if 'sources' in layer and layer.get('type') in ['image', 'video'] and not layer.get('is_dynamic'):
                # Update sources array with product images
                layer['sources'] = product_images
                layer['duration_per_item'] = duration_per_image
                logger.info(f"✅ Updated legacy layer '{layer.get('id')}' with {len(product_images)} images")

        if not dynamic_layers_found and not any('sources' in layer for layer in template.get('layers', [])):
            logger.warning(f"⚠️ Template {template_id} has no dynamic layers or sources arrays. Video may not show product images.")

        # Update template duration to match total duration
        template['duration'] = total_duration

        # Resolve template variables (for text overlays, colors, dynamic arrays, etc.)
        logger.info(f"🔧 Resolving variables: {list(template_variables.keys())}")
        template_str = json.dumps(template)
        for var_name, var_value in template_variables.items():
            # Handle array variables (for dynamic layers)
            if isinstance(var_value, list):
                # Don't replace in template string directly - let variable resolver handle it
                continue
            # Handle simple string/number variables
            template_str = template_str.replace(f'{{{{{var_name}}}}}', str(var_value))
        template = json.loads(template_str)

        logger.info(f"🎨 Template resolved with variables")

        # Call template service preview endpoint to generate video
        logger.info(f"🎬 Calling template service to generate video")
        logger.info(f"📦 Sending sample_data with keys: {list(template_variables.keys())}")
        preview_response = requests.post(
            f"{TEMPLATE_SERVICE_URL}/api/templates/preview",
            json={
                'template': template,
                'sample_data': template_variables,  # Pass variables as sample_data
                'is_initial': False
            },
            headers={'X-Customer-ID': customer_id, 'X-User-ID': user_id},
            timeout=300  # 5 minutes for video generation
        )

        if preview_response.status_code != 200:
            logger.error(f"Failed to generate video: {preview_response.text}")
            return jsonify({'status': 'error', 'message': 'Failed to generate video'}), 500

        preview_result = preview_response.json()
        video_path = preview_result.get('preview_url', '')

        # Convert preview URL to full URL
        video_url = f"{API_SERVER_URL}{video_path}" if video_path else ''

        logger.info(f"✅ Video generated: {video_url}")

        # Update product with video URL and status
        products_collection.update_one(
            {'_id': ObjectId(product_id)},
            {
                '$set': {
                    'video_url': video_url,
                    'status': 'completed',
                    'updated_at': datetime.utcnow(),
                    'video_metadata': {
                        'template_id': template_id,
                        'images_count': len(product_images),
                        'duration': total_duration,
                        'generated_at': datetime.utcnow()
                    }
                }
            }
        )

        logger.info(f"✅ Generated dynamic video for product {product_id}")

        return jsonify({
            'status': 'success',
            'message': 'Dynamic video generated successfully',
            'video_url': video_url,
            'stats': {
                'images': len(product_images),
                'sections': len(sections),
                'duration': total_duration,
                'duration_per_image': duration_per_image
            }
        }), 200

    except Exception as e:
        logger.error(f"❌ Error generating dynamic video: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 8099))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    logger.info(f"🚀 Starting Product Service on {host}:{port}")
    app.run(host=host, port=port, debug=False)

