"""
Audio Library Routes
Migration-compatible endpoints for audio library management

NOTE: This service is called by api-server (API Gateway pattern).
Authentication is handled by api-server, which passes customer_id
and user_id in headers.
"""
import logging
import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Header, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from io import BytesIO
import subprocess

from services.database_service import db_service
from services.audio_library_service import audio_library_service
from services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SaveToLibraryRequest(BaseModel):
    """Request to save audio to library"""
    text: str
    audio_url: str = Field(..., validation_alias='audioUrl')
    duration: float = 0.0  # Will be calculated if not provided
    voice: str
    voice_name: Optional[str] = Field(None, validation_alias='voiceName')
    language: str = "en"  # Default to English
    speed: float = 1.0
    model: str = "kokoro"  # Default model
    folder: Optional[str] = None
    tags: List[str] = []


@router.post("/library")
async def save_to_library(
    request_data: SaveToLibraryRequest,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """
    Save audio to library

    This endpoint delegates all heavy lifting to AudioLibraryService:
    1. Downloads audio file from audio-generation service temp storage
    2. Uploads to MinIO for permanent storage
    3. Saves metadata to MongoDB
    4. Cleans up temp file from audio-generation service

    Migration-compatible endpoint from api-server
    """
    try:
        # Generate unique asset ID
        asset_id = str(uuid.uuid4())

        logger.info(
            f"Save to library request: asset_id={asset_id}, "
            f"customer={x_customer_id}, user={x_user_id}"
        )

        # Delegate all heavy lifting to the service
        result = audio_library_service.save_audio_to_library(
            asset_id=asset_id,
            customer_id=x_customer_id,
            user_id=x_user_id,
            audio_url=request_data.audio_url,
            text=request_data.text,
            duration=request_data.duration,
            voice=request_data.voice,
            voice_name=request_data.voice_name,
            language=request_data.language,
            speed=request_data.speed,
            model=request_data.model,
            folder=request_data.folder,
            tags=request_data.tags
        )

        logger.info(f"Audio saved to library successfully: {asset_id}")

        return {
            "success": True,
            "id": asset_id,
            "message": "Audio saved to library successfully",
            "storage": result["storage"]
        }

    except Exception as e:
        logger.error(f"Error saving to library: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/library/upload")
async def upload_audio_file(
    file: UploadFile = File(...),
    name: Optional[str] = Query(None),
    folder: Optional[str] = Query(None),
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """
    Upload audio file directly to library
    Similar to video/image library upload endpoints

    This endpoint:
    1. Accepts audio file upload (multipart/form-data)
    2. Extracts duration using ffprobe
    3. Uploads to MinIO
    4. Saves metadata to MongoDB
    """
    try:
        # Generate unique audio ID
        audio_id = str(uuid.uuid4())

        # Read file data
        file_data = await file.read()
        file_size = len(file_data)

        # Determine file extension
        filename = file.filename or "audio.wav"
        ext = filename.split('.')[-1] if '.' in filename else 'wav'

        # Extract duration using ffprobe
        duration = 0.0
        try:
            # Save to temp file for ffprobe
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name

            # Use ffprobe to get duration
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', temp_path],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                duration = float(result.stdout.strip())
                logger.info(f"Extracted duration: {duration}s")

            # Clean up temp file
            import os
            os.unlink(temp_path)
        except Exception as e:
            logger.warning(f"Failed to extract duration: {e}")
            duration = 0.0

        # Upload to MinIO
        bucket_name = "audio-assets"
        object_key = f"{x_customer_id}/{x_user_id}/audio/{audio_id}.{ext}"

        storage_service.upload_file(
            bucket=bucket_name,
            object_name=object_key,
            file_data=BytesIO(file_data),
            length=file_size,
            content_type=file.content_type or "audio/wav",
            metadata={
                "customer_id": x_customer_id,
                "user_id": x_user_id,
                "audio_id": audio_id
            }
        )

        logger.info(f"Audio uploaded to MinIO: {bucket_name}/{object_key}")

        # Generate URL for frontend (needed before creating the document)
        url = f"/api/assets/download/audio-assets/{object_key}"

        # Save metadata to MongoDB with flat schema matching audio_library collection
        from bson import Int64
        audio_doc = {
            "audio_id": audio_id,
            "customer_id": x_customer_id,
            "user_id": x_user_id,
            "name": name or filename,  # Required top-level field
            "type": "uploaded",  # Required top-level field
            "source": "upload",  # Required top-level field
            "url": url,  # Required top-level field (flat, not nested)
            "duration": duration,
            "format": ext,
            "size": Int64(file_size),  # Convert to BSON long for MongoDB
            "storage": {
                "bucket": bucket_name,
                "object_key": object_key,
                "file_size": file_size
            },
            "generation_config": {
                "text": name or filename,  # Use name as text for uploaded files
                "voice": "uploaded",
                "voice_name": "Uploaded Audio",
                "model": "uploaded",
                "language": "en",
                "speed": 1.0,
                "duration": duration,
                "folder": folder or "",
                "tags": []
            },
            "folder": folder or "",  # Top-level folder field
            "tags": [],  # Top-level tags field
            "is_deleted": False
        }

        db_service.create_audio_library_entry(audio_doc)
        logger.info(f"Audio metadata saved to MongoDB: {audio_id}")

        return {
            "success": True,
            "audio": {
                "audio_id": audio_id,
                "name": name or filename,
                "url": url,
                "duration": duration,
                "type": "uploaded"
            },
            "message": "Audio uploaded successfully"
        }

    except Exception as e:
        logger.error(f"Error uploading audio file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library")
async def get_library(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    folder: Optional[str] = Query(None),
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Get audio library items"""
    try:
        skip = (page - 1) * page_size

        # Use audio_library collection from news database
        audios = db_service.list_audio_library(
            customer_id=x_customer_id,
            user_id=x_user_id,
            folder=folder,
            skip=skip,
            limit=page_size
        )

        # Convert to API response format
        library_items = []
        for audio in audios:
            gen_config = audio.get("generation_config", {})
            # Generate a name from text or use a default
            text = gen_config.get("text", "")
            name = text[:50] + "..." if len(text) > 50 else text or "Untitled Audio"

            library_items.append({
                "id": audio["audio_id"],
                "audio_id": audio["audio_id"],  # Include both for compatibility
                "customer_id": audio["customer_id"],
                "user_id": audio["user_id"],
                "name": name,  # Add name field for frontend
                "text": text,
                "url": audio["url"],  # Frontend expects 'url' not 'audio_url'
                "audio_url": audio["url"],  # Keep for backward compatibility
                "duration": audio.get("duration", 0.0),
                "voice": gen_config.get("voice", ""),
                "voice_name": gen_config.get("voice", ""),
                "language": "en",  # Default, not stored in schema
                "speed": gen_config.get("settings", {}).get("speed", 1.0),
                "model": gen_config.get("model", ""),
                "folder": audio.get("folder", ""),
                "tags": audio.get("tags", []),
                "type": audio.get("type", "voiceover"),  # Add type field
                "generation_config": gen_config,  # Include full config for frontend
                "created_at": audio.get("created_at"),
                "status": "saved"
            })
        
        return {
            "success": True,
            "audio_files": library_items,  # Frontend expects 'audio_files' key
            "total": len(library_items),
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        logger.error(f"Error getting library: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/{audio_id}/url")
async def get_audio_url(
    audio_id: str,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Get presigned URL for a specific audio library item"""
    try:
        logger.info(f"Getting URL for audio_id={audio_id}, customer={x_customer_id}, user={x_user_id}")

        # Get audio from library
        audio = db_service.get_audio_by_id(
            audio_id=audio_id,
            customer_id=x_customer_id,
            user_id=x_user_id  # Include user_id for proper filtering
        )

        if not audio:
            logger.error(f"Audio not found: audio_id={audio_id}, customer={x_customer_id}")
            raise HTTPException(status_code=404, detail="Audio not found")

        logger.info(f"Found audio: {audio.get('audio_id')}, url={audio.get('url')}")

        # Return the presigned URL
        return {
            "success": True,
            "url": audio.get("url"),
            "audio_id": audio_id,
            "duration": audio.get("duration", 0.0)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audio URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/library/{audio_id}")
async def delete_from_library(
    audio_id: str,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Delete audio from library"""
    try:
        logger.info(f"Deleting audio from library: audio_id={audio_id}, customer={x_customer_id}, user={x_user_id}")

        # Get audio from audio_library collection (not assets collection)
        audio = db_service.get_audio_by_id(
            audio_id=audio_id,
            customer_id=x_customer_id,
            user_id=x_user_id
        )

        if not audio:
            logger.error(f"Audio not found: audio_id={audio_id}, customer={x_customer_id}, user={x_user_id}")
            raise HTTPException(status_code=404, detail="Audio not found")

        # Soft delete from audio_library collection
        db_service.delete_audio_library_entry(
            audio_id=audio_id,
            customer_id=x_customer_id,
            user_id=x_user_id
        )

        logger.info(f"Successfully deleted audio: {audio_id}")

        return {
            "success": True,
            "message": "Audio deleted from library"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting from library: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/{audio_id}/stream")
async def stream_audio(
    audio_id: str,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Stream audio file from library"""
    try:
        # Get audio metadata from database
        audio = db_service.get_audio_library_entry(audio_id)

        if not audio:
            raise HTTPException(status_code=404, detail="Audio not found")

        # Verify ownership
        if audio.get("customer_id") != x_customer_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Extract storage info
        bucket = "audio-assets"
        object_key = f"{audio['customer_id']}/{audio['user_id']}/audio/{audio_id}.wav"

        logger.info(f"Streaming audio: {audio_id} from {bucket}/{object_key}")

        # Download from MinIO
        audio_data = storage_service.download_file(
            bucket=bucket,
            object_name=object_key
        )

        # Return as streaming response
        return StreamingResponse(
            BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f'inline; filename="{audio_id}.wav"',
                "Accept-Ranges": "bytes"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
