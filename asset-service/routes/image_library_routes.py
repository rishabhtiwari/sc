"""
Image Library Routes
Endpoints for image library management

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


class SaveImageRequest(BaseModel):
    """Request to save image to library"""
    name: str
    folder: Optional[str] = None
    tags: List[str] = []


@router.post("/library")
async def save_to_library(
    file: UploadFile = File(...),
    name: str = Query(...),
    folder: Optional[str] = Query(None),
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """
    Save image to library
    
    Uploads image to MinIO and saves metadata to MongoDB
    """
    try:
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Read file data
        file_data = await file.read()
        file_size = len(file_data)
        
        # Determine file extension
        filename = file.filename or "image.png"
        ext = filename.split('.')[-1] if '.' in filename else 'png'
        
        # Upload to MinIO
        bucket_name = "image-assets"
        object_key = f"{x_customer_id}/{x_user_id}/{image_id}.{ext}"
        
        storage_service.upload_file(
            bucket=bucket_name,
            object_name=object_key,
            file_data=BytesIO(file_data),
            length=file_size,
            content_type=file.content_type or "image/png",
            metadata={
                "customer_id": x_customer_id,
                "user_id": x_user_id,
                "image_id": image_id
            }
        )
        
        # Generate download URL
        url = f"/api/assets/download/{bucket_name}/{object_key}"
        
        # Save to MongoDB
        image_library_data = {
            "image_id": image_id,
            "customer_id": x_customer_id,
            "user_id": x_user_id,
            "name": name,
            "url": url,
            "format": ext,
            "size": file_size,
            "folder": folder or "",
            "tags": [],
            "is_deleted": False
        }
        
        db_service.create_image_library_entry(image_library_data)
        
        return {
            "success": True,
            "image": image_library_data
        }
        
    except Exception as e:
        logger.error(f"Error saving image to library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library")
async def get_library(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    folder: Optional[str] = Query(None),
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Get image library items"""
    try:
        skip = (page - 1) * page_size
        
        images = db_service.list_image_library(
            customer_id=x_customer_id,
            user_id=x_user_id,
            folder=folder,
            skip=skip,
            limit=page_size
        )
        
        return {
            "success": True,
            "images": images,
            "page": page,
            "page_size": page_size,
            "total": len(images)
        }
        
    except Exception as e:
        logger.error(f"Error getting image library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/library/{image_id}")
async def delete_from_library(
    image_id: str,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Delete image from library"""
    try:
        success = db_service.delete_image_library_entry(
            image_id=image_id,
            customer_id=x_customer_id,
            user_id=x_user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {
            "success": True,
            "message": "Image deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

