"""
Export Routes
API endpoints for project export functionality - Proxies to export-generator job service
"""
from fastapi import APIRouter, Header, HTTPException
from typing import Optional
import logging
import requests
from models.export import (
    ExportRequest,
    ExportJobResponse,
    ExportStatusResponse,
    ExportFormat,
    ExportStatus
)
from config.settings import settings

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

