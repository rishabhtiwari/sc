"""
Voice Configuration Routes - Voice settings management
"""

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import os
import logging
import tempfile

# Create blueprint
voice_config_bp = Blueprint('voice_config', __name__)

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
voice_config_collection = db['voice_config']

# Logger
logger = logging.getLogger(__name__)

# Audio generation service URL
AUDIO_GENERATION_SERVICE_URL = os.getenv('AUDIO_GENERATION_SERVICE_URL', 'http://audio-generation-factory:3000')


@voice_config_bp.route('/voice/config', methods=['GET'])
def get_voice_config():
    """Get voice configuration"""
    try:
        config = voice_config_collection.find_one({'type': 'default'})
        
        if not config:
            # Return default configuration
            default_config = {
                'type': 'default',
                'defaultVoice': 'am_adam',
                'enableAlternation': True,
                'language': 'en',
                'maleVoices': ['am_adam', 'am_michael'],
                'femaleVoices': ['af_bella', 'af_sarah'],
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow(),
            }
            voice_config_collection.insert_one(default_config)
            config = default_config
        
        # Convert ObjectId to string if present
        if '_id' in config:
            config['_id'] = str(config['_id'])
        
        return jsonify(config), 200
    except Exception as e:
        logger.error(f"Error fetching voice config: {e}")
        return jsonify({'error': str(e)}), 500


@voice_config_bp.route('/voice/config', methods=['PUT'])
def update_voice_config():
    """Update voice configuration"""
    try:
        data = request.get_json()
        
        # Build update document
        update_doc = {
            'updatedAt': datetime.utcnow()
        }
        
        # Update allowed fields
        allowed_fields = ['defaultVoice', 'enableAlternation', 'language', 'maleVoices', 'femaleVoices']
        for field in allowed_fields:
            if field in data:
                update_doc[field] = data[field]
        
        # Upsert configuration
        result = voice_config_collection.update_one(
            {'type': 'default'},
            {'$set': update_doc},
            upsert=True
        )
        
        # Fetch updated config
        config = voice_config_collection.find_one({'type': 'default'})
        if '_id' in config:
            config['_id'] = str(config['_id'])
        
        return jsonify(config), 200
    except Exception as e:
        logger.error(f"Error updating voice config: {e}")
        return jsonify({'error': str(e)}), 500


@voice_config_bp.route('/voice/voices', methods=['GET'])
def get_available_voices():
    """Get available voices"""
    try:
        # English voices (Kokoro-82M)
        english_voices = {
            'male': [
                {'id': 'am_adam', 'name': 'Adam (American Male)', 'gender': 'male', 'language': 'en'},
                {'id': 'am_michael', 'name': 'Michael (American Male)', 'gender': 'male', 'language': 'en'},
                {'id': 'bm_george', 'name': 'George (British Male)', 'gender': 'male', 'language': 'en'},
                {'id': 'bm_lewis', 'name': 'Lewis (British Male)', 'gender': 'male', 'language': 'en'},
            ],
            'female': [
                {'id': 'af_bella', 'name': 'Bella (American Female)', 'gender': 'female', 'language': 'en'},
                {'id': 'af_nicole', 'name': 'Nicole (American Female)', 'gender': 'female', 'language': 'en'},
                {'id': 'af_sarah', 'name': 'Sarah (American Female)', 'gender': 'female', 'language': 'en'},
                {'id': 'af_sky', 'name': 'Sky (American Female)', 'gender': 'female', 'language': 'en'},
                {'id': 'bf_emma', 'name': 'Emma (British Female)', 'gender': 'female', 'language': 'en'},
                {'id': 'bf_isabella', 'name': 'Isabella (British Female)', 'gender': 'female', 'language': 'en'},
            ],
        }
        
        return jsonify({
            'english': english_voices,
            'hindi': {
                'info': 'Hindi uses MMS-TTS-HIN model without named voices'
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching voices: {e}")
        return jsonify({'error': str(e)}), 500


@voice_config_bp.route('/voice/preview', methods=['POST'])
def preview_voice():
    """Preview voice with sample text"""
    try:
        import requests
        
        data = request.get_json()
        
        # Validate required fields
        if 'voice' not in data or 'text' not in data:
            return jsonify({'error': 'Missing required fields: voice, text'}), 400
        
        voice = data['voice']
        text = data['text']
        
        # Call audio generation service
        response = requests.post(
            f'{AUDIO_GENERATION_SERVICE_URL}/tts',
            json={
                'text': text,
                'model': 'kokoro-82m',
                'voice': voice,
                'format': 'wav',
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Audio generation failed', 'details': response.text}), 500
        
        result = response.json()
        
        # Return audio URL
        audio_url = result.get('url', '')
        
        return jsonify({
            'audioUrl': audio_url,
            'voice': voice,
            'duration': result.get('duration', 0),
        }), 200
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Audio generation timeout'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling audio service: {e}")
        return jsonify({'error': 'Failed to call audio service', 'details': str(e)}), 500
    except Exception as e:
        logger.error(f"Error previewing voice: {e}")
        return jsonify({'error': str(e)}), 500


@voice_config_bp.route('/voice/test', methods=['POST'])
def test_voice():
    """Test voice with sample text (legacy endpoint)"""
    return preview_voice()

