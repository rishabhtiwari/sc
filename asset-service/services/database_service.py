"""
MongoDB Database Service
Handles all database operations for asset metadata
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """MongoDB service for asset metadata management"""

    def __init__(self):
        """Initialize MongoDB client"""
        self.client = MongoClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.assets = self.db.assets
        self.projects = self.db.projects  # Add projects collection

        # Audio library uses the news database
        self.news_db = self.client['news']
        self.audio_library = self.news_db.audio_library

        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create necessary indexes"""
        try:
            # Compound index for customer and user queries
            self.assets.create_index([
                ("customer_id", ASCENDING),
                ("user_id", ASCENDING),
                ("type", ASCENDING)
            ])

            # Index for asset_id lookups
            self.assets.create_index("asset_id", unique=True)

            # Index for search
            self.assets.create_index([
                ("metadata.title", "text"),
                ("metadata.description", "text"),
                ("metadata.tags", "text")
            ])

            # Index for folder organization
            self.assets.create_index([
                ("customer_id", ASCENDING),
                ("metadata.folder", ASCENDING)
            ])

            # Note: Project indexes are created by migration 056_create_projects_collection.js
            # No need to create them here to avoid duplication

            logger.info("Database indexes created successfully")

        except PyMongoError as e:
            logger.error(f"Error creating indexes: {e}")

    def create_asset(self, asset_data: Dict[str, Any]) -> str:
        """
        Create a new asset record

        Args:
            asset_data: Asset metadata

        Returns:
            Asset ID
        """
        try:
            asset_data["created_at"] = datetime.utcnow()
            asset_data["updated_at"] = datetime.utcnow()

            result = self.assets.insert_one(asset_data)
            logger.info(f"Created asset: {asset_data.get('asset_id')}")
            return asset_data["asset_id"]

        except PyMongoError as e:
            logger.error(f"Error creating asset: {e}")
            raise

    def create_audio_library_entry(self, audio_data: Dict[str, Any]) -> str:
        """
        Create a new audio library entry in the news.audio_library collection

        This uses the flat schema expected by the audio_library collection:
        - url (string, not nested)
        - size (long, not int)
        - folder (string, not null)

        Args:
            audio_data: Audio metadata matching audio_library schema

        Returns:
            Audio ID
        """
        try:
            audio_data["created_at"] = datetime.utcnow()
            audio_data["updated_at"] = datetime.utcnow()

            result = self.audio_library.insert_one(audio_data)
            logger.info(f"Created audio library entry: {audio_data.get('audio_id')}")
            return audio_data["audio_id"]

        except PyMongoError as e:
            logger.error(f"Error creating audio library entry: {e}")
            raise

    def get_asset(
        self,
        asset_id: str,
        customer_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get asset by ID

        Args:
            asset_id: Asset ID
            customer_id: Customer ID for multi-tenancy (optional for backward compatibility)

        Returns:
            Asset data or None
        """
        try:
            query = {"asset_id": asset_id, "deleted_at": None}

            # CRITICAL: Enforce multi-tenancy if customer_id provided
            if customer_id:
                query["customer_id"] = customer_id

            asset = self.assets.find_one(query, {"_id": 0})
            return asset

        except PyMongoError as e:
            logger.error(f"Error getting asset: {e}")
            raise

    def update_asset(
        self,
        asset_id: str,
        update_data: Dict[str, Any],
        customer_id: Optional[str] = None
    ) -> bool:
        """
        Update asset metadata

        Args:
            asset_id: Asset ID
            update_data: Data to update
            customer_id: Customer ID for multi-tenancy (optional for backward compatibility)

        Returns:
            True if updated
        """
        try:
            update_data["updated_at"] = datetime.utcnow()

            query = {"asset_id": asset_id, "deleted_at": None}

            # CRITICAL: Enforce multi-tenancy if customer_id provided
            if customer_id:
                query["customer_id"] = customer_id

            result = self.assets.update_one(query, {"$set": update_data})

            return result.modified_count > 0

        except PyMongoError as e:
            logger.error(f"Error updating asset: {e}")
            raise

    def delete_asset(
        self,
        asset_id: str,
        soft_delete: bool = True,
        customer_id: Optional[str] = None
    ) -> bool:
        """
        Delete asset (soft or hard delete)

        Args:
            asset_id: Asset ID
            soft_delete: If True, soft delete; if False, hard delete
            customer_id: Customer ID for multi-tenancy (optional for backward compatibility)

        Returns:
            True if deleted
        """
        try:
            query = {"asset_id": asset_id}

            # CRITICAL: Enforce multi-tenancy if customer_id provided
            if customer_id:
                query["customer_id"] = customer_id

            if soft_delete:
                result = self.assets.update_one(
                    query,
                    {"$set": {"deleted_at": datetime.utcnow()}}
                )
                return result.modified_count > 0
            else:
                result = self.assets.delete_one(query)
                return result.deleted_count > 0

        except PyMongoError as e:
            logger.error(f"Error deleting asset: {e}")
            raise

    def get_audio_library_entry(self, audio_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single audio library entry by audio_id

        Args:
            audio_id: Audio ID to retrieve

        Returns:
            Audio library entry or None if not found
        """
        try:
            audio = self.audio_library.find_one(
                {"audio_id": audio_id, "is_deleted": False},
                {"_id": 0}
            )
            return audio

        except PyMongoError as e:
            logger.error(f"Error getting audio library entry: {e}")
            raise

    def get_audio_by_id(
        self,
        audio_id: str,
        customer_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific audio library entry by ID

        Args:
            audio_id: Audio ID
            customer_id: Customer ID (required for multi-tenancy)
            user_id: Optional user ID for additional filtering

        Returns:
            Audio library entry or None if not found
        """
        try:
            query = {
                "audio_id": audio_id,
                "customer_id": customer_id,
                "is_deleted": False
            }

            if user_id:
                query["user_id"] = user_id

            logger.info(f"Querying audio_library with: {query}")
            audio = self.audio_library.find_one(query)

            if audio:
                logger.info(f"Found audio: {audio.get('audio_id')}")
                audio['_id'] = str(audio['_id'])
            else:
                logger.warning(f"Audio not found with query: {query}")

            return audio

        except PyMongoError as e:
            logger.error(f"Error getting audio by ID: {e}")
            raise

    def delete_audio_library_entry(
        self,
        audio_id: str,
        customer_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Soft delete an audio library entry

        Args:
            audio_id: Audio ID
            customer_id: Customer ID (required for multi-tenancy)
            user_id: Optional user ID for additional filtering

        Returns:
            True if deleted successfully
        """
        try:
            query = {
                "audio_id": audio_id,
                "customer_id": customer_id,
                "is_deleted": False
            }

            if user_id:
                query["user_id"] = user_id

            logger.info(f"Soft deleting audio_library entry with query: {query}")

            result = self.audio_library.update_one(
                query,
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.utcnow()
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"Successfully soft deleted audio: {audio_id}")
                return True
            else:
                logger.warning(f"No audio found to delete with query: {query}")
                return False

        except PyMongoError as e:
            logger.error(f"Error deleting audio library entry: {e}")
            raise


    def list_audio_library(
        self,
        customer_id: str,
        user_id: Optional[str] = None,
        audio_type: Optional[str] = None,
        folder: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List audio library entries from news.audio_library collection

        Args:
            customer_id: Customer ID (required for multi-tenancy)
            user_id: Optional user ID filter
            audio_type: Optional type filter (voiceover, music, sound_effect)
            folder: Optional folder filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of audio library entries
        """
        try:
            query = {
                "customer_id": customer_id,
                "is_deleted": False
            }

            if user_id:
                query["user_id"] = user_id

            if audio_type:
                query["type"] = audio_type

            if folder:
                query["folder"] = folder

            audios = list(
                self.audio_library.find(query, {"_id": 0})
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )

            return audios

        except PyMongoError as e:
            logger.error(f"Error listing audio library: {e}")
            raise

    def list_assets(
        self,
        customer_id: str,
        user_id: Optional[str] = None,
        asset_type: Optional[str] = None,
        folder: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List assets with filters"""
        try:
            query = {
                "customer_id": customer_id,
                "deleted_at": None
            }

            if user_id:
                query["user_id"] = user_id

            if asset_type:
                query["type"] = asset_type

            if folder:
                query["metadata.folder"] = folder

            assets = list(
                self.assets.find(query, {"_id": 0})
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )

            return assets

        except PyMongoError as e:
            logger.error(f"Error listing assets: {e}")
            raise

    def search_assets(
        self,
        customer_id: str,
        search_query: str,
        asset_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search assets by text"""
        try:
            query = {
                "customer_id": customer_id,
                "deleted_at": None,
                "$text": {"$search": search_query}
            }

            if asset_type:
                query["type"] = asset_type

            assets = list(
                self.assets.find(query, {"_id": 0, "score": {"$meta": "textScore"}})
                .sort([("score", {"$meta": "textScore"})])
                .skip(skip)
                .limit(limit)
            )

            return assets

        except PyMongoError as e:
            logger.error(f"Error searching assets: {e}")
            raise

    # ==================== Project Methods ====================

    def create_project(self, project_data: Dict[str, Any]) -> str:
        """
        Create a new project

        Args:
            project_data: Project metadata

        Returns:
            Project ID
        """
        try:
            project_data["created_at"] = datetime.utcnow()
            project_data["updated_at"] = datetime.utcnow()

            result = self.projects.insert_one(project_data)
            logger.info(f"Created project: {project_data.get('project_id')}")
            return project_data["project_id"]

        except PyMongoError as e:
            logger.error(f"Error creating project: {e}")
            raise

    def get_project(
        self,
        project_id: str,
        customer_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a project by ID

        Args:
            project_id: Project ID
            customer_id: Customer ID

        Returns:
            Project data or None
        """
        try:
            project = self.projects.find_one(
                {
                    "project_id": project_id,
                    "customer_id": customer_id,
                    "deleted_at": None
                },
                {"_id": 0}
            )
            return project

        except PyMongoError as e:
            logger.error(f"Error getting project: {e}")
            raise

    def update_project(
        self,
        project_id: str,
        customer_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update a project

        Args:
            project_id: Project ID
            customer_id: Customer ID
            update_data: Fields to update

        Returns:
            True if updated
        """
        try:
            update_data["updated_at"] = datetime.utcnow()

            result = self.projects.update_one(
                {
                    "project_id": project_id,
                    "customer_id": customer_id
                },
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Updated project: {project_id}")

            return result.modified_count > 0

        except PyMongoError as e:
            logger.error(f"Error updating project: {e}")
            raise

    def list_projects(
        self,
        customer_id: str,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List projects with filters

        Args:
            customer_id: Customer ID
            user_id: Optional user ID filter
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of projects
        """
        try:
            query = {
                "customer_id": customer_id,
                "deleted_at": None
            }

            if user_id:
                query["user_id"] = user_id
            if status:
                query["status"] = status

            projects = list(
                self.projects.find(query, {"_id": 0})
                .sort("updated_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )

            return projects

        except PyMongoError as e:
            logger.error(f"Error listing projects: {e}")
            raise

    def delete_project(
        self,
        project_id: str,
        customer_id: str,
        hard: bool = False
    ) -> bool:
        """
        Delete a project (soft or hard delete)

        Args:
            project_id: Project ID
            customer_id: Customer ID
            hard: If True, permanently delete; if False, soft delete

        Returns:
            True if deleted
        """
        try:
            if hard:
                result = self.projects.delete_one({
                    "project_id": project_id,
                    "customer_id": customer_id
                })
                deleted = result.deleted_count > 0
            else:
                result = self.projects.update_one(
                    {
                        "project_id": project_id,
                        "customer_id": customer_id
                    },
                    {"$set": {"deleted_at": datetime.utcnow()}}
                )
                deleted = result.modified_count > 0

            if deleted:
                logger.info(f"Deleted project: {project_id} (hard={hard})")

            return deleted

        except PyMongoError as e:
            logger.error(f"Error deleting project: {e}")
            raise


# Global database service instance
db_service = DatabaseService()

