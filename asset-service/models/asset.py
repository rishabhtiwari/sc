"""
Asset Models
Pydantic models for asset data validation
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AssetType(str, Enum):
    """Asset type enumeration"""
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class StorageInfo(BaseModel):
    """Storage information"""
    bucket: str
    key: str
    url: str


class Dimensions(BaseModel):
    """Media dimensions"""
    width: Optional[int] = None
    height: Optional[int] = None


class AssetMetadata(BaseModel):
    """Asset metadata"""
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    folder: Optional[str] = None
    preview: Optional[str] = None  # Text preview for documents (first 150 chars)
    custom: Dict[str, Any] = Field(default_factory=dict)


class AssetVersion(BaseModel):
    """Asset version information"""
    version: int
    created_at: datetime
    size: int
    storage_key: str


class Asset(BaseModel):
    """Complete asset model"""
    asset_id: str
    customer_id: str
    user_id: str
    type: AssetType
    name: str
    original_filename: str
    mime_type: str
    size: int
    duration: Optional[float] = None  # For audio/video
    dimensions: Optional[Dimensions] = None  # For images/videos
    storage: StorageInfo
    metadata: AssetMetadata = Field(default_factory=AssetMetadata)
    versions: List[AssetVersion] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None


class AssetCreate(BaseModel):
    """Asset creation request"""
    name: str
    type: AssetType
    folder: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)


class AssetUpdate(BaseModel):
    """Asset update request"""
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    folder: Optional[str] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class AssetResponse(BaseModel):
    """Asset API response"""
    success: bool
    asset: Optional[Asset] = None
    message: Optional[str] = None
    error: Optional[str] = None


class AssetListResponse(BaseModel):
    """Asset list API response"""
    success: bool
    assets: List[Asset] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50
    message: Optional[str] = None
    error: Optional[str] = None


class UploadResponse(BaseModel):
    """Upload API response"""
    success: bool
    asset_id: Optional[str] = None
    url: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class AudioLibraryItem(BaseModel):
    """Audio library item (for migration compatibility)"""
    id: str
    customer_id: str
    user_id: str
    text: str
    audio_url: str
    duration: float
    voice: str
    voice_name: Optional[str] = None
    language: str
    speed: float = 1.0
    model: str
    folder: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    status: str = "generated"


class AudioLibraryStats(BaseModel):
    """Audio library statistics"""
    total_count: int = 0
    total_duration: float = 0.0
    by_voice: Dict[str, int] = Field(default_factory=dict)
    by_language: Dict[str, int] = Field(default_factory=dict)
    by_folder: Dict[str, int] = Field(default_factory=dict)

