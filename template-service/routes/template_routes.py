"""
Template API Routes
"""
from flask import Blueprint, request, jsonify, g
from services import TemplateManager, VariableResolver
from pymongo import MongoClient
from typing import Dict, Any
import requests
import os
from utils.helpers import substitute_variables
from utils.multi_tenant_utils import get_customer_id
from utils.url_converter import URLConverter


template_bp = Blueprint('template', __name__)

# These will be injected by app.py
template_manager: TemplateManager = None
variable_resolver: VariableResolver = None
db_client: MongoClient = None
logger = None
url_converter = None


def init_routes(tm: TemplateManager, vr: VariableResolver, db: MongoClient, log):
    """Initialize route dependencies"""
    global template_manager, variable_resolver, db_client, logger, url_converter
    template_manager = tm
    variable_resolver = vr
    db_client = db
    logger = log
    url_converter = URLConverter(logger=log)


def _apply_effects_to_layer(layer_video, effects, duration, width, height):
    """
    Apply global effects to a video layer

    Args:
        layer_video: MoviePy VideoClip
        effects: List of effect configurations
        duration: Duration of the layer in seconds
        width: Width of the layer in pixels
        height: Height of the layer in pixels

    Returns:
        Modified VideoClip with effects applied
    """
    from PIL import Image as PILImage
    import numpy as np

    # Apply Ken Burns effect if requested
    ken_burns_effect = next((e for e in effects if e.get('type') == 'ken_burns'), None)
    if ken_burns_effect:
        params = ken_burns_effect.get('params', {})
        zoom_start = params.get('zoom_start', 1.0)
        zoom_end = params.get('zoom_end', 1.2)

        logger.info(f"Applying Ken Burns effect to layer: zoom {zoom_start} -> {zoom_end}")

        # Apply zoom effect using resize
        def zoom_effect(get_frame, t):
            """Apply zoom effect to frame at time t"""
            # Calculate zoom factor at time t (linear interpolation)
            progress = t / duration if duration > 0 else 0
            zoom = zoom_start + (zoom_end - zoom_start) * progress

            # Get the original frame
            frame = get_frame(t)
            h, w = frame.shape[:2]

            # Calculate new dimensions
            new_w = int(w * zoom)
            new_h = int(h * zoom)

            # Ensure frame is uint8
            if frame.dtype != np.uint8:
                frame = np.clip(frame, 0, 255).astype(np.uint8)

            # Resize frame
            pil_frame = PILImage.fromarray(frame)
            pil_frame = pil_frame.resize((new_w, new_h), PILImage.LANCZOS)

            # Crop to original size (center crop)
            left = (new_w - w) // 2
            top = (new_h - h) // 2
            pil_frame = pil_frame.crop((left, top, left + w, top + h))

            return np.array(pil_frame, dtype=np.uint8)

        # Apply the zoom effect
        layer_video = layer_video.fl(zoom_effect)

    return layer_video


@template_bp.route('/templates', methods=['GET'])
def list_templates():
    """
    List all available templates for the current customer

    Query params:
        - category: Filter by category (news, shorts, ecommerce)
    """
    try:
        # Get customer_id from request context (set by middleware)
        customer_id = get_customer_id(getattr(g, 'customer_id', None))

        category = request.args.get('category')
        templates = template_manager.list_templates(
            category=category,
            customer_id=customer_id
        )

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
    Get template details by ID for the current customer

    Path params:
        - template_id: Template identifier
    """
    try:
        # Get customer_id from request context (set by middleware)
        customer_id = get_customer_id(getattr(g, 'customer_id', None))

        template = template_manager.get_template_by_id(
            template_id,
            customer_id=customer_id
        )

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
    Create or update a template for the current customer

    Request body:
        {
            "template_id": "my_custom_template_v1" (optional - will be auto-generated if not provided),
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
        # Get customer_id and user_id from request context (set by middleware)
        customer_id = get_customer_id(getattr(g, 'customer_id', None))
        user_id = getattr(g, 'user_id', None)

        data = request.get_json()

        # DEBUG: Log all settings received from UI
        logger.info("=" * 80)
        logger.info("📝 TEMPLATE SAVE REQUEST - ALL SETTINGS FROM UI")
        logger.info("=" * 80)
        logger.info(f"Customer ID: {customer_id}")
        logger.info(f"User ID: {user_id}")
        logger.info(f"\n📋 BASIC INFO:")
        logger.info(f"  - Name: {data.get('name')}")
        logger.info(f"  - Description: {data.get('description')}")
        logger.info(f"  - Category: {data.get('category')}")
        logger.info(f"  - Template ID: {data.get('template_id')}")
        logger.info(f"  - Aspect Ratio: {data.get('aspect_ratio')}")
        logger.info(f"  - Version: {data.get('version')}")

        logger.info(f"\n🎨 LAYERS ({len(data.get('layers', []))} layers):")
        for idx, layer in enumerate(data.get('layers', [])):
            logger.info(f"  Layer {idx + 1}:")
            logger.info(f"    - Type: {layer.get('type')}")
            logger.info(f"    - ID: {layer.get('id')}")
            logger.info(f"    - Source: {layer.get('source')}")
            logger.info(f"    - Position: {layer.get('position')}")
            logger.info(f"    - Size: {layer.get('size')}")
            logger.info(f"    - Z-Index: {layer.get('z_index')}")
            logger.info(f"    - Opacity: {layer.get('opacity')}")
            logger.info(f"    - Start Time: {layer.get('start_time')}")
            logger.info(f"    - Duration: {layer.get('duration')}")
            if layer.get('type') == 'text':
                logger.info(f"    - Content: {layer.get('content')}")
                logger.info(f"    - Font: {layer.get('font')}")

        logger.info(f"\n✨ EFFECTS ({len(data.get('effects', []))} effects):")
        for idx, effect in enumerate(data.get('effects', [])):
            logger.info(f"  Effect {idx + 1}:")
            logger.info(f"    - Type: {effect.get('type')}")
            logger.info(f"    - Target Layer: {effect.get('target_layer_id')}")
            logger.info(f"    - Params: {effect.get('params')}")

        logger.info(f"\n🎵 BACKGROUND MUSIC:")
        bg_music = data.get('background_music', {})
        logger.info(f"  - Enabled: {bg_music.get('enabled')}")
        logger.info(f"  - Source: {bg_music.get('source')}")
        logger.info(f"  - Volume: {bg_music.get('volume')}")
        logger.info(f"  - Fade In: {bg_music.get('fade_in')}")
        logger.info(f"  - Fade Out: {bg_music.get('fade_out')}")

        logger.info(f"\n🏷️ LOGO:")
        logo = data.get('logo', {})
        logger.info(f"  - Enabled: {logo.get('enabled')}")
        logger.info(f"  - Source: {logo.get('source')}")
        logger.info(f"  - Position: {logo.get('position')}")
        logger.info(f"  - Scale: {logo.get('scale')}")
        logger.info(f"  - Opacity: {logo.get('opacity')}")
        logger.info(f"  - Margin: {logo.get('margin')}")

        logger.info(f"\n🖼️ THUMBNAIL:")
        thumbnail = data.get('thumbnail', {})
        logger.info(f"  - Auto Generate: {thumbnail.get('auto_generate')}")
        logger.info(f"  - Timestamp: {thumbnail.get('timestamp')}")
        logger.info(f"  - Source: {thumbnail.get('source')}")
        logger.info(f"  - Text Config: {thumbnail.get('text')}")

        logger.info(f"\n🔧 VARIABLES ({len(data.get('variables', {}))} variables):")
        for var_name, var_config in data.get('variables', {}).items():
            logger.info(f"  - {var_name}: {var_config}")

        logger.info(f"\n📦 METADATA:")
        metadata = data.get('metadata', {})
        logger.info(f"  - Author: {metadata.get('author')}")
        logger.info(f"  - Tags: {metadata.get('tags')}")
        logger.info(f"  - Thumbnail: {metadata.get('thumbnail')}")

        logger.info("=" * 80)

        # Validate required fields (template_id is now optional)
        required_fields = ['name', 'category']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Auto-generate template_id if not provided
        if 'template_id' not in data or not data['template_id']:
            import uuid
            # Generate template_id from name and UUID
            name_slug = data['name'].lower().replace(' ', '_').replace('-', '_')
            # Remove special characters
            name_slug = ''.join(c for c in name_slug if c.isalnum() or c == '_')
            unique_id = str(uuid.uuid4())[:8]
            template_id = f"{name_slug}_{unique_id}"
            data['template_id'] = template_id
        else:
            template_id = data['template_id']

        category = data['category']

        # Save template with customer_id and user_id
        template_manager.save_template(
            category,
            template_id,
            data,
            customer_id=customer_id,
            user_id=user_id
        )

        logger.info(f"Template saved: {template_id} (category: {category}, customer: {customer_id})")

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
    Only allows deleting templates owned by the current customer

    Path params:
        - template_id: Template identifier
    """
    try:
        # Get customer_id from request context (set by middleware)
        customer_id = get_customer_id(getattr(g, 'customer_id', None))

        # Get the template first to verify ownership
        template = template_manager.get_template_by_id(
            template_id,
            customer_id=customer_id
        )

        if not template:
            return jsonify({
                'status': 'error',
                'error': f'Template not found: {template_id}'
            }), 404

        # Check if any products are using this template
        db = db_client['news']
        products_using_template = db.ecommerce_products.count_documents({
            'template_id': template_id,
            'customer_id': customer_id
        })

        if products_using_template > 0:
            return jsonify({
                'status': 'error',
                'error': f'Cannot delete template. {products_using_template} product(s) are currently using this template.',
                'products_count': products_using_template
            }), 400

        # Soft delete by setting is_active=false
        # Include customer_id in the query to ensure we only delete our own templates
        result = db.templates.update_one(
            {'template_id': template_id, 'customer_id': customer_id},
            {'$set': {'is_active': False}}
        )

        if result.modified_count == 0:
            return jsonify({
                'status': 'error',
                'error': 'Failed to delete template'
            }), 500

        logger.info(f"Template deleted: {template_id} (customer: {customer_id})")

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


