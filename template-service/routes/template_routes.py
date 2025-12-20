"""
Template API Routes
"""
from flask import Blueprint, request, jsonify
from services import TemplateManager, VariableResolver
from pymongo import MongoClient
from typing import Dict, Any
import requests
import os


template_bp = Blueprint('template', __name__)

# These will be injected by app.py
template_manager: TemplateManager = None
variable_resolver: VariableResolver = None
db_client: MongoClient = None
logger = None


def init_routes(tm: TemplateManager, vr: VariableResolver, db: MongoClient, log):
    """Initialize route dependencies"""
    global template_manager, variable_resolver, db_client, logger
    template_manager = tm
    variable_resolver = vr
    db_client = db
    logger = log


@template_bp.route('/templates', methods=['GET'])
def list_templates():
    """
    List all available templates
    
    Query params:
        - category: Filter by category (news, shorts, ecommerce)
    """
    try:
        category = request.args.get('category')
        templates = template_manager.list_templates(category=category)
        
        return jsonify({
            'status': 'success',
            'count': len(templates),
            'templates': templates
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates/<template_id>', methods=['GET'])
def get_template(template_id: str):
    """
    Get template details by ID

    Path params:
        - template_id: Template identifier
    """
    try:
        template = template_manager.get_template_by_id(template_id)

        if not template:
            return jsonify({
                'status': 'error',
                'error': f'Template not found: {template_id}'
            }), 404

        return jsonify({
            'status': 'success',
            'template': template
        }), 200

    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates', methods=['POST'])
def create_template():
    """
    Create or update a template

    Request body:
        {
            "template_id": "my_custom_template_v1",
            "name": "My Custom Template",
            "category": "news",
            "description": "...",
            "version": "1.0.0",
            "aspect_ratio": "16:9",
            "resolution": {"width": 1920, "height": 1080},
            "layers": [...],
            "variables": {...},
            "metadata": {...}
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['template_id', 'name', 'category']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Extract template data
        template_id = data['template_id']
        category = data['category']

        # Save template
        template_manager.save_template(category, template_id, data)

        logger.info(f"Template saved: {template_id} (category: {category})")

        return jsonify({
            'status': 'success',
            'message': 'Template saved successfully',
            'template_id': template_id
        }), 201

    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id: str):
    """
    Delete a template (soft delete by setting is_active=false)

    Path params:
        - template_id: Template identifier
    """
    try:
        # Get the template first to find its category
        template = template_manager.get_template_by_id(template_id)

        if not template:
            return jsonify({
                'status': 'error',
                'error': f'Template not found: {template_id}'
            }), 404

        # Soft delete by setting is_active=false
        db = db_client['news']
        result = db.templates.update_one(
            {'template_id': template_id},
            {'$set': {'is_active': False}}
        )

        if result.modified_count == 0:
            return jsonify({
                'status': 'error',
                'error': 'Failed to delete template'
            }), 500

        logger.info(f"Template deleted: {template_id}")

        return jsonify({
            'status': 'success',
            'message': 'Template deleted successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates/resolve', methods=['POST'])
def resolve_template():
    """
    Resolve template with variables and customer config
    
    Request body:
        {
            "customer_id": "customer_123",
            "template_type": "long_video",  // or "shorts", "product"
            "template_id": "modern_news_v1",  // Optional: override customer default
            "variables": {
                "title": "Breaking News",
                "background_image": "/path/to/image.png",
                ...
            }
        }
    
    Response:
        {
            "status": "success",
            "template_id": "modern_news_v1",
            "resolved_template": { ... }
        }
    """
    try:
        data = request.json
        
        # Validate request
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'Request body is required'
            }), 400
        
        customer_id = data.get('customer_id')
        template_type = data.get('template_type', 'long_video')
        template_id = data.get('template_id')
        variables = data.get('variables', {})
        
        if not customer_id:
            return jsonify({
                'status': 'error',
                'error': 'customer_id is required'
            }), 400
        
        # Get customer configuration
        customer_config = _get_customer_config(customer_id)
        
        # Determine which template to use
        if not template_id:
            template_id = _get_customer_template_preference(customer_config, template_type)
        
        if not template_id:
            return jsonify({
                'status': 'error',
                'error': f'No template configured for type: {template_type}'
            }), 400
        
        # Load template
        template = template_manager.get_template_by_id(template_id)
        
        if not template:
            return jsonify({
                'status': 'error',
                'error': f'Template not found: {template_id}'
            }), 404
        
        # Apply default values for missing variables
        variables = variable_resolver.apply_defaults(template, variables)
        
        # Validate required variables
        validation = variable_resolver.validate_required_variables(template, variables)
        if not validation['valid']:
            return jsonify({
                'status': 'error',
                'error': 'Missing required variables',
                'missing_variables': validation['missing_variables']
            }), 400
        
        # Merge customer configuration
        template_with_customer_config = variable_resolver.merge_customer_config(
            template,
            customer_config.get('video_config', {})
        )
        
        # Resolve template with variables
        resolved_template = variable_resolver.resolve_template(
            template_with_customer_config,
            variables
        )
        
        logger.info(f"Resolved template {template_id} for customer {customer_id}")
        
        return jsonify({
            'status': 'success',
            'template_id': template_id,
            'resolved_template': resolved_template
        }), 200
    
    except Exception as e:
        logger.error(f"Error resolving template: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


def _get_customer_config(customer_id: str) -> Dict[str, Any]:
    """Get customer configuration from database"""
    try:
        db = db_client['news']
        customer = db.customers.find_one({'customer_id': customer_id})

        if not customer:
            logger.warning(f"Customer not found: {customer_id}, using defaults")
            return {}

        return customer

    except Exception as e:
        logger.error(f"Error getting customer config: {e}")
        return {}


def _generate_video_with_generator(template: Dict[str, Any], output_path: str) -> str:
    """
    Call video-generator service to create a video and save it to output_path

    Args:
        template: Resolved template configuration
        output_path: Where to save the generated video

    Returns:
        Path to generated video or None if failed
    """
    try:
        import shutil

        video_generator_url = os.getenv('VIDEO_GENERATOR_URL', 'http://ichat-video-generator:8095')
        preview_endpoint = f'{video_generator_url}/api/preview'

        logger.info(f"Requesting video generation from {preview_endpoint}")

        response = requests.post(
            preview_endpoint,
            json={
                'template': template,
                'preview_mode': True,
                'output_path': output_path
            },
            timeout=300  # 5 minutes timeout for video generation
        )

        if response.status_code == 200:
            result = response.json()

            # If video-generator returns video content, save it
            if result.get('video_content'):
                import base64
                video_data = base64.b64decode(result['video_content'])
                with open(output_path, 'wb') as f:
                    f.write(video_data)
                logger.info(f"Video saved to {output_path}")
                return output_path

            # If video-generator saved it directly, copy/move to desired location
            elif result.get('video_path'):
                generated_path = result['video_path']
                logger.info(f"Video generated at {generated_path}")

                # If the generated path is different from output_path, copy it
                if generated_path != output_path:
                    # Check if generated file exists (it might be a dummy response)
                    if os.path.exists(generated_path):
                        shutil.copy2(generated_path, output_path)
                        logger.info(f"Video copied to {output_path}")
                        return output_path
                    else:
                        # File doesn't exist, create a placeholder
                        logger.warning(f"Generated video not found at {generated_path}, creating placeholder")
                        _create_placeholder_video(output_path)
                        return output_path
                else:
                    return generated_path

            return None
        else:
            logger.error(f"Video generation failed: {response.text}")
            return None

    except requests.exceptions.Timeout:
        logger.error("Video generation timed out")
        return None
    except Exception as e:
        logger.error(f"Error calling video-generator: {e}", exc_info=True)
        return None


def _create_placeholder_video(output_path: str) -> None:
    """
    Create a creative sample video for template preview
    Smaller size (720p) with animated gradient and geometric shapes
    """
    try:
        from moviepy.editor import VideoClip
        import numpy as np
        import math

        # Smaller size for faster loading - 720p instead of 1080p
        duration = 5  # Shorter duration
        size = (1280, 720)  # 720p instead of 1080p
        fps = 30

        def make_frame(t):
            """Create animated gradient with moving geometric shapes"""
            # Create base gradient that shifts colors over time
            frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)

            # Animated gradient background
            for y in range(size[1]):
                for x in range(size[0]):
                    # Create a diagonal gradient that animates
                    r = int(((x + y) / (size[0] + size[1]) * 255 + t * 50) % 255)
                    g = int(((x - y) / (size[0] + size[1]) * 255 + t * 30) % 255)
                    b = int((math.sin(t * 2 + x / 100) * 127 + 128))
                    frame[y, x] = [r, g, b]

            # Add animated circle
            center_x = int(size[0] / 2 + math.cos(t * 2) * 200)
            center_y = int(size[1] / 2 + math.sin(t * 2) * 100)
            radius = int(50 + math.sin(t * 3) * 20)

            for y in range(max(0, center_y - radius), min(size[1], center_y + radius)):
                for x in range(max(0, center_x - radius), min(size[0], center_x + radius)):
                    if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                        frame[y, x] = [255, 255, 255]  # White circle

            # Add pulsing rectangles in corners
            pulse = int(abs(math.sin(t * 4)) * 100)
            # Top-left
            frame[0:pulse, 0:pulse] = [255, 200, 0]
            # Top-right
            frame[0:pulse, size[0]-pulse:size[0]] = [0, 255, 200]
            # Bottom-left
            frame[size[1]-pulse:size[1], 0:pulse] = [200, 0, 255]
            # Bottom-right
            frame[size[1]-pulse:size[1], size[0]-pulse:size[0]] = [255, 100, 100]

            return frame

        video = VideoClip(make_frame, duration=duration)

        # Write video file with optimized settings for smaller size
        video.write_videofile(
            output_path,
            fps=fps,
            codec='libx264',
            audio=False,
            logger=None,
            preset='fast',  # Good balance between speed and compression
            bitrate='500k'  # Lower bitrate for smaller file size
        )

        logger.info(f"Creative placeholder video created at {output_path}")

    except Exception as e:
        logger.error(f"Error creating placeholder video with MoviePy: {e}")
        # Fallback to FFmpeg with creative pattern
        try:
            import subprocess
            # Create a colorful test pattern with FFmpeg
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', '-i',
                'testsrc=duration=5:size=1280x720:rate=30',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                '-preset', 'fast', '-b:v', '500k',
                '-y', output_path
            ], check=True, capture_output=True)
            logger.info(f"Placeholder video created with FFmpeg at {output_path}")
        except Exception as ffmpeg_error:
            logger.error(f"Error creating placeholder video with FFmpeg: {ffmpeg_error}")
            # Last resort: simple gradient with FFmpeg
            try:
                import subprocess
                subprocess.run([
                    'ffmpeg', '-f', 'lavfi', '-i',
                    'color=c=0x4A90E2:s=1280x720:d=5',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-preset', 'ultrafast',
                    '-y', output_path
                ], check=True, capture_output=True)
                logger.info(f"Simple placeholder video created at {output_path}")
            except Exception as final_error:
                logger.error(f"All video creation methods failed: {final_error}")
                raise


def _get_customer_template_preference(customer_config: Dict[str, Any], template_type: str) -> str:
    """Get customer's template preference for given type"""
    video_config = customer_config.get('video_config', {})

    # Map template type to config field
    type_mapping = {
        'long_video': 'long_video_template',
        'shorts': 'shorts_template',
        'product': 'product_template'
    }

    config_field = type_mapping.get(template_type)
    if not config_field:
        return None

    return video_config.get(config_field)


@template_bp.route('/templates/preview', methods=['POST'])
def preview_template():
    """
    Generate a preview video from template configuration

    Strategy:
    1. Check if default sample video exists in /app/public/assets/sample_video.mp4
    2. If not, call video-generator to create it and store in assets
    3. For live changes, generate preview in /app/public/temp/ folder
    4. Return URL to the preview video

    Request body:
        {
            "template": {
                "template_id": "preview_template",
                "name": "Preview Template",
                "category": "news",
                "aspect_ratio": "16:9",
                "resolution": {"width": 1920, "height": 1080},
                "layers": [...],
                "effects": [...],
                "background_music": {...},
                "logo": {...},
                "thumbnail": {...},
                "variables": {...}
            },
            "sample_data": {  // Optional: override default sample data
                "title": "Sample News Title",
                "description": "Sample description text",
                ...
            },
            "is_initial": true  // If true, use/create default sample video
        }

    Response:
        {
            "status": "success",
            "preview_url": "/api/templates/preview/video/preview_abc123.mp4",
            "message": "Preview generated successfully"
        }
    """
    try:
        import hashlib
        import uuid

        data = request.get_json()

        if not data or 'template' not in data:
            return jsonify({
                'status': 'error',
                'error': 'Template data is required'
            }), 400

        template = data['template']
        sample_data = data.get('sample_data', {})
        is_initial = data.get('is_initial', True)

        # Generate sample data for template variables
        resolved_sample_data = _generate_sample_data(template, sample_data)

        # Resolve template with sample data
        resolved_template = variable_resolver.resolve_template(template, resolved_sample_data)

        # Create directories if they don't exist
        assets_dir = '/app/public/assets'
        temp_dir = '/app/public/temp'
        os.makedirs(assets_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

        # If this is initial load, check for default sample video
        if is_initial:
            default_sample_path = os.path.join(assets_dir, 'sample_video.mp4')

            if os.path.exists(default_sample_path):
                logger.info("Using existing default sample video")
                return jsonify({
                    'status': 'success',
                    'preview_url': '/api/templates/preview/video/sample_video.mp4',
                    'video_path': default_sample_path,
                    'message': 'Using default sample video'
                }), 200
            else:
                logger.info("Default sample video not found, generating...")
                # Generate default sample video using video-generator
                video_path = _generate_video_with_generator(resolved_template, default_sample_path)

                if video_path:
                    return jsonify({
                        'status': 'success',
                        'preview_url': '/api/templates/preview/video/sample_video.mp4',
                        'video_path': video_path,
                        'message': 'Default sample video generated'
                    }), 200
                else:
                    return jsonify({
                        'status': 'error',
                        'error': 'Failed to generate default sample video'
                    }), 500

        # For live changes, generate preview in temp folder
        # Create unique filename based on template hash
        template_hash = hashlib.md5(str(template).encode()).hexdigest()[:8]
        preview_id = str(uuid.uuid4())[:8]
        preview_filename = f'preview_{template_hash}_{preview_id}.mp4'
        preview_path = os.path.join(temp_dir, preview_filename)

        logger.info(f"Generating live preview: {preview_filename}")

        # Generate preview video
        video_path = _generate_video_with_generator(resolved_template, preview_path)

        if video_path:
            return jsonify({
                'status': 'success',
                'preview_url': f'/api/templates/preview/video/{preview_filename}',
                'video_path': video_path,
                'is_temp': True,
                'message': 'Preview generated successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'error': 'Failed to generate preview video'
            }), 500

    except Exception as e:
        logger.error(f"Error generating preview: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


def _generate_sample_data(template: Dict[str, Any], override_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate sample data for template variables

    Args:
        template: Template configuration
        override_data: Optional data to override defaults

    Returns:
        Dictionary of sample data for all template variables
    """
    sample_data = {}
    variables = template.get('variables', {})

    # Default sample values by variable type
    defaults_by_type = {
        'text': 'Sample Text',
        'color': '#3B82F6',  # Blue
        'image': '/app/assets/sample_image.jpg',
        'video': '/app/assets/sample_video.mp4',
        'number': 1.0,
        'url': 'https://example.com',
        'audio': '/app/assets/sample_audio.mp3',
        'font': 'Arial'
    }

    # Specific defaults for common variable names
    specific_defaults = {
        'title': 'Breaking News: Sample Headline',
        'description': 'This is a sample description for the news article. It provides context and details about the story.',
        'short_summary': 'Sample news summary for ticker',
        'brand_color': '#3B82F6',
        'background_image': '/app/assets/sample_background.jpg',
        'logo_path': '/app/assets/logo.png',
        'music_file': '/app/assets/background_music.wav',
        'thumbnail_image': '/app/assets/sample_thumbnail.jpg'
    }

    # Generate sample data for each variable
    for var_name, var_config in variables.items():
        # Check if override provided
        if override_data and var_name in override_data:
            sample_data[var_name] = override_data[var_name]
            continue

        # Check specific defaults
        if var_name in specific_defaults:
            sample_data[var_name] = specific_defaults[var_name]
            continue

        # Use type-based default
        var_type = var_config.get('type', 'text')
        sample_data[var_name] = defaults_by_type.get(var_type, 'Sample Value')

    return sample_data


@template_bp.route('/templates/preview/video/<filename>', methods=['GET'])
def serve_preview_video(filename: str):
    """
    Serve preview video files from assets or temp folder

    Path params:
        - filename: Video filename (e.g., sample_video.mp4 or preview_abc123.mp4)
    """
    try:
        from flask import send_file

        # Check in assets folder first
        assets_path = os.path.join('/app/public/assets', filename)
        if os.path.exists(assets_path):
            logger.info(f"Serving video from assets: {filename}")
            return send_file(assets_path, mimetype='video/mp4')

        # Check in temp folder
        temp_path = os.path.join('/app/public/temp', filename)
        if os.path.exists(temp_path):
            logger.info(f"Serving video from temp: {filename}")
            return send_file(temp_path, mimetype='video/mp4')

        logger.warning(f"Video not found: {filename}")
        return jsonify({
            'status': 'error',
            'error': 'Video not found'
        }), 404

    except Exception as e:
        logger.error(f"Error serving video {filename}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates/preview/cleanup', methods=['POST'])
def cleanup_preview_videos():
    """
    Cleanup temporary preview videos

    Request body:
        {
            "preview_url": "/api/templates/preview/video/preview_abc123.mp4"  // Optional: specific file
        }

    If no preview_url provided, cleans up all temp files older than 1 hour
    """
    try:
        import time

        data = request.get_json() or {}
        preview_url = data.get('preview_url')

        temp_dir = '/app/public/temp'

        if preview_url:
            # Clean up specific file
            filename = preview_url.split('/')[-1]
            file_path = os.path.join(temp_dir, filename)

            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted preview video: {filename}")
                return jsonify({
                    'status': 'success',
                    'message': f'Deleted {filename}'
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'File not found'
                }), 404
        else:
            # Clean up old temp files (older than 1 hour)
            if not os.path.exists(temp_dir):
                return jsonify({
                    'status': 'success',
                    'message': 'No temp files to clean'
                }), 200

            current_time = time.time()
            deleted_count = 0

            for filename in os.listdir(temp_dir):
                if filename.startswith('preview_') and filename.endswith('.mp4'):
                    file_path = os.path.join(temp_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path)

                    # Delete files older than 1 hour (3600 seconds)
                    if file_age > 3600:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted old preview: {filename}")

            return jsonify({
                'status': 'success',
                'message': f'Deleted {deleted_count} old preview files'
            }), 200

    except Exception as e:
        logger.error(f"Error cleaning up previews: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

