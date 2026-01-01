"""
Asset Management Routes
REST API endpoints for asset operations

NOTE: This service is called by api-server (API Gateway pattern).
Authentication is handled by api-server, which passes customer_id and user_id in headers.
"""
import logging
import uuid
import os
import magic
from typing import Optional
from datetime import timedelta
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException, Query, Header
from fastapi.responses import StreamingResponse, Response
from io import BytesIO

from models.asset import (
    Asset, AssetCreate, AssetUpdate, AssetResponse, AssetListResponse,
    UploadResponse, AssetType, StorageInfo, AssetMetadata, Dimensions
)
from services.storage_service import storage_service
from services.database_service import db_service
from config.settings import settings
from utils.file_utils import get_file_info, validate_file_type

logger = logging.getLogger(__name__)

router = APIRouter()


def get_user_context(
    x_customer_id: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> dict:
    """
    Get user context from headers (set by api-server)

    Args:
        x_customer_id: Customer ID from header
        x_user_id: User ID from header

    Returns:
        Dict with customer_id and user_id

    Raises:
        HTTPException: If headers are missing
    """
    if not x_customer_id or not x_user_id:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Customer-Id or X-User-Id headers"
        )

    return {
        "customer_id": x_customer_id,
        "user_id": x_user_id
    }


@router.post("/upload", response_model=UploadResponse)
async def upload_asset(
    file: UploadFile = File(...),
    asset_type: str = Form(...),
    name: Optional[str] = Form(None),
    folder: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """
    Upload an asset file
    
    - **file**: File to upload
    - **asset_type**: Type of asset (audio, image, video, document)
    - **name**: Asset name (optional, defaults to filename)
    - **folder**: Folder/category (optional)
    - **title**: Display title (optional)
    - **description**: Description (optional)
    - **tags**: Comma-separated tags (optional)
    """
    try:
        # Validate asset type
        try:
            asset_type_enum = AssetType(asset_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Check file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        # Detect MIME type
        mime_type = magic.from_buffer(file_content, mime=True)
        
        # Validate file type
        if not validate_file_type(mime_type, asset_type_enum):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type {mime_type} for asset type {asset_type}"
            )
        
        # Generate asset ID and storage key
        asset_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        storage_key = f"{x_customer_id}/{x_user_id}/{asset_id}{file_extension}"
        
        # Determine bucket
        bucket_map = {
            AssetType.AUDIO: settings.AUDIO_BUCKET,
            AssetType.IMAGE: settings.IMAGE_BUCKET,
            AssetType.VIDEO: settings.VIDEO_BUCKET,
            AssetType.DOCUMENT: settings.DOCUMENT_BUCKET
        }
        bucket = bucket_map[asset_type_enum]
        
        # Upload to MinIO
        file_stream = BytesIO(file_content)
        storage_url = storage_service.upload_file(
            bucket=bucket,
            object_name=storage_key,
            file_data=file_stream,
            length=file_size,
            content_type=mime_type
        )
        
        # Get file info (duration, dimensions, etc.)
        file_info = get_file_info(file_content, mime_type, asset_type_enum)
        
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
        
        # Create asset document
        asset_data = {
            "asset_id": asset_id,
            "customer_id": x_customer_id,
            "user_id": x_user_id,
            "type": asset_type,
            "name": name or file.filename,
            "original_filename": file.filename,
            "mime_type": mime_type,
            "size": file_size,
            "duration": file_info.get("duration"),
            "dimensions": file_info.get("dimensions"),
            "storage": {
                "bucket": bucket,
                "key": storage_key,
                "url": storage_url
            },
            "metadata": {
                "title": title,
                "description": description,
                "tags": tag_list,
                "folder": folder,
                "custom": {}
            },
            "versions": []
        }
        
        # Save to database
        db_service.create_asset(asset_data)
        
        logger.info(f"Asset uploaded successfully: {asset_id}")
        
        return UploadResponse(
            success=True,
            asset_id=asset_id,
            url=storage_url,
            message="Asset uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Get asset metadata by ID"""
    try:
        # CRITICAL: Pass customer_id for multi-tenancy enforcement
        asset = db_service.get_asset(asset_id, customer_id=x_customer_id)

        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        return AssetResponse(
            success=True,
            asset=Asset(**asset),
            message="Asset retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: str,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Download asset file"""
    try:
        # CRITICAL: Pass customer_id for multi-tenancy enforcement
        asset = db_service.get_asset(asset_id, customer_id=x_customer_id)

        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Download from MinIO
        file_data = storage_service.download_file(
            bucket=asset["storage"]["bucket"],
            object_name=asset["storage"]["key"]
        )

        # Return as streaming response
        return StreamingResponse(
            BytesIO(file_data),
            media_type=asset["mime_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{asset["original_filename"]}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_id}/url")
async def get_asset_url(
    asset_id: str,
    expires_hours: int = Query(default=1, ge=1, le=24),
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Get pre-signed URL for asset"""
    try:
        # CRITICAL: Pass customer_id for multi-tenancy enforcement
        asset = db_service.get_asset(asset_id, customer_id=x_customer_id)

        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Generate pre-signed URL
        url = storage_service.get_presigned_url(
            bucket=asset["storage"]["bucket"],
            object_name=asset["storage"]["key"],
            expires=timedelta(hours=expires_hours)
        )

        return {
            "success": True,
            "url": url,
            "expires_in_hours": expires_hours
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    permanent: bool = Query(default=False),
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Delete asset"""
    try:
        # CRITICAL: Pass customer_id for multi-tenancy enforcement
        asset = db_service.get_asset(asset_id, customer_id=x_customer_id)

        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Delete from database (soft or hard) with multi-tenancy
        db_service.delete_asset(
            asset_id,
            soft_delete=not permanent,
            customer_id=x_customer_id
        )

        # If permanent, also delete from storage
        if permanent:
            storage_service.delete_file(
                bucket=asset["storage"]["bucket"],
                object_name=asset["storage"]["key"]
            )

        return {
            "success": True,
            "message": "Asset deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=AssetListResponse)
async def list_assets(
    asset_type: Optional[str] = Query(None),
    folder: Optional[str] = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """List assets with filters"""
    try:
        skip = (page - 1) * page_size

        assets = db_service.list_assets(
            customer_id=x_customer_id,
            user_id=x_user_id,
            asset_type=asset_type,
            folder=folder,
            skip=skip,
            limit=page_size
        )

        # Get total count (simplified - in production, use a separate count query)
        total = len(assets)

        return AssetListResponse(
            success=True,
            assets=[Asset(**asset) for asset in assets],
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