@template_bp.route('/templates/<template_id>/generate', methods=['POST'])
def generate_video_from_template(template_id: str):
    """
    Generate video from template with variables

    Request body:
        {
            "variables": {
                "product_images": ["url1", "url2", ...],
                "product_name": "Product Name",
                ...
            },
            "audio_url": "http://...",
            "output_path": "videos/product_123.mp4"
        }

    Response:
        {
            "status": "success",
            "video_url": "http://..."
        }
    """
    try:
        customer_id = get_customer_id(getattr(g, 'customer_id', None))
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'error': 'Request body is required'
            }), 400

        variables = data.get('variables', {})
        audio_url = data.get('audio_url')
        output_path = data.get('output_path', f'videos/{template_id}.mp4')

        logger.info(f"🎬 Generating video from template {template_id}")

        # Load template
        template = template_manager.get_template_by_id(template_id, customer_id=customer_id)
        if not template:
            return jsonify({
                'status': 'error',
                'error': f'Template {template_id} not found'
            }), 404

        # Clean template for JSON serialization (remove MongoDB-specific fields)
        template_clean = template.copy()
        # Remove _id if present
        if '_id' in template_clean:
            del template_clean['_id']
        # Remove datetime fields
        for field in ['created_at', 'updated_at', 'deleted_at']:
            if field in template_clean:
                del template_clean[field]
        # Remove audit fields
        for field in ['created_by', 'updated_by', 'deleted_by', 'customer_id', 'user_id']:
            if field in template_clean:
                del template_clean[field]

        # Resolve variables in template
        resolved_template = variable_resolver.resolve_template(template_clean, variables)

        # Add audio URL if provided (convert to internal URL)
        if audio_url:
            resolved_template['audio_url'] = url_converter.convert_url(audio_url)

        # Call preview endpoint to generate video (call our own service)
        preview_response = requests.post(
            'http://localhost:5000/api/templates/preview',
            json={
                'template': resolved_template,
                'is_initial': False
            },
            headers={'X-Customer-ID': customer_id},
            timeout=300
        )

        if preview_response.status_code != 200:
            logger.error(f"Failed to generate video: {preview_response.text}")
            return jsonify({
                'status': 'error',
                'error': 'Failed to generate video',
                'details': preview_response.text
            }), 500

        result = preview_response.json()
        video_url = result.get('preview_url', '')

        # Keep the relative URL - it will be accessed through API server proxy
        # The API server has a proxy endpoint at /api/templates/preview/video/<filename>
        # that forwards requests to the template service
        # Frontend will access it as: http://localhost:8080/api/templates/preview/video/<filename>

        return jsonify({
            'status': 'success',
            'video_url': video_url  # Return relative URL like /api/templates/preview/video/preview_xxx.mp4
        }), 200

    except Exception as e:
        logger.error(f"Error generating video from template: {e}", exc_info=True)
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
                        # File doesn't exist, create a placeholder with effects
                        logger.warning(f"Generated video not found at {generated_path}, creating placeholder with effects")
                        aspect_ratio = template.get('aspect_ratio', '16:9')
                        effects = template.get('effects', [])
                        _create_placeholder_video(output_path, aspect_ratio, effects)
                        return output_path
                else:
                    return generated_path

            return None
        else:
            logger.error(f"Video generation failed: {response.text}")
            return None

    except requests.exceptions.Timeout:
        logger.error("Video generation timed out, creating placeholder with effects")
        aspect_ratio = template.get('aspect_ratio', '16:9')
        effects = template.get('effects', [])
        _create_placeholder_video(output_path, aspect_ratio, effects)
        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        logger.error(f"Error calling video-generator: {e}, creating placeholder with effects", exc_info=True)
        aspect_ratio = template.get('aspect_ratio', '16:9')
        effects = template.get('effects', [])
        _create_placeholder_video(output_path, aspect_ratio, effects)
        return output_path if os.path.exists(output_path) else None


def _create_concatenated_video_from_media(media_list, aspect_ratio, temp_dir, effects=None):
    """
    Create a concatenated video from a list of media assets.
    Each asset has {url, duration, type}.

    For images: Create a video clip showing the image for the duration
    For videos: Loop or trim the video to match the duration

    Effects are applied to each individual clip before concatenation.

    Args:
        media_list: List of media items with {url, duration, type}
        aspect_ratio: Aspect ratio string like '16:9'
        temp_dir: Temporary directory for intermediate files
        effects: List of effects to apply to each clip (e.g., ken_burns)

    Returns: Path to the concatenated video file
    """
    from moviepy.editor import (
        ImageClip, VideoFileClip, concatenate_videoclips
    )
    import requests
    import os
    import uuid

    logger.info(f"🎬 Creating concatenated video from {len(media_list)} assets")
    if effects:
        logger.info(f"   Will apply {len(effects)} effects to each clip")

    # Parse aspect ratio
    width, height = map(int, aspect_ratio.split(':'))
    video_width = 1920
    video_height = int(video_width * height / width)

    clips = []

    for i, item in enumerate(media_list):
        url = item.get('url')
        duration = item.get('duration', 5.0)
        media_type = item.get('type', 'image')

        logger.info(f"  Processing item {i+1}: {media_type} ({duration:.2f}s)")

        try:
            # Download the asset
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save to temp file
            ext = 'jpg' if media_type == 'image' else 'mp4'
            temp_file = os.path.join(temp_dir, f"asset_{uuid.uuid4()}.{ext}")
            with open(temp_file, 'wb') as f:
                f.write(response.content)

            if media_type == 'image':
                # Create video clip from image
                clip = ImageClip(temp_file, duration=duration)
                clip = clip.resize((video_width, video_height))
            else:
                # Load video and loop/trim to match duration
                video_clip = VideoFileClip(temp_file)
                video_duration = video_clip.duration

                if video_duration < duration:
                    # Loop the video to fill the duration
                    loops_needed = int(duration / video_duration) + 1
                    looped = concatenate_videoclips([video_clip] * loops_needed)
                    clip = looped.subclip(0, duration)
                else:
                    # Trim the video to the duration
                    clip = video_clip.subclip(0, duration)

                # Resize to match aspect ratio
                clip = clip.resize((video_width, video_height))

            # Apply effects to this individual clip
            if effects:
                logger.info(f"    🎨 Applying effects to clip {i+1}")
                clip = _apply_effects_to_layer(clip, effects, duration, video_width, video_height)

            clips.append(clip)
            logger.info(f"    ✅ Created clip {i+1}")

        except Exception as e:
            logger.error(f"    ❌ Error processing item {i+1}: {e}")
            # Create a placeholder black clip
            from moviepy.editor import ColorClip
            clip = ColorClip(
                size=(video_width, video_height),
                color=(0, 0, 0),
                duration=duration
            )
            clips.append(clip)

    # Concatenate all clips
    logger.info(f"🔗 Concatenating {len(clips)} clips")
    final_video = concatenate_videoclips(clips, method="compose")

    # Save the concatenated video
    output_path = os.path.join(temp_dir, f"concatenated_{uuid.uuid4()}.mp4")
    final_video.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        fps=30,
        preset='medium'
    )

    # Clean up clips
    for clip in clips:
        clip.close()
    final_video.close()

    logger.info(f"✅ Concatenated video saved to {output_path}")
    return output_path


