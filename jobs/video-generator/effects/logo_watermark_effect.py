"""
Logo Watermark Effect - Add logo watermark overlay to videos
"""

import os
import numpy as np
from typing import Dict, Any, Optional, Tuple
from PIL import Image
from moviepy.editor import VideoClip, ImageClip, CompositeVideoClip

from .base_effect import BaseEffect


class LogoWatermarkEffect(BaseEffect):
    """
    Logo Watermark Effect - Adds a logo watermark overlay to videos
    
    This effect overlays a logo image on the video with configurable position,
    opacity, and size. The logo maintains its aspect ratio and can be positioned
    at various locations on the video.
    """
    
    # Available positions
    POSITIONS = {
        'top-left': ('left', 'top'),
        'top-right': ('right', 'top'),
        'bottom-left': ('left', 'bottom'),
        'bottom-right': ('right', 'bottom'),
        'center': ('center', 'center'),
        'top-center': ('center', 'top'),
        'bottom-center': ('center', 'bottom'),
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, logger=None):
        """
        Initialize Logo Watermark Effect
        
        Config options:
            - logo_path: Path to the logo image file (required)
            - position: Position of the logo (default: 'bottom-right')
            - opacity: Opacity of the logo 0.0-1.0 (default: 0.7)
            - scale: Scale relative to video width (default: 0.15)
            - margin: Margin from edges in pixels (default: 20)
        """
        super().__init__(config, logger)
        
        # Set default configuration
        self.logo_path = self.config.get('logo_path', '/app/assets/logo.png')
        self.position = self.config.get('position', 'bottom-right')
        self.opacity = float(self.config.get('opacity', 0.7))
        self.scale = float(self.config.get('scale', 0.15))
        self.margin = int(self.config.get('margin', 20))
        
        # Validate opacity
        self.opacity = max(0.0, min(1.0, self.opacity))
        
        # Validate scale
        self.scale = max(0.01, min(0.5, self.scale))
        
    def _load_and_resize_logo(self, video_width: int, video_height: int) -> Optional[ImageClip]:
        """
        Load and resize the logo image
        
        Args:
            video_width: Width of the video
            video_height: Height of the video
            
        Returns:
            ImageClip with the logo, or None if loading fails
        """
        try:
            # Check if logo file exists
            if not os.path.exists(self.logo_path):
                self.log_error(f"Logo file not found: {self.logo_path}")
                return None
            
            # Load logo image
            logo_img = Image.open(self.logo_path)
            
            # Convert to RGBA if not already
            if logo_img.mode != 'RGBA':
                logo_img = logo_img.convert('RGBA')
            
            # Calculate target width based on scale
            target_width = int(video_width * self.scale)
            
            # Calculate height maintaining aspect ratio
            aspect_ratio = logo_img.height / logo_img.width
            target_height = int(target_width * aspect_ratio)
            
            # Ensure logo doesn't exceed video dimensions
            if target_height > video_height * 0.3:  # Max 30% of video height
                target_height = int(video_height * 0.3)
                target_width = int(target_height / aspect_ratio)
            
            # Resize logo
            logo_img = logo_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # Convert to numpy array
            logo_array = np.array(logo_img)
            
            # Create ImageClip from the logo
            logo_clip = ImageClip(logo_array, ismask=False)
            
            # Apply opacity
            if self.opacity < 1.0:
                logo_clip = logo_clip.set_opacity(self.opacity)
            
            self.log_info(f"Logo loaded and resized to {target_width}x{target_height} (opacity: {self.opacity})")
            
            return logo_clip
            
        except Exception as e:
            self.log_error(f"Failed to load logo: {str(e)}")
            return None
    
    def _calculate_position(self, video_width: int, video_height: int, 
                           logo_width: int, logo_height: int) -> Tuple[int, int]:
        """
        Calculate the position coordinates for the logo
        
        Args:
            video_width: Width of the video
            video_height: Height of the video
            logo_width: Width of the logo
            logo_height: Height of the logo
            
        Returns:
            Tuple of (x, y) coordinates
        """
        # Get position alignment
        h_align, v_align = self.POSITIONS.get(self.position, ('right', 'bottom'))
        
        # Calculate horizontal position
        if h_align == 'left':
            x = self.margin
        elif h_align == 'right':
            x = video_width - logo_width - self.margin
        else:  # center
            x = (video_width - logo_width) // 2
        
        # Calculate vertical position
        if v_align == 'top':
            y = self.margin
        elif v_align == 'bottom':
            y = video_height - logo_height - self.margin
        else:  # center
            y = (video_height - logo_height) // 2
        
        return (x, y)
    
    def apply(self, clip: VideoClip, **kwargs) -> VideoClip:
        """
        Apply logo watermark effect to a video clip
        
        Args:
            clip: VideoClip to apply the effect to
            **kwargs: Additional parameters
                - logo_path: Override configured logo path
                - position: Override configured position
                - opacity: Override configured opacity
                - scale: Override configured scale
                - margin: Override configured margin
                
        Returns:
            VideoClip with logo watermark applied
        """
        try:
            # Override config with kwargs if provided
            logo_path = kwargs.get('logo_path', self.logo_path)
            position = kwargs.get('position', self.position)
            opacity = float(kwargs.get('opacity', self.opacity))
            scale = float(kwargs.get('scale', self.scale))
            margin = int(kwargs.get('margin', self.margin))
            
            # Temporarily update instance variables for this application
            original_values = (self.logo_path, self.position, self.opacity, self.scale, self.margin)
            self.logo_path = logo_path
            self.position = position
            self.opacity = opacity
            self.scale = scale
            self.margin = margin
            
            # Get video dimensions
            video_width, video_height = clip.size
            
            self.log_info(f"Applying logo watermark: position={position}, opacity={opacity}, scale={scale}")
            
            # Load and resize logo
            logo_clip = self._load_and_resize_logo(video_width, video_height)
            
            if logo_clip is None:
                self.log_warning("Logo watermark skipped - logo could not be loaded")
                # Restore original values
                self.logo_path, self.position, self.opacity, self.scale, self.margin = original_values
                return clip
            
            # Set logo duration to match video
            logo_clip = logo_clip.set_duration(clip.duration)
            
            # Calculate position
            logo_width, logo_height = logo_clip.size
            x, y = self._calculate_position(video_width, video_height, logo_width, logo_height)
            
            # Set logo position
            logo_clip = logo_clip.set_position((x, y))
            
            self.log_info(f"Logo positioned at ({x}, {y})")
            
            # Composite the logo over the video
            result = CompositeVideoClip([clip, logo_clip])
            
            # Restore original values
            self.logo_path, self.position, self.opacity, self.scale, self.margin = original_values
            
            return result
            
        except Exception as e:
            self.log_error(f"Error applying logo watermark: {str(e)}")
            import traceback
            self.log_error(f"Traceback: {traceback.format_exc()}")
            return clip
    
    def validate_params(self, **kwargs) -> bool:
        """
        Validate logo watermark parameters
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        logo_path = kwargs.get('logo_path', self.logo_path)
        position = kwargs.get('position', self.position)
        opacity = kwargs.get('opacity', self.opacity)
        scale = kwargs.get('scale', self.scale)
        
        # Validate logo path
        if not logo_path or not os.path.exists(logo_path):
            self.log_error(f"Invalid logo path: {logo_path}")
            return False
        
        # Validate position
        if position not in self.POSITIONS:
            self.log_error(f"Invalid position: {position}. Must be one of {list(self.POSITIONS.keys())}")
            return False
        
        # Validate opacity
        try:
            opacity = float(opacity)
            if not 0.0 <= opacity <= 1.0:
                self.log_error(f"Invalid opacity: {opacity}. Must be between 0.0 and 1.0")
                return False
        except (ValueError, TypeError):
            self.log_error(f"Invalid opacity value: {opacity}")
            return False
        
        # Validate scale
        try:
            scale = float(scale)
            if not 0.01 <= scale <= 0.5:
                self.log_error(f"Invalid scale: {scale}. Must be between 0.01 and 0.5")
                return False
        except (ValueError, TypeError):
            self.log_error(f"Invalid scale value: {scale}")
            return False
        
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get default parameters for the effect
        
        Returns:
            Dictionary of default parameters
        """
        return {
            'logo_path': self.logo_path,
            'position': self.position,
            'opacity': self.opacity,
            'scale': self.scale,
            'margin': self.margin,
            'available_positions': list(self.POSITIONS.keys())
        }

