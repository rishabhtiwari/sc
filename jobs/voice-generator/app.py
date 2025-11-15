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
        
        # Get articles needing audio
        articles_needing_audio = voice_generator_job.news_audio_service.get_articles_needing_audio()
        
        # Get total articles with audio
        total_with_audio = voice_generator_job.news_audio_service.news_collection.count_documents({
            'audio_path': {'$ne': None, '$ne': ''}
        })
        
        # Get total completed articles
        total_completed = voice_generator_job.news_audio_service.news_collection.count_documents({
            'status': {'$in': ['completed', 'published']}
        })
        
        stats = {
            'articles_needing_audio': len(articles_needing_audio),
            'articles_with_audio': total_with_audio,
            'total_completed_articles': total_completed,
            'audio_coverage_percentage': round((total_with_audio / total_completed * 100), 2) if total_completed > 0 else 0
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
