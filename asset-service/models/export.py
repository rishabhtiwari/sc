"""
Export Models
Pydantic models for project export functionality
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ExportFormat(str, Enum):
    """Export format enumeration"""
    MP4 = "mp4"
    MP3 = "mp3"
    JSON = "json"
    PNG = "png"
    GIF = "gif"


class ExportStatus(str, Enum):
    """Export job status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportSettings(BaseModel):
    """Export settings"""
    quality: str = "1080p"  # 720p, 1080p, 1440p, 2160p
    fps: int = 30  # 24, 30, 60
    includeAudio: bool = True
    codec: str = "libx264"
    bitrate: str = "5000k"
    # Audio-only settings
    audioBitrate: Optional[str] = "192k"
    audioCodec: Optional[str] = "aac"


class ExportRequest(BaseModel):
    """Export request from frontend"""
    project_id: str
    format: ExportFormat
    settings: ExportSettings = Field(default_factory=ExportSettings)


class ExportJob(BaseModel):
    """Export job model"""
    export_job_id: str
    project_id: str
    customer_id: str
    user_id: str
    format: ExportFormat
    settings: ExportSettings
    status: ExportStatus = ExportStatus.QUEUED
    progress: int = 0  # 0-100
    current_step: str = ""
    output_url: Optional[str] = None
    output_video_id: Optional[str] = None  # ID in video library if saved
    file_size: Optional[int] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExportJobResponse(BaseModel):
    """Export job response"""
    success: bool
    export_job_id: str
    status: ExportStatus
    message: Optional[str] = None


class ExportStatusResponse(BaseModel):
    """Export status response"""
    export_job_id: str
    status: ExportStatus
    progress: int
    current_step: str
    output_url: Optional[str] = None
    output_video_id: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ProjectExportMetadata(BaseModel):
    """Export metadata stored in project"""
    export_id: str
    format: ExportFormat
    quality: str
    output_url: str
    output_video_id: Optional[str] = None  # Reference to video library
    file_size: int
    duration: Optional[float] = None
    exported_at: datetime = Field(default_factory=datetime.utcnow)
    exported_by: str  # user_id

