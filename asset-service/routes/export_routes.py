"""
Export Routes
API endpoints for project export functionality - Proxies to export-generator job service
"""
from fastapi import APIRouter, Header, HTTPException
from typing import Optional
import logging
import requests
from datetime import datetime
from models.export import (
    ExportRequest,
    ExportJobResponse,
    ExportStatusResponse,
    ExportFormat,
    ExportStatus
)
from config.settings import settings
from services.database_service import db_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["export"])


@router.post("/export", response_model=ExportJobResponse)
async def create_export(
    export_request: ExportRequest,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """
    Create a new export job

    This endpoint proxies the request to the export-generator job service.
    Use the returned export_job_id to poll for status.
    """
    try:
        # Forward request to export-generator service
        response = requests.post(
            f"{settings.EXPORT_GENERATOR_URL}/export",
            json={
                "project_id": export_request.project_id,
                "customer_id": x_customer_id,
                "user_id": x_user_id,
                "format": export_request.format.value,
                "settings": export_request.settings.dict()
            },
            timeout=30
        )

        if response.status_code != 202:
            logger.error(f"Export generator returned error: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("error", "Failed to create export job")
            )

        result = response.json()

        return ExportJobResponse(
            success=result.get("success", True),
            export_job_id=result.get("export_job_id"),
            status=ExportStatus.QUEUED,
            message=result.get("message", "Export job created successfully")
        )

    except requests.RequestException as e:
        logger.error(f"Error communicating with export-generator: {e}")
        raise HTTPException(
            status_code=503,
            detail="Export service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Error creating export: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{export_job_id}/status", response_model=ExportStatusResponse)
async def get_export_status(
    export_job_id: str,
    x_customer_id: str = Header(...)
):
    """
    Get export job status

    Poll this endpoint to check the progress of an export job.
    Proxies to export-generator service.
    """
    try:
        # Forward request to export-generator service
        response = requests.get(
            f"{settings.EXPORT_GENERATOR_URL}/export/{export_job_id}/status",
            params={"customer_id": x_customer_id},
            timeout=10
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Export job not found")

        if response.status_code != 200:
            logger.error(f"Export generator returned error: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to get export status"
            )

        return ExportStatusResponse(**response.json())

    except requests.RequestException as e:
        logger.error(f"Error communicating with export-generator: {e}")
        raise HTTPException(
            status_code=503,
            detail="Export service temporarily unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/export/{export_job_id}")
async def cancel_export(
    export_job_id: str,
    x_customer_id: str = Header(...)
):
    """
    Cancel an export job

    Note: This only marks the job as cancelled. If processing has already started,
    it may complete anyway. Proxies to export-generator service.
    """
    try:
        # Forward request to export-generator service
        response = requests.delete(
            f"{settings.EXPORT_GENERATOR_URL}/export/{export_job_id}",
            params={"customer_id": x_customer_id},
            timeout=10
        )

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Export job not found")

        if response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail=response.json().get("error", "Cannot cancel export")
            )

        if response.status_code != 200:
            logger.error(f"Export generator returned error: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to cancel export"
            )

        return response.json()

    except requests.RequestException as e:
        logger.error(f"Error communicating with export-generator: {e}")
        raise HTTPException(
            status_code=503,
            detail="Export service temporarily unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling export: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}/exports/{export_id}")
async def delete_project_export(
    project_id: str,
    export_id: str,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """
    Delete a completed export from a project

    This removes:
    1. Export metadata from the project's exports array
    2. Export file from MinIO storage
    3. Video library entry (if MP4 export)
    """
    try:
        from minio import Minio
        from services.storage_service import storage_service

        # Get the project to verify it exists and user has access
        project = db_service.get_project(project_id, x_customer_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Find the export in the project's exports array
        export_to_delete = None
        for export in project.get('exports', []):
            if export.get('export_id') == export_id:
                export_to_delete = export
                break

        if not export_to_delete:
            raise HTTPException(status_code=404, detail="Export not found in project")

        # Delete from MinIO storage
        try:
            # Extract file extension from format
            export_format = export_to_delete.get('format', 'mp4')
            object_key = f"{x_customer_id}/{x_user_id}/exports/{export_id}.{export_format}"

            # Delete from exports bucket
            storage_service.delete_file(
                bucket='exports',
                object_name=object_key
            )
            logger.info(f"Deleted export file from MinIO: {object_key}")
        except Exception as e:
            logger.warning(f"Failed to delete export file from MinIO: {e}")
            # Continue even if MinIO deletion fails

        # Delete from video library if it's an MP4 export
        if export_to_delete.get('output_video_id'):
            try:
                video_id = export_to_delete['output_video_id']
                db_service.video_library.update_one(
                    {
                        "video_id": video_id,
                        "customer_id": x_customer_id
                    },
                    {
                        "$set": {
                            "is_deleted": True,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Marked video library entry as deleted: {video_id}")
            except Exception as e:
                logger.warning(f"Failed to delete video library entry: {e}")
                # Continue even if video library deletion fails

        # Remove the export from the exports array
        result = db_service.projects.update_one(
            {
                "project_id": project_id,
                "customer_id": x_customer_id
            },
            {
                "$pull": {"exports": {"export_id": export_id}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Export not found in project")

        logger.info(f"Deleted export {export_id} from project {project_id}")

        return {
            "success": True,
            "message": "Export deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export: {e}")
        raise HTTPException(status_code=500, detail=str(e))

