"""
Voice Generator Job - Main application
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

# Add common directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from models.base_job import BaseJob
from config.settings import Config
from services.voice_generator_service import VoiceGeneratorService
from services.voice_request_service import VoiceRequestService


class VoiceGeneratorJob(BaseJob):
    """
    Voice Generator Job Implementation
    Extends BaseJob to provide voice cloning functionality
    """

    def __init__(self):
        super().__init__('voice-generator', Config)

        # Initialize services with error handling
        try:
            self.logger.info("🔧 Initializing Voice Request Service...")
            self.voice_request_service = VoiceRequestService(Config.MONGODB_URL, logger=self.logger)
            self.logger.info("✅ Voice Request Service initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Voice Request Service: {e}")
            self.voice_request_service = None

        try:
            self.logger.info("🔧 Initializing Voice Generator Service...")
            self.voice_generator_service = VoiceGeneratorService(Config, logger=self.logger)
            self.logger.info("✅ Voice Generator Service initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Voice Generator Service: {e}")
            self.voice_generator_service = None

    def get_job_type(self) -> str:
        """Return the job type identifier"""
        return 'voice_generation'

    def get_parallel_tasks(self) -> List[Dict[str, Any]]:
        """
        Define parallel tasks for voice generator job
        
        Returns:
            List of task definitions for parallel execution
        """
        return [
            {
                'name': 'process_voice_requests',
                'function': self.process_pending_requests,
                'args': (),
                'kwargs': {}
            },
            {
                'name': 'cleanup_old_files',
                'function': self.cleanup_old_data,
                'args': (),
                'kwargs': {}
            }
        ]

    def validate_job_params(self, params: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate job parameters
        
        Args:
            params: Job parameters to validate
            
        Returns:
            Dict of validation errors (empty if valid)
        """
        errors = {}
        
        # Voice generator doesn't require specific parameters for scheduled runs
        # Configuration validation is done in Config.validate_config()
        
        return errors

    def run_job(self, job_id: str, is_on_demand: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Main job execution method
        
        Args:
            job_id: Unique identifier for this job execution
            is_on_demand: True if this is a manual/on-demand job
            **kwargs: Additional parameters
            
        Returns:
            Dict containing job results and metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting voice generator job {job_id}")
            
            # Validate configuration
            Config.validate_config()
            
            # Process voice requests (specific request if provided, otherwise all pending)
            specific_request_id = kwargs.get('specific_request_id')
            if specific_request_id:
                self.logger.info(f"Processing specific request: {specific_request_id}")
                processing_result = self.process_specific_request(specific_request_id)
            else:
                self.logger.info("Processing all pending requests")
                processing_result = self.process_pending_requests()
            
            # Cleanup old data (only for scheduled jobs)
            cleanup_result = {}
            if not is_on_demand:
                cleanup_result = self.cleanup_old_data()
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Prepare result
            result = {
                'status': 'success',
                'execution_time_seconds': execution_time,
                'requests_processed': processing_result.get('processed_count', 0),
                'requests_completed': processing_result.get('completed_count', 0),
                'requests_failed': processing_result.get('failed_count', 0),
                'cleanup_performed': not is_on_demand,
                'files_cleaned': cleanup_result.get('files_cleaned', 0),
                'requests_cleaned': cleanup_result.get('requests_cleaned', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Voice generator job {job_id} completed successfully")
            self.logger.info(f"Processed {result['requests_processed']} requests in {execution_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Voice generator job failed: {e}"
            self.logger.error(f"Error in voice generator job {job_id}: {e}")
            
            return {
                'status': 'failed',
                'error': error_msg,
                'execution_time_seconds': execution_time,
                'timestamp': datetime.utcnow().isoformat()
            }

    def process_pending_requests(self) -> Dict[str, Any]:
        """
        Process pending voice generation requests

        Returns:
            Dict with processing results
        """
        try:
            self.logger.info("Processing pending voice requests")

            # Check if services are initialized
            if not self.voice_request_service:
                self.logger.error("Voice Request Service not initialized")
                return {
                    'processed_count': 0,
                    'completed_count': 0,
                    'failed_count': 0,
                    'error': 'Voice Request Service not initialized'
                }

            if not self.voice_generator_service:
                self.logger.error("Voice Generator Service not initialized")
                return {
                    'processed_count': 0,
                    'completed_count': 0,
                    'failed_count': 0,
                    'error': 'Voice Generator Service not initialized'
                }

            # Get pending requests
            pending_requests = self.voice_request_service.get_pending_requests(
                limit=self.max_parallel_tasks * 2  # Get a few more than we can process in parallel
            )
            
            if not pending_requests:
                self.logger.info("No pending voice requests found")
                return {
                    'processed_count': 0,
                    'completed_count': 0,
                    'failed_count': 0
                }
            
            self.logger.info(f"Found {len(pending_requests)} pending requests")
            
            processed_count = 0
            completed_count = 0
            failed_count = 0
            
            # Process each request
            for request in pending_requests:
                try:
                    request_id = request['request_id']
                    self.logger.info(f"Processing voice request: {request_id}")
                    
                    # Update status to processing
                    self.voice_request_service.update_request_status(
                        request_id, 'processing'
                    )
                    
                    # Generate voice using REAL voice cloning
                    generation_result = self.voice_generator_service.generate_voice_clone(
                        reference_audio_path=request['reference_audio_path'],
                        text_script=request['text_script'],
                        language=request.get('language', 'en'),
                        request_id=request_id,
                        voice_request_service=self.voice_request_service
                    )
                    
                    processed_count += 1
                    
                    if generation_result['success']:
                        # Update status to completed
                        self.voice_request_service.update_request_status(
                            request_id, 
                            'completed',
                            generated_audio_path=generation_result['generated_audio_path'],
                            metadata={
                                'processing_time_seconds': generation_result['processing_time_seconds'],
                                'output_size_mb': generation_result['output_size_mb'],
                                'output_filename': generation_result['output_filename']
                            }
                        )
                        completed_count += 1
                        self.logger.info(f"Successfully completed voice request: {request_id}")
                        
                    else:
                        # Update status to failed
                        self.voice_request_service.update_request_status(
                            request_id, 
                            'failed',
                            error_message=generation_result['error'],
                            metadata={
                                'processing_time_seconds': generation_result.get('processing_time_seconds', 0)
                            }
                        )
                        failed_count += 1
                        self.logger.error(f"Failed to process voice request {request_id}: {generation_result['error']}")
                    
                except Exception as e:
                    processed_count += 1
                    failed_count += 1
                    request_id = request.get('request_id', 'unknown')
                    error_msg = f"Error processing request {request_id}: {e}"
                    self.logger.error(error_msg)
                    
                    # Update status to failed
                    try:
                        self.voice_request_service.update_request_status(
                            request_id, 
                            'failed',
                            error_message=str(e)
                        )
                    except Exception as update_error:
                        self.logger.error(f"Failed to update request status: {update_error}")
            
            result = {
                'processed_count': processed_count,
                'completed_count': completed_count,
                'failed_count': failed_count
            }
            
            self.logger.info(f"Request processing completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing pending requests: {e}")
            return {
                'processed_count': 0,
                'completed_count': 0,
                'failed_count': 0,
                'error': str(e)
            }

    def process_specific_request(self, request_id: str) -> Dict[str, Any]:
        """
        Process a specific voice generation request immediately

        Args:
            request_id: The specific request ID to process

        Returns:
            Dict with processing results
        """
        try:
            self.logger.info(f"Processing specific voice request: {request_id}")

            # Get the specific request
            request = self.voice_request_service.get_voice_request(request_id)

            if not request:
                error_msg = f"Request {request_id} not found"
                self.logger.error(error_msg)
                return {
                    'processed_count': 0,
                    'completed_count': 0,
                    'failed_count': 1,
                    'error': error_msg
                }

            if request['status'] != 'pending':
                error_msg = f"Request {request_id} is not in pending status (current: {request['status']})"
                self.logger.warning(error_msg)
                return {
                    'processed_count': 0,
                    'completed_count': 0,
                    'failed_count': 0,
                    'skipped': 1,
                    'message': error_msg
                }

            try:
                # Update status to processing
                self.voice_request_service.update_request_status(request_id, 'processing')

                # Generate voice using REAL voice cloning
                generation_result = self.voice_generator_service.generate_voice_clone(
                    reference_audio_path=request['reference_audio_path'],
                    text_script=request['text_script'],
                    language=request.get('language', 'en'),
                    request_id=request_id,
                    voice_request_service=self.voice_request_service
                )

                if generation_result['success']:
                    # Update status to completed
                    self.voice_request_service.update_request_status(
                        request_id,
                        'completed',
                        generated_audio_path=generation_result['generated_audio_path'],
                        metadata={
                            'processing_time_seconds': generation_result['processing_time_seconds'],
                            'output_size_mb': generation_result['output_size_mb'],
                            'output_filename': generation_result['output_filename']
                        }
                    )
                    self.logger.info(f"Successfully completed voice request: {request_id}")
                    return {
                        'processed_count': 1,
                        'completed_count': 1,
                        'failed_count': 0
                    }
                else:
                    # Update status to failed
                    self.voice_request_service.update_request_status(
                        request_id,
                        'failed',
                        error_message=generation_result['error'],
                        metadata={
                            'processing_time_seconds': generation_result.get('processing_time_seconds', 0)
                        }
                    )
                    self.logger.error(f"Failed to process voice request {request_id}: {generation_result['error']}")
                    return {
                        'processed_count': 1,
                        'completed_count': 0,
                        'failed_count': 1,
                        'error': generation_result['error']
                    }

            except Exception as e:
                error_msg = f"Error processing request {request_id}: {e}"
                self.logger.error(error_msg)

                # Update status to failed
                try:
                    self.voice_request_service.update_request_status(
                        request_id,
                        'failed',
                        error_message=str(e)
                    )
                except Exception as update_error:
                    self.logger.error(f"Failed to update request status: {update_error}")

                return {
                    'processed_count': 1,
                    'completed_count': 0,
                    'failed_count': 1,
                    'error': error_msg
                }

        except Exception as e:
            error_msg = f"Error processing specific request {request_id}: {e}"
            self.logger.error(error_msg)
            return {
                'processed_count': 0,
                'completed_count': 0,
                'failed_count': 1,
                'error': error_msg
            }

    def cleanup_old_data(self) -> Dict[str, Any]:
        """
        Clean up old generated files and completed requests

        Returns:
            Dict with cleanup results
        """
        try:
            self.logger.info("Starting cleanup of old data")

            # Check if services are initialized
            if not self.voice_generator_service:
                self.logger.error("Voice Generator Service not initialized - skipping file cleanup")
                files_cleaned = 0
            else:
                # Clean up old generated audio files (7 days)
                self.voice_generator_service.cleanup_old_files(max_age_days=7)
                files_cleaned = 0  # VoiceGeneratorService doesn't return count

            if not self.voice_request_service:
                self.logger.error("Voice Request Service not initialized - skipping request cleanup")
                requests_cleaned = 0
            else:
                # Clean up old completed/failed requests (30 days)
                requests_cleaned = self.voice_request_service.cleanup_old_requests(max_age_days=30)

            result = {
                'files_cleaned': files_cleaned,
                'requests_cleaned': requests_cleaned
            }
            
            self.logger.info(f"Cleanup completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return {
                'files_cleaned': 0,
                'requests_cleaned': 0,
                'error': str(e)
            }


# Create Flask app instance
voice_generator_job = VoiceGeneratorJob()
app = voice_generator_job.app

# Add API endpoints
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
import json


@app.route('/api/voice/submit', methods=['POST'])
def submit_voice_request():
    """Submit a new voice generation request"""
    try:
        # Check if request has file part
        if 'reference_audio' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No reference audio file provided'
            }), 400

        file = request.files['reference_audio']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'error': 'No file selected'
            }), 400

        # Get text script
        text_script = request.form.get('text_script')
        if not text_script:
            return jsonify({
                'status': 'error',
                'error': 'Text script is required'
            }), 400

        # Get optional parameters
        language = request.form.get('language', Config.DEFAULT_LANGUAGE)

        # Validate file extension
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        if file_extension not in Config.ALLOWED_AUDIO_EXTENSIONS:
            return jsonify({
                'status': 'error',
                'error': f'Unsupported file format. Allowed: {", ".join(Config.ALLOWED_AUDIO_EXTENSIONS)}'
            }), 400

        # Save reference audio file
        import uuid
        request_id = str(uuid.uuid4())
        reference_filename = f"ref_{request_id}_{filename}"
        reference_path = os.path.join(Config.REFERENCE_AUDIO_DIR, reference_filename)

        file.save(reference_path)

        # Validate the saved audio file
        validation_result = voice_generator_job.voice_generator_service.validate_audio_file(reference_path)
        if not validation_result['valid']:
            # Remove invalid file
            os.remove(reference_path)
            return jsonify({
                'status': 'error',
                'error': f'Invalid audio file: {validation_result["error"]}'
            }), 400

        # Create voice request in database
        try:
            db_request_id = voice_generator_job.voice_request_service.create_voice_request(
                reference_audio_path=reference_path,
                text_script=text_script,
                language=language,
                metadata={
                    'original_filename': filename,
                    'file_size_mb': validation_result['file_size_mb'],
                    'duration_seconds': validation_result['duration'],
                    'sample_rate': validation_result['sample_rate']
                }
            )

            # Immediately trigger on-demand job processing for this specific request
            voice_generator_job.logger.info(f"Triggering immediate processing for request: {db_request_id}")
            try:
                # Make internal call to trigger on-demand job
                import requests
                response = requests.post(
                    'http://localhost:8094/run',
                    json={'specific_request_id': db_request_id},
                    timeout=5
                )
                if response.status_code == 200:
                    processing_message = 'Voice generation started immediately'
                    estimated_time = '30-120 seconds'
                else:
                    raise Exception(f"Job trigger failed: {response.status_code}")
            except Exception as job_error:
                voice_generator_job.logger.warning(f"Failed to start immediate processing: {job_error}")
                processing_message = 'Voice generation queued for next scheduled run'
                estimated_time = '1-5 minutes'

            return jsonify({
                'status': 'success',
                'request_id': db_request_id,
                'message': processing_message,
                'estimated_processing_time': estimated_time
            }), 201

        except Exception as e:
            # Remove uploaded file if database operation fails
            os.remove(reference_path)
            raise e

    except Exception as e:
        voice_generator_job.logger.error(f"Error submitting voice request: {e}")
        return jsonify({
            'status': 'error',
            'error': f'Failed to submit request: {str(e)}'
        }), 500


