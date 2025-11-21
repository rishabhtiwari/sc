"""
Background Music Effect for Video Generation

This effect adds royalty-free background music to videos with volume control.
"""

import os
import logging
from typing import Optional, Dict, Any
from moviepy.editor import AudioFileClip, CompositeAudioClip
from .base_effect import BaseEffect


class BackgroundMusicEffect(BaseEffect):
    """Effect that adds background music to videos"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self.name = "background_music"
        self.config = config or {}
    
    def validate_params(self, **kwargs) -> Dict[str, Any]:
        """
        Validate parameters for background music effect
        
        Required parameters:
            - video_clip: The video clip to add music to
            - voice_audio: The voice/narration audio clip
            - duration: Duration of the video in seconds
            
        Optional parameters:
            - music_path: Path to background music file (default: use built-in music)
            - music_volume: Volume of background music (0.0 to 1.0, default: 0.15)
            - voice_volume: Volume of voice audio (0.0 to 1.0, default: 1.0)
            - fade_in_duration: Fade in duration in seconds (default: 2.0)
            - fade_out_duration: Fade out duration in seconds (default: 2.0)
        """
        errors = []
        
        # Check required parameters
        if 'video_clip' not in kwargs:
            errors.append("video_clip is required")
        if 'voice_audio' not in kwargs:
            errors.append("voice_audio is required")
        if 'duration' not in kwargs:
            errors.append("duration is required")
        
        # Validate optional parameters
        music_volume = kwargs.get('music_volume', 0.15)
        if not isinstance(music_volume, (int, float)) or music_volume < 0 or music_volume > 1:
            errors.append("music_volume must be between 0.0 and 1.0")
        
        voice_volume = kwargs.get('voice_volume', 1.0)
        if not isinstance(voice_volume, (int, float)) or voice_volume < 0 or voice_volume > 1:
            errors.append("voice_volume must be between 0.0 and 1.0")
        
        fade_in = kwargs.get('fade_in_duration', 2.0)
        if not isinstance(fade_in, (int, float)) or fade_in < 0:
            errors.append("fade_in_duration must be a non-negative number")
        
        fade_out = kwargs.get('fade_out_duration', 2.0)
        if not isinstance(fade_out, (int, float)) or fade_out < 0:
            errors.append("fade_out_duration must be a non-negative number")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def apply(self, base_clip, **kwargs):
        """
        Apply background music effect to video
        
        Args:
            base_clip: Not used (music is applied to video_clip from kwargs)
            **kwargs: Effect parameters
            
        Returns:
            Video clip with background music added
        """
        try:
            # Get parameters
            video_clip = kwargs.get('video_clip')
            voice_audio = kwargs.get('voice_audio')
            duration = kwargs.get('duration')
            music_path = kwargs.get('music_path')
            music_volume = kwargs.get('music_volume', 0.15)
            voice_volume = kwargs.get('voice_volume', 1.0)
            fade_in_duration = kwargs.get('fade_in_duration', 2.0)
            fade_out_duration = kwargs.get('fade_out_duration', 2.0)
            
            self.log_info(f"Adding background music:")
            self.log_info(f"  Music volume: {music_volume}")
            self.log_info(f"  Voice volume: {voice_volume}")
            self.log_info(f"  Duration: {duration}s")
            self.log_info(f"  Fade in: {fade_in_duration}s, Fade out: {fade_out_duration}s")

            # If no music path provided, use default background music
            if not music_path:
                music_path = self._get_default_music_path()
                if not music_path:
                    self.log_warning("No background music file found, skipping music effect")
                    return video_clip.set_audio(voice_audio)

            self.log_info(f"  Music file: {music_path}")
            
            # Load background music
            background_music = AudioFileClip(music_path)
            
            # Loop music if it's shorter than the video duration
            if background_music.duration < duration:
                # Calculate how many times to loop
                loops_needed = int(duration / background_music.duration) + 1
                self.log_info(f"  Looping music {loops_needed} times to match video duration")

                # Create looped music by concatenating
                from moviepy.editor import concatenate_audioclips
                music_clips = [background_music] * loops_needed
                background_music = concatenate_audioclips(music_clips)

            # Trim music to exact duration
            background_music = background_music.subclip(0, duration)

            # Apply fade in and fade out to background music
            if fade_in_duration > 0:
                background_music = background_music.audio_fadein(fade_in_duration)
            if fade_out_duration > 0:
                background_music = background_music.audio_fadeout(fade_out_duration)

            # Adjust volumes
            background_music = background_music.volumex(music_volume)
            voice_audio_adjusted = voice_audio.volumex(voice_volume)

            # Composite the audio tracks (voice on top of music)
            composite_audio = CompositeAudioClip([background_music, voice_audio_adjusted])

            # Set the composite audio to the video
            final_video = video_clip.set_audio(composite_audio)

            self.log_info(f"  ✅ Background music added successfully")

            return final_video

        except Exception as e:
            self.log_error(f"Error applying background music effect: {str(e)}")
            # Return video with original voice audio if music fails
            return video_clip.set_audio(voice_audio)
    
    def _get_default_music_path(self) -> Optional[str]:
        """
        Get path to default background music file
        
        Returns:
            Path to music file or None if not found
        """
        # Check for music file in assets directory
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
        
        # List of possible music file names (royalty-free)
        music_files = [
            'background_music.mp3',
            'background_music.wav',
            'news_background.mp3',
            'news_background.wav'
        ]
        
        for music_file in music_files:
            music_path = os.path.join(assets_dir, music_file)
            if os.path.exists(music_path):
                return music_path
        
        return None

