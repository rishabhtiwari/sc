"""
Audio Library Service
Handles all heavy lifting for audio library operations including:
- Downloading audio from audio-generation service
- Uploading to MinIO
- Managing metadata in MongoDB
- Cleanup of temporary files
"""
import logging
import os
import requests
from io import BytesIO
from typing import Dict, Any, Optional
from datetime import timedelta
from bson import Int64

from services.storage_service import storage_service
from services.database_service import db_service

logger = logging.getLogger(__name__)


class AudioLibraryService:
    """Service for managing audio library operations"""
    
    def __init__(self):
        """Initialize audio library service"""
        self.audio_gen_url = os.getenv(
            'AUDIO_GENERATION_SERVICE_URL',
            'http://audio-generation-factory:3000'
        )
        self.cleanup_enabled = os.getenv(
            'CLEANUP_TEMP_AUDIO',
            'true'
        ).lower() == 'true'
        self.bucket_name = "audio-assets"
    
    def _construct_full_url(self, audio_url: str) -> str:
        """
        Construct full URL from relative or absolute URL
        
        Args:
            audio_url: Audio URL (relative or absolute)
            
        Returns:
            Full URL to audio file
        """
        if audio_url.startswith('/'):
            # Relative URL - construct full URL
            return f"{self.audio_gen_url}{audio_url}"
        return audio_url
    
    def _download_audio(self, audio_url: str) -> tuple[bytes, int]:
        """
        Download audio file from audio-generation service
        
        Args:
            audio_url: URL to audio file
            
        Returns:
            Tuple of (audio_data, file_size)
            
        Raises:
            Exception: If download fails
        """
        full_url = self._construct_full_url(audio_url)
        logger.info(f"Downloading audio from: {full_url}")
        
        try:
            response = requests.get(full_url, timeout=30)
            response.raise_for_status()
            audio_data = response.content
            file_size = len(audio_data)
            logger.info(f"Downloaded audio file: {file_size} bytes")
            return audio_data, file_size
        except requests.RequestException as e:
            logger.error(f"Failed to download audio from {full_url}: {e}")
            raise Exception(f"Failed to download audio file: {str(e)}")
    
    def _upload_to_minio(
        self,
        audio_data: bytes,
        file_size: int,
        object_key: str,
        metadata: Dict[str, str]
    ) -> str:
        """
        Upload audio file to MinIO
        
        Args:
            audio_data: Audio file bytes
            file_size: Size of audio file
            object_key: MinIO object key
            metadata: Metadata to attach to object
            
        Returns:
            Presigned URL for accessing the file
            
        Raises:
            Exception: If upload fails
        """
        logger.info(f"Uploading to MinIO: {self.bucket_name}/{object_key}")
        
        try:
            storage_service.upload_file(
                bucket=self.bucket_name,
                object_name=object_key,
                file_data=BytesIO(audio_data),
                length=file_size,
                content_type="audio/wav",
                metadata=metadata
            )
            logger.info(f"Successfully uploaded to MinIO: {object_key}")
        except Exception as e:
            logger.error(f"Failed to upload to MinIO: {e}")
            raise Exception(f"Failed to upload to storage: {str(e)}")
        
        # Generate presigned URL (valid for 7 days)
        try:
            presigned_url = storage_service.get_presigned_url(
                bucket=self.bucket_name,
                object_name=object_key,
                expires=timedelta(days=7)
            )
            return presigned_url
        except Exception as e:
            logger.warning(f"Failed to generate presigned URL: {e}")
            return f"minio://{self.bucket_name}/{object_key}"
    
    def _cleanup_temp_file(self, audio_url: str) -> None:
        """
        Clean up temporary file from audio-generation service

        Args:
            audio_url: Original audio URL
        """
        if not self.cleanup_enabled or '/temp/' not in audio_url:
            return

        try:
            # Extract filename from URL
            filename = audio_url.split('/temp/')[-1]
            cleanup_url = f"{self.audio_gen_url}/api/cleanup/temp/{filename}"

            # Send cleanup request (fire and forget)
            response = requests.delete(cleanup_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Cleanup successful for: {filename}")
            else:
                logger.warning(
                    f"Cleanup request returned {response.status_code}"
                )
        except Exception as e:
            # Don't fail the request if cleanup fails
            logger.warning(f"Failed to cleanup temp file: {e}")

    def save_audio_to_library(
        self,
        asset_id: str,
        customer_id: str,
        user_id: str,
        audio_url: str,
        text: str,
        duration: float,
        voice: str,
        voice_name: Optional[str],
        language: str,
        speed: float,
        model: str,
        folder: Optional[str],
        tags: list
    ) -> Dict[str, Any]:
        """
        Save audio to library with full processing pipeline:
        1. Download from audio-generation service
        2. Upload to MinIO
        3. Save metadata to MongoDB
        4. Cleanup temp file

        Args:
            asset_id: Unique asset ID
            customer_id: Customer ID
            user_id: User ID
            audio_url: URL to audio file in audio-generation service
            text: Text that was converted to speech
            duration: Audio duration in seconds
            voice: Voice ID used
            voice_name: Human-readable voice name
            language: Language code
            speed: Speech speed
            model: TTS model used
            folder: Optional folder for organization
            tags: List of tags

        Returns:
            Dict with asset information

        Raises:
            Exception: If any step fails
        """
        logger.info(
            f"Saving audio to library: asset_id={asset_id}, "
            f"customer={customer_id}, user={user_id}"
        )

        # Step 1: Download audio from audio-generation service
        audio_data, file_size = self._download_audio(audio_url)

        # Step 2: Generate MinIO object key
        # Format: {customer_id}/{user_id}/audio/{asset_id}.wav
        object_key = f"{customer_id}/{user_id}/audio/{asset_id}.wav"

        # Step 3: Upload to MinIO
        presigned_url = self._upload_to_minio(
            audio_data=audio_data,
            file_size=file_size,
            object_key=object_key,
            metadata={
                "customer_id": customer_id,
                "user_id": user_id,
                "asset_id": asset_id,
                "voice": voice,
                "model": model,
                "language": language
            }
        )

        # Step 4: Create audio library metadata (flat schema for news.audio_library)
        audio_library_data = {
            "audio_id": asset_id,
            "customer_id": customer_id,
            "user_id": user_id,
            "name": f"Audio - {text[:50]}..." if len(text) > 50 else f"Audio - {text}",
            "type": "voiceover",  # TTS generated audio
            "source": "tts",  # Text-to-speech source
            "url": presigned_url,  # Flat field, not nested
            "duration": duration,
            "format": "wav",
            "size": Int64(file_size),  # Convert to BSON long for MongoDB
            "generation_config": {
                "provider": "kokoro",  # Default provider
                "model": model,
                "voice": voice,
                "language": language,  # Add language for cache matching
                "text": text,
                "settings": {
                    "speed": speed
                }
            },
            "tags": tags if tags else [],
            "folder": folder if folder else "",  # Empty string instead of None
            "is_deleted": False
        }

        # Step 5: Save to database (news.audio_library collection)
        db_service.create_audio_library_entry(audio_library_data)
        logger.info(f"Audio metadata saved to audio_library: {asset_id}")

        # Step 6: Cleanup temp file (async, non-blocking)
        self._cleanup_temp_file(audio_url)

        return {
            "asset_id": asset_id,
            "storage": {
                "bucket": self.bucket_name,
                "key": object_key,
                "size": file_size,
                "url": presigned_url
            }
        }


# Global audio library service instance
audio_library_service = AudioLibraryService()

