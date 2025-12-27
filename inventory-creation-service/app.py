"""
Inventory Creation Service - Generic content generation service
Handles AI summary generation, audio generation, and video orchestration
for multiple use cases (products, social media, blogs, etc.)
"""

import logging
import os
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

from workflows import ProductWorkflow
from services import (
    product_bp,
    public_bp,
    prompt_template_bp,
    init_product_service,
    init_public_service,
    init_prompt_template_service
)

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
prompt_templates_collection = db['prompt_templates']

# Service URLs
LLM_SERVICE_URL = os.getenv('LLM_SERVICE_URL', 'http://ichat-llm-service:8083')
VIDEO_GENERATOR_URL = os.getenv('VIDEO_GENERATOR_URL', 'http://ichat-video-generator:8095')
AUDIO_GENERATION_URL = os.getenv('AUDIO_GENERATION_URL', 'http://audio-generation-factory:3000')
TEMPLATE_SERVICE_URL = os.getenv('TEMPLATE_SERVICE_URL', 'http://ichat-template-service:5000')
API_SERVER_URL = os.getenv('API_SERVER_EXTERNAL_URL', 'http://localhost:8080')
API_SERVER_INTERNAL_URL = os.getenv('API_SERVER_INTERNAL_URL', 'http://ichat-api-server:8080')

# Initialize workflows
product_workflow = ProductWorkflow(
    db_collection=products_collection,
    config={
        'llm_service_url': LLM_SERVICE_URL,
        'audio_service_url': AUDIO_GENERATION_URL,
        'template_service_url': TEMPLATE_SERVICE_URL,
        'video_generator_url': VIDEO_GENERATOR_URL
    },
    prompt_templates_collection=prompt_templates_collection
)

# Initialize services with dependencies
init_product_service(products_collection, product_workflow, API_SERVER_URL)
init_public_service(products_collection)
init_prompt_template_service(prompt_templates_collection)

# Register Blueprints
app.register_blueprint(product_bp)
app.register_blueprint(public_bp)
app.register_blueprint(prompt_template_bp)

logger.info("✅ Inventory Creation Service initialized")
logger.info(f"   LLM Service: {LLM_SERVICE_URL}")
logger.info(f"   Audio Service: {AUDIO_GENERATION_URL}")
logger.info(f"   Template Service: {TEMPLATE_SERVICE_URL}")
logger.info(f"   Video Generator: {VIDEO_GENERATOR_URL}")
logger.info(f"   Registered Blueprints: product, public, prompt_template")


# ========== Health Check ==========

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'inventory-creation-service'
    }), 200


# ========== Main Entry Point ==========

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    logger.info(f"🚀 Starting Inventory Creation Service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

