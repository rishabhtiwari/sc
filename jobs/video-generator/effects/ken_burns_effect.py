"""
Ken Burns Effect - Zoom and pan effect for static images
"""

import random
import numpy as np
from typing import Dict, Any, Optional
from PIL import Image
from moviepy.editor import VideoClip, ImageClip

from .base_effect import BaseEffect


class KenBurnsEffect(BaseEffect):
    """
    Ken Burns Effect - Creates dynamic zoom and pan motion on static images
    
    This effect adds cinematic movement to still images by slowly zooming in/out
    and panning across the image, named after documentary filmmaker Ken Burns.
    """
    
    # Available pan styles
    PAN_STYLES = [
        'left_to_right',
        'right_to_left', 
        'top_to_bottom',
        'bottom_to_top',
        'zoom_center',
        'diagonal_tl_br',  # Top-left to bottom-right
        'diagonal_tr_bl',  # Top-right to bottom-left
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, logger=None):
        """
        Initialize Ken Burns Effect
        
        Config options:
            - zoom_start: Starting zoom level (default: 1.0)
            - zoom_end: Ending zoom level (default: 1.2)
            - pan_style: Pan direction (default: random choice)
            - easing: Easing function for smooth motion (default: 'linear')
        """
        super().__init__(config, logger)
        
        # Set default configuration
        self.zoom_start = self.config.get('zoom_start', 1.0)
        self.zoom_end = self.config.get('zoom_end', 1.2)
        self.pan_style = self.config.get('pan_style', None)  # None = random
        self.easing = self.config.get('easing', 'linear')
        
    def apply(self, clip: ImageClip, **kwargs) -> VideoClip:
        """
        Apply Ken Burns effect to an image clip
        
        Args:
            clip: ImageClip to apply the effect to
            **kwargs: Additional parameters
                - duration: Duration of the effect (uses clip duration if not specified)
                - pan_style: Override configured pan style
                
        Returns:
            VideoClip with Ken Burns effect applied
        """
        try:
            duration = kwargs.get('duration', clip.duration)
            pan_style = kwargs.get('pan_style', self.pan_style)
            
            # Choose random pan style if not specified
            if pan_style is None or pan_style not in self.PAN_STYLES:
                pan_style = random.choice(self.PAN_STYLES)
            
            # Get image dimensions
            w, h = clip.size
            
            self.log_info(f"Applying Ken Burns effect: {pan_style}, zoom {self.zoom_start}x → {self.zoom_end}x, duration {duration}s")
            
            def apply_ken_burns(get_frame, t):
                """Apply Ken Burns effect to each frame"""
                frame = get_frame(t)
                
                # Calculate progress (0 to 1) with easing
                progress = self._apply_easing(t / duration if duration > 0 else 0)
                
                # Calculate current zoom level (interpolation)
                current_zoom = self.zoom_start + (self.zoom_end - self.zoom_start) * progress
                
                # Calculate new dimensions
                new_w = int(w * current_zoom)
                new_h = int(h * current_zoom)
                
                # Resize frame
                pil_img = Image.fromarray(frame)
                pil_img_resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                frame_resized = np.array(pil_img_resized)
                
                # Calculate crop position based on pan style
                x_offset, y_offset = self._calculate_pan_offset(
                    pan_style, progress, new_w, new_h, w, h
                )
                
                # Ensure offsets are within bounds
                x_offset = max(0, min(x_offset, new_w - w))
                y_offset = max(0, min(y_offset, new_h - h))
                
                # Crop the frame
                cropped_frame = frame_resized[y_offset:y_offset+h, x_offset:x_offset+w]
                
                return cropped_frame
            
            # Apply the Ken Burns effect
            ken_burns_clip = clip.fl(apply_ken_burns)
            
            return ken_burns_clip
            
        except Exception as e:
            self.log_error(f"Error applying Ken Burns effect: {str(e)}")
            # Fallback to original clip if effect fails
            return clip
    
    def _calculate_pan_offset(self, pan_style: str, progress: float, 
                             new_w: int, new_h: int, w: int, h: int) -> tuple:
        """
        Calculate x and y offset for panning based on style
        
        Args:
            pan_style: The panning style to use
            progress: Current progress (0 to 1)
            new_w: New width after zoom
            new_h: New height after zoom
            w: Original width
            h: Original height
            
        Returns:
            Tuple of (x_offset, y_offset)
        """
        if pan_style == 'left_to_right':
            # Pan from left to right
            x_offset = int((new_w - w) * progress)
            y_offset = (new_h - h) // 2
            
        elif pan_style == 'right_to_left':
            # Pan from right to left
            x_offset = int((new_w - w) * (1 - progress))
            y_offset = (new_h - h) // 2
            
        elif pan_style == 'top_to_bottom':
            # Pan from top to bottom
            x_offset = (new_w - w) // 2
            y_offset = int((new_h - h) * progress)
            
        elif pan_style == 'bottom_to_top':
            # Pan from bottom to top
            x_offset = (new_w - w) // 2
            y_offset = int((new_h - h) * (1 - progress))
            
        elif pan_style == 'diagonal_tl_br':
            # Pan from top-left to bottom-right
            x_offset = int((new_w - w) * progress)
            y_offset = int((new_h - h) * progress)
            
        elif pan_style == 'diagonal_tr_bl':
            # Pan from top-right to bottom-left
            x_offset = int((new_w - w) * (1 - progress))
            y_offset = int((new_h - h) * progress)
            
        else:  # zoom_center
            # Zoom centered (no pan)
            x_offset = (new_w - w) // 2
            y_offset = (new_h - h) // 2
        
        return x_offset, y_offset
    
    def _apply_easing(self, t: float) -> float:
        """
        Apply easing function to progress value
        
        Args:
            t: Progress value (0 to 1)
            
        Returns:
            Eased progress value
        """
        if self.easing == 'ease_in':
            # Quadratic ease in
            return t * t
        elif self.easing == 'ease_out':
            # Quadratic ease out
            return t * (2 - t)
        elif self.easing == 'ease_in_out':
            # Quadratic ease in-out
            return t * t * (3 - 2 * t)
        else:  # linear
            return t
    
    def validate_params(self, **kwargs) -> bool:
        """Validate Ken Burns effect parameters"""
        # Validate zoom levels
        if self.zoom_start <= 0 or self.zoom_end <= 0:
            self.log_error("Zoom levels must be positive")
            return False
        
        # Validate pan style if specified
        pan_style = kwargs.get('pan_style', self.pan_style)
        if pan_style and pan_style not in self.PAN_STYLES:
            self.log_warning(f"Invalid pan style '{pan_style}', will use random")
        
        return True
    
    def get_effect_info(self) -> Dict[str, Any]:
        """Get Ken Burns effect information"""
        info = super().get_effect_info()
        info.update({
            'zoom_range': f"{self.zoom_start}x to {self.zoom_end}x",
            'pan_style': self.pan_style or 'random',
            'easing': self.easing,
            'available_pan_styles': self.PAN_STYLES
        })
        return info

