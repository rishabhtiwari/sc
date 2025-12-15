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
            # Use unique temp file names based on output_dir to avoid race conditions in parallel processing
            temp_dir = '/app/temp'
            os.makedirs(temp_dir, exist_ok=True)
            import hashlib
            # Generate unique ID from output_dir (which contains article ID)
            unique_id = hashlib.md5(output_dir.encode()).hexdigest()[:8]
            temp_news_path_raw = os.path.join(temp_dir, f'news_with_thumbnail_raw_{unique_id}.mp4')
            temp_news_path = os.path.join(temp_dir, f'news_with_thumbnail_{unique_id}.mp4')

            self.logger.info(f"💾 Writing news video with thumbnail to temp file...")
            news_clip.write_videofile(
                temp_news_path_raw,
                codec='libx264',
                audio_codec='aac',
                fps=30,
                preset='medium',
                bitrate='5000k',
                threads=4,
                logger=None,
                ffmpeg_params=[
                    '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                    '-profile:v', 'high',  # H.264 high profile
                    '-level', '4.0',  # H.264 level 4.0
                    '-b:a', '192k',  # Audio bitrate
                    '-ar', '48000',  # Audio sample rate (48kHz)
                    '-ac', '2'  # Stereo audio
                ]
            )

            # Close the clip to free resources
            news_clip.close()

            # Ensure file is fully written to disk
            import time
            time.sleep(0.5)  # Give filesystem time to flush buffers

            # Verify the temp news video is valid before proceeding
            if not os.path.exists(temp_news_path_raw):
                raise Exception(f"Temp news video not created: {temp_news_path_raw}")

            temp_size = os.path.getsize(temp_news_path_raw) / (1024 * 1024)
            self.logger.info(f"✅ Temp news video created: {temp_size:.2f} MB")

            # Re-encode with FFmpeg to fix any NAL unit issues from MoviePy
            # This ensures the video is properly encoded for concatenation
            self.logger.info(f"🔧 Re-encoding video with FFmpeg to fix NAL units...")
            import subprocess
            try:
                subprocess.run([
                    'ffmpeg', '-y',
                    '-i', temp_news_path_raw,
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23',
                    '-pix_fmt', 'yuv420p',
                    '-profile:v', 'high',
                    '-level', '4.0',
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    '-ar', '48000',
                    '-ac', '2',
                    '-movflags', '+faststart',
                    temp_news_path
                ], check=True, capture_output=True, text=True, timeout=60)

                # Remove raw file to save space
                os.remove(temp_news_path_raw)

                re_encoded_size = os.path.getsize(temp_news_path) / (1024 * 1024)
                self.logger.info(f"✅ Video re-encoded successfully: {re_encoded_size:.2f} MB")

            except subprocess.CalledProcessError as e:
                self.logger.error(f"❌ FFmpeg re-encoding failed!")
                self.logger.error(f"FFmpeg stderr: {e.stderr}")
                raise Exception(f"FFmpeg re-encoding failed: {e.stderr[:500]}")

            # Step 2: Prepare video paths for concatenation
            video_paths = [temp_news_path]

            if subscribe_video_path and os.path.exists(subscribe_video_path):
                self.logger.info("📢 Processing subscribe video...")
                scaled_subscribe_path = self._process_subscribe_video(subscribe_video_path, unique_id)
                video_paths.append(scaled_subscribe_path)
            else:
                self.logger.warning("⚠️ Subscribe video not found, skipping...")

            # Step 3: Concatenate videos using FFmpeg
            temp_short_path = short_path.replace('.mp4', '.temp.mp4')
            if len(video_paths) == 1:
                # Only news video, just copy it
                self.logger.info("📋 Single video - copying directly")
                import subprocess
                subprocess.run(['cp', video_paths[0], temp_short_path], check=True)
            else:
                # Concatenate news + subscribe using FFmpeg
                self.logger.info(f"🎨 Concatenating {len(video_paths)} videos using FFmpeg...")
                self._concatenate_videos_ffmpeg(video_paths, temp_short_path)

            # Step 4: Add default background music to the short
            self.logger.info("🎵 Adding default background music to short...")
            success = self._add_background_music_to_short(temp_short_path, short_path)

            if not success:
                self.logger.warning("⚠️ Failed to add background music, using short without it")
                # If background music fails, use the temp file as final
                import subprocess
                subprocess.run(['mv', temp_short_path, short_path], check=True)
            else:
                # Clean up temp file
                if os.path.exists(temp_short_path):
                    os.remove(temp_short_path)

            # Clean up temp files after successful concatenation
            try:
                if os.path.exists(temp_news_path):
                    os.remove(temp_news_path)
                    self.logger.info(f"🗑️ Cleaned up temp file: {temp_news_path}")
                if len(video_paths) > 1 and os.path.exists(video_paths[1]):
                    os.remove(video_paths[1])
                    self.logger.info(f"🗑️ Cleaned up temp file: {video_paths[1]}")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to clean up temp files: {e}")

            # Validate output file
            if not os.path.exists(short_path):
                raise Exception(f"Output file not created: {short_path}")

            # Get file size
            file_size_mb = os.path.getsize(short_path) / (1024 * 1024)

            # Validate file size (should be at least 1MB for a valid video)
            if file_size_mb < 0.001:  # Less than 1KB
                raise Exception(f"Output file is too small ({file_size_mb:.2f} MB), likely corrupted")

            # Get duration using ffprobe
            import subprocess
            try:
                duration_result = subprocess.run([
                    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1', short_path
                ], capture_output=True, text=True, check=True)
                duration = float(duration_result.stdout.strip())

                # Validate duration
                if duration < 1.0:
                    raise Exception(f"Video duration too short ({duration:.2f}s), likely corrupted")

            except Exception as e:
                self.logger.error(f"⚠️ Error getting video duration: {str(e)}")
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
        Concatenate videos using FFmpeg concat demuxer with re-encoding for compatibility

        Re-encoding is necessary because:
        1. The news video and subscribe video may have different encoding parameters
        2. YouTube Shorts requires specific encoding for proper processing
        3. Stream copy (-c copy) fails when videos have incompatible codecs/parameters

        Args:
            video_paths: List of video file paths to concatenate
            output_path: Output path for concatenated video
        """
        import subprocess

        try:
            # Validate all input videos exist and are readable
            for i, video_path in enumerate(video_paths):
                if not os.path.exists(video_path):
                    raise Exception(f"Input video {i+1} not found: {video_path}")

                size_mb = os.path.getsize(video_path) / (1024 * 1024)
                self.logger.info(f"📹 Input video {i+1}: {video_path} ({size_mb:.2f} MB)")

                # Verify video is readable by ffprobe
                try:
                    probe_result = subprocess.run([
                        'ffprobe', '-v', 'error',
                        '-select_streams', 'v:0',
                        '-show_entries', 'stream=codec_name,width,height,pix_fmt',
                        '-of', 'default=noprint_wrappers=1',
                        video_path
                    ], capture_output=True, text=True, check=True, timeout=10)
                    self.logger.info(f"🔍 Video {i+1} info: {probe_result.stdout.strip()}")
                except subprocess.TimeoutExpired:
                    raise Exception(f"Timeout while probing video {i+1}: {video_path}")
                except subprocess.CalledProcessError as e:
                    raise Exception(f"Cannot read video {i+1}: {video_path}. Error: {e.stderr}")

            # Create concat file for FFmpeg
            temp_dir = '/app/temp'
            concat_file = os.path.join(temp_dir, 'concat_list.txt')

            with open(concat_file, 'w') as f:
                for video_path in video_paths:
                    f.write(f"file '{video_path}'\n")

            self.logger.info(f"📝 Concat file created with {len(video_paths)} videos")

            # Concatenate using FFmpeg with re-encoding for maximum compatibility
            # Use filter_complex instead of concat demuxer to avoid h264_mp4toannexb issues
            # This ensures YouTube can process the video properly
            try:
                # Build filter_complex command for concatenation
                # For 2 videos: [0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]
                n_videos = len(video_paths)

                # Build input arguments
                input_args = []
                for video_path in video_paths:
                    input_args.extend(['-i', video_path])

                # Build filter_complex string
                filter_inputs = ''.join([f'[{i}:v][{i}:a]' for i in range(n_videos)])
                filter_complex = f'{filter_inputs}concat=n={n_videos}:v=1:a=1[outv][outa]'

                result = subprocess.run([
                    'ffmpeg', '-y',
                    *input_args,
                    '-filter_complex', filter_complex,
                    '-map', '[outv]',
                    '-map', '[outa]',
                    # Video encoding settings optimized for YouTube Shorts
                    '-c:v', 'libx264',  # H.264 video codec
                    '-preset', 'medium',  # Balanced speed/quality
                    '-crf', '23',  # Constant quality (lower = better, 23 is good)
                    '-pix_fmt', 'yuv420p',  # Pixel format for maximum compatibility
                    '-profile:v', 'high',  # H.264 high profile for better compression
                    '-level', '4.0',  # H.264 level 4.0 for 1080p support
                    # Audio encoding settings
                    '-c:a', 'aac',  # AAC audio codec
                    '-b:a', '192k',  # Audio bitrate
                    '-ar', '48000',  # Audio sample rate (48kHz is YouTube standard)
                    '-ac', '2',  # Stereo audio
                    # Optimization flags
                    '-movflags', '+faststart',  # Enable fast start for streaming
                    '-max_muxing_queue_size', '1024',  # Prevent muxing queue overflow
                    output_path
                ], check=True, capture_output=True, text=True, timeout=120)

                self.logger.info(f"✅ Videos concatenated successfully with re-encoding using filter_complex")

            except subprocess.CalledProcessError as e:
                self.logger.error(f"❌ FFmpeg concatenation failed!")
                self.logger.error(f"FFmpeg stderr output:\n{e.stderr}")
                self.logger.error(f"FFmpeg stdout output:\n{e.stdout}")
                self.logger.error(f"Return code: {e.returncode}")
                raise Exception(f"FFmpeg concatenation failed with exit code {e.returncode}. Error: {e.stderr[:500]}")

        except subprocess.TimeoutExpired:
            self.logger.error(f"❌ FFmpeg concatenation timed out after 120 seconds")
            raise Exception("FFmpeg concatenation timed out")

    def _process_subscribe_video(self, subscribe_video_path: str, unique_id: str = None) -> str:
        """
        Process subscribe video to fit shorts dimensions using FFmpeg

        Args:
            subscribe_video_path: Path to subscribe video
            unique_id: Unique identifier for temp file naming (to avoid race conditions)

        Returns:
            Path to processed subscribe video
        """
        try:
            import subprocess

            # Create temp directory if it doesn't exist
            temp_dir = '/app/temp'
            os.makedirs(temp_dir, exist_ok=True)

            # Output path for scaled subscribe video
            # Use unique ID if provided to avoid race conditions in parallel processing
            if unique_id:
                scaled_subscribe_path = os.path.join(temp_dir, f'subscribe_shorts_scaled_{unique_id}.mp4')
            else:
                scaled_subscribe_path = os.path.join(temp_dir, 'subscribe_shorts_scaled.mp4')

            # Scale subscribe video to shorts dimensions (1080x1920) using FFmpeg
            # Use consistent encoding parameters to ensure compatibility with news video
            self.logger.info(f"📐 Scaling subscribe video to {self.shorts_width}x{self.shorts_height}")

            result = subprocess.run([
                'ffmpeg', '-y', '-i', subscribe_video_path,
                '-vf', f'scale={self.shorts_width}:{self.shorts_height}:force_original_aspect_ratio=decrease,pad={self.shorts_width}:{self.shorts_height}:(ow-iw)/2:(oh-ih)/2,fps=30',
                # Video encoding - match the news video settings
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-profile:v', 'high',
                '-level', '4.0',
                # Audio encoding - match the news video settings
                '-c:a', 'aac',
                '-b:a', '192k',
                '-ar', '48000',
                '-ac', '2',
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

    def _add_background_music_to_short(self, input_path: str, output_path: str) -> bool:
        """
        Add background music to the short video using FFmpeg
        Uses the configured background music from settings (SHORTS_BACKGROUND_MUSIC)

        Args:
            input_path: Path to the short video without background music
            output_path: Path to save the short with background music

        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess
            from moviepy.editor import VideoFileClip

            # Get path to configured background music for shorts
            assets_dir = os.path.join(os.path.dirname(__file__), '..', 'assets')
            music_filename = self.config.SHORTS_BACKGROUND_MUSIC
            music_path = os.path.join(assets_dir, music_filename)

            if not os.path.exists(music_path):
                self.logger.error(f"❌ Configured background music not found: {music_path}")
                self.logger.error(f"❌ Please check SHORTS_BACKGROUND_MUSIC setting: {music_filename}")
                return False

            # Get video duration
            video = VideoFileClip(input_path)
            video_duration = video.duration
            video.close()

            self.logger.info(f"🎵 Using configured background music for shorts: {music_filename}")
            self.logger.info(f"🎵 Music path: {music_path}")
            self.logger.info(f"📊 Video duration: {video_duration:.2f}s")

            # Use FFmpeg to mix background music with existing audio
            music_volume = 0.15  # 15% volume for background music
            fade_duration = 2.0  # 2 seconds fade in/out

            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-i', input_path,  # Input video with original audio
                '-stream_loop', '-1',  # Loop background music
                '-i', music_path,  # Background music
                '-filter_complex',
                f'[1:a]volume={music_volume},afade=t=in:st=0:d={fade_duration},afade=t=out:st={video_duration-fade_duration}:d={fade_duration},aloop=loop=-1:size=2e+09[music];'
                f'[0:a][music]amix=inputs=2:duration=first:dropout_transition=0[aout]',
                '-map', '0:v',  # Use video from first input
                '-map', '[aout]',  # Use mixed audio
                '-c:v', 'copy',  # Copy video stream (no re-encoding)
                '-c:a', 'aac',  # Encode audio as AAC
                '-b:a', '192k',  # Audio bitrate
                '-shortest',  # Stop when shortest stream ends (video)
                output_path
            ]

            self.logger.info("🚀 Running FFmpeg to add background music to short...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"❌ FFmpeg error adding background music: {result.stderr}")
                return False

            self.logger.info(f"✅ Background music added to short successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error adding background music to short: {str(e)}")
            return False