@app.route('/api/voice/status/<request_id>', methods=['GET'])
def get_voice_request_status(request_id):
    """Get status of a voice generation request"""
    try:
        request_data = voice_generator_job.voice_request_service.get_voice_request(request_id)

        if not request_data:
            return jsonify({
                'status': 'error',
                'error': 'Request not found'
            }), 404

        # Prepare response
        response_data = {
            'status': 'success',
            'request_id': request_data['request_id'],
            'request_status': request_data['status'],
            'created_at': request_data['created_at'].isoformat(),
            'updated_at': request_data['updated_at'].isoformat(),
            'text_script': request_data['text_script'],
            'language': request_data['language']
        }

        # Add progress information if available
        if request_data.get('progress_percentage') is not None:
            response_data['progress_percentage'] = request_data['progress_percentage']

        if request_data.get('progress_message'):
            response_data['progress_message'] = request_data['progress_message']

        # Add timestamps if available
        if request_data.get('started_at'):
            response_data['started_at'] = request_data['started_at'].isoformat()

        if request_data.get('completed_at'):
            response_data['completed_at'] = request_data['completed_at'].isoformat()

        # Add error message if failed
        if request_data['status'] == 'failed' and request_data.get('error_message'):
            response_data['error_message'] = request_data['error_message']

        # Add download info if completed
        if request_data['status'] == 'completed' and request_data.get('generated_audio_path'):
            response_data['download_available'] = True
            response_data['download_url'] = f'/api/voice/download/{request_id}'

            # Add metadata if available
            if request_data.get('metadata'):
                metadata = request_data['metadata']
                response_data['processing_time_seconds'] = metadata.get('processing_time_seconds')
                response_data['output_size_mb'] = metadata.get('output_size_mb')

        return jsonify(response_data), 200

    except Exception as e:
        voice_generator_job.logger.error(f"Error getting request status: {e}")
        return jsonify({
            'status': 'error',
            'error': f'Failed to get request status: {str(e)}'
        }), 500


