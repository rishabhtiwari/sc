"""
Voice Generator Job - Generate audio for news articles
"""

import os
import sys
import time
from typing import Dict, List, Any
from flask import jsonify, request

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models.base_job import BaseJob
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
            **kwargs: Additional parameters for the job

        Returns:
            Dict containing job results and metadata
        """
        self.logger.info(f"🎵 Starting Voice Generator Job {job_id} (on_demand: {is_on_demand})")
        
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
            # Execute parallel tasks
            parallel_results = self.run_parallel_tasks(job_id, is_on_demand=is_on_demand)

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

    def process_news_audio_generation(self, job_id: str = None) -> Dict[str, Any]:
        """
        Process news audio generation (wrapper for API endpoints)
        
        Args:
            job_id: Job ID for tracking
            
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
            results = self.news_audio_service.process_news_audio_generation(job_id)
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
        if not voice_generator_job.news_audio_service:
            return jsonify({
                'status': 'error',
                'error': 'News Audio Service not initialized'
            }), 500

        # Get total articles with short_summary (eligible for audio)
        total_eligible = voice_generator_job.news_audio_service.news_collection.count_documents({
            'status': {'$in': ['completed', 'published']},
            'short_summary': {'$exists': True, '$ne': '', '$ne': None}
        })

        # Get total articles with audio generated
        total_generated = voice_generator_job.news_audio_service.news_collection.count_documents({
            'status': {'$in': ['completed', 'published']},
            'short_summary': {'$exists': True, '$ne': '', '$ne': None},
            'audio_paths.short_summary': {'$exists': True, '$ne': None, '$ne': ''}
        })

        # Get total articles pending audio generation
        total_pending = voice_generator_job.news_audio_service.news_collection.count_documents({
            'status': {'$in': ['completed', 'published']},
            'short_summary': {'$exists': True, '$ne': '', '$ne': None},
            '$or': [
                {'audio_paths': {'$exists': False}},
                {'audio_paths': None},
                {'audio_paths': {}},
                {'audio_paths.short_summary': {'$exists': False}}
            ]
        })

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
        if not voice_generator_job.news_audio_service:
            return jsonify({
                'status': 'error',
                'error': 'News Audio Service not initialized'
            }), 500

        # Get optional parameters
        data = request.get_json() or {}
        job_id = data.get('job_id', f'manual_{int(time.time())}')

        # Process audio generation
        results = voice_generator_job.process_news_audio_generation(job_id)

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
        if not voice_generator_job.news_audio_service:
            return jsonify({
                'status': 'error',
                'error': 'News Audio Service not initialized'
            }), 500

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
        import os

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

        # Get document from database
        try:
            doc = voice_generator_job.news_audio_service.news_collection.find_one({
                '_id': ObjectId(doc_id)
            })
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
