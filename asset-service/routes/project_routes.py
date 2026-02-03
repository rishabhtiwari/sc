"""
Project Routes
API endpoints for design editor project management
"""
from fastapi import APIRouter, Header, HTTPException, Query
from typing import Optional, List
from models.project import Project, ProjectCreate, ProjectUpdate
from services.project_service import project_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=Project)
def create_project(
    project_data: ProjectCreate,
    x_customer_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """Create a new project"""
    try:
        project = project_service.create_project(
            x_customer_id,
            x_user_id,
            project_data
        )
        return project
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=Project)
def get_project(
    project_id: str,
    x_customer_id: str = Header(...)
):
    """Get a project by ID"""
    try:
        project = project_service.get_project(project_id, x_customer_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    x_customer_id: str = Header(...)
):
    """Update a project"""
    try:
        project = project_service.update_project(
            project_id,
            x_customer_id,
            update_data
        )
        return project
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[Project])
def list_projects(
    x_customer_id: str = Header(...),
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List projects"""
    try:
        projects = project_service.list_projects(
            x_customer_id,
            user_id,
            status,
            skip,
            limit
        )
        return projects
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    x_customer_id: str = Header(...),
    hard: bool = Query(False)
):
    """Delete a project"""
    try:
        success = project_service.delete_project(
            project_id,
            x_customer_id,
            hard
        )
        return {"success": success, "message": "Project deleted"}
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

