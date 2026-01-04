"""
Voice Generator Job - Generate audio for news articles
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional
from flask import jsonify, request

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models.base_job import BaseJob
from common.utils.multi_tenant_db import extract_user_context_from_headers
from config.settings import Config
from services.news_audio_service import NewsAudioService


class VoiceGeneratorJob(BaseJob):
    """
    Voice Generator Job Implementation
    Extends BaseJob to provide news audio generation functionality
    """

    def __init__(self):
        super().__init__('voice-generator', Config)
        
        # Initialize services
        try:
            self.news_audio_service = NewsAudioService(logger=self.logger)
            self.logger.info("✅ Voice Generator Service initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize News Audio Service: {str(e)}")
            self.news_audio_service = None

    def get_job_type(self) -> str:
        """Return the job type identifier"""
        return 'voice_generation'

    def is_multi_tenant_job(self) -> bool:
        """
        Voice generator is a multi-tenant job - runs separately for each customer

        Returns:
            True to enable per-customer job execution
        """
        return True

    def get_parallel_tasks(self) -> List[Dict[str, Any]]:
        """
        Define parallel tasks for voice generator job

        Returns:
            List of task definitions for parallel execution
        """
        tasks = []
        
        # Add news audio generation task if service is available
        if self.news_audio_service:
            tasks.append({
                'name': 'news_audio_generation',
                'function': self.news_audio_service.process_news_audio_generation,
                'args': (),
                'kwargs': {}
            })
        
        return tasks

    def validate_job_params(self, params: Dict[str, Any]) -> List[str]:
        """
        Validate job parameters

        Args:
            params: Job parameters to validate

        Returns:
            List of validation errors (empty if valid)
        """
        # Voice generator doesn't require specific parameters
        # Configuration validation is done in Config.validate_config()
        return []

    def run_job(self, job_id: str, is_on_demand: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Execute the voice generator job

        Args:
            job_id: Unique identifier for this job execution
            is_on_demand: True if this is a manual/on-demand job
            **kwargs: Additional parameters for the job (customer_id, user_id)

        Returns:
            Dict containing job results and metadata
        """
        # Extract customer_id and user_id from kwargs
        customer_id = kwargs.get('customer_id')
        user_id = kwargs.get('user_id')

        customer_info = f" for customer {customer_id}" if customer_id else ""
        self.logger.info(f"🎵 Starting Voice Generator Job {job_id}{customer_info} (on_demand: {is_on_demand})")

        job_results = {
            'job_id': job_id,
            'job_type': self.get_job_type(),
            'is_on_demand': is_on_demand,
            'status': 'running',
            'results': {},
            'errors': [],
            'total_processing_time_ms': 0
        }

        try:
            # Execute parallel tasks with customer_id and user_id
            # Note: customer_id and user_id are already in kwargs, don't pass them again
            parallel_results = self.run_parallel_tasks(
                job_id,
                is_on_demand=is_on_demand,
                **kwargs
            )

            # Process results from task_details
            for task_name, task_result in parallel_results.get('task_details', {}).items():
                if task_result['status'] == 'completed':
                    job_results['results'][task_name] = task_result['result']
                    self.logger.info(f"✅ Task {task_name} completed successfully")
                else:
                    job_results['errors'].append({
                        'task': task_name,
                        'error': task_result.get('error', 'Unknown error')
                    })
                    self.logger.error(f"❌ Task {task_name} failed: {task_result.get('error', 'Unknown error')}")

            # Calculate total processing time
            total_time = sum(
                result.get('processing_time_ms', 0)
                for result in job_results['results'].values()
                if isinstance(result, dict)
            )
            job_results['total_processing_time_ms'] = total_time

            # Determine overall job status
            if job_results['errors']:
                job_results['status'] = 'completed_with_errors'
                self.logger.warning(f"⚠️ Voice Generator Job {job_id} completed with {len(job_results['errors'])} errors")
            else:
                job_results['status'] = 'completed'
                self.logger.info(f"✅ Voice Generator Job {job_id} completed successfully")

        except Exception as e:
            job_results['status'] = 'failed'
            job_results['errors'].append({
                'task': 'job_execution',
                'error': f"Job execution failed: {str(e)}"
            })
            self.logger.error(f"💥 Voice Generator Job {job_id} failed: {str(e)}")

        return job_results

    def process_news_audio_generation(self, job_id: str = None, customer_id: str = None) -> Dict[str, Any]:
        """
        Process news audio generation (wrapper for API endpoints)

        Args:
            job_id: Job ID for tracking
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            Dictionary with processing results
        """
        if not self.news_audio_service:
            return {
                'success': False,
                'error': 'News Audio Service not initialized',
                'results': {}
            }

        try:
            results = self.news_audio_service.process_news_audio_generation(job_id, customer_id=customer_id)
            return {
                'success': True,
                'results': results
            }
        except Exception as e:
            self.logger.error(f"❌ Error in news audio generation: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': {}
            }


