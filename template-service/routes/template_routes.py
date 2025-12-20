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


def _apply_effects_to_video(input_path: str, output_path: str, effects: list, aspect_ratio: str = '16:9', background_music: dict = None, logo: dict = None) -> None:
    """
    Apply effects to an existing video file

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
    """
    try:
        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip

        logger.info(f"Loading video from {input_path}")

        # Load the existing video
        video = VideoFileClip(input_path)
        duration = video.duration
        fps = video.fps
        w, h = video.size

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

        # Apply Fade Text effect if requested
        fade_text_effect = next((e for e in effects if e.get('type') == 'fade_text'), None)
        if fade_text_effect:
            params = fade_text_effect.get('params', {})
            fade_in_duration = params.get('fade_in_duration', 0.5)
            fade_out_duration = params.get('fade_out_duration', 0.5)
            fade_type = params.get('fade_type', 'both')

            logger.info(f"Applying Fade Text effect: fade_in={fade_in_duration}s, fade_out={fade_out_duration}s, type={fade_type}")

            # Create text overlay using PIL (doesn't require ImageMagick)
            try:
                from PIL import Image as PILImage, ImageDraw, ImageFont
                import numpy as np

                # Calculate font size based on video height
                font_size = int(h * 0.08)  # 8% of video height

                # Create a function to draw text on each frame with fade effect
                def add_text_with_fade(get_frame, t):
                    """Add text overlay with fade effect to frame at time t"""
                    frame = get_frame(t)

                    # Calculate opacity based on time and fade settings
                    opacity = 1.0

                    if fade_type in ['in', 'both'] and t < fade_in_duration:
                        # Fade in
                        opacity = min(opacity, t / fade_in_duration)

                    if fade_type in ['out', 'both'] and t > (duration - fade_out_duration):
                        # Fade out
                        time_until_end = duration - t
                        opacity = min(opacity, time_until_end / fade_out_duration)

                    # Skip drawing if fully transparent
                    if opacity <= 0:
                        return frame

                    # Convert frame to PIL Image
                    pil_frame = PILImage.fromarray(frame)

                    # Create a transparent overlay for text
                    overlay = PILImage.new('RGBA', pil_frame.size, (0, 0, 0, 0))
                    draw = ImageDraw.Draw(overlay)

                    # Try to load a font, fall back to default if not available
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                    except:
                        try:
                            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
                        except:
                            font = ImageFont.load_default()

                    # Text to display
                    text = "Sample Text"

                    # Get text bounding box for centering
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]

                    # Calculate center position
                    x = (w - text_width) // 2
                    y = (h - text_height) // 2

                    # Calculate alpha value (0-255)
                    alpha = int(255 * opacity)

                    # Draw text with stroke (outline)
                    stroke_width = max(2, font_size // 20)
                    draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha),
                             stroke_width=stroke_width, stroke_fill=(0, 0, 0, alpha))

                    # Convert frame to RGBA for compositing
                    pil_frame = pil_frame.convert('RGBA')

                    # Composite the text overlay onto the frame
                    pil_frame = PILImage.alpha_composite(pil_frame, overlay)

                    # Convert back to RGB and return as numpy array
                    pil_frame = pil_frame.convert('RGB')
                    return np.array(pil_frame)

                # Apply the text overlay with fade effect
                video = video.fl(add_text_with_fade)

                logger.info("Fade text effect applied successfully")

            except Exception as text_error:
                logger.warning(f"Failed to add text overlay: {text_error}, skipping fade_text effect", exc_info=True)

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

        # Apply Transition effect if requested
        # Note: Transitions are meant for multiple clips, but we'll demonstrate by creating
        # a transition effect in the middle of the video (first half -> transition -> second half with different appearance)
        transition_effect = next((e for e in effects if e.get('type') == 'transition'), None)
        if transition_effect:
            params = transition_effect.get('params', {})
            transition_type = params.get('transition_type', 'crossfade')
            transition_duration = params.get('duration', 1.0)

            logger.info(f"Applying Transition effect: type={transition_type}, duration={transition_duration}s")

            try:
                from PIL import Image as PILImage
                import numpy as np

                # Create a transition effect in the middle of the video
                # We'll create two versions of the frame (normal and inverted colors) and transition between them
                transition_start = duration / 2 - transition_duration / 2
                transition_end = duration / 2 + transition_duration / 2

                def apply_transition(get_frame, t):
                    """Apply transition effect to demonstrate different transition types"""
                    frame = get_frame(t)

                    # If we're not in the transition period, return frame as-is (or inverted after transition)
                    if t < transition_start:
                        # Before transition - normal frame
                        return frame
                    elif t > transition_end:
                        # After transition - inverted colors to show the transition happened
                        return 255 - frame

                    # We're in the transition period
                    progress = (t - transition_start) / transition_duration  # 0.0 to 1.0

                    # Get both frames (before and after)
                    frame_before = frame
                    frame_after = 255 - frame  # Inverted colors

                    if transition_type == 'crossfade':
                        # Simple crossfade
                        result = (frame_before * (1 - progress) + frame_after * progress).astype(np.uint8)
                        return result

                    elif transition_type == 'fade_black':
                        # Fade to black then fade from black
                        if progress < 0.5:
                            # Fade to black
                            fade_progress = progress * 2
                            result = (frame_before * (1 - fade_progress)).astype(np.uint8)
                        else:
                            # Fade from black
                            fade_progress = (progress - 0.5) * 2
                            result = (frame_after * fade_progress).astype(np.uint8)
                        return result

                    elif transition_type in ['slide_left', 'slide_right', 'slide_up', 'slide_down']:
                        # Slide transitions
                        pil_before = PILImage.fromarray(frame_before)
                        pil_after = PILImage.fromarray(frame_after)
                        result = PILImage.new('RGB', (w, h))

                        if transition_type == 'slide_left':
                            # Slide from right to left
                            offset = int(w * progress)
                            result.paste(pil_before, (-offset, 0))
                            result.paste(pil_after, (w - offset, 0))
                        elif transition_type == 'slide_right':
                            # Slide from left to right
                            offset = int(w * progress)
                            result.paste(pil_before, (offset, 0))
                            result.paste(pil_after, (offset - w, 0))
                        elif transition_type == 'slide_up':
                            # Slide from bottom to top
                            offset = int(h * progress)
                            result.paste(pil_before, (0, -offset))
                            result.paste(pil_after, (0, h - offset))
                        elif transition_type == 'slide_down':
                            # Slide from top to bottom
                            offset = int(h * progress)
                            result.paste(pil_before, (0, offset))
                            result.paste(pil_after, (0, offset - h))

                        return np.array(result)

                    elif transition_type in ['wipe_horizontal', 'wipe_vertical']:
                        # Wipe transitions
                        pil_before = PILImage.fromarray(frame_before)
                        pil_after = PILImage.fromarray(frame_after)
                        result = pil_before.copy()

                        if transition_type == 'wipe_horizontal':
                            # Wipe from left to right
                            wipe_x = int(w * progress)
                            if wipe_x > 0:
                                after_crop = pil_after.crop((0, 0, wipe_x, h))
                                result.paste(after_crop, (0, 0))
                        elif transition_type == 'wipe_vertical':
                            # Wipe from top to bottom
                            wipe_y = int(h * progress)
                            if wipe_y > 0:
                                after_crop = pil_after.crop((0, 0, w, wipe_y))
                                result.paste(after_crop, (0, 0))

                        return np.array(result)

                    # Default: crossfade
                    result = (frame_before * (1 - progress) + frame_after * progress).astype(np.uint8)
                    return result

                # Apply the transition effect
                video = video.fl(apply_transition)

                logger.info("Transition effect applied successfully")

            except Exception as transition_error:
                logger.warning(f"Failed to add transition effect: {transition_error}, skipping transition effect", exc_info=True)

        # Apply Bottom Banner effect if requested
        bottom_banner_effect = next((e for e in effects if e.get('type') == 'bottom_banner'), None)
        if bottom_banner_effect:
            params = bottom_banner_effect.get('params', {})
            banner_height = params.get('height', 120)
            background_color = params.get('background_color', '#1a1a1a')
            banner_opacity = params.get('opacity', 0.9)

            logger.info(f"Applying Bottom Banner effect: height={banner_height}px, bg={background_color}, opacity={banner_opacity}")

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

                    # Draw heading in tier 1 (top part)
                    heading_text = "BREAKING NEWS"
                    heading_bbox = draw.textbbox((0, 0), heading_text, font=heading_font)
                    heading_width = heading_bbox[2] - heading_bbox[0]
                    heading_x = (w - heading_width) // 2
                    heading_y = (tier1_height - (heading_bbox[3] - heading_bbox[1])) // 2
                    draw.text((heading_x, heading_y), heading_text, font=heading_font, fill=(255, 255, 255, alpha))

                    # Draw separator line
                    draw.line([(0, tier1_height), (w, tier1_height)], fill=(255, 255, 255, alpha), width=2)

                    # Draw scrolling ticker in tier 2 (bottom part)
                    ticker_text = "Sample News Ticker • Latest Updates • Breaking Stories • "
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

        # Apply Logo Watermark from separate logo configuration (not from effects)
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
                        # Create a function to draw logo on each frame
                        def add_logo_overlay(get_frame, t):
                            """Add logo overlay to frame at time t"""
                            frame = get_frame(t)

                            # Convert frame to PIL Image
                            pil_frame = PILImage.fromarray(frame)

                            # Load the logo image
                            logo_img = PILImage.open(logo_path)

                            # Convert logo to RGBA if not already
                            if logo_img.mode != 'RGBA':
                                logo_img = logo_img.convert('RGBA')

                            # Calculate logo size based on scale
                            logo_width = int(w * scale)
                            aspect_ratio = logo_img.height / logo_img.width
                            logo_height = int(logo_width * aspect_ratio)

                            # Resize logo
                            logo_img = logo_img.resize((logo_width, logo_height), PILImage.LANCZOS)

                            # Apply opacity to logo
                            if opacity < 1.0:
                                # Split into channels
                                r, g, b, a = logo_img.split()
                                # Multiply alpha channel by opacity
                                a = a.point(lambda p: int(p * opacity))
                                # Merge back
                                logo_img = PILImage.merge('RGBA', (r, g, b, a))

                            # Calculate position
                            if position == 'top-left':
                                x, y = margin_x, margin_y
                            elif position == 'top-right':
                                x, y = w - logo_width - margin_x, margin_y
                            elif position == 'bottom-left':
                                x, y = margin_x, h - logo_height - margin_y
                            else:  # bottom-right (default)
                                x, y = w - logo_width - margin_x, h - logo_height - margin_y

                            # Convert frame to RGBA for compositing
                            pil_frame = pil_frame.convert('RGBA')

                            # Paste logo onto frame
                            pil_frame.paste(logo_img, (x, y), logo_img)

                            # Convert back to RGB and return as numpy array
                            pil_frame = pil_frame.convert('RGB')
                            return np.array(pil_frame)

                        # Apply the logo overlay
                        video = video.fl(add_logo_overlay)

                        logger.info("Logo watermark applied successfully from logo configuration")
                    else:
                        logger.warning(f"Logo file not found: {logo_path}")
            except Exception as logo_error:
                logger.warning(f"Failed to apply logo watermark: {logo_error}", exc_info=True)

        # Apply background music if enabled
        final_audio = None
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
                        logger.info(f"Applying background music: {music_source} (volume={volume}, fade_in={fade_in}s, fade_out={fade_out}s)")

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

                        final_audio = audio
                        logger.info("Background music applied successfully")
                    else:
                        logger.warning(f"Background music file not found: {music_path}")
            except Exception as music_error:
                logger.warning(f"Failed to apply background music: {music_error}", exc_info=True)

        # Set audio on video
        if final_audio:
            video = video.set_audio(final_audio)

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

        # Log the request details
        effects = template.get('effects', [])
        background_music = template.get('background_music', {})
        logger.info(f"Preview request: is_initial={is_initial}, effects={len(effects)}, background_music_enabled={background_music.get('enabled', False)}")

        # Generate sample data for template variables
        resolved_sample_data = _generate_sample_data(template, sample_data)

        # Resolve template with sample data
        resolved_template = variable_resolver.resolve_template(template, resolved_sample_data)

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

        # Now apply effects and/or background music and/or logo to the base sample video
        effects = template.get('effects', [])
        background_music = template.get('background_music', {})
        logo = template.get('logo', {})

        # Apply effects and/or background music and/or logo if any is present
        if effects or (background_music and background_music.get('enabled', False)) or (logo and logo.get('enabled', False)):
            logger.info(f"Applying {len(effects)} effects, background music, and logo to base sample video")
            _apply_effects_to_video(default_sample_path, preview_path, effects, aspect_ratio, background_music, logo)

            if os.path.exists(preview_path):
                return jsonify({
                    'status': 'success',
                    'preview_url': f'/api/templates/preview/video/{preview_filename}',
                    'video_path': preview_path,
                    'is_temp': True,
                    'message': 'Preview generated with effects'
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'Failed to apply effects to video'
                }), 500
        else:
            # No effects or background music, just use the base sample video
            logger.info("No effects or background music to apply, using base sample video")
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


@template_bp.route('/templates/preview/thumbnail', methods=['POST'])
def generate_thumbnail():
    """
    Generate thumbnail from preview video at configured timestamp

    Request body:
        {
            "video_path": "/api/templates/preview/video/sample_video_16_9.mp4",
            "timestamp": 2.0,  // seconds
            "aspect_ratio": "16:9"
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
        from PIL import Image
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

