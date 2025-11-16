"""
Video Merge Service - Handles merging multiple news videos into a single video
"""

import os
import tempfile
from datetime import datetime
from typing import List, Dict, Optional
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont


class VideoMergeService:
    """Service for merging multiple news videos into a single compilation video"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        
    def merge_latest_videos(self, news_list: List[Dict]) -> Dict:
        """
        Merge latest news videos into a single compilation video
        
        Args:
            news_list: List of news documents with video_path
            
        Returns:
            Dict with merge result
        """
        try:
            self.logger.info(f"🎬 Starting merge of {len(news_list)} videos")
            
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
            
            # Concatenate all video clips
            self.logger.info("🔗 Concatenating video clips...")
            try:
                final_video = concatenate_videoclips(video_clips, method="compose")
                self.logger.info("✅ Video concatenation completed")
            except Exception as concat_error:
                self.logger.error(f"❌ Error during concatenation: {str(concat_error)}")
                # Clean up clips before raising error
                for clip in video_clips:
                    try:
                        clip.close()
                    except:
                        pass
                raise concat_error
            
            # Use atomic file operations to prevent partial downloads
            final_output_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news.mp4')
            temp_output_path = os.path.join(self.config.VIDEO_OUTPUT_DIR, 'latest-20-news.tmp.mp4')

            # Ensure output directory exists
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)

            # Write final video to temporary file first
            self.logger.info(f"💾 Writing merged video to temporary file: {temp_output_path}")
            self.logger.info(f"📊 Processing {len(valid_videos)} videos with total duration of {final_video.duration:.1f} seconds")
            self.logger.info("⏳ This process may take 2-5 minutes depending on video length and quality. Please wait...")

            # Remove existing temp file if it exists
            if os.path.exists(temp_output_path):
                os.remove(temp_output_path)
                self.logger.info("🗑️ Removed existing temporary video file")

            # Generate video to temporary file
            final_video.write_videofile(
                temp_output_path,
                fps=24,  # Use standard fps for compatibility
                codec='libx264',  # Use standard codec
                audio_codec='aac',  # Use standard audio codec
                verbose=True,  # Enable verbose for debugging
                logger='bar'  # Show progress bar
            )
            self.logger.info("✅ Video file written to temporary location successfully")

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
            duration = final_video.duration
            
            # Clean up clips
            for clip in video_clips:
                clip.close()
            final_video.close()
            
            self.logger.info(f"✅ Merged video created successfully")
            self.logger.info(f"📊 Duration: {duration:.2f}s, Size: {file_size_mb:.2f}MB")
            
            return {
                'status': 'success',
                'merged_video_path': '/public/latest-20-news.mp4',
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
    