# Create job instance
voice_generator_job = VoiceGeneratorJob()

# Additional Flask routes specific to voice generator
@voice_generator_job.app.route('/api/news/audio/stats', methods=['GET'])
def get_news_audio_stats():
    """
    Get statistics about news audio generation

    Returns:
        JSON response with audio generation statistics
    """
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        if not voice_generator_job.news_audio_service:
            return jsonify({
                'status': 'error',
                'error': 'News Audio Service not initialized'
            }), 500

        from common.utils.multi_tenant_db import build_multi_tenant_query

        # Build base query with multi-tenant filter
        base_query_eligible = {
            'status': {'$in': ['completed', 'published']},
            'short_summary': {'$exists': True, '$ne': '', '$ne': None}
        }
        query_eligible = build_multi_tenant_query(base_query_eligible, customer_id=customer_id)

        # Get total articles with short_summary (eligible for audio)
        total_eligible = voice_generator_job.news_audio_service.news_collection.count_documents(query_eligible)

        # Build query for generated audio
        base_query_generated = {
            'status': {'$in': ['completed', 'published']},
            'short_summary': {'$exists': True, '$ne': '', '$ne': None},
            'audio_paths.short_summary': {'$exists': True, '$ne': None, '$ne': ''}
        }
        query_generated = build_multi_tenant_query(base_query_generated, customer_id=customer_id)

        # Get total articles with audio generated
        total_generated = voice_generator_job.news_audio_service.news_collection.count_documents(query_generated)

        # Build query for pending audio
        base_query_pending = {
            'status': {'$in': ['completed', 'published']},
            'short_summary': {'$exists': True, '$ne': '', '$ne': None},
            '$or': [
                {'audio_paths': {'$exists': False}},
                {'audio_paths': None},
                {'audio_paths': {}},
                {'audio_paths.short_summary': {'$exists': False}}
            ]
        }
        query_pending = build_multi_tenant_query(base_query_pending, customer_id=customer_id)

        # Get total articles pending audio generation
        total_pending = voice_generator_job.news_audio_service.news_collection.count_documents(query_pending)

        stats = {
            'total': total_eligible,
            'generated': total_generated,
            'pending': total_pending,
            'coverage_percentage': round((total_generated / total_eligible * 100), 2) if total_eligible > 0 else 0
        }

        return jsonify({
            'status': 'success',
            'data': stats
        })

    except Exception as e:
        voice_generator_job.logger.error(f"❌ Error getting news audio stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@voice_generator_job.app.route('/api/news/audio/generate', methods=['POST'])
def generate_news_audio():
    """
    Trigger on-demand news audio generation

    Returns:
        JSON response with generation results
    """
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        if not voice_generator_job.news_audio_service:
            return jsonify({
                'status': 'error',
                'error': 'News Audio Service not initialized'
            }), 500

        # Get optional parameters
        data = request.get_json() or {}
        job_id = data.get('job_id', f'manual_{int(time.time())}')

        # Process audio generation with customer_id
        results = voice_generator_job.process_news_audio_generation(job_id, customer_id=customer_id)

        if results['success']:
            return jsonify({
                'status': 'success',
                'message': 'News audio generation completed',
                'data': results['results']
            })
        else:
            return jsonify({
                'status': 'error',
                'error': results['error']
            }), 500

    except Exception as e:
        voice_generator_job.logger.error(f"❌ Error in manual news audio generation: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@voice_generator_job.app.route('/api/news/audio/list', methods=['GET'])
def list_audio_files():
    """
    Get list of audio files with pagination and filtering

    Query Parameters:
        - page: Page number (default: 1)
        - limit: Items per page (default: 20)
        - status: Filter by status (pending, generated, failed)

    Returns:
        JSON response with audio files list
    """
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        if not voice_generator_job.news_audio_service:
            return jsonify({
                'status': 'error',
                'error': 'News Audio Service not initialized'
            }), 500

        from common.utils.multi_tenant_db import build_multi_tenant_query

        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status_filter = request.args.get('status', 'all')  # all, pending, generated, failed

        # Calculate skip
        skip = (page - 1) * limit

        # Build match criteria based on status filter
        match_criteria = {
            'status': {'$in': ['completed', 'published']},  # Only completed articles
            'short_summary': {'$exists': True, '$ne': '', '$ne': None}  # Must have short_summary
        }

        if status_filter == 'pending':
            # Articles without audio
            match_criteria['$or'] = [
                {'audio_paths': {'$exists': False}},
                {'audio_paths': None},
                {'audio_paths': {}},
                {'audio_paths.short_summary': {'$exists': False}}
            ]
        elif status_filter == 'generated':
            # Articles with audio
            match_criteria['audio_paths.short_summary'] = {'$exists': True, '$ne': None, '$ne': ''}

        # Apply multi-tenant filter
        match_criteria = build_multi_tenant_query(match_criteria, customer_id=customer_id)

        # Build aggregation pipeline
        pipeline = [
            {'$match': match_criteria},
            {'$sort': {'created_at': -1}},  # Most recent first
            {
                '$facet': {
                    'metadata': [{'$count': 'total'}],
                    'data': [
                        {'$skip': skip},
                        {'$limit': limit},
                        {
                            '$project': {
                                '_id': 1,
                                'id': 1,
                                'title': 1,
                                'audio_paths': 1,
                                'voice': 1,
                                'voice_updated_at': 1,
                                'created_at': 1
                            }
                        }
                    ]
                }
            }
        ]

        result = list(voice_generator_job.news_audio_service.news_collection.aggregate(pipeline))

        total = result[0]['metadata'][0]['total'] if result[0]['metadata'] else 0
        audio_files = result[0]['data'] if result else []

        # Format response
        formatted_files = []
        for doc in audio_files:
            doc_id = str(doc.get('_id'))
            audio_paths = doc.get('audio_paths', {})
            has_audio = bool(audio_paths and audio_paths.get('short_summary'))

            formatted_files.append({
                'id': doc_id,
                'article_id': doc.get('id'),
                'title': doc.get('title', 'Untitled'),
                'status': 'generated' if has_audio else 'pending',
                'audio_url': f'/api/news/audio/serve/{doc_id}/short_summary' if has_audio else None,
                'voice': doc.get('voice'),
                'generated_at': doc.get('voice_updated_at').isoformat() if doc.get('voice_updated_at') else None,
                'created_at': doc.get('created_at').isoformat() if doc.get('created_at') else None
            })

        return jsonify({
            'status': 'success',
            'data': {
                'audio_files': formatted_files,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit if limit > 0 else 0
                }
            }
        })

    except Exception as e:
        voice_generator_job.logger.error(f"❌ Error listing audio files: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@voice_generator_job.app.route('/api/news/audio/serve/<doc_id>/<audio_type>', methods=['GET'])
def serve_audio_file(doc_id, audio_type):
    """
    Serve audio file for a specific document

    Args:
        doc_id: Document ID (MongoDB ObjectId as string)
        audio_type: Type of audio (title, description, content, short_summary)

    Returns:
        Audio file or error response
    """
    try:
        from flask import send_file
        from bson import ObjectId
        from common.utils.multi_tenant_db import build_multi_tenant_query
        import os

        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        if not voice_generator_job.news_audio_service:
            return jsonify({
                'status': 'error',
                'error': 'News Audio Service not initialized'
            }), 500

        # Validate audio type
        valid_audio_types = ['title', 'description', 'content', 'short_summary']
        if audio_type not in valid_audio_types:
            return jsonify({
                'status': 'error',
                'error': f'Invalid audio type. Must be one of: {", ".join(valid_audio_types)}'
            }), 400

        # Get document from database with multi-tenant filter
        try:
            base_query = {'_id': ObjectId(doc_id)}
            query = build_multi_tenant_query(base_query, customer_id=customer_id)
            doc = voice_generator_job.news_audio_service.news_collection.find_one(query)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': f'Invalid document ID: {str(e)}'
            }), 400

        if not doc:
            return jsonify({
                'status': 'error',
                'error': 'Document not found'
            }), 404

        # Get audio path
        audio_paths = doc.get('audio_paths', {})
        audio_path = audio_paths.get(audio_type)

        if not audio_path:
            return jsonify({
                'status': 'error',
                'error': f'No {audio_type} audio found for this document'
            }), 404

        # Construct full file path
        # audio_path is like "/public/article_id/short_summary.wav"
        file_path = audio_path.replace('/public/', '/app/public/')

        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'error': 'Audio file not found on disk',
                'path': audio_path
            }), 404

        # Serve the file
        return send_file(
            file_path,
            mimetype='audio/wav',
            as_attachment=False,
            download_name=f'{audio_type}.wav'
        )

    except Exception as e:
        voice_generator_job.logger.error(f"❌ Error serving audio file: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@voice_generator_job.app.route('/api/voice/config', methods=['GET'])
def get_voice_config():
    """Get voice configuration for the authenticated customer"""
    try:
        from common.utils.multi_tenant_db import (
            extract_user_context_from_headers,
            build_multi_tenant_query,
            prepare_insert_document
        )

        # Extract user context from headers
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        # Build multi-tenant query
        base_query = {}
        query = build_multi_tenant_query(base_query, customer_id=customer_id)

        # Access voice_config collection through news_audio_service
        voice_config_collection = voice_generator_job.news_audio_service.news_db['voice_config']
        config = voice_config_collection.find_one(query)

        if not config:
            # Check if GPU is enabled via environment variable
            import os
            import requests
            gpu_enabled = os.getenv('USE_GPU', 'false').lower() == 'true'
            audio_generation_url = os.getenv('AUDIO_GENERATION_URL', 'http://audio-generation-factory:3000')

            voice_generator_job.logger.info(f"🔧 Creating default voice config - GPU enabled: {gpu_enabled}")

            # Fetch available models and configuration from audio generation service
            try:
                config_response = requests.get(f'{audio_generation_url}/config', timeout=10)
                audio_config = config_response.json() if config_response.status_code == 200 else {}
                voice_generator_job.logger.info(f"📡 Audio config fetched: GPU={audio_config.get('gpu_enabled')}, Default model={audio_config.get('default_model')}")
            except Exception as e:
                voice_generator_job.logger.warning(f"⚠️ Failed to fetch audio config from service: {e}")
                audio_config = {}

            # Create default configuration based on GPU availability
            if gpu_enabled:
                # GPU configuration - use Coqui XTTS v2 (universal multi-lingual model)
                voice_generator_job.logger.info("🎮 GPU mode detected - fetching Coqui XTTS speakers")

                # Fetch speakers from audio generation service
                try:
                    speakers_response = requests.get(f'{audio_generation_url}/speakers', timeout=10)
                    speakers_data = speakers_response.json() if speakers_response.status_code == 200 else {}
                    all_speakers = speakers_data.get('speakers', [])

                    voice_generator_job.logger.info(f"🎤 Fetched {len(all_speakers)} speakers from audio generation service")

                    # Categorize speakers by gender (if metadata available)
                    male_voices = []
                    female_voices = []

                    for speaker in all_speakers:
                        if isinstance(speaker, dict):
                            speaker_id = speaker.get('id', speaker.get('name', ''))
                            gender = speaker.get('gender', 'unknown')

                            if gender == 'male':
                                male_voices.append(speaker_id)
                            elif gender == 'female':
                                female_voices.append(speaker_id)
                        else:
                            # Speaker is just a string name
                            # Try to infer gender from name or add to both lists
                            # For now, add to male voices by default
                            male_voices.append(speaker)

                    # If no gender metadata found, distribute speakers evenly
                    if not male_voices and not female_voices and all_speakers:
                        voice_generator_job.logger.info("⚠️ No gender metadata found, distributing speakers evenly")
                        mid_point = len(all_speakers) // 2
                        male_voices = [s if isinstance(s, str) else s.get('id', s.get('name', '')) for s in all_speakers[:mid_point]]
                        female_voices = [s if isinstance(s, str) else s.get('id', s.get('name', '')) for s in all_speakers[mid_point:]]

                    # Ensure we have at least some voices
                    if not male_voices:
                        male_voices = ['Claribel Dervla', 'Dionisio Schuyler', 'Royston Min']
                    if not female_voices:
                        female_voices = ['Ana Florence', 'Annmarie Nele', 'Asya Anara']

                    default_voice = male_voices[0] if male_voices else 'Claribel Dervla'

                    voice_generator_job.logger.info(f"✅ GPU voices configured - Male: {len(male_voices)}, Female: {len(female_voices)}, Default: {default_voice}")

                except Exception as e:
                    voice_generator_job.logger.warning(f"⚠️ Failed to fetch speakers: {e}, using fallback defaults")
                    male_voices = ['Claribel Dervla', 'Dionisio Schuyler', 'Royston Min']
                    female_voices = ['Ana Florence', 'Annmarie Nele', 'Asya Anara']
                    default_voice = 'Claribel Dervla'

                default_config = {
                    'language': 'en',  # Primary language
                    'models': {
                        'en': 'coqui-xtts',
                        'hi': 'coqui-xtts'
                    },
                    'voices': {
                        'en': {
                            'defaultVoice': default_voice,
                            'enableAlternation': True,
                            'maleVoices': male_voices,
                            'femaleVoices': female_voices
                        },
                        'hi': {
                            'defaultVoice': default_voice,
                            'enableAlternation': True,
                            'maleVoices': male_voices,
                            'femaleVoices': female_voices
                        }
                    }
                }
            else:
                # CPU configuration - use language-specific models
                voice_generator_job.logger.info("💻 CPU mode detected - using Kokoro (EN) and MMS (HI) models")

                default_config = {
                    'language': 'en',  # Primary language
                    'models': {
                        'en': 'kokoro-82m',
                        'hi': 'mms-tts-hin'
                    },
                    'voices': {
                        'en': {
                            'defaultVoice': 'am_adam',
                            'enableAlternation': True,
                            'maleVoices': ['am_adam', 'am_michael'],
                            'femaleVoices': ['af_bella', 'af_sarah']
                        },
                        'hi': {
                            'defaultVoice': 'hi_male',
                            'enableAlternation': True,
                            'maleVoices': ['hi_male'],
                            'femaleVoices': ['hi_female']
                        }
                    }
                }

            # Use prepare_insert_document to add multi-tenant fields
            prepared_config = prepare_insert_document(
                default_config,
                customer_id=customer_id,
                user_id=user_id
            )

            voice_config_collection.insert_one(prepared_config)
            config = prepared_config

        # Convert ObjectId to string if present
        if '_id' in config:
            config['_id'] = str(config['_id'])

        return jsonify(config), 200
    except Exception as e:
        voice_generator_job.logger.error(f"Error fetching voice config: {e}")
        return jsonify({'error': str(e)}), 500


@voice_generator_job.app.route('/api/voice/config', methods=['PUT'])
def update_voice_config():
    """Update voice configuration for the authenticated customer"""
    try:
        from common.utils.multi_tenant_db import (
            extract_user_context_from_headers,
            build_multi_tenant_query,
            prepare_update_document,
            prepare_insert_document
        )

        # Extract user context from headers
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        data = request.get_json()

        # Build multi-tenant query
        base_query = {}
        query = build_multi_tenant_query(base_query, customer_id=customer_id)

        # Access voice_config collection through news_audio_service
        voice_config_collection = voice_generator_job.news_audio_service.news_db['voice_config']

        # Check if config exists
        existing_config = voice_config_collection.find_one(query)

        if existing_config:
            # Update existing config
            update_data = {}

            # Handle top-level fields
            if 'language' in data:
                update_data['language'] = data['language']

            # Handle models object
            if 'models' in data:
                update_data['models'] = data['models']

            # Handle voices object (nested structure)
            if 'voices' in data:
                update_data['voices'] = data['voices']

            # Use prepare_update_document to add updated_by and updated_at
            prepared_updates = prepare_update_document(
                update_data,
                user_id=user_id
            )

            # Update configuration
            voice_config_collection.update_one(
                query,
                {'$set': prepared_updates}
            )
        else:
            # Create new config with default structure
            new_config = {
                'language': data.get('language', 'en'),
                'models': data.get('models', {
                    'en': 'kokoro-82m',
                    'hi': 'mms-tts-hin'
                }),
                'voices': data.get('voices', {
                    'en': {
                        'defaultVoice': 'am_adam',
                        'enableAlternation': True,
                        'maleVoices': ['am_adam', 'am_michael'],
                        'femaleVoices': ['af_bella', 'af_sarah']
                    },
                    'hi': {
                        'defaultVoice': 'hi_male',
                        'enableAlternation': True,
                        'maleVoices': ['hi_male'],
                        'femaleVoices': ['hi_female']
                    }
                })
            }

            # Use prepare_insert_document to add multi-tenant fields
            prepared_config = prepare_insert_document(
                new_config,
                customer_id=customer_id,
                user_id=user_id
            )

            voice_config_collection.insert_one(prepared_config)

        # Fetch updated config
        config = voice_config_collection.find_one(query)
        if config and '_id' in config:
            config['_id'] = str(config['_id'])

        return jsonify(config), 200
    except Exception as e:
        voice_generator_job.logger.error(f"Error updating voice config: {e}")
        return jsonify({'error': str(e)}), 500


@voice_generator_job.app.route('/api/voice/available-models', methods=['GET'])
def get_available_models():
    """Get list of available TTS models with their supported languages and voices"""
    try:
        models = {
            'kokoro-82m': {
                'id': 'kokoro-82m',
                'name': 'Kokoro TTS',
                'description': 'High-quality English text-to-speech with multiple voices',
                'languages': ['en'],
                'voices': {
                    'male': [
                        {'id': 'am_adam', 'name': 'Adam (American Male)'},
                        {'id': 'am_michael', 'name': 'Michael (American Male)'},
                        {'id': 'bm_george', 'name': 'George (British Male)'},
                        {'id': 'bm_lewis', 'name': 'Lewis (British Male)'},
                    ],
                    'female': [
                        {'id': 'af_bella', 'name': 'Bella (American Female)'},
                        {'id': 'af_sarah', 'name': 'Sarah (American Female)'},
                        {'id': 'bf_emma', 'name': 'Emma (British Female)'},
                        {'id': 'bf_isabella', 'name': 'Isabella (British Female)'},
                    ]
                }
            },
            'mms-tts-hin': {
                'id': 'mms-tts-hin',
                'name': 'MMS Hindi TTS',
                'description': 'Hindi text-to-speech model (single voice only)',
                'languages': ['hi'],
                'voices': {
                    'default': [
                        {'id': 'hi_default', 'name': 'Hindi Voice (Default)'},
                    ],
                    'male': [],
                    'female': []
                },
                'note': 'MMS Hindi model only supports one voice. Male/female alternation is not available for this model.'
            }
        }

        return jsonify({'models': models}), 200
    except Exception as e:
        voice_generator_job.logger.error(f"Error fetching available models: {e}")
        return jsonify({'error': str(e)}), 500


@voice_generator_job.app.route('/api/voice/available', methods=['GET'])
def get_available_voices():
    """Get list of available voices (legacy endpoint - kept for backward compatibility)"""
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
                {'id': 'af_sarah', 'name': 'Sarah (American Female)', 'gender': 'female', 'language': 'en'},
                {'id': 'bf_emma', 'name': 'Emma (British Female)', 'gender': 'female', 'language': 'en'},
                {'id': 'bf_isabella', 'name': 'Isabella (British Female)', 'gender': 'female', 'language': 'en'},
            ],
            'default': []
        }

        # Hindi voices (MMS-TTS-HIN - single voice only)
        hindi_voices = {
            'male': [],
            'female': [],
            'default': [
                {'id': 'hi_default', 'name': 'Hindi Voice (Default)', 'gender': 'default', 'language': 'hi'},
            ]
        }

        return jsonify({
            'english': english_voices,
            'hindi': hindi_voices
        }), 200
    except Exception as e:
        voice_generator_job.logger.error(f"Error fetching available voices: {e}")
        return jsonify({'error': str(e)}), 500


