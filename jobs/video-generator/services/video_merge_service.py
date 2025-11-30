"""
Video Merge Service - Handles merging multiple news videos into a single video
"""

import os
import tempfile
import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
from effects.effects_factory import EffectsFactory
from services.thumbnail_service import ThumbnailService


class VideoMergeService:
    """Service for merging multiple news videos into a single compilation video"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.effects_factory = EffectsFactory(logger=logger)
        self.thumbnail_service = ThumbnailService(config, logger)
        
    def merge_latest_videos(self, news_list: List[Dict], title: str = None, config_id: str = None) -> Dict:
        """
        Merge latest news videos into a single compilation video

        Args:
            news_list: List of news documents with video_path
            title: Optional title for the video thumbnail
            config_id: Optional config ID to save video in config-specific folder

        Returns:
            Dict with merge result
        """
        try:
            if title is None:
                title = "TOP 20 NEWS"

            self.logger.info(f"🎬 Starting merge of {len(news_list)} videos with title: {title}, config_id: {config_id}")
            
            # Collect video clips
            video_clips = []
            valid_videos = []
            
            for news in news_list:
                video_path = self._get_full_video_path(news.get('video_path'))
                
                if not video_path or not os.path.exists(video_path):
                    self.logger.warning(f"⚠️ Video not found: {video_path}")
                    continue
                
                try:
                    # Load video clip
                    clip = VideoFileClip(video_path)

                    # Add title overlay at the beginning of each clip
                    title_clip = self._create_title_overlay(
                        news.get('title', 'News Update'),
                        clip.duration,
                        clip.size
                    )

                    # Composite video with title
                    final_clip = CompositeVideoClip([clip, title_clip])

                    video_clips.append(final_clip)
                    valid_videos.append(news)
                    
                    self.logger.info(f"✅ Added video: {news.get('title', 'Unknown')[:50]}...")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error processing video {video_path}: {str(e)}")
                    continue
            
            if not video_clips:
                return {
                    'status': 'error',
                    'error': 'No valid videos found to merge'
                }
            
            self.logger.info(f"📊 Successfully loaded {len(video_clips)} video clips")

            # Clean up MoviePy clips - we'll use FFmpeg directly for speed
            for clip in video_clips:
                clip.close()

            # Determine output paths based on config_id
            if config_id:
                # Save in config-specific folder: /public/<config_id>/latest.mp4
                config_dir = os.path.join(self.config.VIDEO_OUTPUT_DIR, config_id)
                os.makedirs(config_dir, exist_ok=True)
                final_output_path = os.path.join(config_dir, 'latest.mp4')
                temp_output_path = os.path.join(config_dir, 'latest.tmp.mp4')
                video_public_path = f'/public/{config_id}/latest.mp4'
                thumbnail_public_path = f'/public/{config_id}/latest-thumbnail.jpg'
            else:
                # Legacy path for backward compatibility
                final_output_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news.mp4')
                temp_output_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news.tmp.mp4')
                video_public_path = '/public/latest-20-news.mp4'
                thumbnail_public_path = '/public/latest-20-news-thumbnail.jpg'

            # Ensure output directory exists
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)

            # Remove existing temp file if it exists
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
                self.logger.info("🗑️ Removed existing temporary video file")

            # Use FFmpeg for fast merging with sliding transitions
            self.logger.info(f"🚀 Using FFmpeg for fast video merging with sliding transitions...")

            # Get video paths
            video_paths = [self._get_full_video_path(news.get('video_path')) for news in valid_videos]

            # Merge videos using FFmpeg with xfade filter (append subscribe video at the end)
            duration = self._merge_videos_with_ffmpeg(
                video_paths,
                temp_output_path,
                transition_duration=self.config.TRANSITION_DURATION if self.config.ENABLE_TRANSITIONS else 0,
                append_subscribe_video=True  # Always append subscribe video
            )

            # Atomic operation: Move temp file to final location
            if os.path.exists(final_output_path):
                self.logger.info("🔄 Replacing existing merged video file")
            else:
                self.logger.info("📁 Creating new merged video file")

            # Atomic rename operation (this is instantaneous)
            os.rename(temp_output_path, final_output_path)
            self.logger.info(f"✅ Merged video atomically moved to: {final_output_path}")

            # Get file info from final location
            file_size = os.path.getsize(final_output_path)
            file_size_mb = file_size / (1024 * 1024)

            self.logger.info(f"✅ Merged video created successfully")
            self.logger.info(f"📊 Duration: {duration:.2f}s, Size: {file_size_mb:.2f}MB")

            # Generate thumbnail for the merged video
            thumbnail_path = None
            try:
                thumbnail_path = self._generate_thumbnail(valid_videos, final_output_path, title, config_id)
            except Exception as thumb_error:
                self.logger.warning(f"⚠️ Thumbnail generation failed: {thumb_error}")

            return {
                'status': 'success',
                'merged_video_path': video_public_path,
                'thumbnail_path': thumbnail_path if thumbnail_path else thumbnail_public_path,
                'video_count': len(valid_videos),
                'duration_seconds': round(duration, 2),
                'file_size_mb': round(file_size_mb, 2),
                'news_titles': [news.get('title', 'Unknown') for news in valid_videos]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error merging videos: {str(e)}")

            # Clean up temporary file if it exists
            try:
                temp_output_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news.tmp.mp4')
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
                    self.logger.info("🗑️ Cleaned up temporary video file after error")
            except Exception as cleanup_error:
                self.logger.warning(f"⚠️ Could not clean up temporary file: {cleanup_error}")

            return {
                'status': 'error',
                'error': str(e)
            }

    def _merge_videos_with_ffmpeg(self, video_paths: List[str], output_path: str, transition_duration: float = 1.0, append_subscribe_video: bool = False) -> float:
        """
        Merge videos using FFmpeg with xfade sliding transitions for maximum speed

        Args:
            video_paths: List of video file paths to merge
            output_path: Output file path
            transition_duration: Duration of transition in seconds
            append_subscribe_video: Whether to append CNI News subscribe video at the end

        Returns:
            Total duration of merged video in seconds
        """
        # Add subscribe video at the end if requested
        if append_subscribe_video:
            subscribe_video_path = '/app/public/CNINews_Subscribe.mp4'
            if os.path.exists(subscribe_video_path):
                # Scale subscribe video to match the resolution of other videos
                # Get resolution of first video
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                     '-show_entries', 'stream=width,height',
                     '-of', 'csv=s=x:p=0', video_paths[0]],
                    capture_output=True, text=True, check=True
                )
                target_resolution = result.stdout.strip()  # e.g., "1920x1080"

                # Get resolution of subscribe video
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                     '-show_entries', 'stream=width,height',
                     '-of', 'csv=s=x:p=0', subscribe_video_path],
                    capture_output=True, text=True, check=True
                )
                subscribe_resolution = result.stdout.strip()

                # If resolutions don't match, scale the subscribe video
                if target_resolution != subscribe_resolution:
                    self.logger.info(f"📐 Scaling subscribe video from {subscribe_resolution} to {target_resolution}")
                    scaled_subscribe_path = '/app/temp/CNINews_Subscribe_scaled.mp4'

                    # Parse target resolution (e.g., "1920x1080" -> width=1920, height=1080)
                    width, height = target_resolution.split('x')

                    # Scale video using FFmpeg and match frame rate to 30fps
                    try:
                        result = subprocess.run([
                            'ffmpeg', '-y', '-i', subscribe_video_path,
                            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps=30',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                            '-c:a', 'copy',
                            scaled_subscribe_path
                        ], check=True, capture_output=True, text=True)

                        video_paths = video_paths + [scaled_subscribe_path]
                        self.logger.info(f"📺 Appending scaled CNI News subscribe video at the end")
                    except subprocess.CalledProcessError as e:
                        self.logger.error(f"❌ FFmpeg scaling error: {e.stderr}")
                        # If scaling fails, try to use the original video anyway
                        self.logger.warning(f"⚠️ Using original subscribe video without scaling")
                        video_paths = video_paths + [subscribe_video_path]
                else:
                    video_paths = video_paths + [subscribe_video_path]
                    self.logger.info(f"📺 Appending CNI News subscribe video at the end")
            else:
                self.logger.warning(f"⚠️ Subscribe video not found at {subscribe_video_path}")

        if len(video_paths) == 1:
            # Single video - just copy it
            self.logger.info("📋 Single video - copying directly")
            subprocess.run(['cp', video_paths[0], output_path], check=True)

            # Get duration
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', video_paths[0]],
                capture_output=True, text=True, check=True
            )
            return float(result.stdout.strip())

        # For multiple videos, use FFmpeg xfade filter for sliding transitions
        self.logger.info(f"🎬 Merging {len(video_paths)} videos with FFmpeg xfade (slideleft) transitions...")

        # Get duration of each video
        durations = []
        for video_path in video_paths:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
                capture_output=True, text=True, check=True
            )
            durations.append(float(result.stdout.strip()))

        # Build FFmpeg command with xfade filter
        # Format: ffmpeg -i v1.mp4 -i v2.mp4 -i v3.mp4 -filter_complex "[0][1]xfade=transition=slideleft:duration=1:offset=14[v01];[v01][2]xfade=transition=slideleft:duration=1:offset=28" output.mp4

        # Build input arguments
        input_args = []
        for video_path in video_paths:
            input_args.extend(['-i', video_path])

        # Build filter complex with sliding transitions that don't affect audio sync
        # Strategy: Add black padding at the end of each video equal to transition duration,
        # then apply xfade. This keeps total duration same as concatenation.
        filter_parts = []

        # Step 1: Pad each video (except the last) with black frames at the end
        for i in range(len(video_paths) - 1):
            filter_parts.append(f"[{i}:v]tpad=stop_mode=clone:stop_duration={transition_duration}[v{i}pad]")
        # Last video doesn't need padding
        filter_parts.append(f"[{len(video_paths)-1}:v]copy[v{len(video_paths)-1}pad]")

        # Step 2: Apply xfade transitions between padded videos
        offset = durations[0]  # First transition starts at end of first video (now padded)
        filter_parts.append(f"[v0pad][v1pad]xfade=transition=slideleft:duration={transition_duration}:offset={offset}[v01]")

        # Subsequent transitions
        for i in range(2, len(video_paths)):
            offset += durations[i-1]  # Add full duration (padding compensates for overlap)
            prev_label = f"v0{i-1}" if i == 2 else f"v{i-1}"
            curr_label = f"v{i}"
            filter_parts.append(f"[{prev_label}][v{i}pad]xfade=transition=slideleft:duration={transition_duration}:offset={offset}[{curr_label}]")

        # Step 3: Concatenate audio normally (no transitions)
        audio_inputs = "".join([f"[{i}:a]" for i in range(len(video_paths))])
        filter_parts.append(f"{audio_inputs}concat=n={len(video_paths)}:v=0:a=1[aout]")

        filter_complex = ";".join(filter_parts)

        # Final video and audio labels
        final_video_label = f"v{len(video_paths)-1}" if len(video_paths) > 2 else "v01"
        final_audio_label = "aout"

        # Build full FFmpeg command with maximum compatibility for QuickTime, Android, and web
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            *input_args,
            '-filter_complex', filter_complex,
            '-map', f'[{final_video_label}]',  # Map final video with transitions
            '-map', f'[{final_audio_label}]',  # Map concatenated audio
            '-c:v', 'libx264',  # Video codec
            '-preset', 'ultrafast',  # Fast encoding
            '-crf', '23',  # Quality
            '-pix_fmt', 'yuv420p',  # Pixel format for maximum compatibility
            '-profile:v', 'baseline',  # H.264 baseline profile for Android/iOS/web compatibility
            '-level', '3.1',  # H.264 level 3.1 for broad device support
            '-c:a', 'aac',  # Audio codec
            '-b:a', '192k',  # Audio bitrate
            '-ar', '44100',  # Audio sample rate (standard for Android/iOS)
            '-ac', '2',  # Stereo audio
            '-movflags', '+faststart',  # Enable fast start for web/QuickTime/Android playback
            output_path
        ]

        self.logger.info(f"🚀 Running FFmpeg with sliding transitions (audio-synced)...")
        self.logger.info(f"📊 Transition duration: {transition_duration}s between each video")

        # Run FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            self.logger.error(f"❌ FFmpeg error: {result.stderr}")
            raise Exception(f"FFmpeg failed: {result.stderr}")

        self.logger.info("✅ FFmpeg merge completed successfully!")

        # Calculate total duration (sum of all durations minus overlaps)
        total_duration = sum(durations) - (transition_duration * (len(video_paths) - 1))

        return total_duration

    def _get_full_video_path(self, relative_path: str) -> Optional[str]:
        """Convert relative video path to full system path"""
        if not relative_path:
            return None
            
        # Remove leading slash if present
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
            
        # Convert to full path
        full_path = os.path.join('/app', relative_path)
        return full_path
    
    def _create_title_overlay(self, title: str, duration: float, video_size: tuple) -> TextClip:
        """
        Create a title overlay for the video
        
        Args:
            title: News title text
            duration: Duration to show the title
            video_size: (width, height) of the video
            
        Returns:
            TextClip with title overlay
        """
        try:
            # Limit title length
            if len(title) > 80:
                title = title[:77] + "..."
            
            # Create text clip
            title_clip = TextClip(
                title,
                fontsize=min(video_size[0] // 25, 40),  # Responsive font size
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2
            ).set_duration(min(duration, 5.0))  # Show title for max 5 seconds
            
            # Position at bottom of video
            title_clip = title_clip.set_position(('center', video_size[1] - 100))
            
            return title_clip
            
        except Exception as e:
            self.logger.error(f"Error creating title overlay: {str(e)}")
            # Return empty clip if title creation fails
            return TextClip("", fontsize=1).set_duration(0.1)

    def _apply_transitions_to_clips(self, clips: List[VideoFileClip],
                                   transition_type: str = 'crossfade',
                                   transition_duration: float = 1.0) -> VideoFileClip:
        """
        Apply smooth transitions between video clips

        Args:
            clips: List of video clips to merge with transitions
            transition_type: Type of transition to apply
            transition_duration: Duration of each transition in seconds

        Returns:
            Single video clip with all clips merged with transitions
        """
        if len(clips) == 0:
            raise ValueError("No clips provided for transition")

        if len(clips) == 1:
            return clips[0]

        # Create transition effect
        transition_effect = self.effects_factory.create_effect('transition', config={
            'default_type': transition_type,
            'default_duration': transition_duration
        })

        # Start with the first clip
        result_clip = clips[0]

        # Apply transitions between consecutive clips
        for i in range(1, len(clips)):
            self.logger.info(f"🎬 Applying transition {i}/{len(clips)-1}: {transition_type}")

            # Apply transition between result_clip and next clip
            result_clip = transition_effect.apply_transition(
                result_clip,
                clips[i],
                transition_type=transition_type,
                duration=transition_duration
            )

        return result_clip

    def _generate_thumbnail(self, news_list: List[Dict], video_path: str, title: str = "TOP 20 NEWS", config_id: str = None) -> Optional[str]:
        """
        Generate a YouTube-style thumbnail for the merged video

        Args:
            news_list: List of news documents
            title: Title to display on the thumbnail
            video_path: Path to the merged video
            config_id: Optional config ID to save thumbnail in config-specific folder

        Returns:
            Path to generated thumbnail or None
        """
        try:
            self.logger.info("🎨 Generating thumbnail for merged video...")

            # Extract frames from first 2-3 news videos for the collage
            news_thumbnails = []
            temp_files = []

            try:
                # Take first 3 news videos
                for i, news in enumerate(news_list[:3]):
                    video_file_path = news.get('video_path', '')

                    if not video_file_path:
                        continue

                    # Convert to absolute path
                    if video_file_path.startswith('/public/'):
                        video_file_path = os.path.join(
                            self.config.VIDEO_OUTPUT_DIR,
                            video_file_path.replace('/public/', '')
                        )

                    if not os.path.exists(video_file_path):
                        self.logger.warning(f"⚠️ Video file not found: {video_file_path}")
                        continue

                    # Extract frame from this video
                    temp_frame_path = os.path.join(
                        self.config.VIDEO_OUTPUT_DIR,
                        f'thumb_news_{i}.jpg'
                    )

                    subprocess.run([
                        'ffmpeg', '-y',
                        '-i', video_file_path,
                        '-ss', '00:00:02',  # Extract at 2 seconds
                        '-vframes', '1',
                        '-q:v', '2',  # High quality
                        temp_frame_path
                    ], check=True, capture_output=True, timeout=10)

                    if os.path.exists(temp_frame_path):
                        news_thumbnails.append(temp_frame_path)
                        temp_files.append(temp_frame_path)
                        self.logger.info(f"✅ Extracted frame from news video {i+1}")

            except Exception as frame_error:
                self.logger.warning(f"⚠️ Could not extract news frames: {frame_error}")

            # Generate thumbnail with split design
            if config_id:
                # Save in config-specific folder
                thumbnail_output_path = os.path.join(
                    self.config.VIDEO_OUTPUT_DIR,
                    config_id,
                    'latest-thumbnail.jpg'
                )
            else:
                # Legacy path
                thumbnail_output_path = os.path.join(
                    self.config.VIDEO_OUTPUT_DIR,
                    'latest-20-news-thumbnail.jpg'
                )

            thumbnail_path = self.thumbnail_service.generate_thumbnail(
                background_image_path=None,  # Not used in split design
                title=title,  # Use the provided title
                subtitle=None,
                output_path=thumbnail_output_path,
                news_thumbnails=news_thumbnails
            )

            # Clean up temp frames
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception:
                    pass

            self.logger.info(f"✅ Thumbnail generated: {thumbnail_path}")

            # Return public path
            if config_id:
                return f'/public/{config_id}/latest-thumbnail.jpg'
            else:
                return '/public/latest-20-news-thumbnail.jpg'

        except Exception as e:
            self.logger.error(f"❌ Thumbnail generation failed: {str(e)}")
            return None