def _apply_effects_to_video(input_path: str, output_path: str, effects: list, aspect_ratio: str = '16:9', background_music: dict = None, logo: dict = None, layers: list = None, resolved_sample_data: dict = None, custom_audio_url: str = None) -> None:
    """
    Apply effects and layers to an existing video file

    Args:
        input_path: Path to the input video file
        output_path: Path where the output video should be saved
        effects: List of effects to apply
        aspect_ratio: Aspect ratio string like '16:9', '9:16', '1:1', '4:5'
        background_music: Background music configuration dict with keys:
            - enabled: bool
            - source: str (filename in /app/public/assets/)
            - volume: float (0.0 to 1.0)
            - fade_in: float (seconds)
            - fade_out: float (seconds)
        logo: Logo watermark configuration dict with keys:
            - enabled: bool
            - source: str (filename in /app/public/assets/ or path to logo image)
            - position: str (top-left, top-right, bottom-left, bottom-right)
            - scale: float (0.05 to 0.5)
            - opacity: float (0.0 to 1.0)
            - margin: dict with x and y keys (pixels from edges)
        layers: List of layer configurations to composite onto the video
        custom_audio_url: Optional custom audio URL to replace video audio
    """
    try:
        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip

        logger.info(f"Loading video from {input_path}")

        # Load the existing video
        video = VideoFileClip(input_path)
        duration = video.duration
        fps = video.fps
        w, h = video.size

        # Ken Burns effect will be applied after layer composition

        # Apply Logo Watermark effect if requested
        logo_watermark_effect = next((e for e in effects if e.get('type') == 'logo_watermark'), None)
        if logo_watermark_effect:
            params = logo_watermark_effect.get('params', {})
            position = params.get('position', 'bottom-right')
            opacity = params.get('opacity', 0.7)
            scale = params.get('scale', 0.15)
            margin = params.get('margin', 20)

            logger.info(f"Applying Logo Watermark effect: position={position}, opacity={opacity}, scale={scale}")

            # Create logo overlay using PIL
            try:
                from PIL import Image as PILImage, ImageDraw
                import numpy as np

                # Create a function to draw logo on each frame
                def add_logo_watermark(get_frame, t):
                    """Add logo watermark to frame at time t"""
                    frame = get_frame(t)

                    # Convert frame to PIL Image
                    pil_frame = PILImage.fromarray(frame)

                    # Create a simple logo (circle with "LOGO" text)
                    logo_size = int(min(w, h) * scale)
                    logo = PILImage.new('RGBA', (logo_size, logo_size), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(logo)

                    # Draw a circle background
                    alpha = int(255 * opacity)
                    draw.ellipse([0, 0, logo_size, logo_size], fill=(100, 100, 100, alpha))

                    # Add "LOGO" text in the center
                    try:
                        from PIL import ImageFont
                        font_size = logo_size // 4
                        try:
                            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                        except:
                            font = ImageFont.load_default()

                        text = "LOGO"
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        text_x = (logo_size - text_width) // 2
                        text_y = (logo_size - text_height) // 2
                        draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, alpha))
                    except:
                        pass

                    # Calculate position
                    if position == 'top-left':
                        x, y = margin, margin
                    elif position == 'top-right':
                        x, y = w - logo_size - margin, margin
                    elif position == 'bottom-left':
                        x, y = margin, h - logo_size - margin
                    else:  # bottom-right (default)
                        x, y = w - logo_size - margin, h - logo_size - margin

                    # Convert frame to RGBA for compositing
                    pil_frame = pil_frame.convert('RGBA')

                    # Paste logo onto frame
                    pil_frame.paste(logo, (x, y), logo)

                    # Convert back to RGB and return as numpy array
                    pil_frame = pil_frame.convert('RGB')
                    return np.array(pil_frame)

                # Apply the logo watermark
                video = video.fl(add_logo_watermark)

                logger.info("Logo watermark effect applied successfully")

            except Exception as logo_error:
                logger.warning(f"Failed to add logo watermark: {logo_error}, skipping logo_watermark effect", exc_info=True)

        # Note: Transition effect is now handled in the layer composition section
        # It adds a second dummy clip to demonstrate the transition between clips

        # Note: Bottom Banner effect is now applied AFTER layer composition and transitions
        # to ensure it appears on the final composited video

        # Logo watermark will be applied AFTER layer composition and effects (moved below)

        # PRE-LOAD AUDIO to get the target duration for video layers
        # This allows us to divide the audio duration equally among videos in auto mode
        target_audio_duration = None
        voice_audio_preload = None

        if custom_audio_url:
            try:
                import tempfile
                logger.info(f"🎵 Pre-loading custom audio to determine target duration: {custom_audio_url}")

                # Download audio file
                response = requests.get(custom_audio_url, timeout=30)
                if response.status_code == 200:
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                        temp_audio.write(response.content)
                        temp_audio_path = temp_audio.name

                    # Load audio file to get duration
                    audio = AudioFileClip(temp_audio_path)
                    voice_audio_preload = audio
                    target_audio_duration = audio.duration
                    logger.info(f"✅ Custom audio duration: {target_audio_duration:.2f}s")
                else:
                    logger.warning(f"Failed to download custom audio: HTTP {response.status_code}")
            except Exception as audio_error:
                logger.warning(f"Failed to pre-load custom audio: {audio_error}", exc_info=True)

        # Apply layers if provided
        if layers and len(layers) > 0:
            try:
                from moviepy.editor import ImageClip, VideoFileClip as LayerVideoClip, CompositeVideoClip
                from PIL import Image as PILImage, ImageDraw, ImageFont
                import numpy as np

                logger.info(f"Processing {len(layers)} layers")

                # Expand layers with sources array into multiple sequential layers
                expanded_layers = []
                max_end_time = 0  # Track the maximum end time of all layers

                for layer in layers:
                    # Skip dynamic_images and dynamic_videos layers if we have dynamic_media
                    # These layers are already processed into the base video
                    var_name = layer.get('variable_name')
                    if var_name in ['dynamic_images', 'dynamic_videos']:
                        # Check if we have dynamic_media in resolved_sample_data
                        has_dynamic_media = False
                        if resolved_sample_data:
                            dynamic_media = resolved_sample_data.get('dynamic_media', [])
                            has_dynamic_media = bool(dynamic_media and len(dynamic_media) > 0)

                        if has_dynamic_media:
                            logger.info(f"⏭️  Skipping layer '{var_name}' (already in base video from dynamic_media)")
                            continue

                    # Check for sources in multiple places:
                    # 1. 'sources' field (legacy)
                    # 2. 'source' field as a list (from variable substitution)
                    sources = layer.get('sources', [])
                    source_field = layer.get('source')

                    # If source is a list, use it as sources
                    if isinstance(source_field, list) and len(source_field) > 0:
                        sources = source_field

                    if sources and len(sources) > 0 and layer.get('type') in ['image', 'video', 'mixed']:
                        # Get timing metadata from resolved_sample_data (sent by ecommerce service)
                        # Timings contain: url, start_time, duration, section, type (image/video)
                        timing_metadata = []
                        if resolved_sample_data and layer.get('variable_name'):
                            var_name = layer.get('variable_name')
                            timing_var_name = f"{var_name}_timings"
                            timing_metadata = resolved_sample_data.get(timing_var_name, [])
                            if timing_metadata:
                                logger.info(f"📊 Found {len(timing_metadata)} timings for '{var_name}'")

                        # Create URL-to-timing mapping
                        timing_by_url = {}
                        if timing_metadata:
                            for timing in timing_metadata:
                                url = timing.get('url')
                                if url:
                                    timing_by_url[url] = timing

                        # Expand each source into a separate layer with timing info
                        # Use duration_per_item from layer if provided, otherwise calculate from audio
                        duration_per_item = layer.get('duration_per_item')
                        if duration_per_item:
                            default_duration = duration_per_item
                            logger.info(f"Using duration_per_item: {duration_per_item}s for each video")
                        else:
                            default_duration = target_audio_duration / len(sources) if target_audio_duration else 5.0
                            logger.info(f"Calculated default_duration: {default_duration}s per video")

                        for idx, source in enumerate(sources):
                            expanded_layer = layer.copy()
                            expanded_layer['source'] = source

                            # Get timing for this source
                            timing = timing_by_url.get(source)

                            if timing:
                                # Use ecommerce service timing (for sorting and duration)
                                expanded_layer['start_time'] = timing.get('start_time', idx * default_duration)
                                expanded_layer['duration'] = timing.get('duration', default_duration)

                                # For mixed layers, set the actual type (image or video) from timing metadata
                                if layer.get('type') == 'mixed':
                                    expanded_layer['type'] = timing.get('type', 'image')
                                    logger.info(f"  📦 Item {idx+1}: {timing.get('type')} at {expanded_layer['start_time']:.2f}s for {expanded_layer['duration']:.2f}s")
                            else:
                                # Fallback: sequential with equal duration
                                expanded_layer['start_time'] = idx * default_duration
                                expanded_layer['duration'] = default_duration

                                # For mixed layers without timing, infer type from URL extension
                                if layer.get('type') == 'mixed':
                                    if source.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
                                        expanded_layer['type'] = 'video'
                                    else:
                                        expanded_layer['type'] = 'image'

                            # Clean up
                            if 'sources' in expanded_layer:
                                del expanded_layer['sources']
                            if 'image_timings' in expanded_layer:
                                del expanded_layer['image_timings']

                            expanded_layers.append(expanded_layer)

                            # Track max end time
                            end_time = expanded_layer['start_time'] + expanded_layer['duration']
                            max_end_time = max(max_end_time, end_time)
                    else:
                        # No sources array, keep layer as-is
                        expanded_layers.append(layer)

                        # Track max end time for non-expanded layers too
                        layer_start = layer.get('start_time', 0)
                        layer_dur = layer.get('duration')
                        # If duration is None, use the video duration as fallback
                        if layer_dur is None:
                            layer_dur = duration
                        max_end_time = max(max_end_time, layer_start + layer_dur)

                # Check if there are ANY video layers - if so, don't include base sample video
                # The uploaded videos should be the only content, not overlays on a base video
                has_video_layers = any(layer.get('type') == 'video' for layer in expanded_layers)

                # Separate video layers from overlay layers (image, text, shape)
                # Video layers will be concatenated sequentially
                # Overlay layers will be composited on top based on z_index
                video_layers_list = [l for l in expanded_layers if l.get('type') == 'video']
                overlay_layers_list = [l for l in expanded_layers if l.get('type') != 'video']

                # Sort video layers by start_time for sequential playback
                if video_layers_list:
                    video_layers_list = sorted(video_layers_list, key=lambda l: l.get('start_time', 0))
                    logger.info(f"Found {len(video_layers_list)} video layer(s) for sequential processing")

                # Sort overlay layers by z_index for proper layering
                if overlay_layers_list:
                    overlay_layers_list = sorted(overlay_layers_list, key=lambda l: l.get('z_index', 0))
                    logger.info(f"Found {len(overlay_layers_list)} overlay layer(s) for composition")

                # Track temp files for cleanup
                temp_files_to_cleanup = []

                # Process video layers first (if any) - concatenate them sequentially
                if has_video_layers and len(video_layers_list) > 0:
                    # Use the same logic as create_concatenated_video_from_media
                    logger.info(f"🎬 Processing {len(video_layers_list)} sequential video layers")

                    from moviepy.editor import VideoFileClip as SimpleVideoClip, concatenate_videoclips
                    import requests

                    video_clips = []

                    for idx, layer in enumerate(video_layers_list):
                        source = layer.get('source', '')
                        layer_duration = layer.get('duration', 5.0)
                        layer_id = layer.get('id', f'video_{idx}')

                        logger.info(f"  Processing video {idx+1}/{len(video_layers_list)}: {layer_id} (duration={layer_duration:.2f}s)")

                        try:
                            video_path = None
                            temp_video_path = None

                            # Download or locate video file
                            if source.startswith('http://') or source.startswith('https://'):
                                import tempfile
                                logger.info(f"    Downloading from URL: {source}")
                                response = requests.get(source, timeout=60)
                                response.raise_for_status()

                                file_ext = os.path.splitext(source.split('?')[0])[1] or '.mp4'
                                temp_video_path = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext).name
                                with open(temp_video_path, 'wb') as f:
                                    f.write(response.content)
                                video_path = temp_video_path
                                temp_files_to_cleanup.append(temp_video_path)
                                logger.info(f"    ✅ Downloaded to {video_path}")
                            else:
                                # Local file
                                if not source.startswith('/'):
                                    video_path = os.path.join('/app/public/assets', source)
                                else:
                                    video_path = source

                            if video_path and os.path.exists(video_path):
                                # Load video
                                video_clip = SimpleVideoClip(video_path)
                                original_duration = video_clip.duration

                                logger.info(f"    Video duration: {original_duration:.2f}s, target: {layer_duration:.2f}s")

                                # Loop or trim to match target duration
                                if original_duration < layer_duration:
                                    # Loop the video to fill the duration
                                    loops_needed = int(layer_duration / original_duration) + 1
                                    logger.info(f"    🔁 Looping {loops_needed} times to reach {layer_duration:.2f}s")
                                    looped = concatenate_videoclips([video_clip] * loops_needed)
                                    clip = looped.subclip(0, layer_duration)
                                else:
                                    # Trim the video to the duration
                                    logger.info(f"    ✂️ Trimming from {original_duration:.2f}s to {layer_duration:.2f}s")
                                    clip = video_clip.subclip(0, layer_duration)

                                # Resize to match video dimensions
                                clip = clip.resize((w, h))

                                # Apply effects to this individual clip
                                if effects:
                                    logger.info(f"    🎨 Applying effects to video {idx+1}")
                                    clip = _apply_effects_to_layer(clip, effects, layer_duration, w, h)

                                video_clips.append(clip)
                                logger.info(f"    ✅ Video clip {idx+1} ready")
                            else:
                                logger.warning(f"    ❌ Video file not found: {video_path}")
                                # Create black placeholder
                                from moviepy.editor import ColorClip
                                clip = ColorClip(size=(w, h), color=(0, 0, 0), duration=layer_duration)
                                video_clips.append(clip)

                        except Exception as video_error:
                            logger.error(f"    ❌ Error processing video {idx+1}: {video_error}", exc_info=True)
                            # Create black placeholder
                            from moviepy.editor import ColorClip
                            clip = ColorClip(size=(w, h), color=(0, 0, 0), duration=layer_duration)
                            video_clips.append(clip)

                    # Concatenate all video clips
                    if len(video_clips) > 0:
                        logger.info(f"🔗 Concatenating {len(video_clips)} video clips")
                        video = concatenate_videoclips(video_clips, method="compose")
                        duration = video.duration  # Update duration to match concatenated video
                        logger.info(f"✅ Final video duration: {video.duration:.2f}s")

                        # Mark that we have a concatenated video base
                        has_concatenated_video = True

                # Now process overlay layers (image, text, shape) to composite on top of video
                logger.info(f"Processing {len(overlay_layers_list)} overlay layers")

                # Create list to hold overlay clips
                overlay_clips = []

                for layer in overlay_layers_list:
                    try:
                        layer_type = layer.get('type')
                        layer_id = layer.get('id', 'unknown')
                        logger.info(f"Processing overlay layer {layer_id} (type={layer_type})")

                        # Skip video layers - they're already processed above
                        if layer_type == 'video':
                            logger.info(f"  Skipping video layer (already processed)")
                            continue

                        # Get layer properties
                        position = layer.get('position', {'x': 0.5, 'y': 0.5})
                        size = layer.get('size', {'width': 1.0, 'height': 1.0})
                        start_time = layer.get('start_time', 0)
                        layer_duration = layer.get('duration', None) or duration
                        opacity = layer.get('opacity', 1.0)

                        # Calculate pixel positions and sizes
                        pos_x = int(position['x'] * w)
                        pos_y = int(position['y'] * h)
                        width = int(size['width'] * w)
                        height = int(size['height'] * h)

                        clip = None

                        # Process different layer types
                        if layer_type == 'image':
                            source = layer.get('source', '')
                            # Skip if source is a list (should have been expanded earlier)
                            if isinstance(source, list):
                                logger.warning(f"Skipping image layer {layer_id} with list source (should have been expanded)")
                                continue
                            if source:
                                img = None

                                # Check if source is a URL
                                if source.startswith('http://') or source.startswith('https://'):
                                    try:
                                        logger.info(f"Downloading image from URL: {source}")
                                        response = requests.get(source, timeout=30)
                                        if response.status_code == 200:
                                            from io import BytesIO
                                            img = PILImage.open(BytesIO(response.content))
                                            logger.info(f"✅ Downloaded image from {source}")
                                        else:
                                            logger.warning(f"Failed to download image: HTTP {response.status_code}")
                                    except Exception as download_error:
                                        logger.warning(f"Failed to download image from {source}: {download_error}")
                                else:
                                    # Resolve source path for local files
                                    if not source.startswith('/'):
                                        image_path = os.path.join('/app/public/assets', source)
                                    else:
                                        image_path = source

                                    if os.path.exists(image_path):
                                        img = PILImage.open(image_path)

                                if img:
                                    # Resize image
                                    img = img.resize((width, height), PILImage.LANCZOS)
                                    # Convert to numpy array
                                    img_array = np.array(img)
                                    # Create ImageClip
                                    image_clip = ImageClip(img_array)
                                    image_clip = image_clip.set_duration(layer_duration)

                                    # Apply global effects to image layer (e.g., Ken Burns)
                                    image_clip = _apply_effects_to_layer(image_clip, effects, layer_duration, width, height)

                                    # Set position (centered at pos_x, pos_y)
                                    image_clip = image_clip.set_position((pos_x - width//2, pos_y - height//2))
                                    # Set start and end time
                                    if start_time > 0:
                                        image_clip = image_clip.set_start(start_time)
                                        image_clip = image_clip.set_end(start_time + layer_duration)
                                    # Set opacity
                                    if opacity < 1.0:
                                        image_clip = image_clip.set_opacity(opacity)
                                    clip = image_clip
                                    logger.info(f"Added image layer from {source} with global effects applied")

                        elif layer_type == 'text':
                            content = layer.get('content', 'Sample Text')
                            font_config = layer.get('font', {})
                            font_family = font_config.get('family', 'Arial')
                            font_size = font_config.get('size', 48)
                            font_color = font_config.get('color', '#FFFFFF')
                            font_weight = font_config.get('weight', 'normal')

                            # Get fade configuration
                            fade_config = layer.get('fade', {})
                            fade_enabled = fade_config.get('enabled', False)
                            fade_in_duration = fade_config.get('fade_in_duration', 0.5)
                            fade_out_duration = fade_config.get('fade_out_duration', 0.5)
                            fade_type = fade_config.get('fade_type', 'both')

                            # Convert hex color to RGB
                            color = font_color.lstrip('#')
                            r = int(color[0:2], 16)
                            g = int(color[2:4], 16)
                            b = int(color[4:6], 16)

                            # Create text image using PIL
                            text_img = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
                            draw = ImageDraw.Draw(text_img)

                            # Try to load font
                            try:
                                if font_weight == 'bold':
                                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                                else:
                                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                            except:
                                font = ImageFont.load_default()

                            # Get text bounding box for centering
                            bbox = draw.textbbox((0, 0), content, font=font)
                            text_width = bbox[2] - bbox[0]
                            text_height = bbox[3] - bbox[1]

                            # Calculate center position within the text image
                            text_x = (width - text_width) // 2
                            text_y = (height - text_height) // 2

                            # Draw text
                            draw.text((text_x, text_y), content, font=font, fill=(r, g, b, 255))

                            # Convert to numpy array
                            text_array = np.array(text_img)

                            # Create ImageClip
                            text_clip = ImageClip(text_array)
                            text_clip = text_clip.set_duration(layer_duration)

                            # Apply base opacity first if needed
                            if opacity < 1.0:
                                text_clip = text_clip.set_opacity(opacity)

                            # Apply fade animation if enabled
                            if fade_enabled:
                                logger.info(f"Applying fade animation to text layer: {content} (type={fade_type}, in={fade_in_duration}s, out={fade_out_duration}s, duration={layer_duration}s)")

                                # Apply fade in
                                if fade_type in ['in', 'both'] and fade_in_duration > 0:
                                    text_clip = text_clip.fadein(fade_in_duration)
                                    logger.info(f"Applied fade in: {fade_in_duration}s")

                                # Apply fade out
                                if fade_type in ['out', 'both'] and fade_out_duration > 0:
                                    text_clip = text_clip.fadeout(fade_out_duration)
                                    logger.info(f"Applied fade out: {fade_out_duration}s")

                            # Set position (centered at pos_x, pos_y)
                            text_clip = text_clip.set_position((pos_x - width//2, pos_y - height//2))
                            # Set start and end time
                            if start_time > 0:
                                text_clip = text_clip.set_start(start_time)
                                text_clip = text_clip.set_end(start_time + layer_duration)

                            clip = text_clip
                            logger.info(f"Added text layer: {content} (fade={'enabled' if fade_enabled else 'disabled'})")

                        elif layer_type == 'shape':
                            shape_type = layer.get('shape_type', 'rectangle')
                            fill_color = layer.get('fill_color', '#3B82F6')
                            stroke_color = layer.get('stroke_color', '#1E40AF')
                            stroke_width = layer.get('stroke_width', 2)

                            # Convert hex colors to RGB
                            fill = fill_color.lstrip('#')
                            fill_r = int(fill[0:2], 16)
                            fill_g = int(fill[2:4], 16)
                            fill_b = int(fill[4:6], 16)

                            stroke = stroke_color.lstrip('#')
                            stroke_r = int(stroke[0:2], 16)
                            stroke_g = int(stroke[2:4], 16)
                            stroke_b = int(stroke[4:6], 16)

                            # Create shape image using PIL
                            shape_img = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
                            draw = ImageDraw.Draw(shape_img)

                            if shape_type == 'rectangle':
                                draw.rectangle([0, 0, width, height], fill=(fill_r, fill_g, fill_b, 255), outline=(stroke_r, stroke_g, stroke_b, 255), width=stroke_width)
                            elif shape_type == 'circle':
                                draw.ellipse([0, 0, width, height], fill=(fill_r, fill_g, fill_b, 255), outline=(stroke_r, stroke_g, stroke_b, 255), width=stroke_width)
                            elif shape_type == 'line':
                                draw.line([(0, height//2), (width, height//2)], fill=(stroke_r, stroke_g, stroke_b, 255), width=stroke_width)

                            # Convert to numpy array
                            shape_array = np.array(shape_img)

                            # Create ImageClip
                            shape_clip = ImageClip(shape_array)
                            shape_clip = shape_clip.set_duration(layer_duration)
                            # Set position (centered at pos_x, pos_y)
                            shape_clip = shape_clip.set_position((pos_x - width//2, pos_y - height//2))
                            # Set start and end time
                            if start_time > 0:
                                shape_clip = shape_clip.set_start(start_time)
                                shape_clip = shape_clip.set_end(start_time + layer_duration)
                            # Set opacity
                            if opacity < 1.0:
                                shape_clip = shape_clip.set_opacity(opacity)
                            clip = shape_clip
                            logger.info(f"Added shape layer: {shape_type}")

                        # Add clip to overlay_clips if it was created
                        if clip:
                            overlay_clips.append(clip)

                    except Exception as layer_error:
                        logger.warning(f"Failed to process layer {layer.get('id', 'unknown')}: {layer_error}", exc_info=True)

                # Composite overlay layers on top of the video (if any)
                if len(overlay_clips) > 0:
                    # We have overlay layers (text, shapes, images) to composite on top of the video
                    logger.info(f"Compositing {len(overlay_clips)} overlay layer(s) on top of video")

                    # Add the base video as the first layer
                    all_clips = [video] + overlay_clips

                    # Composite all layers
                    video = CompositeVideoClip(all_clips, size=(w, h))
                    video = video.set_duration(duration)
                    logger.info(f"Overlays composited successfully, video size: {video.size}, duration: {duration}s")
                elif not has_video_layers and len(overlay_clips) == 0:
                    # No video layers and no overlay layers - just use the base sample video
                    logger.info("Using base sample video (no layers)")
                # else: video is already set to the concatenated video, no overlays needed

                # Check if transition effect is enabled
                # DISABLED: Don't add dummy clip when user has uploaded videos
                # The transition will be applied between the user's videos when they loop
                transition_effect = next((e for e in effects if e.get('type') == 'transition'), None)
                if False and transition_effect and has_video_layers:  # Disabled
                    params = transition_effect.get('params', {})
                    transition_type = params.get('transition_type', 'crossfade')
                    transition_duration = params.get('duration', 1.0)

                    logger.info(f"Transition effect enabled: type={transition_type}, duration={transition_duration}s")
                    logger.info("Adding second dummy clip to demonstrate transition effect")

                    try:
                        # Create a second dummy clip (use the base sample video)
                        # The first clip is the user's background video
                        # The second clip is the dummy sample video to show the transition

                        # Split the duration: first half for user's video, second half for dummy video
                        clip1_duration = duration / 2
                        clip2_duration = duration / 2

                        # First clip: user's background video (already composited with layers)
                        clip1 = video.subclip(0, min(clip1_duration, video.duration))

                        # Second clip: load the sample video again as a dummy clip
                        sample_video_path = f'/app/public/assets/sample_video_{aspect_ratio.replace(":", "_")}.mp4'
                        if os.path.exists(sample_video_path):
                            from moviepy.editor import VideoFileClip as MoviePyVideoFileClip
                            clip2 = MoviePyVideoFileClip(sample_video_path)
                            clip2 = clip2.subclip(0, min(clip2_duration, clip2.duration))
                            clip2 = clip2.set_duration(clip2_duration)

                            # Apply the transition between clip1 and clip2
                            from moviepy.editor import concatenate_videoclips, CompositeVideoClip as MoviePyCompositeVideoClip

                            if transition_type in ['crossfade', 'fade_black']:
                                # Crossfade transition
                                # Make clip2 start earlier by transition_duration to create overlap
                                clip1 = clip1.set_end(clip1_duration)
                                clip2 = clip2.set_start(clip1_duration - transition_duration)

                                # Apply fade out to clip1 and fade in to clip2
                                clip1 = clip1.fadeout(transition_duration)
                                clip2 = clip2.fadein(transition_duration)

                                # Composite the two clips
                                video = MoviePyCompositeVideoClip([clip1, clip2], size=(w, h))
                                video = video.set_duration(clip1_duration + clip2_duration - transition_duration)
                                logger.info(f"Applied {transition_type} transition between clips")

                            else:
                                # For other transitions, just concatenate with a simple fade
                                clip1 = clip1.fadeout(transition_duration)
                                clip2 = clip2.fadein(transition_duration)
                                video = concatenate_videoclips([clip1, clip2], method="compose")
                                logger.info(f"Applied {transition_type} transition (using fade) between clips")
                        else:
                            logger.warning(f"Sample video not found at {sample_video_path}, skipping transition demo")

                    except Exception as transition_error:
                        logger.warning(f"Failed to apply transition effect: {transition_error}, using original video", exc_info=True)

            except Exception as layers_error:
                logger.warning(f"Failed to apply layers: {layers_error}", exc_info=True)

        # Apply Ken Burns effect if requested (AFTER layer composition and transitions)
        # ENABLED when we have dynamic_media (base video from concatenated clips)
        # DISABLED when we have individual layers (Ken Burns applied to each layer)
        ken_burns_effect = next((e for e in effects if e.get('type') == 'ken_burns'), None)

        # Check if we have dynamic_media (all layers were skipped)
        has_dynamic_media_base = False
        if resolved_sample_data:
            dynamic_media = resolved_sample_data.get('dynamic_media', [])
            has_dynamic_media_base = bool(dynamic_media and len(dynamic_media) > 0)

        # Apply Ken Burns to final video only if we have dynamic_media base
        if ken_burns_effect and has_dynamic_media_base:
            params = ken_burns_effect.get('params', {})
            zoom_start = params.get('zoom_start', 1.0)
            zoom_end = params.get('zoom_end', 1.2)

            logger.info(f"Applying Ken Burns effect to final video: zoom {zoom_start} -> {zoom_end}")

            # Apply zoom effect using resize
            def zoom_effect(get_frame, t):
                """Apply zoom effect to frame at time t"""
                # Calculate zoom factor at time t (linear interpolation)
                progress = t / duration
                zoom = zoom_start + (zoom_end - zoom_start) * progress

                # Get the original frame
                frame = get_frame(t)
                h, w = frame.shape[:2]

                # Calculate new dimensions
                new_w = int(w * zoom)
                new_h = int(h * zoom)

                # Resize frame
                from PIL import Image as PILImage
                import numpy as np
                pil_frame = PILImage.fromarray(frame)
                pil_frame = pil_frame.resize((new_w, new_h), PILImage.LANCZOS)

                # Crop to original size (center crop)
                left = (new_w - w) // 2
                top = (new_h - h) // 2
                pil_frame = pil_frame.crop((left, top, left + w, top + h))

                return np.array(pil_frame)

            # Apply the zoom effect
            video = video.fl(zoom_effect)
            logger.info("Ken Burns effect applied successfully to final video")

        # Apply Bottom Banner effect if requested (AFTER layer composition and transitions)
        bottom_banner_effect = next((e for e in effects if e.get('type') == 'bottom_banner'), None)
        if bottom_banner_effect:
            params = bottom_banner_effect.get('params', {})
            banner_height = params.get('height', 120)
            background_color = params.get('background_color', '#1a1a1a')
            banner_opacity = params.get('opacity', 0.9)

            # Get banner text from params first, then from resolved sample data, then use defaults
            # This allows users to either use variables ({{banner_heading}}) or hardcoded text
            banner_heading_raw = params.get('heading', '{{banner_heading}}')
            banner_ticker_raw = params.get('ticker', '{{banner_ticker}}')

            # Use resolved_sample_data if provided, otherwise use empty dict
            sample_data = resolved_sample_data if resolved_sample_data is not None else {}

            # Resolve variables in the banner text using the imported substitute_variables function
            banner_heading = substitute_variables(banner_heading_raw, sample_data)
            banner_ticker = substitute_variables(banner_ticker_raw, sample_data)

            # If still contains placeholders (variable not defined), use defaults
            if '{{' in banner_heading:
                banner_heading = 'BREAKING NEWS'
            if '{{' in banner_ticker:
                banner_ticker = 'Sample News Ticker • Latest Updates • Breaking Stories • '

            logger.info(f"Applying Bottom Banner effect: height={banner_height}px, bg={background_color}, opacity={banner_opacity}")
            logger.info(f"Banner text: heading='{banner_heading}', ticker='{banner_ticker}'")

            try:
                from PIL import Image as PILImage, ImageDraw, ImageFont
                import numpy as np

                # Parse background color (hex to RGB)
                bg_color = background_color.lstrip('#')
                bg_r = int(bg_color[0:2], 16)
                bg_g = int(bg_color[2:4], 16)
                bg_b = int(bg_color[4:6], 16)

                # Create a function to draw bottom banner on each frame
                def add_bottom_banner(get_frame, t):
                    """Add bottom banner with scrolling ticker to frame at time t"""
                    frame = get_frame(t)

                    # Ensure frame is in uint8 format (0-255 range)
                    if frame.dtype != np.uint8:
                        # Convert from float (0.0-1.0) to uint8 (0-255)
                        frame = (frame * 255).astype(np.uint8)

                    # Convert frame to PIL Image
                    pil_frame = PILImage.fromarray(frame)

                    # Create banner overlay
                    banner = PILImage.new('RGBA', (w, banner_height), (0, 0, 0, 0))
                    draw = ImageDraw.Draw(banner)

                    # Calculate alpha value
                    alpha = int(255 * banner_opacity)

                    # Draw background rectangle
                    draw.rectangle([0, 0, w, banner_height], fill=(bg_r, bg_g, bg_b, alpha))

                    # Two-tier layout
                    tier1_height = int(banner_height * 0.4)  # 40% for heading
                    tier2_height = banner_height - tier1_height  # 60% for ticker

                    # Try to load fonts
                    try:
                        heading_font_size = max(16, tier1_height - 10)
                        ticker_font_size = max(14, tier2_height - 20)

                        heading_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", heading_font_size)
                        ticker_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", ticker_font_size)
                    except:
                        heading_font = ImageFont.load_default()
                        ticker_font = ImageFont.load_default()

                    # Draw heading in tier 1 (top part) - use variable
                    heading_text = banner_heading
                    heading_bbox = draw.textbbox((0, 0), heading_text, font=heading_font)
                    heading_width = heading_bbox[2] - heading_bbox[0]
                    heading_x = (w - heading_width) // 2
                    heading_y = (tier1_height - (heading_bbox[3] - heading_bbox[1])) // 2
                    draw.text((heading_x, heading_y), heading_text, font=heading_font, fill=(255, 255, 255, alpha))

                    # Draw separator line
                    draw.line([(0, tier1_height), (w, tier1_height)], fill=(255, 255, 255, alpha), width=2)

                    # Draw scrolling ticker in tier 2 (bottom part) - use variable
                    ticker_text = banner_ticker
                    ticker_bbox = draw.textbbox((0, 0), ticker_text, font=ticker_font)
                    ticker_text_width = ticker_bbox[2] - ticker_bbox[0]

                    # Calculate scroll position based on time
                    scroll_speed = 100  # pixels per second
                    scroll_offset = int(t * scroll_speed) % ticker_text_width

                    # Draw ticker text (scrolling from right to left)
                    ticker_y = tier1_height + (tier2_height - (ticker_bbox[3] - ticker_bbox[1])) // 2

                    # Draw multiple copies to create seamless scrolling
                    for i in range(-1, (w // ticker_text_width) + 2):
                        ticker_x = i * ticker_text_width - scroll_offset
                        draw.text((ticker_x, ticker_y), ticker_text, font=ticker_font, fill=(255, 255, 255, alpha))

                    # Position banner at bottom of frame
                    banner_y = h - banner_height

                    # Convert frame to RGBA for compositing
                    pil_frame = pil_frame.convert('RGBA')

                    # Paste banner onto frame
                    pil_frame.paste(banner, (0, banner_y), banner)

                    # Convert back to RGB and return as numpy array
                    pil_frame = pil_frame.convert('RGB')
                    return np.array(pil_frame)

                # Apply the bottom banner
                video = video.fl(add_bottom_banner)

                logger.info("Bottom banner effect applied successfully")

            except Exception as banner_error:
                logger.warning(f"Failed to add bottom banner: {banner_error}, skipping bottom_banner effect", exc_info=True)

        # Handle custom audio URL if provided (takes precedence over background music)
        # Reuse the preloaded audio if available
        voice_audio = voice_audio_preload
        background_music_audio = None

        # If we didn't preload (shouldn't happen), load it now
        if custom_audio_url and not voice_audio:
            try:
                import tempfile

                logger.info(f"🎵 Using custom audio from: {custom_audio_url}")

                # Download audio file
                response = requests.get(custom_audio_url, timeout=30)
                if response.status_code == 200:
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                        temp_audio.write(response.content)
                        temp_audio_path = temp_audio.name

                    # Load audio file
                    audio = AudioFileClip(temp_audio_path)
                    voice_audio = audio
                    logger.info("✅ Custom audio loaded successfully")
                else:
                    logger.warning(f"Failed to download custom audio: HTTP {response.status_code}")
            except Exception as audio_error:
                logger.warning(f"Failed to apply custom audio: {audio_error}", exc_info=True)
        elif voice_audio:
            logger.info(f"✅ Using pre-loaded custom audio (duration: {voice_audio.duration:.2f}s)")

        # Load background music if enabled
        if background_music and background_music.get('enabled', False):
            try:
                music_source = background_music.get('source', '')
                volume = background_music.get('volume', 0.5)
                fade_in = background_music.get('fade_in', 0.0)
                fade_out = background_music.get('fade_out', 0.0)

                # Construct full path to music file
                if music_source:
                    # If it's just a filename, look in assets folder
                    if not music_source.startswith('/'):
                        music_path = os.path.join('/app/public/assets', music_source)
                    else:
                        music_path = music_source

                    if os.path.exists(music_path):
                        logger.info(f"Loading background music: {music_source} (volume={volume}, fade_in={fade_in}s, fade_out={fade_out}s)")

                        # Load audio file
                        audio = AudioFileClip(music_path)

                        # Loop audio if it's shorter than video
                        if audio.duration < duration:
                            # Calculate how many times to loop
                            loops_needed = int(duration / audio.duration) + 1
                            from moviepy.editor import concatenate_audioclips
                            audio = concatenate_audioclips([audio] * loops_needed)

                        # Trim audio to match video duration
                        audio = audio.subclip(0, duration)

                        # Apply volume
                        if volume != 1.0:
                            audio = audio.volumex(volume)

                        # Apply fade in
                        if fade_in > 0:
                            audio = audio.audio_fadein(fade_in)

                        # Apply fade out
                        if fade_out > 0:
                            audio = audio.audio_fadeout(fade_out)

                        background_music_audio = audio
                        logger.info("✅ Background music loaded successfully")
                    else:
                        logger.warning(f"Background music file not found: {music_path}")
            except Exception as music_error:
                logger.warning(f"Failed to load background music: {music_error}", exc_info=True)

        # Mix audio tracks: voice + background music
        final_audio = None
        if voice_audio and background_music_audio:
            try:
                from moviepy.editor import CompositeAudioClip
                logger.info("🎵 Mixing voice audio with background music")
                final_audio = CompositeAudioClip([voice_audio, background_music_audio])
                logger.info("✅ Audio tracks mixed successfully")
            except Exception as mix_error:
                logger.warning(f"Failed to mix audio tracks: {mix_error}", exc_info=True)
                # Fallback to voice only
                final_audio = voice_audio
        elif voice_audio:
            logger.info("Using voice audio only (no background music)")
            final_audio = voice_audio
        elif background_music_audio:
            logger.info("Using background music only (no voice)")
            final_audio = background_music_audio

        # Set audio on video and loop video if audio is longer
        if final_audio:
            audio_duration = final_audio.duration
            video_duration = video.duration

            # If audio is longer than video, loop the video to match audio duration
            if audio_duration > video_duration:
                logger.info(f"🔁 Audio duration ({audio_duration:.2f}s) > Video duration ({video_duration:.2f}s), looping video")
                from moviepy.editor import concatenate_videoclips

                # Calculate how many times to loop the video
                loops_needed = int(audio_duration / video_duration) + 1
                logger.info(f"Looping video {loops_needed} times to match audio duration")

                # Loop the video
                video = concatenate_videoclips([video] * loops_needed)

                # Trim to exact audio duration
                video = video.subclip(0, audio_duration)
                logger.info(f"✅ Video looped and trimmed to {audio_duration:.2f}s")

            # Set the audio on the video
            video = video.set_audio(final_audio)

        # Apply Logo Watermark from separate logo configuration (AFTER layer composition and effects)
        if logo and logo.get('enabled', False):
            try:
                from PIL import Image as PILImage, ImageDraw
                import numpy as np

                logo_source = logo.get('source', '')
                position = logo.get('position', 'top-right')
                opacity = logo.get('opacity', 0.8)
                scale = logo.get('scale', 0.15)
                margin_config = logo.get('margin', {})

                # Handle margin as dict or int
                if isinstance(margin_config, dict):
                    margin_x = margin_config.get('x', 20)
                    margin_y = margin_config.get('y', 20)
                else:
                    margin_x = margin_y = margin_config

                logger.info(f"Applying Logo Watermark: source={logo_source}, position={position}, opacity={opacity}, scale={scale}")

                # Determine logo path
                logo_path = None
                if logo_source:
                    # If it's just a filename, look in assets folder
                    if not logo_source.startswith('/'):
                        logo_path = os.path.join('/app/public/assets', logo_source)
                    else:
                        logo_path = logo_source

                    if logo_path and os.path.exists(logo_path):
                        # Load and prepare logo image ONCE (not on every frame)
                        logo_img_original = PILImage.open(logo_path)

                        # Convert logo to RGBA if not already
                        if logo_img_original.mode != 'RGBA':
                            logo_img_original = logo_img_original.convert('RGBA')

                        # Get video dimensions
                        video_w, video_h = video.size
                        logger.info(f"Video dimensions from video.size: {video_w}x{video_h}, Logo scale: {scale}")
                        logger.info(f"Logo original dimensions: {logo_img_original.width}x{logo_img_original.height}")

                        # Store logo preparation parameters (we'll calculate size and position per frame)
                        logo_img_prepared = logo_img_original

                        # Apply opacity to logo template
                        if opacity < 1.0:
                            # Split into channels
                            r, g, b, a = logo_img_prepared.split()
                            # Multiply alpha channel by opacity
                            a = a.point(lambda p: int(p * opacity))
                            # Merge back
                            logo_img_prepared = PILImage.merge('RGBA', (r, g, b, a))

                        # Track if we've logged frame info (only log once)
                        logged_frame_info = {'done': False}

                        # Create a function to draw logo on each frame
                        def add_logo_overlay(get_frame, t):
                            """Add logo overlay to frame at time t"""
                            try:
                                frame = get_frame(t)

                                # Validate frame shape early
                                if len(frame.shape) < 2:
                                    logger.warning(f"Frame has invalid shape: {frame.shape}, skipping logo overlay")
                                    return frame

                                # Get frame dimensions (use actual frame dimensions, not video.size)
                                frame_h, frame_w = frame.shape[:2]

                                # Skip invalid frames (too small)
                                if frame_h < 2 or frame_w < 2:
                                    logger.warning(f"Frame has invalid dimensions: {frame_w}x{frame_h}, skipping logo overlay")
                                    return frame

                                # Ensure frame is uint8 before any PIL operations
                                if frame.dtype != np.uint8:
                                    # Handle different dtypes
                                    if frame.dtype in [np.int8, np.int16, np.int32, np.int64]:
                                        # For signed integers, clip to valid range
                                        frame = np.clip(frame, 0, 255).astype(np.uint8)
                                    elif frame.dtype in [np.float32, np.float64]:
                                        # For floats, assume 0-1 range and scale to 0-255
                                        frame = (np.clip(frame, 0, 1) * 255).astype(np.uint8)
                                    else:
                                        # For other types, try direct conversion
                                        frame = frame.astype(np.uint8)

                                # Calculate logo size based on ACTUAL frame width
                                logo_width = int(frame_w * scale)
                                logo_aspect_ratio = logo_img_prepared.height / logo_img_prepared.width
                                logo_height = int(logo_width * logo_aspect_ratio)

                                # Ensure logo size is valid
                                if logo_width < 1 or logo_height < 1:
                                    logger.warning(f"Calculated logo size is invalid: {logo_width}x{logo_height}, skipping logo overlay")
                                    return frame

                                # Resize logo based on actual frame dimensions
                                logo_img_resized = logo_img_prepared.resize((logo_width, logo_height), PILImage.LANCZOS)

                                # Calculate position based on ACTUAL frame dimensions
                                if position == 'top-left':
                                    x, y = margin_x, margin_y
                                elif position == 'top-right':
                                    x, y = frame_w - logo_width - margin_x, margin_y
                                elif position == 'bottom-left':
                                    x, y = margin_x, frame_h - logo_height - margin_y
                                else:  # bottom-right (default)
                                    x, y = frame_w - logo_width - margin_x, frame_h - logo_height - margin_y

                                # Log frame info only once
                                if not logged_frame_info['done']:
                                    logger.info(f"Frame dimensions: {frame_w}x{frame_h}, Logo size: {logo_width}x{logo_height}, Position: ({x}, {y}) for position={position}")
                                    logger.info(f"Logo will be pasted at pixel coordinates: x={x}, y={y}, width={logo_width}, height={logo_height}")
                                    logger.info(f"Logo bounds: top-left=({x},{y}), bottom-right=({x+logo_width},{y+logo_height})")
                                    logged_frame_info['done'] = True

                                # Convert frame to PIL Image (RGB)
                                try:
                                    pil_frame = PILImage.fromarray(frame)
                                except (TypeError, ValueError) as e:
                                    logger.warning(f"Failed to convert frame to PIL Image: {e}, frame shape: {frame.shape}, dtype: {frame.dtype}, skipping logo overlay")
                                    return frame

                                # Ensure logo has alpha channel
                                if logo_img_resized.mode != 'RGBA':
                                    logo_img_resized = logo_img_resized.convert('RGBA')

                                # Paste logo onto frame using alpha channel as mask
                                # This ensures transparency is handled correctly
                                pil_frame.paste(logo_img_resized, (x, y), logo_img_resized)

                                # Return as numpy array
                                return np.array(pil_frame, dtype=np.uint8)

                            except Exception as e:
                                # Silently skip logo for frames with data type issues
                                # This is expected for some frame types and doesn't need logging
                                # Return original frame on any error
                                try:
                                    return get_frame(t)
                                except:
                                    # If we can't even get the frame, return a black frame
                                    return np.zeros((video.h, video.w, 3), dtype=np.uint8)

                        # Apply the logo overlay
                        video = video.fl(add_logo_overlay)

                        logger.info("Logo watermark applied successfully from logo configuration")
                    else:
                        logger.warning(f"Logo file not found: {logo_path}")
            except Exception as logo_error:
                logger.warning(f"Failed to apply logo watermark: {logo_error}", exc_info=True)

        # Write video file with optimized settings
        video.write_videofile(
            output_path,
            fps=fps,
            codec='libx264',
            audio=True if final_audio else False,
            logger=None,
            preset='fast',
            bitrate='500k'
        )

        # Close the video clip and audio
        video.close()
        if final_audio:
            final_audio.close()

        # Cleanup temp files created during video processing
        # Check if video has temp files attached (from concatenation or processing)
        if hasattr(video, 'temp_concat_file') and video.temp_concat_file:
            try:
                if os.path.exists(video.temp_concat_file):
                    os.unlink(video.temp_concat_file)
                    logger.debug(f"Cleaned up concatenated temp file: {video.temp_concat_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp concat file: {e}")

        # Cleanup individual layer temp files
        if temp_files_to_cleanup:
            for temp_file in temp_files_to_cleanup:
                try:
                    if temp_file and os.path.exists(temp_file):
                        os.unlink(temp_file)
                        logger.debug(f"Cleaned up layer temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")

        logger.info(f"Effects applied successfully to {output_path}")

    except Exception as e:
        logger.error(f"Error applying effects to video: {e}", exc_info=True)
        # If effects application fails, just copy the original video
        import shutil
        shutil.copy2(input_path, output_path)
        logger.info(f"Copied original video to {output_path} (effects failed)")


def _create_placeholder_video(output_path: str, aspect_ratio: str = '16:9', effects: list = None) -> None:
    """
    Create a simple static sample video for template preview
    Uses a basic dummy image (simple illustration) so effects are clearly visible

    Args:
        output_path: Path where video should be saved
        aspect_ratio: Aspect ratio string like '16:9', '9:16', '1:1', '4:5'
        effects: List of effects to apply (e.g., ken_burns, fade_text, etc.)
    """
    try:
        from moviepy.editor import ImageClip, CompositeVideoClip
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np

        # Calculate dimensions based on aspect ratio
        aspect_ratios = {
            '16:9': (1280, 720),   # Landscape - YouTube, TV
            '9:16': (720, 1280),   # Portrait - TikTok, Instagram Reels
            '1:1': (720, 720),     # Square - Instagram Post
            '4:5': (720, 900),     # Portrait - Instagram Feed
        }

        size = aspect_ratios.get(aspect_ratio, (1280, 720))  # Default to 16:9
        effects = effects or []

        # Create a simple static image with a dummy person illustration
        img = Image.new('RGB', size, color=(240, 240, 245))  # Light gray background
        draw = ImageDraw.Draw(img)

        # Calculate center and scale based on image size
        center_x = size[0] // 2
        center_y = size[1] // 2
        scale = min(size[0], size[1]) / 720  # Scale factor based on smallest dimension

        # Draw a simple person illustration (stick figure style but more refined)

        # Head (circle)
        head_radius = int(80 * scale)
        head_y = int(center_y - 150 * scale)
        draw.ellipse(
            [center_x - head_radius, head_y - head_radius,
             center_x + head_radius, head_y + head_radius],
            fill=(255, 220, 200),  # Skin tone
            outline=(200, 180, 160),
            width=3
        )

        # Eyes
        eye_y = head_y - int(10 * scale)
        eye_offset = int(25 * scale)
        eye_radius = int(8 * scale)
        # Left eye
        draw.ellipse(
            [center_x - eye_offset - eye_radius, eye_y - eye_radius,
             center_x - eye_offset + eye_radius, eye_y + eye_radius],
            fill=(60, 60, 60)
        )
        # Right eye
        draw.ellipse(
            [center_x + eye_offset - eye_radius, eye_y - eye_radius,
             center_x + eye_offset + eye_radius, eye_y + eye_radius],
            fill=(60, 60, 60)
        )

        # Smile
        smile_y = head_y + int(20 * scale)
        draw.arc(
            [center_x - int(30 * scale), smile_y - int(15 * scale),
             center_x + int(30 * scale), smile_y + int(15 * scale)],
            start=0, end=180,
            fill=(60, 60, 60),
            width=3
        )

        # Body (rectangle with rounded edges - shirt)
        body_top = head_y + head_radius + int(10 * scale)
        body_width = int(140 * scale)
        body_height = int(180 * scale)
        draw.rounded_rectangle(
            [center_x - body_width // 2, body_top,
             center_x + body_width // 2, body_top + body_height],
            radius=int(20 * scale),
            fill=(100, 150, 200),  # Blue shirt
            outline=(80, 120, 160),
            width=3
        )

        # Arms
        arm_width = int(30 * scale)
        arm_length = int(120 * scale)
        # Left arm
        draw.rounded_rectangle(
            [center_x - body_width // 2 - arm_width, body_top + int(20 * scale),
             center_x - body_width // 2, body_top + int(20 * scale) + arm_length],
            radius=int(15 * scale),
            fill=(100, 150, 200),
            outline=(80, 120, 160),
            width=2
        )
        # Right arm
        draw.rounded_rectangle(
            [center_x + body_width // 2, body_top + int(20 * scale),
             center_x + body_width // 2 + arm_width, body_top + int(20 * scale) + arm_length],
            radius=int(15 * scale),
            fill=(100, 150, 200),
            outline=(80, 120, 160),
            width=2
        )

        # Add text label
        try:
            # Try to use a default font, fallback to basic if not available
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(40 * scale))
        except:
            font = ImageFont.load_default()

        text = "Sample Video"
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = center_x - text_width // 2
        text_y = int(size[1] - 100 * scale)

        # Draw text with shadow
        draw.text((text_x + 2, text_y + 2), text, fill=(0, 0, 0, 128), font=font)
        draw.text((text_x, text_y), text, fill=(60, 60, 60), font=font)

        # Convert PIL image to numpy array
        frame = np.array(img)

        # Create a static video clip (5 seconds)
        duration = 5
        fps = 24  # Standard frame rate
        video = ImageClip(frame, duration=duration)

        # Apply Ken Burns effect if requested
        ken_burns_effect = next((e for e in effects if e.get('type') == 'ken_burns'), None)
        if ken_burns_effect:
            params = ken_burns_effect.get('params', {})
            zoom_start = params.get('zoom_start', 1.0)
            zoom_end = params.get('zoom_end', 1.2)

            logger.info(f"Applying Ken Burns effect: zoom {zoom_start} -> {zoom_end}")

            # Apply zoom effect using resize
            def zoom_effect(get_frame, t):
                """Apply zoom effect to frame at time t"""
                # Calculate zoom factor at time t (linear interpolation)
                progress = t / duration
                zoom = zoom_start + (zoom_end - zoom_start) * progress

                # Get the original frame
                frame = get_frame(t)
                h, w = frame.shape[:2]

                # Calculate new dimensions
                new_w = int(w * zoom)
                new_h = int(h * zoom)

                # Resize frame
                from PIL import Image as PILImage
                pil_frame = PILImage.fromarray(frame)
                pil_frame = pil_frame.resize((new_w, new_h), PILImage.LANCZOS)

                # Crop to original size (center crop)
                left = (new_w - w) // 2
                top = (new_h - h) // 2
                pil_frame = pil_frame.crop((left, top, left + w, top + h))

                return np.array(pil_frame)

            # Apply the zoom effect
            video = video.fl(zoom_effect)

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
                "variables": {...},
                "audio_url": "http://..."  // Optional: custom audio URL
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

        logger.info(f"📥 Incoming sample_data keys: {list(sample_data.keys()) if sample_data else 'None'}")

        # Extract custom audio URL if provided and convert to internal URL
        # Check both top-level audio_url and template.audio_url
        custom_audio_url = data.get('audio_url') or template.get('audio_url')
        if custom_audio_url:
            logger.info(f"🎵 Found custom audio URL: {custom_audio_url}")
            custom_audio_url = url_converter.convert_url(custom_audio_url)
            template['audio_url'] = custom_audio_url
            logger.info(f"🎵 Converted audio URL: {custom_audio_url}")
        else:
            logger.info("ℹ️ No custom audio URL provided")

        # Log the request details
        effects = template.get('effects', [])
        background_music = template.get('background_music', {})
        logger.info(f"Preview request: is_initial={is_initial}, effects={len(effects)}, background_music_enabled={background_music.get('enabled', False)}, custom_audio={bool(custom_audio_url)}")

        # Generate sample data for template variables
        resolved_sample_data = _generate_sample_data(template, sample_data)

        # Add any additional metadata from sample_data that's not in template variables
        # (e.g., {var_name}_timings metadata)
        if sample_data:
            for key, value in sample_data.items():
                if key not in resolved_sample_data:
                    resolved_sample_data[key] = value

        logger.info(f"Template variables config: {template.get('variables', {})}")
        logger.info(f"Resolved sample data (before URL conversion): {resolved_sample_data}")

        # Convert external URLs to internal service URLs for inter-service communication
        resolved_sample_data = url_converter.convert_variables(resolved_sample_data)
        logger.info(f"Resolved sample data (after URL conversion): {resolved_sample_data}")

        # IMPORTANT: Merge dynamic_images and dynamic_videos data BEFORE template resolution
        # Check if we have dynamic_media (new simplified format)
        # Format: [{url, duration, type}, ...]
        has_dynamic_media = 'dynamic_media' in resolved_sample_data and resolved_sample_data['dynamic_media']

        if has_dynamic_media:
            media_list = resolved_sample_data['dynamic_media']
            logger.info(f"📦 Detected dynamic_media with {len(media_list)} items")

            # Log each item
            for i, item in enumerate(media_list):
                media_type = item.get('type', 'unknown')
                duration = item.get('duration', 0)
                logger.info(f"   - Item {i+1}: {media_type} ({duration:.2f}s)")

        # If we have dynamic_media, we'll create the base video differently
        # But keep the template layers intact for the user
        if has_dynamic_media:
            logger.info("🎬 Using simplified dynamic_media approach")
            logger.info("   Will create base video from concatenated clips")

        # Resolve template with sample data
        resolved_template = variable_resolver.resolve_template(template, resolved_sample_data)
        logger.info(f"Resolved template layers: {resolved_template.get('layers', [])}")

        # Create directories if they don't exist
        assets_dir = '/app/public/assets'
        temp_dir = '/app/public/temp'
        os.makedirs(assets_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

        # Get aspect ratio from template
        aspect_ratio = template.get('aspect_ratio', '16:9')

        # If this is initial load, check for aspect-ratio-specific default sample video
        if is_initial:
            # Create aspect-ratio-specific filename
            aspect_ratio_safe = aspect_ratio.replace(':', '_')  # e.g., '16:9' -> '16_9'
            default_sample_filename = f'sample_video_{aspect_ratio_safe}.mp4'
            default_sample_path = os.path.join(assets_dir, default_sample_filename)

            if os.path.exists(default_sample_path):
                logger.info(f"Using existing default sample video for {aspect_ratio}")
                return jsonify({
                    'status': 'success',
                    'preview_url': f'/api/templates/preview/video/{default_sample_filename}',
                    'video_path': default_sample_path,
                    'message': f'Using default sample video ({aspect_ratio})'
                }), 200
            else:
                logger.info(f"Default sample video not found for {aspect_ratio}, generating...")
                # Create placeholder video directly (video-generator is not implemented yet)
                _create_placeholder_video(default_sample_path, aspect_ratio)

                if os.path.exists(default_sample_path):
                    return jsonify({
                        'status': 'success',
                        'preview_url': f'/api/templates/preview/video/{default_sample_filename}',
                        'video_path': default_sample_path,
                        'message': f'Default sample video generated ({aspect_ratio})'
                    }), 200
                else:
                    return jsonify({
                        'status': 'error',
                        'error': 'Failed to generate default sample video'
                    }), 500

        # For live changes, apply effects to the existing sample video
        # Create unique filename based on template hash
        template_hash = hashlib.md5(str(template).encode()).hexdigest()[:8]
        preview_id = str(uuid.uuid4())[:8]
        preview_filename = f'preview_{template_hash}_{preview_id}.mp4'
        preview_path = os.path.join(temp_dir, preview_filename)

        logger.info(f"Generating live preview: {preview_filename}")

        # Get the base sample video for this aspect ratio
        aspect_ratio_safe = aspect_ratio.replace(':', '_')
        default_sample_filename = f'sample_video_{aspect_ratio_safe}.mp4'
        default_sample_path = os.path.join(assets_dir, default_sample_filename)

        # If base sample video doesn't exist, create it first
        if not os.path.exists(default_sample_path):
            logger.info(f"Base sample video not found, creating it first: {default_sample_filename}")
            _create_placeholder_video(default_sample_path, aspect_ratio, effects=[])

        # NEW APPROACH: If we have dynamic_media, create clips and concatenate
        if has_dynamic_media:
            logger.info("🎬 Creating video from dynamic_media assets")
            media_list = resolved_sample_data['dynamic_media']

            # Get effects from template to apply to each clip
            template_effects = template.get('effects', [])

            # Create individual clips for each asset with effects applied
            base_video_path = _create_concatenated_video_from_media(
                media_list,
                aspect_ratio,
                temp_dir,
                effects=template_effects
            )

            logger.info(f"✅ Created base video from {len(media_list)} assets with effects")
        else:
            # Use default sample video as base
            base_video_path = default_sample_path

        # Now apply effects and/or background music and/or logo and/or layers to the base video
        # Use resolved_template to get layers with variables substituted
        effects = resolved_template.get('effects', [])
        background_music = resolved_template.get('background_music', {})
        logo = resolved_template.get('logo', {})
        layers = resolved_template.get('layers', [])

        # If we have dynamic_media, effects were already applied to individual clips
        # So we skip effects here (but still apply background music, logo, layers)
        if has_dynamic_media:
            logger.info("⚠️ Skipping effects (already applied to individual clips)")
            effects_to_apply = []  # Don't re-apply effects
        else:
            effects_to_apply = effects

        # Apply effects and/or background music and/or logo and/or layers if any is present
        if effects_to_apply or (background_music and background_music.get('enabled', False)) or (logo and logo.get('enabled', False)) or layers or custom_audio_url:
            logger.info(f"Applying {len(effects_to_apply)} effects, background music, logo, and {len(layers)} layers to base video")
            _apply_effects_to_video(base_video_path, preview_path, effects_to_apply, aspect_ratio, background_music, logo, layers, resolved_sample_data, custom_audio_url)

            if os.path.exists(preview_path):
                return jsonify({
                    'status': 'success',
                    'preview_url': f'/api/templates/preview/video/{preview_filename}',
                    'video_path': preview_path,
                    'is_temp': True,
                    'message': 'Preview generated with effects and layers'
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'Failed to apply effects and layers to video'
                }), 500
        else:
            # No effects, background music, logo, or layers, just use the base sample video
            logger.info("No effects, background music, logo, or layers to apply, using base sample video")
            return jsonify({
                'status': 'success',
                'preview_url': f'/api/templates/preview/video/{default_sample_filename}',
                'video_path': default_sample_path,
                'message': 'Using base sample video'
            }), 200

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

        # Check if variable has a default value defined in config
        if 'default' in var_config and var_config['default']:
            sample_data[var_name] = var_config['default']
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


@template_bp.route('/templates/upload/audio', methods=['POST'])
def upload_audio():
    """
    Upload audio file for background music

    Accepts multipart/form-data with 'file' field
    Returns the path to the uploaded file
    """
    try:
        from flask import request
        from werkzeug.utils import secure_filename
        import uuid

        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'error': 'No file selected'
            }), 400

        # Validate file extension
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            return jsonify({
                'status': 'error',
                'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
            }), 400

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = secure_filename(file.filename)
        filename = f"music_{unique_id}_{safe_filename}"

        # Save to assets folder
        assets_dir = '/app/public/assets'
        os.makedirs(assets_dir, exist_ok=True)

        file_path = os.path.join(assets_dir, filename)
        file.save(file_path)

        logger.info(f"Audio file uploaded successfully: {filename}")

        return jsonify({
            'status': 'success',
            'filename': filename,
            'path': f'/api/templates/assets/{filename}'
        }), 200

    except Exception as e:
        logger.error(f"Error uploading audio file: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates/upload/logo', methods=['POST'])
def upload_logo():
    """
    Upload logo image file

    Accepts multipart/form-data with 'file' field
    Returns the path to the uploaded file
    """
    try:
        from flask import request
        from werkzeug.utils import secure_filename
        import uuid

        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'error': 'No file selected'
            }), 400

        # Validate file extension
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg'}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            return jsonify({
                'status': 'error',
                'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
            }), 400

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = secure_filename(file.filename)
        filename = f"logo_{unique_id}_{safe_filename}"

        # Save to assets folder
        assets_dir = '/app/public/assets'
        os.makedirs(assets_dir, exist_ok=True)

        file_path = os.path.join(assets_dir, filename)
        file.save(file_path)

        logger.info(f"Logo file uploaded successfully: {filename}")

        return jsonify({
            'status': 'success',
            'filename': filename,
            'path': f'/api/templates/assets/{filename}'
        }), 200

    except Exception as e:
        logger.error(f"Error uploading logo file: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates/upload/image', methods=['POST'])
def upload_image():
    """
    Upload image file for layers

    Accepts multipart/form-data with 'file' field
    Returns the path to the uploaded file
    """
    try:
        from flask import request
        from werkzeug.utils import secure_filename
        import uuid

        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'error': 'No file selected'
            }), 400

        # Validate file extension
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            return jsonify({
                'status': 'error',
                'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
            }), 400

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = secure_filename(file.filename)
        filename = f"image_{unique_id}_{safe_filename}"

        # Save to assets folder
        assets_dir = '/app/public/assets'
        os.makedirs(assets_dir, exist_ok=True)

        file_path = os.path.join(assets_dir, filename)
        file.save(file_path)

        logger.info(f"Image file uploaded successfully: {filename}")

        return jsonify({
            'status': 'success',
            'filename': filename,
            'path': f'/api/templates/assets/{filename}'
        }), 200

    except Exception as e:
        logger.error(f"Error uploading image file: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates/upload/video', methods=['POST'])
def upload_video():
    """
    Upload video file for layers

    Accepts multipart/form-data with 'file' field
    Returns the path to the uploaded file
    """
    try:
        from flask import request
        from werkzeug.utils import secure_filename
        import uuid

        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'error': 'No file selected'
            }), 400

        # Validate file extension
        allowed_extensions = {'.mp4', '.webm', '.ogg', '.mov', '.avi'}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            return jsonify({
                'status': 'error',
                'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
            }), 400

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = secure_filename(file.filename)
        filename = f"video_{unique_id}_{safe_filename}"

        # Save to assets folder
        assets_dir = '/app/public/assets'
        os.makedirs(assets_dir, exist_ok=True)

        file_path = os.path.join(assets_dir, filename)
        file.save(file_path)

        logger.info(f"Video file uploaded successfully: {filename}")

        return jsonify({
            'status': 'success',
            'filename': filename,
            'path': f'/api/templates/assets/{filename}'
        }), 200

    except Exception as e:
        logger.error(f"Error uploading video file: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


def _add_text_overlay_to_thumbnail(thumbnail_img, text_config, logger):
    """
    Add text overlay to thumbnail image similar to video generation service

    Args:
        thumbnail_img: PIL Image object
        text_config: Dictionary with text configuration
        logger: Logger instance

    Returns:
        PIL Image with text overlay
    """
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Get text configuration
        title = text_config.get('title', '')
        subtitle = text_config.get('subtitle', '')
        position = text_config.get('position', 'top-left')
        font_size = text_config.get('font_size', 88)
        title_color = text_config.get('title_color', '#FFFFFF')
        subtitle_color = text_config.get('subtitle_color', '#FFFFFF')
        bg_color = text_config.get('background_color', '#003399')
        bg_opacity = text_config.get('background_opacity', 0.9)

        logger.info(f"Adding text overlay: title={title}, position={position}")

        # Convert to RGBA for transparency support
        img_rgba = thumbnail_img.convert('RGBA')
        img_width, img_height = img_rgba.size

        # Create overlay layer
        overlay = Image.new('RGBA', img_rgba.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Load fonts
        try:
            font_paths_bold = [
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            ]

            title_font = None
            for font_path in font_paths_bold:
                if os.path.exists(font_path):
                    title_font = ImageFont.truetype(font_path, font_size)
                    break

            if not title_font:
                title_font = ImageFont.load_default()

            # Subtitle font is smaller
            subtitle_font = None
            for font_path in font_paths_bold:
                if os.path.exists(font_path):
                    subtitle_font = ImageFont.truetype(
                        font_path, int(font_size * 0.6)
                    )
                    break

            if not subtitle_font:
                subtitle_font = ImageFont.load_default()

        except Exception as e:
            logger.warning(f"Font loading failed: {e}")
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # Convert hex colors to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        title_rgb = hex_to_rgb(title_color)
        subtitle_rgb = hex_to_rgb(subtitle_color)
        bg_rgb = hex_to_rgb(bg_color)

        # Measure text dimensions
        temp_draw = ImageDraw.Draw(img_rgba)

        title_bbox = temp_draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]

        subtitle_bbox = temp_draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]

        # Calculate banner dimensions
        padding_x = 40
        padding_y = 30
        line_spacing = 20

        banner_width = max(title_width, subtitle_width) + (padding_x * 2)
        banner_height = title_height + subtitle_height + line_spacing + (padding_y * 2)

        # Calculate position based on configuration
        if position == 'top-left':
            banner_x = 0
            banner_y = 0
        elif position == 'top-right':
            banner_x = img_width - banner_width
            banner_y = 0
        elif position == 'bottom-left':
            banner_x = 0
            banner_y = img_height - banner_height
        elif position == 'bottom-right':
            banner_x = img_width - banner_width
            banner_y = img_height - banner_height
        elif position == 'center':
            banner_x = (img_width - banner_width) // 2
            banner_y = (img_height - banner_height) // 2
        else:
            banner_x = 0
            banner_y = 0

        # Draw semi-transparent background banner
        bg_alpha = int(255 * bg_opacity)
        draw.rectangle(
            [
                (banner_x, banner_y),
                (banner_x + banner_width, banner_y + banner_height)
            ],
            fill=(*bg_rgb, bg_alpha)
        )

        # Draw title text (centered in banner)
        text_x = banner_x + (banner_width - title_width) // 2
        text_y = banner_y + padding_y
        draw.text(
            (text_x, text_y),
            title,
            font=title_font,
            fill=(*title_rgb, 255)
        )

        # Draw subtitle text if provided
        if subtitle:
            text_x = banner_x + (banner_width - subtitle_width) // 2
            text_y = banner_y + padding_y + title_height + line_spacing
            draw.text(
                (text_x, text_y),
                subtitle,
                font=subtitle_font,
                fill=(*subtitle_rgb, 255)
            )

        # Composite overlay onto image
        img_rgba = Image.alpha_composite(img_rgba, overlay)

        # Convert back to RGB
        result = img_rgba.convert('RGB')

        logger.info("Text overlay added successfully")
        return result

    except Exception as e:
        logger.warning(f"Failed to add text overlay: {e}", exc_info=True)
        return thumbnail_img


@template_bp.route('/templates/preview/thumbnail', methods=['POST'])
def generate_thumbnail():
    """
    Generate thumbnail from preview video at configured timestamp with optional text overlay

    Request body:
        {
            "video_path": "/api/templates/preview/video/sample_video_16_9.mp4",
            "timestamp": 2.0,  // seconds
            "aspect_ratio": "16:9",
            "text": {  // Optional text overlay
                "enabled": true,
                "title": "TOP 20 NEWS",
                "subtitle": "27 November 2025",
                "position": "top-left",
                "font_size": 88,
                "title_color": "#FFFFFF",
                "subtitle_color": "#FFFFFF",
                "background_color": "#003399",
                "background_opacity": 0.9
            },
            "variables": {  // Optional variables config for resolving {{placeholders}}
                "title": {
                    "type": "text",
                    "default": "Breaking News"
                },
                "date": {
                    "type": "text",
                    "default": "December 20, 2025"
                }
            }
        }

    Response:
        {
            "status": "success",
            "thumbnail_url": "/api/templates/preview/thumbnail/thumb_abc123.jpg",
            "thumbnail_path": "/app/public/temp/thumb_abc123.jpg"
        }
    """
    try:
        from moviepy.editor import VideoFileClip
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        import uuid

        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'error': 'Request body is required'
            }), 400

        video_path = data.get('video_path', '')
        timestamp = data.get('timestamp', 2.0)
        aspect_ratio = data.get('aspect_ratio', '16:9')
        variables_config = data.get('variables', {})

        # Convert URL path to file system path
        if video_path.startswith('/api/templates/preview/video/'):
            filename = video_path.replace('/api/templates/preview/video/', '')

            # Check in assets folder first (default sample videos)
            assets_path = os.path.join('/app/public/assets', filename)
            temp_path = os.path.join('/app/public/temp', filename)

            if os.path.exists(assets_path):
                video_file_path = assets_path
            elif os.path.exists(temp_path):
                video_file_path = temp_path
            else:
                return jsonify({
                    'status': 'error',
                    'error': f'Video file not found: {filename}'
                }), 404
        else:
            return jsonify({
                'status': 'error',
                'error': 'Invalid video path format'
            }), 400

        logger.info(f"🖼️ Generating thumbnail from {video_file_path} at {timestamp}s")

        # Load video and extract frame at timestamp
        with VideoFileClip(video_file_path) as video:
            # Ensure timestamp is within video duration
            if timestamp > video.duration:
                timestamp = video.duration / 2  # Use middle of video if timestamp is too large
                logger.warning(f"Timestamp {data.get('timestamp')}s exceeds video duration {video.duration}s, using {timestamp}s")

            # Extract frame at timestamp
            frame = video.get_frame(timestamp)

        # Convert frame to PIL Image
        thumbnail_img = Image.fromarray(frame)

        # Apply text overlay if configured
        text_config = data.get('text')
        if text_config and text_config.get('enabled'):
            # Resolve variables in text config if variables are provided
            if variables_config:
                from utils.helpers import substitute_variables

                # Generate sample data from variables config
                sample_data = {}
                for var_name, var_config in variables_config.items():
                    if 'default' in var_config and var_config['default']:
                        sample_data[var_name] = var_config['default']

                logger.info(f"Resolving thumbnail text with variables: {sample_data}")

                # Resolve variables in text config
                import json
                text_config_str = json.dumps(text_config)
                resolved_text_config_str = substitute_variables(text_config_str, sample_data)
                text_config = json.loads(resolved_text_config_str)

                logger.info(f"Resolved thumbnail text config: {text_config}")

            thumbnail_img = _add_text_overlay_to_thumbnail(thumbnail_img, text_config, logger)

        # Generate unique filename for thumbnail
        unique_id = str(uuid.uuid4())[:8]
        thumbnail_filename = f"thumb_{aspect_ratio.replace(':', '_')}_{unique_id}.jpg"

        # Save to temp folder
        temp_dir = '/app/public/temp'
        os.makedirs(temp_dir, exist_ok=True)

        thumbnail_path = os.path.join(temp_dir, thumbnail_filename)
        thumbnail_img.save(thumbnail_path, 'JPEG', quality=90)

        logger.info(f"✅ Thumbnail generated: {thumbnail_filename}")

        return jsonify({
            'status': 'success',
            'thumbnail_url': f'/api/templates/preview/thumbnail/{thumbnail_filename}',
            'thumbnail_path': thumbnail_path,
            'timestamp': timestamp
        }), 200

    except Exception as e:
        logger.error(f"Error generating thumbnail: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates/preview/thumbnail/<filename>')
def serve_thumbnail(filename):
    """Serve thumbnail image from temp folder"""
    try:
        from flask import send_file

        temp_dir = '/app/public/temp'
        file_path = os.path.join(temp_dir, filename)

        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'error': 'Thumbnail not found'
            }), 404

        return send_file(file_path, mimetype='image/jpeg')

    except Exception as e:
        logger.error(f"Error serving thumbnail: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@template_bp.route('/templates/assets/<filename>')
def serve_asset(filename):
    """
    Serve asset files (audio, images, etc.)

    Args:
        - filename: Asset filename
    """
    try:
        from flask import send_file

        assets_path = os.path.join('/app/public/assets', filename)

        if not os.path.exists(assets_path):
            logger.warning(f"Asset not found: {filename}")
            return jsonify({
                'status': 'error',
                'error': 'Asset not found'
            }), 404

        # Determine mimetype based on extension
        ext = os.path.splitext(filename)[1].lower()
        mimetype_map = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml'
        }

        mimetype = mimetype_map.get(ext, 'application/octet-stream')

        logger.info(f"Serving asset: {filename} ({mimetype})")
        return send_file(assets_path, mimetype=mimetype)

    except Exception as e:
        logger.error(f"Error serving asset {filename}: {e}")
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