@voice_generator_job.app.route('/api/voice/preview', methods=['POST'])
def preview_voice():
    """
    Preview a voice with sample text

    Request body:
        {
            "voice": "am_adam",
            "text": "Sample text to preview"
        }

    Returns:
        JSON response with audio URL
    """
    try:
        import tempfile
        import os
        from common.utils.multi_tenant_db import extract_user_context_from_headers

        # Extract user context from headers
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        # Get request data
        data = request.get_json()
        voice = data.get('voice')

        if not voice:
            return jsonify({'error': 'Voice ID is required'}), 400

        # Determine language from voice ID
        # hi_default, hi_male, hi_female all map to Hindi
        language = 'hi' if voice.startswith('hi_') else 'en'

        # Use language-appropriate default preview text if not provided
        default_preview_texts = {
            'en': 'This is a preview of the selected voice for news narration.',
            'hi': 'यह समाचार वाचन के लिए चयनित आवाज का पूर्वावलोकन है।'
        }
        text = data.get('text', default_preview_texts.get(language, default_preview_texts['en']))

        # Get appropriate model for language
        if not voice_generator_job.news_audio_service:
            return jsonify({'error': 'News Audio Service not initialized'}), 500

        model = voice_generator_job.news_audio_service._get_audio_model_for_language(
            language,
            customer_id=customer_id
        )

        # Use audio generation service's /preview endpoint which has caching support
        import requests
        audio_generation_url = os.getenv('AUDIO_GENERATION_URL', 'http://audio-generation-factory:3000')

        try:
            preview_response = requests.post(
                f'{audio_generation_url}/preview',
                json={
                    'text': text,
                    'model': model,
                    'voice': voice,
                    'language': language
                },
                timeout=60
            )

            if preview_response.status_code != 200:
                error_data = preview_response.json() if preview_response.headers.get('content-type') == 'application/json' else {}
                error_msg = error_data.get('error', f'Preview generation failed with status {preview_response.status_code}')

                # Check if error is due to model not being loaded
                if 'not loaded' in error_msg.lower():
                    return jsonify({
                        'error': error_msg,
                        'model_loading': True,
                        'message': f'The {model} model is currently loading. This may take a few minutes on first use. Please try again in a moment.'
                    }), 503  # Service Unavailable

                return jsonify({'error': error_msg}), preview_response.status_code

            result = preview_response.json()

            # The audio generation service returns audio_url which could be:
            # 1. A relative path like "/temp/kokoro_1234567890_abc.wav"
            # 2. A presigned URL from MinIO (if cached)
            audio_url = result.get('audio_url')
            if not audio_url:
                return jsonify({'error': 'No audio URL returned from generation service'}), 500

            # If it's a presigned URL (starts with http), return it directly
            if audio_url.startswith('http'):
                return jsonify({
                    'audioUrl': audio_url,
                    'voice': voice,
                    'model': model,
                    'language': language,
                    'cached': result.get('cached', False)
                }), 200

            # Otherwise, it's a relative path - proxy it through our endpoint
            filename = os.path.basename(audio_url)
            proxy_url = f'/api/voice/preview/audio/{filename}'

            return jsonify({
                'audioUrl': proxy_url,
                'voice': voice,
                'model': model,
                'language': language,
                'cached': result.get('cached', False)
            }), 200

        except requests.exceptions.Timeout:
            return jsonify({
                'error': 'Preview generation timed out. The model may be loading.',
                'model_loading': True
            }), 503
        except requests.exceptions.RequestException as e:
            voice_generator_job.logger.error(f"Error calling audio generation service: {e}")
            return jsonify({'error': f'Failed to connect to audio generation service: {str(e)}'}), 500

    except Exception as e:
        voice_generator_job.logger.error(f"❌ Error previewing voice: {str(e)}")
        import traceback
        voice_generator_job.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@voice_generator_job.app.route('/api/voice/preview/audio/<filename>', methods=['GET'])
