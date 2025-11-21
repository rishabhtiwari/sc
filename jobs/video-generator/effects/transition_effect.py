"""
Transition Effect - Smooth transitions between video clips

This effect provides various transition types for smooth video transitions:
- Crossfade: Gradual fade from one clip to another
- Fade to Black: Fade out to black, then fade in from black
- Slide: Slide transition (left, right, up, down)
- Wipe: Wipe transition (horizontal or vertical)
"""

import numpy as np
from typing import List, Optional, Dict, Any
from moviepy.editor import VideoClip, CompositeVideoClip, ColorClip
from .base_effect import BaseEffect


class TransitionEffect(BaseEffect):
    """
    Smooth transition effect for video clips
    
    Supports multiple transition types:
    - crossfade: Gradual blend between clips
    - fade_black: Fade to black then fade from black
    - slide_left: Slide from right to left
    - slide_right: Slide from left to right
    - slide_up: Slide from bottom to top
    - slide_down: Slide from top to bottom
    - wipe_horizontal: Horizontal wipe
    - wipe_vertical: Vertical wipe
    """
    
    SUPPORTED_TRANSITIONS = [
        'crossfade',
        'fade_black',
        'slide_left',
        'slide_right',
        'slide_up',
        'slide_down',
        'wipe_horizontal',
        'wipe_vertical'
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, logger=None):
        """Initialize transition effect"""
        super().__init__(config, logger)
        
        # Default configuration
        self.default_duration = self.config.get('default_duration', 1.0)  # 1 second default
        self.default_type = self.config.get('default_type', 'crossfade')
    
    def apply(self, clip: VideoClip, **kwargs) -> VideoClip:
        """
        This effect is not applied to a single clip.
        Use apply_transition() method instead to transition between two clips.
        """
        self.log_warning("TransitionEffect.apply() called on single clip. Use apply_transition() instead.")
        return clip
    
    def apply_transition(self, clip1: VideoClip, clip2: VideoClip, 
                        transition_type: str = 'crossfade',
                        duration: float = 1.0) -> VideoClip:
        """
        Apply transition between two video clips
        
        Args:
            clip1: First video clip (outgoing)
            clip2: Second video clip (incoming)
            transition_type: Type of transition to apply
            duration: Duration of transition in seconds
            
        Returns:
            Combined video clip with transition
        """
        if transition_type not in self.SUPPORTED_TRANSITIONS:
            self.log_warning(f"Unsupported transition type '{transition_type}', using 'crossfade'")
            transition_type = 'crossfade'
        
        self.log_info(f"Applying {transition_type} transition (duration: {duration}s)")
        
        # Route to appropriate transition method
        if transition_type == 'crossfade':
            return self._crossfade_transition(clip1, clip2, duration)
        elif transition_type == 'fade_black':
            return self._fade_black_transition(clip1, clip2, duration)
        elif transition_type.startswith('slide_'):
            direction = transition_type.split('_')[1]
            return self._slide_transition(clip1, clip2, duration, direction)
        elif transition_type.startswith('wipe_'):
            orientation = transition_type.split('_')[1]
            return self._wipe_transition(clip1, clip2, duration, orientation)
        else:
            return self._crossfade_transition(clip1, clip2, duration)
    
    def _crossfade_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """
        Fast crossfade transition - simple concatenation with clean audio

        Args:
            clip1: First clip
            clip2: Second clip
            duration: Transition duration (not used for speed)

        Returns:
            Combined clip with clean audio cut
        """
        self.logger.info(f"[TransitionEffect] Applying fast transition with clean audio")

        # Ensure clips have the same size
        if clip1.size != clip2.size:
            clip2 = clip2.resize(clip1.size)

        # Separate audio and video for clean audio transition
        clip1_audio = clip1.audio
        clip2_audio = clip2.audio

        # Simply concatenate videos (no complex effects for speed)
        from moviepy.video.compositing.concatenate import concatenate_videoclips
        final_video = concatenate_videoclips([clip1, clip2], method="compose")

        # Concatenate audio cleanly (no overlap)
        if clip1_audio and clip2_audio:
            from moviepy.audio.AudioClip import concatenate_audioclips
            final_audio = concatenate_audioclips([clip1_audio, clip2_audio])
            final_video = final_video.set_audio(final_audio)

        return final_video
    
    def _fade_black_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """
        Fade to black transition - fade out to black, then fade in from black
        
        Args:
            clip1: First clip (fades out to black)
            clip2: Second clip (fades in from black)
            duration: Transition duration (split between fade out and fade in)
            
        Returns:
            Combined clip with fade to black transition
        """
        # Ensure clips have the same size
        if clip1.size != clip2.size:
            clip2 = clip2.resize(clip1.size)
        
        fade_duration = duration / 2  # Split duration between fade out and fade in
        
        # Create black clip for the middle
        black_clip = ColorClip(
            size=clip1.size,
            color=(0, 0, 0),
            duration=fade_duration
        ).set_start(clip1.duration - fade_duration)
        
        # Fade out clip1
        clip1_faded = clip1.fadeout(fade_duration)
        
        # Fade in clip2
        clip2_faded = clip2.fadein(fade_duration)
        clip2_positioned = clip2_faded.set_start(clip1.duration)
        
        # Composite all clips
        final_clip = CompositeVideoClip([clip1_faded, black_clip, clip2_positioned])
        
        return final_clip
    
    def _slide_transition(self, clip1: VideoClip, clip2: VideoClip, 
                         duration: float, direction: str) -> VideoClip:
        """
        Slide transition - one clip slides in while the other slides out
        
        Args:
            clip1: First clip (slides out)
            clip2: Second clip (slides in)
            duration: Transition duration
            direction: Slide direction (left, right, up, down)
            
        Returns:
            Combined clip with slide transition
        """
        # Ensure clips have the same size
        if clip1.size != clip2.size:
            clip2 = clip2.resize(clip1.size)
        
        w, h = clip1.size
        transition_start = clip1.duration - duration
        
        def position_func(t):
            """Calculate position based on time and direction"""
            if t < transition_start:
                return ('center', 'center')
            
            # Progress from 0 to 1 during transition
            progress = (t - transition_start) / duration
            
            if direction == 'left':
                x = int(-w * progress)
                return (x, 'center')
            elif direction == 'right':
                x = int(w * progress)
                return (x, 'center')
            elif direction == 'up':
                y = int(-h * progress)
                return ('center', y)
            elif direction == 'down':
                y = int(h * progress)
                return ('center', y)
            else:
                return ('center', 'center')
        
        def position_func_incoming(t):
            """Calculate position for incoming clip"""
            if t < transition_start:
                # Position off-screen before transition
                if direction == 'left':
                    return (w, 'center')
                elif direction == 'right':
                    return (-w, 'center')
                elif direction == 'up':
                    return ('center', h)
                elif direction == 'down':
                    return ('center', -h)
            
            # Progress from 0 to 1 during transition
            progress = (t - transition_start) / duration
            
            if direction == 'left':
                x = int(w - w * progress)
                return (x, 'center')
            elif direction == 'right':
                x = int(-w + w * progress)
                return (x, 'center')
            elif direction == 'up':
                y = int(h - h * progress)
                return ('center', y)
            elif direction == 'down':
                y = int(-h + h * progress)
                return ('center', y)
            else:
                return ('center', 'center')
        
        # Apply position animation to clip1 (sliding out)
        clip1_sliding = clip1.set_position(position_func)
        
        # Position clip2 to start at transition point (sliding in)
        clip2_sliding = clip2.set_start(transition_start).set_position(position_func_incoming)
        
        # Composite the clips
        final_clip = CompositeVideoClip([clip1_sliding, clip2_sliding], size=clip1.size)
        
        return final_clip
    
    def _wipe_transition(self, clip1: VideoClip, clip2: VideoClip, 
                        duration: float, orientation: str) -> VideoClip:
        """
        Wipe transition - one clip wipes over the other
        
        Args:
            clip1: First clip (being wiped away)
            clip2: Second clip (wiping in)
            duration: Transition duration
            orientation: Wipe orientation (horizontal or vertical)
            
        Returns:
            Combined clip with wipe transition
        """
        # Ensure clips have the same size
        if clip1.size != clip2.size:
            clip2 = clip2.resize(clip1.size)
        
        w, h = clip1.size
        transition_start = clip1.duration - duration
        
        def make_frame(t):
            """Create frame with wipe effect"""
            if t < transition_start:
                return clip1.get_frame(t)
            elif t >= clip1.duration:
                return clip2.get_frame(t - transition_start)
            
            # During transition
            progress = (t - transition_start) / duration
            frame1 = clip1.get_frame(t)
            frame2 = clip2.get_frame(t - transition_start)
            
            # Create mask for wipe
            if orientation == 'horizontal':
                # Wipe from left to right
                split_point = int(w * progress)
                frame1[:, split_point:] = frame2[:, split_point:]
            else:  # vertical
                # Wipe from top to bottom
                split_point = int(h * progress)
                frame1[split_point:, :] = frame2[split_point:, :]
            
            return frame1
        
        # Create the wiped clip
        final_duration = clip1.duration + clip2.duration - duration
        final_clip = VideoClip(make_frame, duration=final_duration)
        final_clip = final_clip.set_fps(clip1.fps)
        
        # Copy audio from both clips
        if clip1.audio is not None:
            audio1 = clip1.audio
            if clip2.audio is not None:
                audio2 = clip2.audio.set_start(transition_start)
                from moviepy.audio.AudioClip import CompositeAudioClip
                final_clip = final_clip.set_audio(CompositeAudioClip([audio1, audio2]))
            else:
                final_clip = final_clip.set_audio(audio1)
        elif clip2.audio is not None:
            final_clip = final_clip.set_audio(clip2.audio.set_start(transition_start))
        
        return final_clip
    
    def validate_params(self, **kwargs) -> bool:
        """Validate transition parameters"""
        transition_type = kwargs.get('transition_type', self.default_type)
        duration = kwargs.get('duration', self.default_duration)
        
        if transition_type not in self.SUPPORTED_TRANSITIONS:
            self.log_error(f"Invalid transition type: {transition_type}")
            return False
        
        if duration <= 0:
            self.log_error(f"Invalid duration: {duration}")
            return False
        
        return True

