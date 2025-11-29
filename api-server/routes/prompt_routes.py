"""
Prompt Management Routes - LLM Prompt CRUD operations
"""

from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
import os
import logging

# Create blueprint
prompt_bp = Blueprint('prompt', __name__)

# MongoDB connection
from pymongo import MongoClient

# Get MongoDB connection details from environment
MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'admin')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'password')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'ichat')

# Create MongoDB client
mongo_client = MongoClient(
    f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/?authSource=admin'
)
db = mongo_client[MONGODB_DATABASE]
prompts_collection = db['llm_prompts']

# Logger
logger = logging.getLogger(__name__)


@prompt_bp.route('/llm/prompts', methods=['GET'])
def get_all_prompts():
    """Get all LLM prompts"""
    try:
        prompts = list(prompts_collection.find())
        
        # Convert ObjectId to string for JSON serialization
        for prompt in prompts:
            prompt['_id'] = str(prompt['_id'])
        
        return jsonify(prompts), 200
    except Exception as e:
        logger.error(f"Error fetching prompts: {e}")
        return jsonify({'error': str(e)}), 500


@prompt_bp.route('/llm/prompts/<prompt_id>', methods=['GET'])
def get_prompt_by_id(prompt_id):
    """Get prompt by ID"""
    try:
        prompt = prompts_collection.find_one({'_id': ObjectId(prompt_id)})
        
        if not prompt:
            return jsonify({'error': 'Prompt not found'}), 404
        
        prompt['_id'] = str(prompt['_id'])
        return jsonify(prompt), 200
    except Exception as e:
        logger.error(f"Error fetching prompt: {e}")
        return jsonify({'error': str(e)}), 500


@prompt_bp.route('/llm/prompts/type/<prompt_type>', methods=['GET'])
def get_prompt_by_type(prompt_type):
    """Get prompt by type"""
    try:
        prompt = prompts_collection.find_one({'type': prompt_type})
        
        if not prompt:
            return jsonify({'error': 'Prompt not found'}), 404
        
        prompt['_id'] = str(prompt['_id'])
        return jsonify(prompt), 200
    except Exception as e:
        logger.error(f"Error fetching prompt: {e}")
        return jsonify({'error': str(e)}), 500


