"""
Project Service
Business logic for managing design editor projects
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from services.database_service import db_service
from services.storage_service import storage_service
from models.project import Project, ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing design editor projects"""
    
    def __init__(self):
        self.db = db_service
        self.storage = storage_service
    
    def create_project(
        self,
        customer_id: str,
        user_id: str,
        project_data: ProjectCreate
    ) -> Project:
        """Create a new project"""
        try:
            project_id = f"proj_{uuid.uuid4().hex[:12]}"
            
            # Extract asset references from pages, audio, and video tracks
            asset_refs = self._extract_asset_references(project_data)
            
            project = Project(
                project_id=project_id,
                customer_id=customer_id,
                user_id=user_id,
                **project_data.dict(),
                assetReferences=asset_refs
            )
            
            # Save to database
            self.db.create_project(project.dict(by_alias=True))
            
            logger.info(f"Created project: {project_id}")
            return project
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    def update_project(
        self,
        project_id: str,
        customer_id: str,
        update_data: ProjectUpdate
    ) -> Project:
        """Update an existing project"""
        try:
            # Get existing project
            existing = self.db.get_project(project_id, customer_id)
            if not existing:
                raise ValueError(f"Project not found: {project_id}")
            
            # Update fields
            update_dict = update_data.dict(exclude_unset=True)
            
            # Re-extract asset references if pages/tracks updated
            if any(k in update_dict for k in ["pages", "audioTracks", "videoTracks"]):
                asset_refs = self._extract_asset_references(update_data)
                update_dict["assetReferences"] = asset_refs
            
            # Update in database
            self.db.update_project(project_id, customer_id, update_dict)
            
            # Get updated project
            updated = self.db.get_project(project_id, customer_id)
            
            logger.info(f"Updated project: {project_id}")
            return Project(**updated)
            
        except Exception as e:
            logger.error(f"Error updating project: {e}")
            raise
    
    def get_project(
        self,
        project_id: str,
        customer_id: str
    ) -> Optional[Project]:
        """Get a project by ID"""
        try:
            project_data = self.db.get_project(project_id, customer_id)
            if not project_data:
                return None
            
            # Update last_opened_at
            self.db.update_project(
                project_id,
                customer_id,
                {"last_opened_at": datetime.utcnow()}
            )
            
            return Project(**project_data)
            
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            raise
    
    def list_projects(
        self,
        customer_id: str,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Project]:
        """List projects with filters"""
        try:
            projects = self.db.list_projects(
                customer_id,
                user_id,
                status,
                skip,
                limit
            )
            return [Project(**p) for p in projects]
            
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            raise
    
    def delete_project(
        self,
        project_id: str,
        customer_id: str,
        hard_delete: bool = False
    ) -> bool:
        """Delete a project (soft or hard delete)"""
        try:
            deleted = self.db.delete_project(project_id, customer_id, hard=hard_delete)
            
            logger.info(f"Deleted project: {project_id} (hard={hard_delete})")
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            raise

    def _extract_asset_references(self, project_data) -> List[str]:
        """Extract all asset IDs from project data"""
        asset_ids = set()

        # From pages/elements
        if hasattr(project_data, 'pages') and project_data.pages:
            for page in project_data.pages:
                # Background assets
                if page.background.imageAssetId:
                    asset_ids.add(page.background.imageAssetId)
                if page.background.videoAssetId:
                    asset_ids.add(page.background.videoAssetId)

                # Element assets
                for element in page.elements:
                    if element.assetId:
                        asset_ids.add(element.assetId)

        # From audio tracks
        if hasattr(project_data, 'audioTracks') and project_data.audioTracks:
            for track in project_data.audioTracks:
                if track.assetId:
                    asset_ids.add(track.assetId)

        # From video tracks
        if hasattr(project_data, 'videoTracks') and project_data.videoTracks:
            for track in project_data.videoTracks:
                if track.assetId:
                    asset_ids.add(track.assetId)

        return list(asset_ids)


# Global instance
project_service = ProjectService()

