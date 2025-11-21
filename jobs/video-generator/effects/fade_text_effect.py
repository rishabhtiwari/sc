"""
Fade Text Effect for Video Generation
Provides fade-in and fade-out transitions for text overlays
"""

from typing import Dict, Any, Optional
from moviepy.editor import TextClip
from .base_effect import BaseEffect


class FadeTextEffect(BaseEffect):
    """
    Applies fade-in and fade-out transitions to text clips
    
    Supported parameters:
    - fade_in_duration: Duration of fade-in effect in seconds (default: 0.5)
    - fade_out_duration: Duration of fade-out effect in seconds (default: 0.5)
    - fade_type: Type of fade ('both', 'in', 'out') (default: 'both')
    """
    
    def __init__(self, config=None, logger=None):
        super().__init__(config, logger)
        self.effect_name = "fade_text"
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate fade text effect parameters
        
        Args:
            params: Dictionary containing effect parameters
            
        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}
        
        # Validate fade_in_duration
        if 'fade_in_duration' in params:
            try:
                fade_in = float(params['fade_in_duration'])
                if fade_in < 0:
                    errors['fade_in_duration'] = "Fade in duration must be non-negative"
                elif fade_in > 5.0:
                    errors['fade_in_duration'] = "Fade in duration should not exceed 5 seconds"
            except (ValueError, TypeError):
                errors['fade_in_duration'] = "Fade in duration must be a number"
        
        # Validate fade_out_duration
        if 'fade_out_duration' in params:
            try:
                fade_out = float(params['fade_out_duration'])
                if fade_out < 0:
                    errors['fade_out_duration'] = "Fade out duration must be non-negative"
                elif fade_out > 5.0:
                    errors['fade_out_duration'] = "Fade out duration should not exceed 5 seconds"
            except (ValueError, TypeError):
                errors['fade_out_duration'] = "Fade out duration must be a number"
        
        # Validate fade_type
        if 'fade_type' in params:
            fade_type = params['fade_type']
            if fade_type not in ['both', 'in', 'out']:
                errors['fade_type'] = "Fade type must be 'both', 'in', or 'out'"
        
        return errors
    
    def apply(self, clip: TextClip, **params) -> TextClip:
        """
        Apply fade transition to text clip using opacity

        Args:
            clip: TextClip to apply fade effect to
            **params: Effect parameters
                - fade_in_duration: Duration of fade-in (default: 0.5)
                - fade_out_duration: Duration of fade-out (default: 0.5)
                - fade_type: Type of fade ('both', 'in', 'out') (default: 'both')

        Returns:
            TextClip with fade effect applied
        """
        # Get parameters with defaults
        fade_in_duration = float(params.get('fade_in_duration', 0.5))
        fade_out_duration = float(params.get('fade_out_duration', 0.5))
        fade_type = params.get('fade_type', 'both')

        # Get clip duration - ensure it's a float value
        # clip.duration might be a function or a float, handle both cases
        duration_value = clip.duration
        if callable(duration_value):
            duration_value = duration_value()
        clip_duration = float(duration_value) if duration_value is not None else 1.0

        # Ensure fade durations don't exceed clip duration
        total_fade = fade_in_duration + fade_out_duration
        if total_fade > clip_duration:
            # Scale down proportionally
            scale_factor = clip_duration / total_fade
            fade_in_duration = float(fade_in_duration * scale_factor)
            fade_out_duration = float(fade_out_duration * scale_factor)

        # Create opacity function for smooth fade in/out
        def make_opacity_function(fade_in_dur, fade_out_dur, fade_t, clip_dur):
            """Create opacity function with captured parameters"""
            def opacity_function(get_frame, t):
                """Calculate opacity at time t and modify the frame"""
                opacity = 1.0

                # Fade in
                if fade_t in ['both', 'in'] and fade_in_dur > 0:
                    if t < fade_in_dur:
                        opacity = min(opacity, t / fade_in_dur)

                # Fade out
                if fade_t in ['both', 'out'] and fade_out_dur > 0:
                    fade_out_start = clip_dur - fade_out_dur
                    if t > fade_out_start:
                        time_into_fadeout = t - fade_out_start
                        opacity = min(opacity, 1.0 - (time_into_fadeout / fade_out_dur))

                opacity = max(0.0, min(1.0, opacity))

                # Get the original frame and apply opacity
                frame = get_frame(t)
                # Apply opacity by multiplying the alpha channel or the entire frame
                return (opacity * frame).astype('uint8')
            return opacity_function

        # Apply opacity function to clip using fl()
        opacity_func = make_opacity_function(fade_in_duration, fade_out_duration, fade_type, clip_duration)
        clip = clip.fl(opacity_func)

        return clip
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get default parameters for fade text effect
        
        Returns:
            Dictionary of default parameters
        """
        return {
            'fade_in_duration': 0.5,
            'fade_out_duration': 0.5,
            'fade_type': 'both'
        }
    
    def get_parameter_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about effect parameters
        
        Returns:
            Dictionary describing each parameter
        """
        return {
            'fade_in_duration': {
                'type': 'float',
                'description': 'Duration of fade-in effect in seconds',
                'default': 0.5,
                'min': 0.0,
                'max': 5.0
            },
            'fade_out_duration': {
                'type': 'float',
                'description': 'Duration of fade-out effect in seconds',
                'default': 0.5,
                'min': 0.0,
                'max': 5.0
            },
            'fade_type': {
                'type': 'string',
                'description': 'Type of fade transition',
                'default': 'both',
                'options': ['both', 'in', 'out']
            }
        }

