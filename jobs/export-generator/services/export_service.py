"""
Export Service for Job Framework
Handles video/audio export from Design Editor projects
"""
import os
import uuid
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from io import BytesIO
import json

import ffmpeg
from PIL import Image, ImageDraw, ImageFont
import requests
from pymongo import MongoClient
from minio import Minio


class ExportService:
    """Service for exporting Design Editor projects"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.temp_dir = config.TEMP_DIR
        self.export_bucket = config.MINIO_BUCKET_EXPORTS

        # Initialize MongoDB
        self.mongo_client = MongoClient(config.MONGODB_URI)
        self.db = self.mongo_client[config.MONGODB_DATABASE]
        self.projects_collection = self.db['projects']
        self.export_jobs_collection = self.db['export_jobs']

        # Initialize news database for video library
        self.news_client = MongoClient(config.NEWS_MONGODB_URL)
        self.news_db = self.news_client[config.NEWS_MONGODB_DATABASE]
        self.video_library_collection = self.news_db['video_library']

        # Initialize MinIO
        self.minio_client = Minio(
            config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=config.MINIO_SECURE
        )

        # Ensure bucket exists
        if not self.minio_client.bucket_exists(self.export_bucket):
            self.minio_client.make_bucket(self.export_bucket)

        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def process_export(
        self,
        job_id: str,
        project_id: str,
        customer_id: str,
        user_id: str,
        export_format: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process export job (main export pipeline)

        Args:
            job_id: Job instance ID from JobInstanceService
            project_id: Project to export
            customer_id: Customer ID
            user_id: User ID
            export_format: Export format (mp4, mp3, json)
            settings: Export settings (quality, fps, includeAudio, etc.)

        Returns:
            Dict with export results
        """
        try:
            self.logger.info(f"🎬 Starting export for project {project_id} (format: {export_format})")

            # Create export job tracking entry
            self._create_export_job(job_id, project_id, customer_id, user_id, export_format, settings)

            # Update status to processing
            self._update_export_job(job_id, customer_id, {
                "status": "processing",
                "started_at": datetime.utcnow(),
                "progress": 5,
                "current_step": "Loading project..."
            })

            # Get project from database
            project_data = self.projects_collection.find_one({
                "project_id": project_id,
                "customer_id": customer_id
            })

            if not project_data:
                raise Exception(f"Project not found: {project_id}")
            
            # Route to appropriate export handler
            if export_format.lower() == 'mp4':
                output_path, duration = self._export_mp4(job_id, project_data, settings, customer_id, user_id)
            elif export_format.lower() == 'mp3':
                output_path, duration = self._export_mp3(job_id, project_data, settings, customer_id, user_id)
            elif export_format.lower() == 'json':
                output_path, duration = self._export_json(job_id, project_data, settings, customer_id, user_id)
            else:
                raise Exception(f"Unsupported export format: {export_format}")
            
            # Upload to MinIO
            self.logger.info(f"📤 Uploading export to MinIO...")
            self._update_export_job(job_id, customer_id, {
                "progress": 95,
                "current_step": "Uploading to storage..."
            })

            file_size = os.path.getsize(output_path)
            output_url, video_id = self._upload_export(
                output_path,
                job_id,
                project_id,
                customer_id,
                user_id,
                export_format,
                duration
            )

            # Update project with export metadata
            self._update_project_exports(
                project_id,
                customer_id,
                job_id,
                export_format,
                output_url,
                video_id,
                file_size,
                duration,
                settings
            )

            # Mark export job as completed
            self._update_export_job(job_id, customer_id, {
                "status": "completed",
                "progress": 100,
                "current_step": "Export completed",
                "output_url": output_url,
                "output_video_id": video_id,
                "file_size": file_size,
                "duration": duration,
                "completed_at": datetime.utcnow()
            })

            # Cleanup temp file
            if os.path.exists(output_path):
                os.remove(output_path)

            self.logger.info(f"✅ Export completed: {job_id}")

            return {
                'status': 'success',
                'output_url': output_url,
                'video_id': video_id,
                'file_size': file_size,
                'duration': duration,
                'format': export_format
            }

        except Exception as e:
            self.logger.error(f"❌ Error processing export {job_id}: {str(e)}")

            # Mark export job as failed
            self._update_export_job(job_id, customer_id, {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow()
            })

            raise

    def _export_mp4(
        self,
        job_id: str,
        project_data: Dict[str, Any],
        settings: Dict[str, Any],
        customer_id: str,
        user_id: str
    ) -> Tuple[str, float]:
        """Export project as MP4 video"""
        try:
            self.logger.info(f"🎬 Exporting MP4 for job {job_id}")

            # Create temp directory for this export
            export_dir = os.path.join(self.temp_dir, job_id)
            os.makedirs(export_dir, exist_ok=True)

            frames_dir = os.path.join(export_dir, "frames")
            os.makedirs(frames_dir, exist_ok=True)

            # Calculate total duration
            total_duration = sum(page.get('duration', 5) for page in project_data.get('pages', []))
            self.logger.info(f"📊 Total video duration: {total_duration}s")

            # Render slides to frames
            self.logger.info(f"=" * 60)
            self.logger.info(f"🎨 STEP 1: Rendering slides to frames...")
            self.logger.info(f"=" * 60)
            # Default to 24 fps (cinema standard) for better performance
            # Users can override with 30 or 60 fps in export settings
            self._render_slides_to_frames(
                project_data,
                frames_dir,
                settings.get('fps', 24),
                customer_id,
                user_id,
                job_id
            )
            self.logger.info(f"✅ Frame rendering complete!")

            # Create video from frames
            output_path = os.path.join(export_dir, f"{job_id}.mp4")

            # Build FFmpeg command
            quality_map = {
                "720p": {"width": 1280, "height": 720},
                "1080p": {"width": 1920, "height": 1080},
                "1440p": {"width": 2560, "height": 1440},
                "2160p": {"width": 3840, "height": 2160}
            }

            resolution = quality_map.get(settings.get('quality', '1080p'), quality_map["1080p"])
            fps = settings.get('fps', 24)  # Default 24 fps (cinema standard)
            codec = settings.get('codec', 'libx264')
            bitrate = settings.get('bitrate', '5M')

            # Try to use GPU encoding (NVENC) if available, fallback to CPU
            use_gpu = self._check_gpu_available()
            if use_gpu:
                codec = 'h264_nvenc'
                self.logger.info(f"🚀 Using GPU-accelerated encoding (NVENC)")
            else:
                codec = 'libx264'
                self.logger.info(f"💻 Using CPU encoding (libx264)")

            # Update progress
            self._update_export_job(job_id, customer_id, {
                "progress": 80,
                "current_step": "Encoding video with FFmpeg..."
            })

            # Create video from frames (handling static and animated slides)
            self.logger.info(f"=" * 60)
            self.logger.info(f"🎞️ STEP 3: Creating video from frames...")
            self.logger.info(f"=" * 60)
            video_path = self._create_video_from_frames(
                frames_dir,
                output_path,
                fps,
                resolution,
                codec,
                bitrate,
                use_gpu
            )
            self.logger.info(f"✅ Video creation complete!")

            # Update progress after video creation
            self._update_export_job(job_id, customer_id, {
                "progress": 85,
                "current_step": "Video encoding complete"
            })

            # Add audio if requested
            self.logger.info(f"=" * 60)
            self.logger.info(f"🎵 STEP 4: Processing audio...")
            self.logger.info(f"=" * 60)
            if settings.get('includeAudio', True) and (project_data.get('audioTracks') or project_data.get('videoTracks')):
                # Update progress
                self._update_export_job(job_id, customer_id, {
                    "progress": 87,
                    "current_step": "Mixing audio tracks..."
                })

                self.logger.info(f"🎵 Mixing audio tracks...")
                audio_path = self._mix_audio_tracks(project_data, export_dir, total_duration, customer_id, user_id)
                if audio_path and os.path.exists(audio_path):
                    # Update progress
                    self._update_export_job(job_id, customer_id, {
                        "progress": 90,
                        "current_step": "Adding audio to video..."
                    })

                    self.logger.info(f"🎵 Adding audio to video...")
                    # Create final video with audio
                    final_output = os.path.join(export_dir, f"{job_id}_final.mp4")

                    video_stream = ffmpeg.input(video_path)
                    audio_stream = ffmpeg.input(audio_path)

                    if use_gpu:
                        stream = ffmpeg.output(
                            video_stream,
                            audio_stream,
                            final_output,
                            vcodec='copy',  # Copy video stream (already encoded)
                            acodec='aac',
                            audio_bitrate='192k',
                            shortest=None
                        )
                    else:
                        stream = ffmpeg.output(
                            video_stream,
                            audio_stream,
                            final_output,
                            vcodec='copy',  # Copy video stream (already encoded)
                            acodec='aac',
                            audio_bitrate='192k',
                            shortest=None
                        )

                    try:
                        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
                        # Replace video_path with final output
                        os.remove(video_path)
                        os.rename(final_output, output_path)
                        self.logger.info(f"✅ Audio added to video")
                    except ffmpeg.Error as e:
                        self.logger.error(f"FFmpeg audio mixing failed: {e.stderr.decode()}")
                        raise
                else:
                    # No audio, just rename video_path to output_path
                    if video_path != output_path:
                        os.rename(video_path, output_path)
            else:
                # No audio requested, just rename video_path to output_path
                if video_path != output_path:
                    os.rename(video_path, output_path)

            self.logger.info(f"✅ Video encoding completed")

            # Cleanup frames
            self.logger.info(f"=" * 60)
            self.logger.info(f"🗑️ STEP 5: Cleanup...")
            self.logger.info(f"=" * 60)
            self.logger.info(f"🗑️ Removing frames directory: {frames_dir}")
            shutil.rmtree(frames_dir)
            self.logger.info(f"✅ Cleanup complete")

            # Final summary
            self.logger.info(f"=" * 60)
            self.logger.info(f"🎉 EXPORT COMPLETE!")
            self.logger.info(f"=" * 60)
            self.logger.info(f"📁 Output file: {output_path}")
            self.logger.info(f"⏱️ Duration: {total_duration}s")
            import os as os_module
            if os_module.path.exists(output_path):
                file_size_mb = os_module.path.getsize(output_path) / (1024 * 1024)
                self.logger.info(f"💾 File size: {file_size_mb:.2f} MB")
            self.logger.info(f"=" * 60)

            return output_path, total_duration

        except Exception as e:
            self.logger.error(f"❌ Error exporting MP4: {e}")
            raise

    def _export_mp3(
        self,
        job_id: str,
        project_data: Dict[str, Any],
        settings: Dict[str, Any],
        customer_id: str,
        user_id: str
    ) -> Tuple[str, float]:
        """Export project audio as MP3"""
        try:
            self.logger.info(f"🎵 Exporting MP3 for job {job_id}")

            export_dir = os.path.join(self.temp_dir, job_id)
            os.makedirs(export_dir, exist_ok=True)

            total_duration = sum(page.get('duration', 5) for page in project_data.get('pages', []))

            # Mix audio tracks
            audio_path = self._mix_audio_tracks(project_data, export_dir, total_duration, customer_id, user_id)

            if not audio_path or not os.path.exists(audio_path):
                raise Exception("No audio tracks found in project")

            # Convert to MP3
            output_path = os.path.join(export_dir, f"{job_id}.mp3")

            stream = ffmpeg.input(audio_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                acodec='libmp3lame',
                audio_bitrate=settings.get('audioBitrate', '192k')
            )
            ffmpeg.run(stream, overwrite_output=True, quiet=True)

            return output_path, total_duration

        except Exception as e:
            self.logger.error(f"Error exporting MP3: {e}")
            raise

    def _export_json(
        self,
        job_id: str,
        project_data: Dict[str, Any],
        settings: Dict[str, Any],
        customer_id: str
    ) -> Tuple[str, float]:
        """Export project as JSON"""
        try:
            self.logger.info(f"📄 Exporting JSON for job {job_id}")

            export_dir = os.path.join(self.temp_dir, job_id)
            os.makedirs(export_dir, exist_ok=True)

            output_path = os.path.join(export_dir, f"{job_id}.json")

            # Save project data as JSON
            with open(output_path, 'w') as f:
                json.dump(project_data, f, indent=2, default=str)

            total_duration = sum(page.get('duration', 5) for page in project_data.get('pages', []))

            return output_path, total_duration

        except Exception as e:
            self.logger.error(f"Error exporting JSON: {e}")
            raise

    def _is_slide_static(self, page: Dict[str, Any]) -> bool:
        """
        Detect if a slide is static (no animations or videos)
        Returns True if slide only contains static elements (images, text, shapes)
        Returns False if slide contains videos or animations
        """
        elements = page.get('elements', [])

        for element in elements:
            element_type = element.get('type', '')

            # Check for video elements
            if element_type == 'video':
                return False

            # Check for animations
            if element.get('animations') or element.get('animation'):
                return False

        # Check for background animations
        background = page.get('background', {})
        if background.get('type') == 'video' or background.get('animation'):
            return False

        return True

    def _render_slides_to_frames(
        self,
        project_data: Dict[str, Any],
        frames_dir: str,
        fps: int,
        customer_id: str,
        user_id: str,
        job_id: str = None
    ):
        """Render all slides to frame sequences with smart static/animated detection"""
        try:
            frame_number = 0
            pages = project_data.get('pages', [])
            total_slides = len(pages)

            canvas_width = project_data.get('settings', {}).get('canvasWidth', 1920)
            canvas_height = project_data.get('settings', {}).get('canvasHeight', 1080)

            # Calculate total frames needed for progress tracking
            total_frames_needed = sum(int(page.get('duration', 5) * fps) for page in pages)
            frames_saved = 0

            self.logger.info(f"Starting to render {total_slides} slides at {canvas_width}x{canvas_height}, {fps} fps")
            self.logger.info(f"Total frames needed: {total_frames_needed}")

            for slide_idx, page in enumerate(pages):
                self.logger.info(f"Rendering slide {slide_idx + 1}/{total_slides}...")

                # Calculate number of frames for this slide
                duration = page.get('duration', 5)
                num_frames = int(duration * fps)

                # Detect if slide is static or animated
                is_static = self._is_slide_static(page)

                if is_static:
                    self.logger.info(f"✨ Slide {slide_idx + 1} is STATIC (image/text only)")
                    self.logger.info(f"⏱️ Duration: {duration}s → Will save 1 frame and loop in FFmpeg")
                else:
                    self.logger.info(f"🎬 Slide {slide_idx + 1} is ANIMATED (video/animations)")
                    self.logger.info(f"⏱️ Duration: {duration}s → Will save {num_frames} frames")

                # Render slide to image
                self.logger.info(f"� Rendering slide {slide_idx + 1}...")
                slide_image = self._render_slide(page, canvas_width, canvas_height, customer_id, user_id)
                self.logger.info(f"✅ Slide {slide_idx + 1} rendered successfully")

                if is_static:
                    # For static slides: save only 1 frame
                    frame_path = os.path.join(frames_dir, f"frame_{frame_number:05d}.png")
                    slide_image.save(frame_path, 'PNG', compress_level=1)
                    frame_number += 1
                    frames_saved += num_frames  # Count as if we saved all frames for progress

                    # Store metadata for FFmpeg to know this is a static slide
                    metadata_path = os.path.join(frames_dir, f"frame_{frame_number-1:05d}.meta")
                    with open(metadata_path, 'w') as f:
                        json.dump({
                            'static': True,
                            'duration': duration,
                            'num_frames': num_frames
                        }, f)

                    # Update progress for static slide
                    progress = int((frames_saved / total_frames_needed) * 70) + 10  # 10-80%
                    if job_id and customer_id:
                        self._update_export_job(job_id, customer_id, {
                            "progress": progress,
                            "current_step": f"Rendered slide {slide_idx + 1}/{total_slides} (static)"
                        })
                    self.logger.info(f"💾 Progress: {frames_saved}/{total_frames_needed} frames ({progress}%)")

                    self.logger.info(f"✅ Slide {slide_idx + 1} saved (1 static frame)")
                else:
                    # For animated slides: render and save each frame individually
                    # This is needed for video elements that change over time
                    self.logger.info(f"💾 Rendering and saving {num_frames} frames for slide {slide_idx + 1}...")

                    # Check if slide has video elements
                    has_video = any(elem.get('type') == 'video' for elem in page.get('elements', []))

                    if has_video:
                        self.logger.info(f"🎬 Slide has video elements - rendering frame-by-frame")
                        # Download video files first and get their durations
                        video_elements = [elem for elem in page.get('elements', []) if elem.get('type') == 'video']
                        video_files = {}
                        video_durations = {}
                        for idx, video_elem in enumerate(video_elements):
                            video_url = video_elem.get('src')
                            if video_url:
                                video_file = self._download_video(video_url, frames_dir, f"video_{slide_idx}_{idx}", customer_id, user_id)
                                if video_file:
                                    video_files[video_elem.get('id')] = video_file
                                    # Get video duration using FFprobe
                                    video_duration = self._get_video_duration(video_file)
                                    if video_duration:
                                        video_durations[video_elem.get('id')] = video_duration
                                        self.logger.info(f"🎬 Video {idx} duration: {video_duration}s")

                        # Render each frame with video
                        for frame_idx in range(num_frames):
                            frame_time = frame_idx / fps
                            frame_image = self._render_slide_with_video(page, canvas_width, canvas_height, customer_id, user_id, frame_time, video_files, video_durations, fps)
                            frame_path = os.path.join(frames_dir, f"frame_{frame_number:05d}.png")
                            frame_image.save(frame_path, 'PNG', compress_level=1)
                            frame_image.close()
                            frame_number += 1
                            frames_saved += 1

                            # Update progress every 50 frames
                            if frame_idx > 0 and frame_idx % 50 == 0:
                                progress = int((frames_saved / total_frames_needed) * 70) + 10
                                if job_id and customer_id:
                                    self._update_export_job(job_id, customer_id, {
                                        "progress": progress,
                                        "current_step": f"Rendering frames: {frames_saved}/{total_frames_needed}"
                                    })
                                self.logger.info(f"💾 Progress: {frame_idx}/{num_frames} frames ({progress}%)")
                    else:
                        # No video - just save the same frame multiple times (for animations)
                        for frame_idx in range(num_frames):
                            frame_path = os.path.join(frames_dir, f"frame_{frame_number:05d}.png")
                            slide_image.save(frame_path, 'PNG', compress_level=1)
                            frame_number += 1
                            frames_saved += 1

                            # Update progress every 50 frames (more frequent updates)
                            if frame_idx > 0 and frame_idx % 50 == 0:
                                progress = int((frames_saved / total_frames_needed) * 70) + 10  # 10-80%
                                if job_id and customer_id:
                                    self._update_export_job(job_id, customer_id, {
                                        "progress": progress,
                                        "current_step": f"Rendering frames: {frames_saved}/{total_frames_needed}"
                                    })
                                self.logger.info(f"💾 Progress: {frame_idx}/{num_frames} frames ({progress}%)")

                    self.logger.info(f"✅ Slide {slide_idx + 1} saved ({num_frames} frames)")

                slide_image.close()

                # Update progress after each slide
                progress = int((frames_saved / total_frames_needed) * 70) + 10  # 10-80%
                if job_id and customer_id:
                    self._update_export_job(job_id, customer_id, {
                        "progress": progress,
                        "current_step": f"Rendered slide {slide_idx + 1}/{total_slides}"
                    })
                self.logger.info(f"📊 Overall progress: {progress}% ({frames_saved}/{total_frames_needed} frames)")

            self.logger.info(f"✅ Rendered {frame_number} actual frames for {total_slides} slides")
            self.logger.info(f"✅ Saved {frames_saved} equivalent frames (with static optimization)")

        except Exception as e:
            self.logger.error(f"❌ Error rendering slides to frames: {e}", exc_info=True)
            raise

    def _render_slide_with_video(
        self,
        page: Dict[str, Any],
        width: int,
        height: int,
        customer_id: str,
        user_id: str,
        frame_time: float,
        video_files: Dict[str, str],
        video_durations: Dict[str, float],
        fps: int
    ) -> Image.Image:
        """Render a single slide at a specific time (for video elements)"""
        try:
            # Create blank canvas
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)

            # Render background (same as _render_slide)
            background = page.get('background', {})
            bg_type = background.get('type', 'solid')

            if bg_type == 'solid':
                color = background.get('color', '#ffffff')
                img = Image.new('RGB', (width, height), color=color)
                draw = ImageDraw.Draw(img)
            elif bg_type == 'gradient':
                gradient_config = background.get('gradient')

                # Handle null or empty gradient config
                if not gradient_config or gradient_config is None:
                    gradient_config = {
                        'startColor': '#667eea',
                        'endColor': '#764ba2'
                    }

                img = self._create_gradient(width, height, gradient_config)
                draw = ImageDraw.Draw(img)
            elif bg_type == 'image' and background.get('imageUrl'):
                bg_img = self._download_image(background.get('imageUrl'), customer_id, user_id)
                if bg_img:
                    bg_img = bg_img.resize((width, height))
                    img = bg_img
                    draw = ImageDraw.Draw(img)

            # Render elements
            elements = page.get('elements', [])
            sorted_elements = sorted(elements, key=lambda e: e.get('zIndex', 0))

            for element in sorted_elements:
                self._render_element_with_video(img, draw, element, width, height, customer_id, user_id, frame_time, video_files, video_durations, fps)

            return img

        except Exception as e:
            self.logger.error(f"❌ Error rendering slide with video: {e}", exc_info=True)
            return Image.new('RGB', (width, height), color='white')

    def _render_slide(self, page: Dict[str, Any], width: int, height: int, customer_id: str, user_id: str) -> Image.Image:
        """Render a single slide to an image"""
        try:
            self.logger.info(f"📐 Creating canvas {width}x{height}")
            # Create blank canvas
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)

            # Render background
            background = page.get('background', {})
            bg_type = background.get('type', 'solid')
            self.logger.info(f"🎨 Rendering background type: {bg_type}")

            if bg_type == 'solid':
                color = background.get('color', '#ffffff')
                img = Image.new('RGB', (width, height), color=color)
                draw = ImageDraw.Draw(img)
                self.logger.info(f"✅ Solid background rendered: {color}")
            elif bg_type == 'gradient':
                gradient_config = background.get('gradient')
                self.logger.info(f"🎨 Gradient config: {gradient_config}")

                # Handle null or empty gradient config
                if not gradient_config or gradient_config is None:
                    self.logger.warning(f"⚠️ Gradient type specified but gradient config is null/empty, using default gradient")
                    gradient_config = {
                        'startColor': '#667eea',
                        'endColor': '#764ba2'
                    }

                img = self._create_gradient(width, height, gradient_config)
                draw = ImageDraw.Draw(img)
                self.logger.info(f"✅ Gradient background rendered")
            elif bg_type == 'image' and background.get('imageUrl'):
                self.logger.info(f"📥 Downloading background image: {background.get('imageUrl')}")
                bg_img = self._download_image(background.get('imageUrl'), customer_id, user_id)
                if bg_img:
                    self.logger.info(f"✅ Background image downloaded, resizing to {width}x{height}")
                    img = bg_img.resize((width, height))
                    draw = ImageDraw.Draw(img)
                    self.logger.info(f"✅ Background image rendered")
                else:
                    self.logger.warning(f"⚠️ Failed to download background image")

            # Render elements (text, images, shapes, videos)
            elements = page.get('elements', [])
            self.logger.info(f"🎭 Rendering {len(elements)} elements")

            # Sort by zIndex (lower values render first = behind)
            sorted_elements = sorted(elements, key=lambda e: e.get('zIndex', 0))
            self.logger.info(f"📊 Element rendering order (by zIndex):")
            for idx, elem in enumerate(sorted_elements):
                self.logger.info(f"   {idx + 1}. type={elem.get('type')}, zIndex={elem.get('zIndex', 0)}, id={elem.get('id')}")

            for idx, element in enumerate(sorted_elements):
                elem_type = element.get('type')
                z_index = element.get('zIndex', 0)
                self.logger.info(f"🔧 Rendering element {idx + 1}/{len(elements)}: type={elem_type}, zIndex={z_index}")
                self._render_element(img, draw, element, width, height, customer_id, user_id)
                self.logger.info(f"✅ Element {idx + 1}/{len(elements)} rendered")

            self.logger.info("✅ Slide rendering complete")
            return img

        except Exception as e:
            self.logger.error(f"❌ Error rendering slide: {e}", exc_info=True)
            # Return blank image on error
            return Image.new('RGB', (width, height), color='white')

    def _render_element(
        self,
        img: Image.Image,
        draw: ImageDraw.Draw,
        element: Dict[str, Any],
        width: int,
        height: int,
        customer_id: str,
        user_id: str
    ):
        """Render a single element on the canvas"""
        try:
            elem_type = element.get('type')
            self.logger.info(f"🎨 Rendering element type: {elem_type}")

            if elem_type == 'text':
                # Render text
                x = int(element.get('x', 0))
                y = int(element.get('y', 0))
                text = element.get('text', "")
                font_size = int(element.get('fontSize', 16))
                color = element.get('color', '#000000')
                text_width = int(element.get('width', width))  # Max width for text wrapping
                text_height = int(element.get('height', height))
                z_index = element.get('zIndex', 0)

                # Log text element details for debugging
                self.logger.info(f"📝 Text element details:")
                self.logger.info(f"   Position: ({x}, {y})")
                self.logger.info(f"   Size: {text_width}x{text_height}")
                self.logger.info(f"   Text content: '{text}'")
                self.logger.info(f"   Font size: {font_size}")
                self.logger.info(f"   Color: {color}")
                self.logger.info(f"   Z-Index: {z_index}")

                # Validate text content
                if not text or text.strip() == "":
                    self.logger.warning(f"⚠️ Text element has empty or missing text content!")
                    self.logger.warning(f"   Element keys: {list(element.keys())}")
                    return

                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                    self.logger.info(f"✅ Loaded TrueType font at size {font_size}")
                except Exception as font_error:
                    self.logger.warning(f"⚠️ Failed to load TrueType font: {font_error}, using default")
                    font = ImageFont.load_default()

                # Wrap text to fit within the specified width
                wrapped_lines = self._wrap_text(text, font, text_width, draw)
                self.logger.info(f"📏 Text wrapped into {len(wrapped_lines)} lines")

                # Draw each line
                current_y = y
                line_height = font_size + int(font_size * 0.2)  # Add 20% line spacing

                for line in wrapped_lines:
                    draw.text((x, current_y), line, fill=color, font=font)
                    current_y += line_height

                self.logger.info(f"✅ Text rendered successfully: {len(wrapped_lines)} lines at ({x}, {y})")

            elif elem_type == 'image' and element.get('src'):
                # Download and composite image
                z_index = element.get('zIndex', 0)
                self.logger.info(f"🖼️ Image element - src: {element.get('src')}, zIndex: {z_index}")
                elem_img = self._download_image(element.get('src'), customer_id, user_id)
                if elem_img:
                    # Resize and position
                    elem_width = int(element.get('width', 100))
                    elem_height = int(element.get('height', 100))
                    elem_img = elem_img.resize((elem_width, elem_height))

                    x = int(element.get('x', 0))
                    y = int(element.get('y', 0))

                    self.logger.info(f"   Pasting image at ({x}, {y}) with size {elem_width}x{elem_height}")
                    img.paste(elem_img, (x, y), elem_img if elem_img.mode == 'RGBA' else None)
                    elem_img.close()
                    self.logger.info(f"✅ Image rendered successfully")
                else:
                    self.logger.warning(f"⚠️ Failed to download/render image")

            elif elem_type == 'video':
                # Render video element - download thumbnail or first frame
                x = int(element.get('x', 0))
                y = int(element.get('y', 0))
                w = int(element.get('width', 100))
                h = int(element.get('height', 100))
                video_src = element.get('src', '')

                self.logger.info(f"🎬 Video element - position: ({x}, {y}), size: {w}x{h}")
                self.logger.info(f"   Video URL: {video_src}")

                # Try to download and render the video thumbnail
                # For now, we'll treat it like an image element
                if video_src:
                    # Check if there's a thumbnail URL
                    thumbnail_url = element.get('thumbnail') or video_src

                    # Download the thumbnail/video
                    video_img = self._download_image(thumbnail_url, customer_id, user_id)
                    if video_img:
                        # Resize to fit the video element dimensions
                        video_img = video_img.resize((w, h))

                        # Paste onto the canvas
                        self.logger.info(f"   Pasting video thumbnail at ({x}, {y}) with size {w}x{h}")
                        img.paste(video_img, (x, y), video_img if video_img.mode == 'RGBA' else None)
                        video_img.close()
                        self.logger.info(f"✅ Video thumbnail rendered successfully")
                    else:
                        # Fallback: draw black rectangle with "VIDEO" text
                        self.logger.warning(f"⚠️ Failed to download video thumbnail, using placeholder")
                        draw.rectangle([x, y, x + w, y + h], fill='#000000')
                        try:
                            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                        except:
                            font = ImageFont.load_default()
                        text = "VIDEO"
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        text_x = x + (w - text_width) // 2
                        text_y = y + (h - text_height) // 2
                        draw.text((text_x, text_y), text, fill='#FFFFFF', font=font)
                else:
                    self.logger.warning(f"⚠️ Video element has no src, skipping")

            elif elem_type == 'shape':
                # Render basic shapes
                x = int(element.get('x', 0))
                y = int(element.get('y', 0))
                w = int(element.get('width', 100))
                h = int(element.get('height', 100))
                fill_color = element.get('fill', '#000000')

                shape_type = element.get('shapeType', 'rectangle')
                self.logger.info(f"🔷 Shape element - type: {shape_type}, position: ({x}, {y}), size: {w}x{h}")
                if shape_type == 'rectangle':
                    draw.rectangle([x, y, x + w, y + h], fill=fill_color)
                elif shape_type == 'circle':
                    draw.ellipse([x, y, x + w, y + h], fill=fill_color)
                self.logger.info(f"✅ Shape rendered successfully")
            else:
                self.logger.warning(f"⚠️ Unknown or unsupported element type: {elem_type}")

        except Exception as e:
            self.logger.error(f"❌ Error rendering element {element.get('type')}: {e}", exc_info=True)
            self.logger.error(f"   Element data: {element}")

    def _render_element_with_video(
        self,
        img: Image.Image,
        draw: ImageDraw.Draw,
        element: Dict[str, Any],
        width: int,
        height: int,
        customer_id: str,
        user_id: str,
        frame_time: float,
        video_files: Dict[str, str],
        video_durations: Dict[str, float],
        fps: int
    ):
        """Render a single element with video support at a specific time"""
        try:
            elem_type = element.get('type')

            if elem_type == 'video':
                # Render video frame at specific time
                x = int(element.get('x', 0))
                y = int(element.get('y', 0))
                w = int(element.get('width', 100))
                h = int(element.get('height', 100))
                elem_id = element.get('id')

                video_file = video_files.get(elem_id)
                video_duration = video_durations.get(elem_id)

                if video_file and os.path.exists(video_file) and video_duration:
                    try:
                        # Loop the video if frame_time exceeds video duration
                        # If video is 5s and timeline is 10s, it should loop twice
                        looped_time = frame_time % video_duration

                        # Extract frame from video at looped time using FFmpeg
                        import subprocess
                        import tempfile

                        # Create temp file for extracted frame
                        temp_frame = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        temp_frame_path = temp_frame.name
                        temp_frame.close()

                        # Use FFmpeg to extract frame at specific time
                        cmd = [
                            'ffmpeg',
                            '-ss', str(looped_time),
                            '-i', video_file,
                            '-frames:v', '1',
                            '-y',
                            '-loglevel', 'error',  # Suppress FFmpeg output
                            temp_frame_path
                        ]

                        subprocess.run(cmd, capture_output=True, check=True)

                        # Load and composite the frame
                        video_frame = Image.open(temp_frame_path)
                        video_frame = video_frame.resize((w, h))
                        img.paste(video_frame, (x, y))
                        video_frame.close()

                        # Clean up temp file
                        os.unlink(temp_frame_path)

                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to extract video frame at {frame_time}s (looped: {looped_time}s): {e}")
                        # Draw placeholder
                        draw.rectangle([x, y, x + w, y + h], fill='#000000')
                else:
                    # No video file - draw placeholder
                    draw.rectangle([x, y, x + w, y + h], fill='#000000')
            else:
                # For non-video elements, use the regular rendering method but suppress verbose logs
                # Temporarily reduce logging for repetitive frame rendering
                self._render_element_quiet(img, draw, element, width, height, customer_id, user_id)

        except Exception as e:
            self.logger.error(f"❌ Error rendering element with video {element.get('type')}: {e}", exc_info=True)

    def _render_element_quiet(
        self,
        img: Image.Image,
        draw: ImageDraw.Draw,
        element: Dict[str, Any],
        width: int,
        height: int,
        customer_id: str,
        user_id: str
    ):
        """Render a single element on the canvas with minimal logging (for frame-by-frame rendering)"""
        try:
            elem_type = element.get('type')

            if elem_type == 'text':
                # Render text
                x = int(element.get('x', 0))
                y = int(element.get('y', 0))
                text = element.get('text', "")
                font_size = int(element.get('fontSize', 16))
                color = element.get('color', '#000000')
                text_width = int(element.get('width', width))
                text_height = int(element.get('height', height))

                if not text or text.strip() == "":
                    return

                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    font = ImageFont.load_default()

                # Wrap text to fit within the specified width
                wrapped_lines = self._wrap_text(text, font, text_width, draw)

                # Draw each line
                current_y = y
                line_height = font_size + int(font_size * 0.2)

                for line in wrapped_lines:
                    draw.text((x, current_y), line, fill=color, font=font)
                    current_y += line_height

            elif elem_type == 'image' and element.get('src'):
                # Download and composite image
                elem_img = self._download_image(element.get('src'), customer_id, user_id)
                if elem_img:
                    elem_width = int(element.get('width', 100))
                    elem_height = int(element.get('height', 100))
                    elem_img = elem_img.resize((elem_width, elem_height))

                    x = int(element.get('x', 0))
                    y = int(element.get('y', 0))

                    img.paste(elem_img, (x, y), elem_img if elem_img.mode == 'RGBA' else None)
                    elem_img.close()

            elif elem_type == 'shape':
                # Render basic shapes
                x = int(element.get('x', 0))
                y = int(element.get('y', 0))
                w = int(element.get('width', 100))
                h = int(element.get('height', 100))
                fill_color = element.get('fill', '#000000')

                shape_type = element.get('shapeType', 'rectangle')
                if shape_type == 'rectangle':
                    draw.rectangle([x, y, x + w, y + h], fill=fill_color)
                elif shape_type == 'circle':
                    draw.ellipse([x, y, x + w, y + h], fill=fill_color)

        except Exception as e:
            self.logger.error(f"❌ Error rendering element {element.get('type')}: {e}", exc_info=True)

    def _mix_audio_tracks(
        self,
        project_data: Dict[str, Any],
        export_dir: str,
        total_duration: float,
        customer_id: str,
        user_id: str
    ) -> Optional[str]:
        """Mix all audio tracks into a single file"""
        try:
            audio_tracks = project_data.get('audioTracks', [])
            video_tracks = project_data.get('videoTracks', [])

            if not audio_tracks and not video_tracks:
                return None

            audio_files = []

            # Download audio tracks
            for idx, track in enumerate(audio_tracks):
                if track.get('url'):
                    audio_file = self._download_audio(track.get('url'), export_dir, f"audio_{idx}", customer_id, user_id)
                    if audio_file:
                        audio_files.append({
                            'path': audio_file,
                            'start': track.get('startTime', 0),
                            'duration': track.get('duration'),
                            'volume': (track.get('volume', 100)) / 100.0
                        })

            # Download video audio tracks
            for idx, track in enumerate(video_tracks):
                if track.get('url') and not track.get('muted'):
                    audio_file = self._download_audio(track.get('url'), export_dir, f"video_audio_{idx}", customer_id, user_id)
                    if audio_file:
                        audio_files.append({
                            'path': audio_file,
                            'start': track.get('startTime', 0),
                            'duration': track.get('duration'),
                            'volume': (track.get('volume', 100)) / 100.0
                        })

            if not audio_files:
                return None

            # Mix audio files using FFmpeg
            output_path = os.path.join(export_dir, "mixed_audio.wav")

            if len(audio_files) == 1:
                # Single audio file - just copy with volume adjustment
                audio = audio_files[0]
                stream = ffmpeg.input(audio['path'])
                stream = ffmpeg.filter(stream, 'volume', audio['volume'])
                stream = ffmpeg.output(stream, output_path, t=total_duration)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
            else:
                # Multiple audio files - mix them
                inputs = [ffmpeg.input(af['path']) for af in audio_files]
                mixed = ffmpeg.filter(inputs, 'amix', inputs=len(inputs), duration='longest')
                stream = ffmpeg.output(mixed, output_path, t=total_duration)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)

            return output_path

        except Exception as e:
            self.logger.error(f"Error mixing audio tracks: {e}")
            return None

    def _create_video_from_frames(
        self,
        frames_dir: str,
        output_path: str,
        fps: int,
        resolution: Dict[str, int],
        codec: str,
        bitrate: str,
        use_gpu: bool
    ) -> str:
        """
        Create video from frames, handling both static and animated slides
        Returns path to the created video file
        """
        try:
            # Scan frames directory for frames and metadata
            self.logger.info(f"📂 Scanning frames directory: {frames_dir}")
            frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
            meta_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.meta')])

            self.logger.info(f"📊 Found {len(frame_files)} frame files and {len(meta_files)} metadata files")

            # If no metadata files, use simple sequential encoding
            if not meta_files:
                self.logger.info("⚠️ No metadata files found, using sequential frame encoding")
                self.logger.info("ℹ️ This means all slides were rendered as animated (all frames saved)")
                return self._encode_sequential_frames(
                    frames_dir,
                    output_path,
                    fps,
                    resolution,
                    codec,
                    bitrate,
                    use_gpu
                )

            # Build video segments for each slide (static or animated)
            self.logger.info(f"🎬 Building video segments from {len(meta_files)} slides...")
            segments_dir = os.path.join(os.path.dirname(frames_dir), "segments")
            os.makedirs(segments_dir, exist_ok=True)
            self.logger.info(f"📁 Created segments directory: {segments_dir}")

            segment_paths = []
            frame_idx = 0

            for slide_num, meta_file in enumerate(meta_files, 1):
                meta_path = os.path.join(frames_dir, meta_file)
                self.logger.info(f"📄 Reading metadata for slide {slide_num}/{len(meta_files)}: {meta_file}")
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)

                self.logger.info(f"📋 Metadata: {metadata}")

                if metadata.get('static'):
                    # Static slide - create video from single frame
                    duration = metadata['duration']
                    frame_file = frame_files[frame_idx]
                    frame_path = os.path.join(frames_dir, frame_file)
                    segment_path = os.path.join(segments_dir, f"segment_{len(segment_paths):03d}.mp4")

                    self.logger.info(f"✨ Creating STATIC segment from {frame_file} (duration: {duration}s)")
                    self.logger.info(f"🔄 Using FFmpeg loop to extend single frame to {duration}s")

                    # Use FFmpeg to loop single frame for duration
                    stream = ffmpeg.input(frame_path, loop=1, t=duration, framerate=fps)
                    stream = ffmpeg.filter(stream, 'scale', resolution["width"], resolution["height"])

                    if use_gpu:
                        self.logger.info(f"🚀 Encoding with GPU (NVENC)")
                        stream = ffmpeg.output(
                            stream,
                            segment_path,
                            vcodec=codec,
                            preset='fast',
                            video_bitrate=bitrate,
                            pix_fmt='yuv420p'
                        )
                    else:
                        self.logger.info(f"💻 Encoding with CPU (libx264)")
                        stream = ffmpeg.output(
                            stream,
                            segment_path,
                            vcodec=codec,
                            preset='medium',
                            video_bitrate=bitrate,
                            pix_fmt='yuv420p'
                        )

                    self.logger.info(f"⏳ Running FFmpeg encoding for static segment...")
                    ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
                    self.logger.info(f"✅ Static segment created: {segment_path}")
                    segment_paths.append(segment_path)
                    frame_idx += 1

                else:
                    # Animated slide - create video from frame sequence
                    num_frames = metadata['num_frames']
                    segment_path = os.path.join(segments_dir, f"segment_{len(segment_paths):03d}.mp4")

                    self.logger.info(f"🎬 Creating ANIMATED segment from {num_frames} frames")

                    # Create temporary directory for this segment's frames
                    segment_frames_dir = os.path.join(segments_dir, f"frames_{len(segment_paths):03d}")
                    os.makedirs(segment_frames_dir, exist_ok=True)
                    self.logger.info(f"📁 Created temp frames directory: {segment_frames_dir}")

                    # Copy frames for this segment
                    self.logger.info(f"📋 Copying {num_frames} frames to segment directory...")
                    for i in range(num_frames):
                        src = os.path.join(frames_dir, frame_files[frame_idx + i])
                        dst = os.path.join(segment_frames_dir, f"frame_{i:05d}.png")
                        shutil.copy(src, dst)
                        if i > 0 and i % 500 == 0:
                            self.logger.info(f"📋 Copied {i}/{num_frames} frames...")
                    self.logger.info(f"✅ All {num_frames} frames copied")

                    # Encode segment
                    input_pattern = os.path.join(segment_frames_dir, "frame_%05d.png")
                    stream = ffmpeg.input(input_pattern, framerate=fps)
                    stream = ffmpeg.filter(stream, 'scale', resolution["width"], resolution["height"])

                    if use_gpu:
                        self.logger.info(f"🚀 Encoding with GPU (NVENC)")
                        stream = ffmpeg.output(
                            stream,
                            segment_path,
                            vcodec=codec,
                            preset='fast',
                            video_bitrate=bitrate,
                            pix_fmt='yuv420p'
                        )
                    else:
                        self.logger.info(f"💻 Encoding with CPU (libx264)")
                        stream = ffmpeg.output(
                            stream,
                            segment_path,
                            vcodec=codec,
                            preset='medium',
                            video_bitrate=bitrate,
                            pix_fmt='yuv420p'
                        )

                    self.logger.info(f"⏳ Running FFmpeg encoding for animated segment...")
                    ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
                    self.logger.info(f"✅ Animated segment created: {segment_path}")
                    segment_paths.append(segment_path)
                    frame_idx += num_frames

                    # Cleanup segment frames
                    self.logger.info(f"🗑️ Cleaning up temporary frames directory...")
                    shutil.rmtree(segment_frames_dir)
                    self.logger.info(f"✅ Cleanup complete")

            # Concatenate all segments
            self.logger.info(f"🎞️ Total segments created: {len(segment_paths)}")
            if len(segment_paths) == 1:
                # Only one segment, just rename it
                self.logger.info("ℹ️ Only one segment, using it directly (no concatenation needed)")
                shutil.copy(segment_paths[0], output_path)
                self.logger.info(f"✅ Video created: {output_path}")
            else:
                # Multiple segments, concatenate them
                self.logger.info(f"🔗 Concatenating {len(segment_paths)} segments into final video...")
                self._concatenate_videos(segment_paths, output_path)
                self.logger.info(f"✅ Final video created: {output_path}")

            # Cleanup segments
            self.logger.info(f"🗑️ Cleaning up segments directory...")
            shutil.rmtree(segments_dir)
            self.logger.info(f"✅ Segments cleanup complete")

            return output_path

        except Exception as e:
            self.logger.error(f"Error creating video from frames: {e}", exc_info=True)
            raise

    def _encode_sequential_frames(
        self,
        frames_dir: str,
        output_path: str,
        fps: int,
        resolution: Dict[str, int],
        codec: str,
        bitrate: str,
        use_gpu: bool
    ) -> str:
        """Encode video from sequential frames (fallback method)"""
        try:
            self.logger.info(f"🎬 Encoding video from sequential frames...")
            input_pattern = os.path.join(frames_dir, "frame_%05d.png")
            self.logger.info(f"📂 Input pattern: {input_pattern}")
            self.logger.info(f"⚙️ Settings: {fps} fps, {resolution['width']}x{resolution['height']}, {bitrate}")

            stream = ffmpeg.input(input_pattern, framerate=fps)
            stream = ffmpeg.filter(stream, 'scale', resolution["width"], resolution["height"])

            if use_gpu:
                self.logger.info(f"🚀 Encoding with GPU (NVENC)")
                stream = ffmpeg.output(
                    stream,
                    output_path,
                    vcodec=codec,
                    preset='fast',
                    video_bitrate=bitrate,
                    pix_fmt='yuv420p'
                )
            else:
                self.logger.info(f"💻 Encoding with CPU (libx264)")
                stream = ffmpeg.output(
                    stream,
                    output_path,
                    vcodec=codec,
                    preset='medium',
                    video_bitrate=bitrate,
                    pix_fmt='yuv420p'
                )

            self.logger.info(f"⏳ Running FFmpeg encoding...")
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            self.logger.info(f"✅ Video encoding complete: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error encoding sequential frames: {e}", exc_info=True)
            raise

    def _concatenate_videos(self, video_paths: List[str], output_path: str):
        """Concatenate multiple video files using FFmpeg concat demuxer"""
        try:
            self.logger.info(f"🔗 Starting concatenation of {len(video_paths)} video segments...")

            # Create concat file
            concat_file = os.path.join(os.path.dirname(output_path), "concat_list.txt")
            self.logger.info(f"📝 Creating concat list file: {concat_file}")
            with open(concat_file, 'w') as f:
                for idx, video_path in enumerate(video_paths, 1):
                    f.write(f"file '{video_path}'\n")
                    self.logger.info(f"  {idx}. {video_path}")

            # Use FFmpeg concat demuxer
            self.logger.info(f"⏳ Running FFmpeg concat demuxer...")
            stream = ffmpeg.input(concat_file, format='concat', safe=0)
            stream = ffmpeg.output(stream, output_path, c='copy')
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

            # Cleanup concat file
            self.logger.info(f"🗑️ Removing concat list file...")
            os.remove(concat_file)

            self.logger.info(f"✅ Successfully concatenated {len(video_paths)} segments into {output_path}")

        except Exception as e:
            self.logger.error(f"Error concatenating videos: {e}", exc_info=True)
            raise

    def _check_gpu_available(self) -> bool:
        """Check if NVIDIA GPU is available for hardware encoding"""
        try:
            import subprocess
            # Check if nvidia-smi is available
            result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=5)
            if result.returncode == 0:
                self.logger.info("✅ NVIDIA GPU detected")
                return True
            else:
                self.logger.info("ℹ️ No NVIDIA GPU detected, using CPU encoding")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            self.logger.info(f"ℹ️ GPU check failed: {e}, using CPU encoding")
            return False

    def _download_image(self, url: str, customer_id: str, user_id: str) -> Optional[Image.Image]:
        """Download image from URL"""
        try:
            # Handle both asset-service URLs and external URLs
            if url.startswith('/api/assets/download/'):
                # Internal asset-service URL - make request to asset-service with auth headers
                asset_service_url = f"{self.config.ASSET_SERVICE_URL}{url}"
                self.logger.debug(f"Downloading image from asset-service: {asset_service_url}")
                headers = {
                    'x-customer-id': customer_id,
                    'x-user-id': user_id
                }
                response = requests.get(asset_service_url, headers=headers, timeout=30)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
            else:
                # External URL
                self.logger.debug(f"Downloading image from external URL: {url}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
        except Exception as e:
            self.logger.warning(f"Error downloading image {url}: {e}")
            return None

    def _get_video_duration(self, video_path: str) -> Optional[float]:
        """Get video duration in seconds using FFprobe"""
        try:
            import subprocess
            import json

            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration

        except Exception as e:
            self.logger.error(f"❌ Error getting video duration for {video_path}: {e}")
            return None

    def _download_video(self, url: str, export_dir: str, filename: str, customer_id: str, user_id: str) -> Optional[str]:
        """
        Download video file from URL

        Handles both relative URLs (e.g., /api/assets/...) and absolute URLs.
        For relative URLs, converts them to absolute URLs using the asset-service.
        """
        try:
            output_path = os.path.join(export_dir, f"{filename}.mp4")

            # Convert relative URL to absolute URL if needed
            if url.startswith('/api/'):
                # Asset service URL - call asset-service directly
                full_url = f"{self.config.ASSET_SERVICE_URL}{url}"
                self.logger.info(f"🔗 Converting video URL to asset-service: {url} -> {full_url}")
            elif url.startswith('/'):
                # Other relative URL - prepend asset service URL
                full_url = f"{self.config.ASSET_SERVICE_URL}{url}"
                self.logger.info(f"🔗 Converting relative URL to absolute: {url} -> {full_url}")
            else:
                full_url = url

            self.logger.info(f"📥 Downloading video from URL: {full_url}")

            # Add authentication headers for internal API calls
            headers = {
                'x-customer-id': customer_id,
                'x-user-id': user_id
            }

            # Download video
            response = requests.get(full_url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.logger.info(f"✅ Successfully downloaded video to: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"❌ Error downloading video {url}: {e}", exc_info=True)
            return None

    def _download_audio(self, url: str, export_dir: str, filename: str, customer_id: str, user_id: str) -> Optional[str]:
        """
        Download audio file from URL

        Handles both relative URLs (e.g., /api/audio-studio/library/...) and absolute URLs.
        For relative URLs, converts them to absolute URLs using the asset-service directly.
        """
        try:
            output_path = os.path.join(export_dir, f"{filename}.wav")

            # Convert relative URL to absolute URL if needed
            if url.startswith('/api/audio-studio/library/'):
                # Audio library URL - call asset-service directly
                # Extract the path after /api/
                asset_path = url.replace('/api/', '')
                full_url = f"{self.config.ASSET_SERVICE_URL}/api/{asset_path}"
                self.logger.info(f"🔗 Converting audio library URL to asset-service: {url} -> {full_url}")
            elif url.startswith('/'):
                # Other relative URL - prepend asset service URL
                full_url = f"{self.config.ASSET_SERVICE_URL}{url}"
                self.logger.info(f"🔗 Converting relative URL to absolute: {url} -> {full_url}")
            else:
                full_url = url

            self.logger.info(f"📥 Downloading audio from URL: {full_url}")

            # Add authentication headers for internal API calls
            headers = {
                'x-customer-id': customer_id,
                'x-user-id': user_id
            }

            # Download audio
            response = requests.get(full_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.logger.info(f"✅ Successfully downloaded audio to: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"❌ Error downloading audio {url}: {e}", exc_info=True)
            return None

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list:
        """
        Wrap text to fit within a specified width

        Args:
            text: The text to wrap
            font: The font to use for measuring
            max_width: Maximum width in pixels
            draw: ImageDraw object for text measurement

        Returns:
            List of wrapped text lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            # Try adding this word to the current line
            test_line = ' '.join(current_line + [word])

            # Get the bounding box of the test line
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]

            if text_width <= max_width:
                # Word fits, add it to current line
                current_line.append(word)
            else:
                # Word doesn't fit
                if current_line:
                    # Save current line and start new one
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)
                    current_line = []

        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]

    def _create_gradient(self, width: int, height: int, gradient_config: Dict[str, Any]) -> Image.Image:
        """Create a gradient image"""
        try:
            # Simple top-to-bottom gradient
            img = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(img)

            # Handle None or empty gradient config
            if gradient_config is None or not isinstance(gradient_config, dict):
                self.logger.warning(f"⚠️ Invalid gradient config (None or not a dict), using default colors")
                gradient_config = {}

            # Parse colors (simplified - assumes hex colors)
            start_color = gradient_config.get('startColor', '#667eea')
            end_color = gradient_config.get('endColor', '#764ba2')

            self.logger.info(f"🎨 Creating gradient: {start_color} → {end_color}")

            # Convert hex to RGB
            start_rgb = tuple(int(start_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            end_rgb = tuple(int(end_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

            # Draw gradient
            for y in range(height):
                ratio = y / height
                r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            self.logger.info(f"✅ Gradient created successfully")
            return img
        except Exception as e:
            self.logger.error(f"❌ Error creating gradient: {e}", exc_info=True)
            return Image.new('RGB', (width, height), color='white')

    def _upload_export(
        self,
        file_path: str,
        job_id: str,
        project_id: str,
        customer_id: str,
        user_id: str,
        export_format: str,
        duration: Optional[float]
    ) -> Tuple[str, Optional[str]]:
        """Upload exported file to MinIO and optionally to video library"""
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()

            file_size = len(file_data)
            ext = file_path.split('.')[-1]

            # Upload to exports bucket
            object_key = f"{customer_id}/{user_id}/exports/{job_id}.{ext}"

            content_type_map = {
                'mp4': 'video/mp4',
                'mp3': 'audio/mpeg',
                'json': 'application/json'
            }

            self.minio_client.put_object(
                bucket_name=self.export_bucket,
                object_name=object_key,
                data=BytesIO(file_data),
                length=file_size,
                content_type=content_type_map.get(ext, 'application/octet-stream'),
                metadata={
                    "customer_id": customer_id,
                    "user_id": user_id,
                    "export_job_id": job_id,
                    "project_id": project_id
                }
            )

            output_url = f"/api/assets/download/{self.export_bucket}/{object_key}"

            # If MP4, also save to video library
            video_id = None
            if export_format.lower() == 'mp4':
                video_id = self._save_to_video_library(
                    file_data,
                    job_id,
                    project_id,
                    customer_id,
                    user_id,
                    output_url,
                    file_size,
                    duration,
                    ext
                )

            return output_url, video_id

        except Exception as e:
            self.logger.error(f"Error uploading export: {e}")
            raise

    def _save_to_video_library(
        self,
        file_data: bytes,
        job_id: str,
        project_id: str,
        customer_id: str,
        user_id: str,
        url: str,
        file_size: int,
        duration: Optional[float],
        ext: str
    ) -> str:
        """Save exported video to video library"""
        try:
            video_id = str(uuid.uuid4())

            # Get project name for video name
            project_data = self.projects_collection.find_one({
                "project_id": project_id,
                "customer_id": customer_id
            })
            video_name = f"{project_data.get('name', 'Untitled')} - Export" if project_data else f"Export {job_id}"

            # Save to video library collection
            video_library_data = {
                "video_id": video_id,
                "customer_id": customer_id,
                "user_id": user_id,
                "name": video_name,
                "url": url,
                "duration": duration or 0.0,
                "format": ext,
                "size": file_size,
                "folder": "Exports",
                "tags": ["export", "design-editor"],
                "is_deleted": False,
                "source_project_id": project_id,
                "export_job_id": job_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            self.video_library_collection.insert_one(video_library_data)
            self.logger.info(f"Saved export to video library: {video_id}")

            return video_id

        except Exception as e:
            self.logger.error(f"Error saving to video library: {e}")
            raise

    def _update_project_exports(
        self,
        project_id: str,
        customer_id: str,
        job_id: str,
        export_format: str,
        output_url: str,
        video_id: Optional[str],
        file_size: int,
        duration: Optional[float],
        settings: Dict[str, Any]
    ):
        """Update project with export metadata"""
        try:
            export_metadata = {
                "export_id": job_id,
                "format": export_format,
                "quality": settings.get('quality', '1080p'),
                "output_url": output_url,
                "output_video_id": video_id,
                "file_size": file_size,
                "duration": duration,
                "exported_at": datetime.utcnow(),
                "exported_by": customer_id
            }

            # Add to project's exports array
            self.projects_collection.update_one(
                {
                    "project_id": project_id,
                    "customer_id": customer_id
                },
                {
                    "$push": {"exports": export_metadata},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            self.logger.info(f"Updated project {project_id} with export metadata")

        except Exception as e:
            self.logger.error(f"Error updating project exports: {e}")
            # Don't raise - this is not critical

    def _create_export_job(
        self,
        job_id: str,
        project_id: str,
        customer_id: str,
        user_id: str,
        export_format: str,
        settings: Dict[str, Any]
    ):
        """Create export job tracking entry in MongoDB"""
        try:
            export_job = {
                "export_job_id": job_id,
                "project_id": project_id,
                "customer_id": customer_id,
                "user_id": user_id,
                "format": export_format,
                "settings": settings,
                "status": "queued",
                "progress": 0,
                "current_step": "Export job created",
                "output_url": None,
                "output_video_id": None,
                "file_size": None,
                "duration": None,
                "error": None,
                "created_at": datetime.utcnow(),
                "started_at": None,
                "completed_at": None
            }

            self.export_jobs_collection.insert_one(export_job)
            self.logger.info(f"Created export job tracking: {job_id}")

        except Exception as e:
            self.logger.error(f"Error creating export job tracking: {e}")
            # Non-critical, continue processing

    def _update_export_job(
        self,
        job_id: str,
        customer_id: str,
        updates: Dict[str, Any]
    ):
        """Update export job tracking entry"""
        try:
            updates["updated_at"] = datetime.utcnow()

            self.export_jobs_collection.update_one(
                {
                    "export_job_id": job_id,
                    "customer_id": customer_id
                },
                {"$set": updates}
            )

            self.logger.debug(f"Updated export job {job_id}: {updates}")

        except Exception as e:
            self.logger.error(f"Error updating export job tracking: {e}")
            # Non-critical, continue processing

    def get_export_job(self, job_id: str, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get export job by ID"""
        try:
            job_data = self.export_jobs_collection.find_one({
                "export_job_id": job_id,
                "customer_id": customer_id
            })

            if not job_data:
                return None

            # Remove MongoDB _id
            job_data.pop('_id', None)

            # Convert datetime objects to ISO format strings for JSON serialization
            datetime_fields = ['created_at', 'started_at', 'completed_at', 'updated_at']
            for field in datetime_fields:
                if field in job_data and job_data[field] is not None:
                    if isinstance(job_data[field], datetime):
                        job_data[field] = job_data[field].isoformat()

            return job_data

        except Exception as e:
            self.logger.error(f"Error getting export job: {e}")
            return None