def serve_preview_audio(filename):
    """
    Proxy audio file from audio-generation service

    Args:
        filename: Audio filename to serve

    Returns:
        Audio file stream
    """
    try:
        import requests
        from flask import Response

        # Try multiple locations for the audio file
        # Kokoro files are in /temp/, MMS files are in root /
        possible_urls = [
            f'http://audio-generation-factory:3000/temp/{filename}',  # Kokoro location
            f'http://audio-generation-factory:3000/{filename}'         # MMS location
        ]

        response = None
        for audio_url in possible_urls:
            try:
                response = requests.get(audio_url, stream=True, timeout=30)
                if response.status_code == 200:
                    break
            except:
                continue

        if not response or response.status_code != 200:
            voice_generator_job.logger.error(f"❌ Audio file not found at any location: {filename}")
            return jsonify({
                'error': 'Audio file not found'
            }), 404

        # Return the audio stream
        return Response(
            response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type='audio/wav',
            headers={
                'Content-Disposition': f'inline; filename="{filename}"'
            }
        )

    except Exception as e:
        voice_generator_job.logger.error(f"❌ Error serving preview audio: {str(e)}")
        return jsonify({'error': str(e)}), 500





if __name__ == '__main__':
    import time
    
    # Validate configuration
    config_errors = Config.validate_config()
    if config_errors:
        voice_generator_job.logger.error("❌ Configuration validation failed:")
        for error in config_errors:
            voice_generator_job.logger.error(f"  - {error}")
        sys.exit(1)
    
    voice_generator_job.logger.info("Starting voice-generator Job Service")
    voice_generator_job.logger.info(f"Scheduler running: {voice_generator_job.scheduler.running}")
    
    # Run Flask app
    voice_generator_job.app.run(
        host='0.0.0.0',
        port=Config.HEALTH_CHECK_PORT,
        debug=False
    )
