"""
File Utilities
Helper functions for file processing
"""
import logging
from typing import Dict, Any, Optional
from io import BytesIO
from PIL import Image
from mutagen import File as MutagenFile
from models.asset import AssetType
from config.settings import settings

logger = logging.getLogger(__name__)


def validate_file_type(mime_type: str, asset_type: AssetType) -> bool:
    """
    Validate if MIME type matches asset type
    
    Args:
        mime_type: File MIME type
        asset_type: Expected asset type
        
    Returns:
        True if valid, False otherwise
    """
    type_map = {
        AssetType.AUDIO: settings.ALLOWED_AUDIO_TYPES,
        AssetType.IMAGE: settings.ALLOWED_IMAGE_TYPES,
        AssetType.VIDEO: settings.ALLOWED_VIDEO_TYPES,
        AssetType.DOCUMENT: settings.ALLOWED_DOCUMENT_TYPES
    }
    
    allowed_types = type_map.get(asset_type, [])
    return mime_type in allowed_types


def get_file_info(file_content: bytes, mime_type: str, asset_type: AssetType) -> Dict[str, Any]:
    """
    Extract file information (duration, dimensions, etc.)
    
    Args:
        file_content: File content as bytes
        mime_type: File MIME type
        asset_type: Asset type
        
    Returns:
        Dict with file information
    """
    info = {}
    
    try:
        if asset_type == AssetType.AUDIO:
            info.update(_get_audio_info(file_content))
        elif asset_type == AssetType.IMAGE:
            info.update(_get_image_info(file_content))
        elif asset_type == AssetType.VIDEO:
            info.update(_get_video_info(file_content))
    except Exception as e:
        logger.warning(f"Error extracting file info: {e}")
    
    return info


def _get_audio_info(file_content: bytes) -> Dict[str, Any]:
    """Extract audio file information"""
    try:
        # Save to temp file for mutagen
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.audio') as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        try:
            audio = MutagenFile(temp_path)
            if audio and audio.info:
                return {
                    "duration": float(audio.info.length),
                    "sample_rate": getattr(audio.info, 'sample_rate', None),
                    "channels": getattr(audio.info, 'channels', None),
                    "bitrate": getattr(audio.info, 'bitrate', None)
                }
        finally:
            import os
            os.unlink(temp_path)
    except Exception as e:
        logger.warning(f"Error getting audio info: {e}")
    
    return {"duration": 0.0}


def _get_image_info(file_content: bytes) -> Dict[str, Any]:
    """Extract image file information"""
    try:
        image = Image.open(BytesIO(file_content))
        return {
            "dimensions": {
                "width": image.width,
                "height": image.height
            },
            "format": image.format,
            "mode": image.mode
        }
    except Exception as e:
        logger.warning(f"Error getting image info: {e}")
    
    return {}


def _get_video_info(file_content: bytes) -> Dict[str, Any]:
    """Extract video file information"""
    # For video, we'd need ffmpeg-python
    # Simplified for now
    try:
        import tempfile
        import subprocess
        import json
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.video') as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        try:
            # Use ffprobe to get video info
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                video_stream = next(
                    (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                    None
                )
                
                if video_stream:
                    return {
                        "duration": float(data.get('format', {}).get('duration', 0)),
                        "dimensions": {
                            "width": video_stream.get('width'),
                            "height": video_stream.get('height')
                        },
                        "codec": video_stream.get('codec_name'),
                        "fps": eval(video_stream.get('r_frame_rate', '0/1'))
                    }
        finally:
            import os
            os.unlink(temp_path)
    except Exception as e:
        logger.warning(f"Error getting video info: {e}")
    
    return {}