@app.route('/api/voice/download/<request_id>', methods=['GET'])
def download_generated_voice(request_id):
    """Download generated voice file"""
    try:
        request_data = voice_generator_job.voice_request_service.get_voice_request(request_id)

        if not request_data:
            return jsonify({
                'status': 'error',
                'error': 'Request not found'
            }), 404

        if request_data['status'] != 'completed':
            return jsonify({
                'status': 'error',
                'error': f'Request is not completed. Current status: {request_data["status"]}'
            }), 400

        generated_audio_path = request_data.get('generated_audio_path')
        if not generated_audio_path or not os.path.exists(generated_audio_path):
            return jsonify({
                'status': 'error',
                'error': 'Generated audio file not found'
            }), 404

        # Get filename from metadata or generate one
        filename = request_data.get('metadata', {}).get('output_filename')
        if not filename:
            filename = f"voice_clone_{request_id}.wav"

        return send_file(
            generated_audio_path,
            as_attachment=True,
            download_name=filename,
            mimetype='audio/wav'
        )

    except Exception as e:
        voice_generator_job.logger.error(f"Error downloading generated voice: {e}")
        return jsonify({
            'status': 'error',
            'error': f'Failed to download file: {str(e)}'
        }), 500


@app.route('/api/voice/requests', methods=['GET'])
def list_voice_requests():
    """List voice generation requests with optional status filter"""
    try:
        # Get query parameters
        status = request.args.get('status')
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 requests

        # Get requests
        requests = voice_generator_job.voice_request_service.get_request_history(
            limit=limit,
            status=status
        )

        # Format response
        formatted_requests = []
        for req in requests:
            formatted_req = {
                'request_id': req['request_id'],
                'status': req['status'],
                'created_at': req['created_at'].isoformat(),
                'updated_at': req['updated_at'].isoformat(),
                'language': req['language'],
                'text_length': len(req['text_script'])
            }

            # Add completion info if available
            if req.get('completed_at'):
                formatted_req['completed_at'] = req['completed_at'].isoformat()

            # Add error message if failed
            if req['status'] == 'failed' and req.get('error_message'):
                formatted_req['error_message'] = req['error_message']

            # Add processing time if available
            if req.get('metadata', {}).get('processing_time_seconds'):
                formatted_req['processing_time_seconds'] = req['metadata']['processing_time_seconds']

            formatted_requests.append(formatted_req)

        return jsonify({
            'status': 'success',
            'requests': formatted_requests,
            'count': len(formatted_requests),
            'filter': {'status': status, 'limit': limit}
        }), 200

    except Exception as e:
        voice_generator_job.logger.error(f"Error listing requests: {e}")
        return jsonify({
            'status': 'error',
            'error': f'Failed to list requests: {str(e)}'
        }), 500


