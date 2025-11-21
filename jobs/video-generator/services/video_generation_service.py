"""
Video Generation Service - Core video processing and composition
"""

import os
import sys
import requests
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
from pathlib import Path

# Add common directory to path for job framework
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from moviepy.editor import (
    VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip,
    TextClip, concatenate_videoclips
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from common.utils.logger import setup_logger

# Add effects directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from effects import EffectsFactory


class VideoGenerationService:
    """Service for generating videos from news articles with audio and background images"""
    
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or setup_logger('video-generation-service', config.LOG_FILE)

        # Ensure output directories exist
        os.makedirs(self.config.VIDEO_OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.config.TEMP_DIR, exist_ok=True)

        # Initialize effects factory
        self.effects_factory = EffectsFactory(logger=self.logger)

        self.logger.info("Video Generation Service initialized")
        self.logger.info(f"Available effects: {self.effects_factory.get_available_effects()}")
    
    def generate_video_for_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate video for a single news article
        
        Args:
            article_data: Dictionary containing article information with:
                - id: Article ID
                - title: Article title
                - description: Article description
                - audio_paths: Dictionary with audio file paths (title, description, content, short_summary)
                - image: Image URL
                
        Returns:
            Dictionary with generation result
        """
        try:
            article_id = article_data.get('id')
            title = article_data.get('title', '')
            description = article_data.get('description', '')
            audio_paths = article_data.get('audio_paths', {})
            # Use short_summary audio as primary, fallback to content, description, then title
            audio_path = audio_paths.get('short_summary') or audio_paths.get('content') or audio_paths.get('description') or audio_paths.get('title')
            image_url = article_data.get('image')
            
            self.logger.info(f"🎬 Starting video generation for article: {article_id}")
            
            # Validate inputs
            validation_result = self._validate_inputs(article_data)
            if not validation_result['valid']:
                return {
                    'status': 'error',
                    'error': validation_result['error'],
                    'article_id': article_id
                }
            
            # Create output directory for this article
            output_dir = os.path.join(self.config.VIDEO_OUTPUT_DIR, article_id)
            os.makedirs(output_dir, exist_ok=True)
            
            # Step 1: Download and process background image
            self.logger.info(f"📸 Downloading background image from: {image_url}")
            background_image_path = self._download_and_process_image(image_url, output_dir)
            
            if not background_image_path:
                return {
                    'status': 'error',
                    'error': 'Failed to download or process background image',
                    'article_id': article_id
                }
            
            # Step 2: Download audio file from audio-generation service
            self.logger.info(f"🎵 Downloading audio file for article: {article_id}")
            local_audio_path = self._download_audio_file(article_id, audio_paths, output_dir)

            if not local_audio_path:
                return {
                    'status': 'error',
                    'error': 'Failed to download audio file',
                    'article_id': article_id
                }

            # Step 3: Validate and get audio duration
            self.logger.info(f"🔍 DEBUG: Validating audio file: {local_audio_path}")

            # Check if file exists and has content
            if not os.path.exists(local_audio_path):
                self.logger.error(f"❌ Audio file does not exist: {local_audio_path}")
                return {
                    'status': 'error',
                    'error': 'Audio file does not exist after download',
                    'article_id': article_id
                }

            file_size = os.path.getsize(local_audio_path)
            self.logger.info(f"🔍 DEBUG: Audio file size: {file_size} bytes")

            if file_size == 0:
                self.logger.error(f"❌ Audio file is empty: {local_audio_path}")
                return {
                    'status': 'error',
                    'error': 'Downloaded audio file is empty',
                    'article_id': article_id
                }

            audio_duration = self._get_audio_duration(local_audio_path)
            self.logger.info(f"🔍 DEBUG: Audio duration: {audio_duration} seconds")

            if audio_duration <= 0:
                return {
                    'status': 'error',
                    'error': 'Invalid audio file or duration',
                    'article_id': article_id
                }

            self.logger.info(f"🎵 Audio duration: {audio_duration:.2f} seconds")
            
            # Step 4: Create video composition
            video_path = self._create_video_composition(
                background_image_path=background_image_path,
                audio_path=local_audio_path,
                title=title,
                description=description,
                duration=audio_duration,
                output_dir=output_dir
            )
            
            if not video_path:
                return {
                    'status': 'error',
                    'error': 'Failed to create video composition',
                    'article_id': article_id
                }
            
            # Step 5: Generate thumbnail
            thumbnail_path = self._generate_thumbnail(video_path, output_dir)
            
            # Calculate file size
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)

            # Convert local file path to relative path for database storage
            # video_path is like: /app/public/article_id/video.mp4
            # Convert to: /public/article_id/video.mp4
            relative_video_path = video_path.replace('/app', '')
            relative_thumbnail_path = thumbnail_path.replace('/app', '') if thumbnail_path else None

            self.logger.info(f"✅ Video generation completed for article {article_id}")
            self.logger.info(f"📁 Video saved to: {video_path}")
            self.logger.info(f"🔗 Relative path for DB: {relative_video_path}")
            self.logger.info(f"📊 File size: {file_size_mb:.2f} MB")

            return {
                'status': 'success',
                'article_id': article_id,
                'video_path': relative_video_path,
                'thumbnail_path': relative_thumbnail_path,
                'duration_seconds': audio_duration,
                'file_size_mb': round(file_size_mb, 2),
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error generating video for article {article_data.get('id', 'unknown')}: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'article_id': article_data.get('id', 'unknown')
            }
    
    def _validate_inputs(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data for video generation"""
        errors = []
        
        # Check required fields
        required_fields = ['id', 'title', 'audio_paths', 'image']
        for field in required_fields:
            if not article_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Check if audio paths are available (we'll download them from audio-generation service)
        audio_paths = article_data.get('audio_paths', {})
        if not audio_paths or not any(audio_paths.values()):
            errors.append("No valid audio paths found in audio_paths")
        
        # Check image URL format
        image_url = article_data.get('image')
        if image_url:
            try:
                parsed = urlparse(image_url)
                if not parsed.scheme or not parsed.netloc:
                    errors.append("Invalid image URL format")
            except Exception:
                errors.append("Invalid image URL")
        
        return {
            'valid': len(errors) == 0,
            'error': '; '.join(errors) if errors else None
        }
    
    def _download_and_process_image(self, image_url: str, output_dir: str) -> Optional[str]:
        """Download and process background image"""
        try:
            # Download image
            response = requests.get(
                image_url, 
                timeout=self.config.IMAGE_DOWNLOAD_TIMEOUT,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; VideoGenerator/1.0)'}
            )
            response.raise_for_status()
            
            # Check file size
            content_length = len(response.content)
            if content_length > self.config.MAX_IMAGE_SIZE_MB * 1024 * 1024:
                self.logger.warning(f"Image too large: {content_length / (1024*1024):.2f} MB")
                return None
            
            # Save original image
            image_filename = f"background_original{self._get_image_extension(image_url)}"
            original_path = os.path.join(output_dir, image_filename)
            
            with open(original_path, 'wb') as f:
                f.write(response.content)
            
            # Process and resize image
            processed_path = self._resize_and_process_image(original_path, output_dir)
            
            return processed_path
            
        except Exception as e:
            self.logger.error(f"Error downloading image from {image_url}: {str(e)}")
            return None
    
    def _get_image_extension(self, url: str) -> str:
        """Get appropriate image extension from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
            if path.endswith(ext):
                return ext
        
        return '.jpg'  # Default to jpg
    
    def _resize_and_process_image(self, image_path: str, output_dir: str) -> str:
        """Resize and process image for video background"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate dimensions maintaining aspect ratio
                target_width = self.config.VIDEO_WIDTH
                target_height = self.config.VIDEO_HEIGHT
                
                # Resize to cover the entire video frame
                img_ratio = img.width / img.height
                target_ratio = target_width / target_height
                
                if img_ratio > target_ratio:
                    # Image is wider, fit by height
                    new_height = target_height
                    new_width = int(target_height * img_ratio)
                else:
                    # Image is taller, fit by width
                    new_width = target_width
                    new_height = int(target_width / img_ratio)
                
                # Resize image
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create final image with exact video dimensions
                final_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))
                
                # Center the resized image
                x_offset = (target_width - new_width) // 2
                y_offset = (target_height - new_height) // 2
                final_img.paste(img_resized, (x_offset, y_offset))
                
                # Apply subtle dark overlay for better text readability
                overlay = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 80))
                final_img = Image.alpha_composite(final_img.convert('RGBA'), overlay).convert('RGB')
                
                # Save processed image
                processed_path = os.path.join(output_dir, 'background_processed.jpg')
                final_img.save(processed_path, 'JPEG', quality=90)
                
                return processed_path
                
        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {str(e)}")
            return image_path  # Return original if processing fails
    
    def _download_audio_file(self, article_id: str, audio_paths: Dict[str, str], output_dir: str) -> Optional[str]:
        """
        Download audio file from audio-generation service

        Args:
            article_id: Article ID
            audio_paths: Dictionary with audio paths (title, description, content, short_summary)
            output_dir: Directory to save the audio file

        Returns:
            Path to downloaded audio file or None if failed
        """
        try:
            # Determine which audio type to use (prioritize short_summary > content > description > title)
            audio_type = None
            if audio_paths.get('short_summary'):
                audio_type = 'short_summary'
            elif audio_paths.get('content'):
                audio_type = 'content'
            elif audio_paths.get('description'):
                audio_type = 'description'
            elif audio_paths.get('title'):
                audio_type = 'title'

            if not audio_type:
                self.logger.error(f"No audio paths found for article {article_id}")
                return None

            # Construct audio-generation service URL
            audio_service_url = f"http://audio-generation-factory:3000/api/audio/{article_id}/{audio_type}"

            self.logger.info(f"🎵 Downloading {audio_type} audio from: {audio_service_url}")

            # Download audio file
            response = requests.get(audio_service_url, timeout=30)

            if response.status_code == 404:
                self.logger.warning(f"Audio file not found: {audio_service_url}")
                return None
            elif response.status_code != 200:
                self.logger.error(f"Failed to download audio file: HTTP {response.status_code}")
                return None

            # Save audio file locally
            local_audio_filename = f"{audio_type}.wav"
            local_audio_path = os.path.join(output_dir, local_audio_filename)

            self.logger.info(f"🔍 DEBUG: Saving audio to: {local_audio_path}")
            self.logger.info(f"🔍 DEBUG: Response content length: {len(response.content)} bytes")

            with open(local_audio_path, 'wb') as f:
                f.write(response.content)

            # Verify the file was written correctly
            if os.path.exists(local_audio_path):
                actual_size = os.path.getsize(local_audio_path)
                self.logger.info(f"🔍 DEBUG: File written successfully, size: {actual_size} bytes")

                if actual_size != len(response.content):
                    self.logger.warning(f"⚠️ File size mismatch: expected {len(response.content)}, got {actual_size}")
            else:
                self.logger.error(f"❌ File was not created: {local_audio_path}")
                return None

            self.logger.info(f"✅ Audio file downloaded successfully: {local_audio_path}")
            return local_audio_path

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error downloading audio file: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error downloading audio file for article {article_id}: {str(e)}")
            return None

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            with AudioFileClip(audio_path) as audio:
                return audio.duration
        except Exception as e:
            self.logger.error(f"Error getting audio duration from {audio_path}: {str(e)}")
            return 0.0

    def _create_video_composition(self, background_image_path: str, audio_path: str,
                                title: str, description: str, duration: float,
                                output_dir: str) -> Optional[str]:
        """Create the final video composition"""
        try:
            self.logger.info("🎬 Creating video composition...")

            # Load background image as video clip
            background_clip = ImageClip(background_image_path, duration=duration)

            # Apply Ken Burns effect if enabled
            if self.config.ENABLE_KEN_BURNS:
                background_clip = self.effects_factory.apply_effect(
                    'ken_burns',
                    background_clip,
                    config={
                        'zoom_start': self.config.KEN_BURNS_ZOOM_START,
                        'zoom_end': self.config.KEN_BURNS_ZOOM_END,
                        'easing': self.config.KEN_BURNS_EASING
                    },
                    duration=duration
                )

            # Load audio
            audio_clip = AudioFileClip(audio_path)

            # Create text overlays
            text_clips = self._create_text_overlays(title, description, duration)

            # Combine all clips
            final_clips = [background_clip] + text_clips
            final_video = CompositeVideoClip(final_clips)

            # Apply logo watermark effect if enabled
            if self.config.ENABLE_LOGO_WATERMARK:
                final_video = self.effects_factory.apply_effect(
                    'logo_watermark',
                    final_video,
                    config={
                        'logo_path': self.config.LOGO_PATH,
                        'position': self.config.LOGO_POSITION,
                        'opacity': self.config.LOGO_OPACITY,
                        'scale': self.config.LOGO_SCALE,
                        'margin': self.config.LOGO_MARGIN
                    }
                )

            # Apply background music effect if enabled
            if self.config.ENABLE_BACKGROUND_MUSIC:
                self.logger.info("🎵 Adding background music to video...")
                final_video = self.effects_factory.apply_effect(
                    'background_music',
                    None,  # Not used by this effect
                    video_clip=final_video,
                    voice_audio=audio_clip,
                    duration=duration,
                    music_path=self.config.BACKGROUND_MUSIC_PATH if os.path.exists(self.config.BACKGROUND_MUSIC_PATH) else None,
                    music_volume=self.config.BACKGROUND_MUSIC_VOLUME,
                    voice_volume=self.config.VOICE_VOLUME,
                    fade_in_duration=self.config.MUSIC_FADE_IN_DURATION,
                    fade_out_duration=self.config.MUSIC_FADE_OUT_DURATION
                )
            else:
                # Set audio without background music
                final_video = final_video.set_audio(audio_clip)

            # Output path
            output_path = os.path.join(output_dir, 'video.mp4')

            # Get quality settings
            quality_settings = self.config.get_video_quality_settings()

            # Write video file
            self.logger.info(f"💾 Writing video to: {output_path}")

            # Create a unique temporary audio file name to avoid conflicts
            import uuid
            temp_audio_filename = f"temp_audio_{uuid.uuid4().hex[:8]}.m4a"
            temp_audio_path = os.path.join(self.config.TEMP_DIR, temp_audio_filename)

            # Ensure temp directory exists
            os.makedirs(self.config.TEMP_DIR, exist_ok=True)

            self.logger.info(f"🔍 DEBUG: Using temp audio file: {temp_audio_path}")

            final_video.write_videofile(
                output_path,
                fps=self.config.VIDEO_FPS,
                codec=self.config.VIDEO_CODEC,
                audio_codec=self.config.AUDIO_CODEC,
                temp_audiofile=temp_audio_path,
                remove_temp=True,
                verbose=False,
                logger=None  # Disable moviepy logging
            )

            # Clean up clips
            background_clip.close()
            audio_clip.close()
            final_video.close()
            for clip in text_clips:
                clip.close()

            return output_path

        except Exception as e:
            self.logger.error(f"Error creating video composition: {str(e)}")
            return None

    def _create_text_overlays(self, title: str, description: str, duration: float) -> List:
        """Create text overlay clips for title and description"""
        text_clips = []

        try:
            # Title overlay (appears for first 5 seconds or full duration if shorter)
            title_duration = min(5.0, duration)
            if title and title_duration > 0:
                title_clip = TextClip(
                    self._wrap_text(title, 40),  # Wrap at 40 characters
                    fontsize=self.config.TITLE_FONT_SIZE,
                    color=self.config.TEXT_COLOR
                ).set_position(('center', 0.1), relative=True).set_duration(title_duration)

                # Apply fade text effect if enabled
                if self.config.ENABLE_FADE_TEXT:
                    title_clip = self.effects_factory.apply_effect(
                        'fade_text',
                        title_clip,
                        fade_in_duration=self.config.FADE_TEXT_IN_DURATION,
                        fade_out_duration=self.config.FADE_TEXT_OUT_DURATION,
                        fade_type=self.config.FADE_TEXT_TYPE
                    )

                text_clips.append(title_clip)

            # Description overlay (appears after title, for remaining duration)
            if description and duration > title_duration:
                desc_start_time = title_duration
                desc_duration = duration - title_duration

                description_clip = TextClip(
                    self._wrap_text(description, 60),  # Wrap at 60 characters
                    fontsize=self.config.DESCRIPTION_FONT_SIZE,
                    color=self.config.TEXT_COLOR
                ).set_position(('center', 0.85), relative=True).set_start(desc_start_time).set_duration(desc_duration)

                # Apply fade text effect if enabled
                if self.config.ENABLE_FADE_TEXT:
                    description_clip = self.effects_factory.apply_effect(
                        'fade_text',
                        description_clip,
                        fade_in_duration=self.config.FADE_TEXT_IN_DURATION,
                        fade_out_duration=self.config.FADE_TEXT_OUT_DURATION,
                        fade_type=self.config.FADE_TEXT_TYPE
                    )

                text_clips.append(description_clip)

        except Exception as e:
            self.logger.error(f"Error creating text overlays: {str(e)}")

        return text_clips

    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to specified width"""
        import textwrap
        return '\n'.join(textwrap.wrap(text, width=width))

    def _generate_thumbnail(self, video_path: str, output_dir: str) -> Optional[str]:
        """Generate thumbnail from video"""
        try:
            thumbnail_path = os.path.join(output_dir, 'thumbnail.jpg')

            with VideoFileClip(video_path) as video:
                # Get frame at 1 second or middle of video
                frame_time = min(1.0, video.duration / 2)
                frame = video.get_frame(frame_time)

                # Save as image
                thumbnail_img = Image.fromarray(frame)
                thumbnail_img.save(thumbnail_path, 'JPEG', quality=85)

            return thumbnail_path

        except Exception as e:
            self.logger.error(f"Error generating thumbnail: {str(e)}")
            return None
