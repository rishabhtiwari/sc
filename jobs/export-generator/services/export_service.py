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
                output_path, duration = self._export_mp4(job_id, project_data, settings, customer_id)
            elif export_format.lower() == 'mp3':
                output_path, duration = self._export_mp3(job_id, project_data, settings, customer_id)
            elif export_format.lower() == 'json':
                output_path, duration = self._export_json(job_id, project_data, settings, customer_id)
            else:
                raise Exception(f"Unsupported export format: {export_format}")
            
            # Upload to MinIO
            self.logger.info(f"📤 Uploading export to MinIO...")
            self._update_export_job(job_id, customer_id, {
                "progress": 90,
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
        customer_id: str
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

            # Render slides to frames
            self._render_slides_to_frames(
                project_data,
                frames_dir,
                settings.get('fps', 30)
            )

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
            fps = settings.get('fps', 30)
            codec = settings.get('codec', 'libx264')
            bitrate = settings.get('bitrate', '5M')

            # Create video from frames
            input_pattern = os.path.join(frames_dir, "frame_%05d.png")

            stream = ffmpeg.input(input_pattern, framerate=fps)
            stream = ffmpeg.filter(stream, 'scale', resolution["width"], resolution["height"])

            # Add audio if requested
            if settings.get('includeAudio', True) and (project_data.get('audioTracks') or project_data.get('videoTracks')):
                self.logger.info(f"🎵 Mixing audio tracks...")
                audio_path = self._mix_audio_tracks(project_data, export_dir, total_duration)
                if audio_path and os.path.exists(audio_path):
                    audio_stream = ffmpeg.input(audio_path)
                    stream = ffmpeg.output(
                        stream,
                        audio_stream,
                        output_path,
                        vcodec=codec,
                        video_bitrate=bitrate,
                        acodec='aac',
                        audio_bitrate='192k',
                        shortest=None
                    )
                else:
                    stream = ffmpeg.output(
                        stream,
                        output_path,
                        vcodec=codec,
                        video_bitrate=bitrate
                    )
            else:
                stream = ffmpeg.output(
                    stream,
                    output_path,
                    vcodec=codec,
                    video_bitrate=bitrate
                )

            # Run FFmpeg
            self.logger.info(f"🎞️ Encoding video...")
            ffmpeg.run(stream, overwrite_output=True, quiet=True)

            # Cleanup frames
            shutil.rmtree(frames_dir)

            return output_path, total_duration

        except Exception as e:
            self.logger.error(f"Error exporting MP4: {e}")
            raise

    def _export_mp3(
        self,
        job_id: str,
        project_data: Dict[str, Any],
        settings: Dict[str, Any],
        customer_id: str
    ) -> Tuple[str, float]:
        """Export project audio as MP3"""
        try:
            self.logger.info(f"🎵 Exporting MP3 for job {job_id}")

            export_dir = os.path.join(self.temp_dir, job_id)
            os.makedirs(export_dir, exist_ok=True)

            total_duration = sum(page.get('duration', 5) for page in project_data.get('pages', []))

            # Mix audio tracks
            audio_path = self._mix_audio_tracks(project_data, export_dir, total_duration)

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

    def _render_slides_to_frames(
        self,
        project_data: Dict[str, Any],
        frames_dir: str,
        fps: int
    ):
        """Render all slides to frame sequences"""
        try:
            frame_number = 0
            pages = project_data.get('pages', [])
            total_slides = len(pages)

            canvas_width = project_data.get('settings', {}).get('canvasWidth', 1920)
            canvas_height = project_data.get('settings', {}).get('canvasHeight', 1080)

            for slide_idx, page in enumerate(pages):
                self.logger.info(f"Rendering slide {slide_idx + 1}/{total_slides}...")

                # Calculate number of frames for this slide
                duration = page.get('duration', 5)
                num_frames = int(duration * fps)

                # Render slide to image
                slide_image = self._render_slide(page, canvas_width, canvas_height)

                # Save frame for each frame in duration
                for _ in range(num_frames):
                    frame_path = os.path.join(frames_dir, f"frame_{frame_number:05d}.png")
                    slide_image.save(frame_path, 'PNG')
                    frame_number += 1

                slide_image.close()

            self.logger.info(f"Rendered {frame_number} frames for {total_slides} slides")

        except Exception as e:
            self.logger.error(f"Error rendering slides to frames: {e}")
            raise

    def _render_slide(self, page: Dict[str, Any], width: int, height: int) -> Image.Image:
        """Render a single slide to an image"""
        try:
            # Create blank canvas
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)

            # Render background
            background = page.get('background', {})
            bg_type = background.get('type', 'solid')

            if bg_type == 'solid':
                color = background.get('color', '#ffffff')
                img = Image.new('RGB', (width, height), color=color)
                draw = ImageDraw.Draw(img)
            elif bg_type == 'gradient':
                img = self._create_gradient(width, height, background.get('gradient', {}))
                draw = ImageDraw.Draw(img)
            elif bg_type == 'image' and background.get('imageUrl'):
                bg_img = self._download_image(background.get('imageUrl'))
                if bg_img:
                    img = bg_img.resize((width, height))
                    draw = ImageDraw.Draw(img)

            # Render elements (text, images, shapes, videos)
            elements = page.get('elements', [])
            for element in sorted(elements, key=lambda e: e.get('zIndex', 0)):
                self._render_element(img, draw, element, width, height)

            return img

        except Exception as e:
            self.logger.error(f"Error rendering slide: {e}")
            # Return blank image on error
            return Image.new('RGB', (width, height), color='white')

    def _render_element(
        self,
        img: Image.Image,
        draw: ImageDraw.Draw,
        element: Dict[str, Any],
        width: int,
        height: int
    ):
        """Render a single element on the canvas"""
        try:
            elem_type = element.get('type')

            if elem_type == 'text':
                # Render text
                x = int(element.get('x', 0))
                y = int(element.get('y', 0))
                text = element.get('text', "")
                font_size = int(element.get('fontSize', 16))
                color = element.get('color', '#000000')

                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    font = ImageFont.load_default()

                draw.text((x, y), text, fill=color, font=font)

            elif elem_type == 'image' and element.get('src'):
                # Download and composite image
                elem_img = self._download_image(element.get('src'))
                if elem_img:
                    # Resize and position
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
            self.logger.warning(f"Error rendering element {element.get('type')}: {e}")

    def _mix_audio_tracks(
        self,
        project_data: Dict[str, Any],
        export_dir: str,
        total_duration: float
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
                    audio_file = self._download_audio(track.get('url'), export_dir, f"audio_{idx}")
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
                    audio_file = self._download_audio(track.get('url'), export_dir, f"video_audio_{idx}")
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

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download image from URL"""
        try:
            # Handle both MinIO URLs and external URLs
            if url.startswith('/api/assets/download/'):
                # Internal MinIO URL - extract bucket and key
                parts = url.replace('/api/assets/download/', '').split('/', 1)
                if len(parts) == 2:
                    bucket, key = parts
                    response = self.minio_client.get_object(bucket, key)
                    file_data = response.read()
                    response.close()
                    response.release_conn()
                    return Image.open(BytesIO(file_data))
            else:
                # External URL
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
        except Exception as e:
            self.logger.warning(f"Error downloading image {url}: {e}")
            return None

    def _download_audio(self, url: str, export_dir: str, filename: str) -> Optional[str]:
        """Download audio file from URL"""
        try:
            output_path = os.path.join(export_dir, f"{filename}.wav")

            # Handle both MinIO URLs and external URLs
            if url.startswith('/api/assets/download/'):
                # Internal MinIO URL
                parts = url.replace('/api/assets/download/', '').split('/', 1)
                if len(parts) == 2:
                    bucket, key = parts
                    response = self.minio_client.get_object(bucket, key)
                    file_data = response.read()
                    response.close()
                    response.release_conn()
                    with open(output_path, 'wb') as f:
                        f.write(file_data)
                    return output_path
            else:
                # External URL
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return output_path
        except Exception as e:
            self.logger.warning(f"Error downloading audio {url}: {e}")
            return None

    def _create_gradient(self, width: int, height: int, gradient_config: Dict[str, Any]) -> Image.Image:
        """Create a gradient image"""
        try:
            # Simple top-to-bottom gradient
            img = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(img)

            # Parse colors (simplified - assumes hex colors)
            start_color = gradient_config.get('startColor', '#ffffff')
            end_color = gradient_config.get('endColor', '#000000')

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

            return img
        except Exception as e:
            self.logger.warning(f"Error creating gradient: {e}")
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
