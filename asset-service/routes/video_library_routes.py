"""
Video Library Routes
Endpoints for video library management

NOTE: This service is called by api-server (API Gateway pattern).
Authentication is handled by api-server, which passes customer_id
and user_id in headers.
"""
import logging
import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Header, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from io import BytesIO

from services.database_service import db_service
from services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SaveVideoRequest(BaseModel):
    """Request to save video to library"""
    name: str
    duration: float = 0.0
    folder: Optional[str] = None
    tags: List[str] = []


@router.post("/library")
async def save_to_library(
    file: UploadFile = File(...),
    name: str = Query(...),
    duration: float = Query(0.0),
    folder: Optional[str] = Query(None),
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """
    Save video to library
    
    Uploads video to MinIO and saves metadata to MongoDB
    """
    try:
        # Generate unique video ID
        video_id = str(uuid.uuid4())
        
        # Read file data
        file_data = await file.read()
        file_size = len(file_data)
        
        # Determine file extension
        filename = file.filename or "video.mp4"
        ext = filename.split('.')[-1] if '.' in filename else 'mp4'
        
        # Upload to MinIO
        bucket_name = "video-assets"
        object_key = f"{x_customer_id}/{x_user_id}/{video_id}.{ext}"
        
        storage_service.upload_file(
            bucket=bucket_name,
            object_name=object_key,
            file_data=BytesIO(file_data),
            length=file_size,
            content_type=file.content_type or "video/mp4",
            metadata={
                "customer_id": x_customer_id,
                "user_id": x_user_id,
                "video_id": video_id
            }
        )
        
        # Generate download URL
        url = f"/api/assets/download/{bucket_name}/{object_key}"
        
        # Save to MongoDB
        video_library_data = {
            "video_id": video_id,
            "customer_id": x_customer_id,
            "user_id": x_user_id,
            "name": name,
            "url": url,
            "duration": duration,
            "format": ext,
            "size": file_size,
            "folder": folder or "",
            "tags": [],
            "is_deleted": False
        }
        
        db_service.create_video_library_entry(video_library_data)
        
        return {
            "success": True,
            "video": video_library_data
        }
        
    except Exception as e:
        logger.error(f"Error saving video to library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library")
async def get_library(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    folder: Optional[str] = Query(None),
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Get video library items"""
    try:
        skip = (page - 1) * page_size
        
        videos = db_service.list_video_library(
            customer_id=x_customer_id,
            user_id=x_user_id,
            folder=folder,
            skip=skip,
            limit=page_size
        )
        
        return {
            "success": True,
            "videos": videos,
            "page": page,
            "page_size": page_size,
            "total": len(videos)
        }
        
    except Exception as e:
        logger.error(f"Error getting video library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/library/{video_id}")
async def delete_from_library(
    video_id: str,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Delete video from library"""
    try:
        success = db_service.delete_video_library_entry(
            video_id=video_id,
            customer_id=x_customer_id,
            user_id=x_user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return {
            "success": True,
            "message": "Video deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

