"""
Project Models
Pydantic models for design editor project data validation
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class CanvasSettings(BaseModel):
    """Canvas settings"""
    width: int = 1920
    height: int = 1080
    background: str = "#ffffff"


class ProjectSettings(BaseModel):
    """Project settings"""
    canvas: CanvasSettings = Field(default_factory=CanvasSettings)
    duration: float = 0
    fps: int = 30
    quality: str = "1080p"


class Background(BaseModel):
    """Page background configuration"""
    type: str = "solid"  # solid, gradient, image, video
    color: Optional[str] = None
    gradient: Optional[Dict[str, Any]] = None
    imageAssetId: Optional[str] = None
    videoAssetId: Optional[str] = None


class Element(BaseModel):
    """Canvas element"""
    id: str
    type: str  # text, image, video, shape, etc.
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    assetId: Optional[str] = None  # Reference to assets collection
    src: Optional[str] = None
    # Element-specific properties stored as dict
    text: Optional[str] = None
    fontSize: Optional[int] = None
    fontFamily: Optional[str] = None
    color: Optional[str] = None
    rotation: Optional[float] = 0
    opacity: Optional[float] = 1
    # Store all other properties
    properties: Dict[str, Any] = Field(default_factory=dict)


class Page(BaseModel):
    """Project page/slide"""
    id: str
    name: str
    duration: float = 5
    startTime: float = 0
    background: Background = Field(default_factory=Background)
    elements: List[Element] = Field(default_factory=list)


class AudioTrack(BaseModel):
    """Audio track on timeline"""
    id: str
    assetId: Optional[str] = None
    name: str
    url: str
    type: str = "music"  # music, voiceover, sfx
    startTime: float = 0
    duration: float = 0
    volume: int = 100
    fadeIn: float = 0
    fadeOut: float = 0
    playbackSpeed: float = 1


class VideoTrack(BaseModel):
    """Video track on timeline"""
    id: str
    elementId: str
    assetId: Optional[str] = None
    name: str
    url: str
    startTime: float = 0
    duration: float = 0
    originalDuration: float = 0
    trimStart: float = 0
    trimEnd: float = 0
    volume: int = 100
    playbackSpeed: float = 1
    slideIndex: int = 0


class Project(BaseModel):
    """Complete project model"""
    project_id: str
    customer_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    pages: List[Page] = Field(default_factory=list)
    audioTracks: List[AudioTrack] = Field(default_factory=list)
    videoTracks: List[VideoTrack] = Field(default_factory=list)
    assetReferences: List[str] = Field(default_factory=list)
    version: int = 1
    status: ProjectStatus = ProjectStatus.DRAFT
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_opened_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class ProjectCreate(BaseModel):
    """Project creation request"""
    name: str
    description: Optional[str] = None
    settings: Optional[ProjectSettings] = None
    pages: List[Page] = Field(default_factory=list)
    audioTracks: List[AudioTrack] = Field(default_factory=list)
    videoTracks: List[VideoTrack] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    """Project update request"""
    name: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    settings: Optional[ProjectSettings] = None
    pages: Optional[List[Page]] = None
    audioTracks: Optional[List[AudioTrack]] = None
    videoTracks: Optional[List[VideoTrack]] = None
    status: Optional[ProjectStatus] = None
    tags: Optional[List[str]] = None

