"""
Shorts Video Generation Service
Generates vertical YouTube Shorts videos (9:16 aspect ratio) with:
1. News video with thumbnail overlay at the top
2. Subscribe video appended at the end (sequential playback)
"""

import os
import logging
from typing import Optional, Dict, Any
from moviepy.editor import (
    VideoFileClip, ImageClip, CompositeVideoClip,
    concatenate_videoclips, TextClip
)
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import subprocess


class ShortsGenerationService:
    """Service for generating YouTube Shorts videos"""

    def __init__(self, config, logger: Optional[logging.Logger] = None):
        """
        Initialize Shorts Generation Service

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # YouTube Shorts dimensions (9:16 aspect ratio)
        self.shorts_width = 1080
        self.shorts_height = 1920

        # Layout configuration for thumbnail overlay
        self.thumbnail_height = 300  # Height of thumbnail overlay at top
        
    def generate_short(
        self,
        news_video_path: str,
        thumbnail_path: str,
        title: str,
        output_dir: str,
        subscribe_video_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a YouTube Short from news video
        
        Args:
            news_video_path: Path to the news video file
            thumbnail_path: Path to the thumbnail image
            title: News title for overlay
            output_dir: Directory to save the short
            subscribe_video_path: Path to subscribe video (optional)
            
        Returns:
            Dictionary with status and short_path
        """
        try:
            self.logger.info(f"🎬 Generating YouTube Short for: {title[:50]}...")
            
            # Validate inputs
            if not os.path.exists(news_video_path):
                return {
                    'status': 'error',
                    'error': f'News video not found: {news_video_path}'
                }
            
            if not os.path.exists(thumbnail_path):
                return {
                    'status': 'error',
                    'error': f'Thumbnail not found: {thumbnail_path}'
                }
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Generate short video path - simple filename
            short_filename = "short.mp4"
            short_path = os.path.join(output_dir, short_filename)
            
            # Step 1: Create news video with thumbnail overlay
            self.logger.info("🎥 Creating news video with thumbnail overlay...")
            news_clip = self._create_news_video_with_thumbnail(
                news_video_path,
                thumbnail_path,
                title
            )

            # Save news clip to temp file
            temp_dir = '/app/temp'
            os.makedirs(temp_dir, exist_ok=True)
            temp_news_path = os.path.join(temp_dir, 'news_with_thumbnail.mp4')

            self.logger.info(f"💾 Writing news video with thumbnail to temp file...")
            news_clip.write_videofile(
                temp_news_path,
                codec='libx264',
                audio_codec='aac',
                fps=30,
                preset='medium',
                bitrate='5000k',
                threads=4,
                logger=None
            )

            # Close the clip to free resources
            news_clip.close()

            # Step 2: Prepare video paths for concatenation
            video_paths = [temp_news_path]

            if subscribe_video_path and os.path.exists(subscribe_video_path):
                self.logger.info("📢 Processing subscribe video...")
                scaled_subscribe_path = self._process_subscribe_video(subscribe_video_path)
                video_paths.append(scaled_subscribe_path)
            else:
                self.logger.warning("⚠️ Subscribe video not found, skipping...")

            # Step 3: Concatenate videos using FFmpeg
            if len(video_paths) == 1:
                # Only news video, just copy it
                self.logger.info("📋 Single video - copying directly")
                import subprocess
                subprocess.run(['cp', video_paths[0], short_path], check=True)
            else:
                # Concatenate news + subscribe using FFmpeg
                self.logger.info(f"🎨 Concatenating {len(video_paths)} videos using FFmpeg...")
                self._concatenate_videos_ffmpeg(video_paths, short_path)
            
            # Get file size
            file_size_mb = os.path.getsize(short_path) / (1024 * 1024)

            # Get duration using ffprobe
            import subprocess
            try:
                duration_result = subprocess.run([
                    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1', short_path
                ], capture_output=True, text=True, check=True)
                duration = float(duration_result.stdout.strip())
            except:
                duration = 0.0

            self.logger.info(f"✅ Short generated successfully: {short_path}")
            self.logger.info(f"📊 File size: {file_size_mb:.2f} MB")
            self.logger.info(f"⏱️ Duration: {duration:.2f}s")

            return {
                'status': 'success',
                'short_path': short_path,
                'file_size_mb': round(file_size_mb, 2),
                'duration': duration,
                'dimensions': f"{self.shorts_width}x{self.shorts_height}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error generating short: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _create_news_video_with_thumbnail(
        self,
        news_video_path: str,
        thumbnail_path: str,
        title: str
    ) -> VideoFileClip:
        """
        Create news video with thumbnail overlay at the top

        Args:
            news_video_path: Path to news video
            thumbnail_path: Path to thumbnail image
            title: News title

        Returns:
            VideoFileClip with thumbnail overlay
        """
        try:
            # Load news video
            video = VideoFileClip(news_video_path)

            # Resize video to shorts dimensions (9:16 aspect ratio)
            # Calculate scaling to fit width
            scale_factor = self.shorts_width / video.w
            new_height = int(video.h * scale_factor)

            # Resize video
            video_resized = video.resize(width=self.shorts_width)

            # If video is taller than shorts height, crop it
            if new_height > self.shorts_height:
                # Center crop
                y_center = new_height // 2
                y1 = y_center - (self.shorts_height // 2)
                y2 = y1 + self.shorts_height
                video_resized = video_resized.crop(y1=y1, y2=y2)
            # If video is shorter, pad with black bars
            elif new_height < self.shorts_height:
                # Create black background
                from moviepy.editor import ColorClip
                background = ColorClip(
                    size=(self.shorts_width, self.shorts_height),
                    color=(0, 0, 0),
                    duration=video_resized.duration
                )
                # Center video on background
                y_offset = (self.shorts_height - new_height) // 2
                video_resized = CompositeVideoClip([
                    background,
                    video_resized.set_position(('center', y_offset))
                ], size=(self.shorts_width, self.shorts_height))

            # Create thumbnail overlay
            thumbnail_clip = self._create_thumbnail_overlay(thumbnail_path, video_resized.duration)

            # Composite video with thumbnail overlay at top
            final_video = CompositeVideoClip([
                video_resized,
                thumbnail_clip.set_position(('center', 0))
            ], size=(self.shorts_width, self.shorts_height))

            # Preserve audio from original video
            final_video = final_video.set_audio(video.audio)

            return final_video

        except Exception as e:
            self.logger.error(f"Error creating news video with thumbnail: {str(e)}")
            raise

    def _create_thumbnail_overlay(self, thumbnail_path: str, duration: float) -> ImageClip:
        """Create thumbnail overlay for top of video"""
        try:
            # Load and resize thumbnail
            img = Image.open(thumbnail_path)
            img = img.resize((self.shorts_width, self.thumbnail_height), Image.Resampling.LANCZOS)

            # Add semi-transparent overlay for better visibility
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 80))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay)

            # Save processed thumbnail
            temp_thumb_path = thumbnail_path.replace('.jpg', '_shorts_overlay.png')
            img.save(temp_thumb_path, 'PNG')

            # Create image clip with duration
            return ImageClip(temp_thumb_path).set_duration(duration)

        except Exception as e:
            self.logger.error(f"Error creating thumbnail overlay: {str(e)}")
            # Create fallback black image
            fallback = Image.new('RGB', (self.shorts_width, self.thumbnail_height), (0, 0, 0))
            fallback_path = os.path.join(os.path.dirname(thumbnail_path), 'fallback_overlay.jpg')
            fallback.save(fallback_path, 'JPEG')
            return ImageClip(fallback_path).set_duration(duration)
    
    def _concatenate_videos_ffmpeg(self, video_paths: list, output_path: str):
        """
        Concatenate videos using FFmpeg concat demuxer (simple concatenation without transitions)

        Args:
            video_paths: List of video file paths to concatenate
            output_path: Output path for concatenated video
        """
        import subprocess

        try:
            # Create concat file for FFmpeg
            temp_dir = '/app/temp'
            concat_file = os.path.join(temp_dir, 'concat_list.txt')

            with open(concat_file, 'w') as f:
                for video_path in video_paths:
                    f.write(f"file '{video_path}'\n")

            # Concatenate using FFmpeg concat demuxer
            # This is the simplest method and preserves audio perfectly
            result = subprocess.run([
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',  # Copy streams without re-encoding
                output_path
            ], check=True, capture_output=True, text=True)

            self.logger.info(f"✅ Videos concatenated successfully")

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ FFmpeg concatenation error: {e.stderr}")
            raise

    def _process_subscribe_video(self, subscribe_video_path: str) -> str:
        """
        Process subscribe video to fit shorts dimensions using FFmpeg

        Args:
            subscribe_video_path: Path to subscribe video

        Returns:
            Path to processed subscribe video
        """
        try:
            import subprocess

            # Create temp directory if it doesn't exist
            temp_dir = '/app/temp'
            os.makedirs(temp_dir, exist_ok=True)

            # Output path for scaled subscribe video
            scaled_subscribe_path = os.path.join(temp_dir, 'subscribe_shorts_scaled.mp4')

            # Scale subscribe video to shorts dimensions (1080x1920) using FFmpeg
            # This preserves audio automatically with -c:a copy
            self.logger.info(f"📐 Scaling subscribe video to {self.shorts_width}x{self.shorts_height}")

            result = subprocess.run([
                'ffmpeg', '-y', '-i', subscribe_video_path,
                '-vf', f'scale={self.shorts_width}:{self.shorts_height}:force_original_aspect_ratio=decrease,pad={self.shorts_width}:{self.shorts_height}:(ow-iw)/2:(oh-ih)/2,fps=30',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-c:a', 'copy',  # Copy audio without re-encoding
                scaled_subscribe_path
            ], check=True, capture_output=True, text=True)

            self.logger.info(f"✅ Subscribe video scaled successfully")
            return scaled_subscribe_path

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ FFmpeg scaling error: {e.stderr}")
            # If scaling fails, return original video
            self.logger.warning(f"⚠️ Using original subscribe video without scaling")
            return subscribe_video_path
        except Exception as e:
            self.logger.error(f"Error processing subscribe video: {str(e)}")
            raise