@prompt_bp.route('/llm/prompts', methods=['POST'])
def create_prompt():
    """Create new prompt"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'type', 'template']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create prompt document
        prompt = {
            'name': data['name'],
            'type': data['type'],
            'template': data['template'],
            'description': data.get('description', ''),
            'maxTokens': data.get('maxTokens', 150),
            'temperature': data.get('temperature', 0.7),
            'variables': data.get('variables', []),
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
        }
        
        result = prompts_collection.insert_one(prompt)
        prompt['_id'] = str(result.inserted_id)
        
        return jsonify(prompt), 201
    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        return jsonify({'error': str(e)}), 500


@prompt_bp.route('/llm/prompts/<prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """Update existing prompt"""
    try:
        data = request.get_json()
        
        # Build update document
        update_doc = {
            'updatedAt': datetime.utcnow()
        }
        
        # Update allowed fields
        allowed_fields = ['name', 'type', 'template', 'description', 'maxTokens', 'temperature', 'variables']
        for field in allowed_fields:
            if field in data:
                update_doc[field] = data[field]
        
        result = prompts_collection.update_one(
            {'_id': ObjectId(prompt_id)},
            {'$set': update_doc}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Prompt not found'}), 404
        
        # Fetch updated prompt
        prompt = prompts_collection.find_one({'_id': ObjectId(prompt_id)})
        prompt['_id'] = str(prompt['_id'])
        
        return jsonify(prompt), 200
    except Exception as e:
        logger.error(f"Error updating prompt: {e}")
        return jsonify({'error': str(e)}), 500


@prompt_bp.route('/llm/prompts/<prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """Delete prompt"""
    try:
        result = prompts_collection.delete_one({'_id': ObjectId(prompt_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Prompt not found'}), 404
        
        return jsonify({'message': 'Prompt deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting prompt: {e}")
        return jsonify({'error': str(e)}), 500


@prompt_bp.route('/llm/prompts/test', methods=['POST'])
def test_prompt():
    """Test prompt with sample data"""
    try:
        import requests
        import time
        
        data = request.get_json()
        
        # Validate required fields
        if 'template' not in data or 'sampleData' not in data:
            return jsonify({'error': 'Missing required fields: template, sampleData'}), 400
        
        template = data['template']
        sample_data = data['sampleData']
        max_tokens = data.get('maxTokens', 150)
        temperature = data.get('temperature', 0.7)
        
        # Process template with sample data
        processed_prompt = template
        for key, value in sample_data.items():
            processed_prompt = processed_prompt.replace(f'{{{{{key}}}}}', str(value))
        
        # Call LLM service
        llm_service_url = os.getenv('LLM_SERVICE_URL', 'http://ichat-llm-service:8083')
        
        start_time = time.time()
        
        response = requests.post(
            f'{llm_service_url}/llm/generate',
            json={
                'query': processed_prompt,
                'use_rag': False,
                'max_tokens': max_tokens,
                'temperature': temperature,
            },
            timeout=30
        )
        
        response_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        
        if response.status_code != 200:
            return jsonify({'error': 'LLM service error', 'details': response.text}), 500
        
        llm_result = response.json()
        
        # Extract output
        output = llm_result.get('response', '')
        
        # Calculate estimated cost (rough estimate: $0.002 per 1K tokens)
        tokens_used = len(processed_prompt.split()) + len(output.split())
        estimated_cost = (tokens_used / 1000) * 0.002
        
        return jsonify({
            'output': output,
            'tokensUsed': tokens_used,
            'responseTime': response_time,
            'estimatedCost': round(estimated_cost, 6),
            'model': llm_result.get('model', 'N/A'),
        }), 200
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'LLM service timeout'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling LLM service: {e}")
        return jsonify({'error': 'Failed to call LLM service', 'details': str(e)}), 500
    except Exception as e:
        logger.error(f"Error testing prompt: {e}")
        return jsonify({'error': str(e)}), 500


@prompt_bp.route('/llm/prompts/seed', methods=['POST'])
def seed_default_prompts():
    """Seed default prompts (for initial setup)"""
    try:
        # Check if prompts already exist
        if prompts_collection.count_documents({}) > 0:
            return jsonify({'message': 'Prompts already exist'}), 200
        
        # Default prompts based on existing usage
        default_prompts = [
            {
                'name': 'News Summary Generation',
                'type': 'summary',
                'description': 'Generate a concise summary of news articles (45-70 words)',
                'template': '''You are a professional news editor. Write a detailed summary of this news article.

Title: {{title}}
Content: {{content}}

Requirements:
1. Write EXACTLY 45-70 words (count carefully)
2. Focus on the key facts: who, what, when, where, why
3. Use clear, professional language
4. Do NOT include any meta-commentary about word count
5. Write in plain English, no markdown

Write your 45-70 word detailed summary:''',
                'maxTokens': 150,
                'temperature': 0.7,
                'variables': ['title', 'content'],
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow(),
            },
            {
                'name': 'YouTube Title Generation',
                'type': 'title',
                'description': 'Generate engaging YouTube video titles (max 100 characters)',
                'template': '''Generate an engaging, SEO-optimized YouTube title for this news video.

Content: {{content}}
Category: {{category}}

Requirements:
1. Maximum 100 characters
2. Include key facts and impact
3. Use engaging language
4. No clickbait
5. Professional tone

Generate the title:''',
                'maxTokens': 50,
                'temperature': 0.8,
                'variables': ['content', 'category'],
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow(),
            },
        ]
        
        prompts_collection.insert_many(default_prompts)
        
        return jsonify({'message': f'Seeded {len(default_prompts)} default prompts'}), 201
    except Exception as e:
        logger.error(f"Error seeding prompts: {e}")
        return jsonify({'error': str(e)}), 500