@app.route('/api/voice/stats', methods=['GET'])
def get_voice_stats():
    """Get voice generation statistics"""
    try:
        stats = voice_generator_job.voice_request_service.get_request_stats()
        engine_info = voice_generator_job.voice_generator_service.get_engine_info()

        return jsonify({
            'status': 'success',
            'request_stats': stats,
            'engine_info': engine_info,
            'service_info': {
                'max_file_size_mb': Config.MAX_FILE_SIZE_MB,
                'allowed_extensions': list(Config.ALLOWED_AUDIO_EXTENSIONS),
                'default_language': Config.DEFAULT_LANGUAGE,
                'max_parallel_tasks': voice_generator_job.max_parallel_tasks
            }
        }), 200

    except Exception as e:
        voice_generator_job.logger.error(f"Error getting stats: {e}")
        return jsonify({
            'status': 'error',
            'error': f'Failed to get stats: {str(e)}'
        }), 500

if __name__ == '__main__':
    try:
        # Validate configuration
        Config.validate_config()
        
        # Start the job service
        voice_generator_job.run_flask_app()
        
    except KeyboardInterrupt:
        voice_generator_job.logger.info("Voice generator job stopped by user")
    except Exception as e:
        voice_generator_job.logger.error(f"Voice generator job failed to start: {e}")
        sys.exit(1)
