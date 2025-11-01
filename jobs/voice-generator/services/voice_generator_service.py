"""
Voice Generator Service using XTTS Voice Cloning Service

This service integrates with the voice-cloning-service running on port 5003,
providing stable voice cloning through the XTTS API wrapper.
"""

import os
import time
import uuid
import requests
import threading
from datetime import datetime
from typing import Dict, Optional, Any


class VoiceGeneratorService:
    """
    Service for voice cloning using XTTS Voice Cloning Service
    
    This integrates with the voice-cloning-service container running on port 5003
    to provide high-quality voice cloning capabilities.
    """

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        # Voice cloning service configuration
        self.voice_service_url = getattr(config, 'VOICE_SERVICE_URL', 'http://voice-cloning-service:5003')
        self.voice_service_timeout = getattr(config, 'VOICE_SERVICE_TIMEOUT', 600)  # 10 minutes
        
        # Thread safety
        self._generation_lock = threading.Lock()
        
        # Configuration
        self.max_text_length = getattr(config, 'MAX_TEXT_LENGTH', 2000)  # XTTS can handle longer text

        # Chunking configuration
        self.chunking_threshold = getattr(config, 'CHUNKING_THRESHOLD', 300)  # Use chunking for texts > 300 chars
        self.max_chunk_length = getattr(config, 'MAX_CHUNK_LENGTH', 200)  # Max chars per chunk
        self.max_workers = getattr(config, 'MAX_WORKERS', 3)  # Parallel workers for chunks
        self.enable_chunking = getattr(config, 'ENABLE_CHUNKING', True)  # Enable chunking feature

        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'pl': 'Polish',
            'tr': 'Turkish',
            'ru': 'Russian',
            'nl': 'Dutch',
            'cs': 'Czech',
            'ar': 'Arabic',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'hu': 'Hungarian',
            'ko': 'Korean',
            'hi': 'Hindi'
        }
        
        self.logger.info("VoiceGeneratorService initialized with XTTS Voice Cloning Service")
        self.logger.info(f"Voice service URL: {self.voice_service_url}")
        self.logger.info(f"Chunking enabled: {self.enable_chunking}")
        self.logger.info(f"Chunking threshold: {self.chunking_threshold} characters")
        self.logger.info(f"Max chunk length: {self.max_chunk_length} characters")
        self.logger.info(f"Max parallel workers: {self.max_workers}")

        # Test connection to voice service
        self._test_voice_service_connection()

    def _test_voice_service_connection(self):
        """Test connection to the voice cloning service"""
        try:
            response = requests.get(f"{self.voice_service_url}/health", timeout=10)
            if response.status_code == 200:
                self.logger.info("✅ Successfully connected to voice cloning service")
                return True
            else:
                self.logger.warning(f"⚠️ Voice service health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to voice cloning service: {e}")
            return False

    def generate_voice_clone(self, reference_audio_path, text_script,
                           language="en", request_id=None, voice_request_service=None):
        """
        Generate voice clone using XTTS Voice Cloning Service

        Args:
            reference_audio_path: Path to reference voice audio
            text_script: Text to synthesize
            language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh, ja, hu, ko, hi)
            request_id: Request ID for progress tracking
            voice_request_service: Service for progress updates

        Returns:
            Dict with generation results
        """
        start_time = time.time()

        try:
            with self._generation_lock:
                self.logger.info(f"Starting XTTS voice generation for request {request_id}")
                self.logger.info(f"Text: {text_script[:100]}...")
                self.logger.info(f"Reference audio: {reference_audio_path}")
                self.logger.info(f"Language: {language}")

                # Generate output path
                if not request_id:
                    request_id = str(uuid.uuid4())

                output_filename = f"voice_clone_{request_id}.wav"
                output_path = os.path.join(getattr(self.config, 'DATA_DIR', 'data'), 'generated_audio', output_filename)

                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                self.logger.info(f"Output path: {output_path}")

                # Validate inputs
                if not text_script or not text_script.strip():
                    return {
                        'success': False,
                        'error': "Text script is empty",
                        'processing_time_seconds': time.time() - start_time,
                        'request_id': request_id
                    }

                if not os.path.exists(reference_audio_path):
                    return {
                        'success': False,
                        'error': f"Reference audio file not found: {reference_audio_path}",
                        'processing_time_seconds': time.time() - start_time,
                        'request_id': request_id
                    }

                # Truncate text if too long
                if len(text_script) > self.max_text_length:
                    text_script = text_script[:self.max_text_length]
                    self.logger.warning(f"Text truncated to {self.max_text_length} characters")

                # Validate language
                if language not in self.supported_languages:
                    language = "en"  # Default to English
                    self.logger.warning(f"Unsupported language, defaulting to English")

                # Update progress: Starting
                if voice_request_service and request_id:
                    voice_request_service.update_request_progress(
                        request_id, 10, "Starting XTTS voice generation..."
                    )

                # Determine whether to use chunked processing
                use_chunking = (
                    self.enable_chunking and
                    len(text_script) > self.chunking_threshold
                )

                if use_chunking:
                    self.logger.info(f"Using chunked processing for text length: {len(text_script)} characters")
                    return self._generate_voice_chunked(
                        reference_audio_path, text_script, language,
                        request_id, voice_request_service, output_path, output_filename
                    )
                else:
                    self.logger.info(f"Using regular processing for text length: {len(text_script)} characters")
                    return self._generate_voice_regular(
                        reference_audio_path, text_script, language,
                        request_id, voice_request_service, output_path, output_filename
                    )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Voice generation error: {str(e)}"
            self.logger.error(error_msg)

            if voice_request_service and request_id:
                voice_request_service.update_request_progress(
                    request_id, 0, f"Generation failed: {str(e)}"
                )

            return {
                'success': False,
                'error': error_msg,
                'processing_time_seconds': processing_time,
                'request_id': request_id
            }

    def _generate_voice_regular(self, reference_audio_path, text_script, language,
                               request_id, voice_request_service, output_path, output_filename):
        """Generate voice using regular (non-chunked) processing"""
        start_time = time.time()

        try:
            with open(reference_audio_path, 'rb') as audio_file:
                files = {
                    'speaker_wav': audio_file
                }
                data = {
                    'text': text_script,
                    'language': language
                }

                # Update progress: Uploading
                if voice_request_service and request_id:
                    voice_request_service.update_request_progress(
                        request_id, 20, "Uploading reference audio and text..."
                    )

                self.logger.info("Sending request to voice cloning service (regular)...")
                response = requests.post(
                    f"{self.voice_service_url}/clone_voice",
                    files=files,
                    data=data,
                    timeout=self.voice_service_timeout
                )

                # Update progress: Processing
                if voice_request_service and request_id:
                    voice_request_service.update_request_progress(
                        request_id, 50, "Voice cloning in progress..."
                    )

                if response.status_code == 200:
                    # Save the generated audio
                    with open(output_path, 'wb') as output_file:
                        output_file.write(response.content)

                    # Update progress: Completed
                    if voice_request_service and request_id:
                        voice_request_service.update_request_progress(
                            request_id, 100, "Voice generation completed successfully"
                        )

                    processing_time = time.time() - start_time
                    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)

                    self.logger.info(f"Voice generation completed successfully: {output_path}")
                    self.logger.info(f"Processing time: {processing_time:.2f} seconds")
                    self.logger.info(f"Output file size: {file_size_mb:.2f} MB")

                    return {
                        'success': True,
                        'message': "Voice generation completed successfully",
                        'generated_audio_path': output_path,
                        'output_filename': output_filename,
                        'processing_time_seconds': processing_time,
                        'output_size_mb': round(file_size_mb, 2),
                        'request_id': request_id
                    }
                else:
                    error_msg = f"Voice service returned error: {response.status_code} - {response.text}"
                    self.logger.error(error_msg)

                    if voice_request_service and request_id:
                        voice_request_service.update_request_progress(
                            request_id, 0, f"Generation failed: {response.status_code}"
                        )

                    return {
                        'success': False,
                        'error': error_msg,
                        'processing_time_seconds': time.time() - start_time,
                        'request_id': request_id
                    }

        except requests.exceptions.Timeout:
            error_msg = "Voice generation timed out"
            self.logger.error(error_msg)

            if voice_request_service and request_id:
                voice_request_service.update_request_progress(
                    request_id, 0, "Generation timed out"
                )

            return {
                'success': False,
                'error': error_msg,
                'processing_time_seconds': time.time() - start_time,
                'request_id': request_id
            }

    def _generate_voice_chunked(self, reference_audio_path, text_script, language,
                               request_id, voice_request_service, output_path, output_filename):
        """Generate voice using chunked processing for faster generation of long texts"""
        start_time = time.time()

        try:
            with open(reference_audio_path, 'rb') as audio_file:
                files = {
                    'speaker_wav': audio_file
                }
                data = {
                    'text': text_script,
                    'language': language,
                    'max_chunk_length': self.max_chunk_length,
                    'max_workers': self.max_workers,
                    'enable_chunking': True
                }

                # Update progress: Uploading
                if voice_request_service and request_id:
                    voice_request_service.update_request_progress(
                        request_id, 20, "Uploading reference audio and text for chunked processing..."
                    )

                self.logger.info("Sending request to voice cloning service (chunked)...")
                self.logger.info(f"Chunk settings: max_length={self.max_chunk_length}, max_workers={self.max_workers}")

                response = requests.post(
                    f"{self.voice_service_url}/clone_voice_chunked",
                    files=files,
                    data=data,
                    timeout=self.voice_service_timeout
                )

                # Update progress: Processing
                if voice_request_service and request_id:
                    voice_request_service.update_request_progress(
                        request_id, 50, "Chunked voice cloning in progress..."
                    )

                if response.status_code == 200:
                    # Save the generated audio
                    with open(output_path, 'wb') as output_file:
                        output_file.write(response.content)

                    # Update progress: Completed
                    if voice_request_service and request_id:
                        voice_request_service.update_request_progress(
                            request_id, 100, "Chunked voice generation completed successfully"
                        )

                    processing_time = time.time() - start_time
                    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)

                    self.logger.info(f"Chunked voice generation completed successfully: {output_path}")
                    self.logger.info(f"Processing time: {processing_time:.2f} seconds")
                    self.logger.info(f"Output file size: {file_size_mb:.2f} MB")

                    return {
                        'success': True,
                        'message': "Chunked voice generation completed successfully",
                        'generated_audio_path': output_path,
                        'output_filename': output_filename,
                        'processing_time_seconds': processing_time,
                        'output_size_mb': round(file_size_mb, 2),
                        'request_id': request_id,
                        'processing_method': 'chunked'
                    }
                else:
                    error_msg = f"Chunked voice service returned error: {response.status_code} - {response.text}"
                    self.logger.error(error_msg)

                    if voice_request_service and request_id:
                        voice_request_service.update_request_progress(
                            request_id, 0, f"Chunked generation failed: {response.status_code}"
                        )

                    return {
                        'success': False,
                        'error': error_msg,
                        'processing_time_seconds': time.time() - start_time,
                        'request_id': request_id
                    }

        except requests.exceptions.Timeout:
            error_msg = "Chunked voice generation timed out"
            self.logger.error(error_msg)

            if voice_request_service and request_id:
                voice_request_service.update_request_progress(
                    request_id, 0, "Chunked generation timed out"
                )

            return {
                'success': False,
                'error': error_msg,
                'processing_time_seconds': time.time() - start_time,
                'request_id': request_id
            }

    def get_engine_info(self):
        """Get information about the voice generation service"""
        try:
            # Try to get info from voice service
            response = requests.get(f"{self.voice_service_url}/health", timeout=10)
            service_status = "connected" if response.status_code == 200 else "disconnected"
        except:
            service_status = "disconnected"

        return {
            "service": "XTTS Voice Cloning Service with Chunking",
            "version": "2.1",
            "status": service_status,
            "description": "High-quality voice cloning using XTTS technology with chunked processing for faster generation",
            "service_url": self.voice_service_url,
            "supported_languages": self.supported_languages,
            "max_text_length": self.max_text_length,
            "timeout_seconds": self.voice_service_timeout,
            "chunking_enabled": self.enable_chunking,
            "chunking_threshold": self.chunking_threshold,
            "max_chunk_length": self.max_chunk_length,
            "max_workers": self.max_workers
        }

    def cleanup_old_files(self, max_age_days=7):
        """Clean up old generated audio files"""
        try:
            data_dir = getattr(self.config, 'DATA_DIR', 'data')
            generated_audio_dir = os.path.join(data_dir, 'generated_audio')
            
            if not os.path.exists(generated_audio_dir):
                return
                
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            files_cleaned = 0
            for filename in os.listdir(generated_audio_dir):
                file_path = os.path.join(generated_audio_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        files_cleaned += 1
                        self.logger.info(f"Cleaned up old file: {filename}")
            
            self.logger.info(f"Cleaned up {files_cleaned} old audio files")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old files: {e}")

    def validate_audio_file(self, audio_path):
        """Validate reference audio file"""
        try:
            if not os.path.exists(audio_path):
                return {
                    'valid': False,
                    'error': "Audio file does not exist"
                }

            if os.path.getsize(audio_path) == 0:
                return {
                    'valid': False,
                    'error': "Audio file is empty"
                }

            # Check file size (max 50MB)
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            if file_size_mb > 50:
                return {
                    'valid': False,
                    'error': f"Audio file too large: {file_size_mb:.1f}MB (max 50MB)"
                }

            # Try to load audio to validate format
            try:
                import librosa
                audio, sr = librosa.load(audio_path, sr=None)

                if len(audio) == 0:
                    return {
                        'valid': False,
                        'error': "Audio file contains no audio data"
                    }

                if len(audio) < sr * 0.5:  # Less than 0.5 seconds
                    return {
                        'valid': False,
                        'error': "Audio file is too short (minimum 0.5 seconds)"
                    }

                # Calculate duration for metadata
                duration_seconds = len(audio) / sr

                return {
                    'valid': True,
                    'file_size_mb': round(file_size_mb, 2),
                    'duration': round(duration_seconds, 2),
                    'sample_rate': sr
                }

            except ImportError:
                # If librosa is not available, do basic validation
                return {
                    'valid': True,
                    'file_size_mb': round(file_size_mb, 2),
                    'duration': None,
                    'sample_rate': None
                }

        except Exception as e:
            return {
                'valid': False,
                'error': f"Invalid audio file: {str(e)}"
            }

    def get_supported_languages(self):
        """Get list of supported languages"""
        return self.supported_languages

    def health_check(self):
        """Check service health"""
        try:
            voice_service_healthy = self._test_voice_service_connection()
            
            return {
                "status": "healthy" if voice_service_healthy else "degraded",
                "service": "XTTS Voice Cloning Integration",
                "voice_service_connected": voice_service_healthy,
                "supported_languages": len(self.supported_languages),
                "service_url": self.voice_service_url
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
