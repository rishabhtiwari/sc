"""
Bottom Banner Effect for Video Generation
Adds a two-tier banner at the bottom of the video:
1. Top section: Blue banner with heading text
2. Bottom section: Thin ticker banner with scrolling summary text
"""

from typing import Dict, Any, Optional
from moviepy.editor import VideoClip, ImageClip, CompositeVideoClip, TextClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from .base_effect import BaseEffect


class BottomBannerEffect(BaseEffect):
    """
    Adds a two-tier banner at the bottom of the video (news channel style):
    - Top section: Navy Blue banner with heading text
    - Bottom section: Thin ticker banner with scrolling summary text

    Supported parameters:
    - heading: Text to display on the main banner
    - summary: Text to display on the ticker (scrolling)
    - banner_height: Height of the main banner in pixels (default: 100)
    - ticker_height: Height of the ticker banner in pixels (default: 40)
    - banner_color: RGB tuple for main banner color (default: (0, 51, 153) - Navy Blue)
    - ticker_color: RGB tuple for ticker color (default: (20, 20, 20) - Dark Gray)
    - text_color: Color of the text (default: 'white')
    - font_size: Font size for the heading (default: 42)
    - ticker_font_size: Font size for ticker text (default: 24)
    - duration: Duration to show the banner (default: 5.0 seconds)
    """

    def __init__(self, config=None, logger=None):
        super().__init__(config, logger)
        self.effect_name = "bottom_banner"

        # Default configuration
        self.banner_height = self.config.get('banner_height', 100)
        self.ticker_height = self.config.get('ticker_height', 40)
        self.banner_color = self.config.get('banner_color', (0, 51, 153))  # Navy Blue
        self.ticker_color = self.config.get('ticker_color', (20, 20, 20))  # Dark Gray
        self.text_color = self.config.get('text_color', 'white')
        self.font_size = self.config.get('font_size', 42)
        self.ticker_font_size = self.config.get('ticker_font_size', 24)
        self.default_duration = self.config.get('duration', 5.0)
        
    def validate_params(self, **kwargs) -> bool:
        """
        Validate effect parameters
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        heading = kwargs.get('heading')
        if not heading:
            self.log_warning("No heading provided for bottom banner")
            return False
        
        return True
    
    def apply(self, clip: VideoClip, **params) -> VideoClip:
        """
        Apply two-tier bottom banner effect to video clip

        Args:
            clip: VideoClip to apply the effect to
            **params: Effect parameters
                - heading: Text to display on the main banner (required)
                - summary: Text to display on the ticker (optional)
                - banner_height: Height of the main banner in pixels
                - ticker_height: Height of the ticker banner in pixels
                - banner_color: RGB tuple for main banner color
                - ticker_color: RGB tuple for ticker color
                - text_color: Color of the text
                - font_size: Font size for the heading
                - ticker_font_size: Font size for ticker text
                - duration: Duration to show the banner

        Returns:
            VideoClip with two-tier bottom banner effect applied
        """
        try:
            # Get parameters with defaults
            heading = params.get('heading', '')
            summary = params.get('summary', '')
            banner_height = params.get('banner_height', self.banner_height)
            ticker_height = params.get('ticker_height', self.ticker_height)
            banner_color = params.get('banner_color', self.banner_color)
            ticker_color = params.get('ticker_color', self.ticker_color)
            text_color = params.get('text_color', self.text_color)
            font_size = params.get('font_size', self.font_size)
            ticker_font_size = params.get('ticker_font_size', self.ticker_font_size)
            duration = params.get('duration', self.default_duration)

            # Limit duration to clip duration
            clip_duration = float(clip.duration) if clip.duration else 5.0
            banner_duration = min(duration, clip_duration)

            self.log_info(f"Adding two-tier bottom banner with heading: '{heading}' for {banner_duration}s")

            # Get video dimensions
            video_width, video_height = clip.size

            # Total height for both banners
            total_banner_height = banner_height + ticker_height

            # Create main banner image using PIL
            main_banner_img = self._create_banner_image(
                video_width,
                banner_height,
                heading,
                banner_color,
                text_color,
                font_size
            )

            # Convert PIL image to numpy array
            main_banner_array = np.array(main_banner_img)

            # Create ImageClip from the main banner
            main_banner_clip = ImageClip(main_banner_array).set_duration(banner_duration)

            # Position main banner above the ticker
            main_banner_y_position = video_height - total_banner_height
            main_banner_clip = main_banner_clip.set_position((0, main_banner_y_position))

            # Apply fade in/out to main banner
            main_banner_clip = self._apply_fade_to_banner(main_banner_clip, banner_duration)

            # Create ticker banner with scrolling text if summary is provided
            clips_to_composite = [clip, main_banner_clip]

            if summary:
                ticker_clip = self._create_scrolling_ticker(
                    video_width,
                    ticker_height,
                    summary,
                    ticker_color,
                    text_color,
                    ticker_font_size,
                    banner_duration
                )

                # Position ticker at the very bottom
                ticker_y_position = video_height - ticker_height
                ticker_clip = ticker_clip.set_position((0, ticker_y_position))

                # Apply fade in/out to ticker
                ticker_clip = self._apply_fade_to_banner(ticker_clip, banner_duration)

                clips_to_composite.append(ticker_clip)

            # Composite all clips together
            final_clip = CompositeVideoClip(clips_to_composite)

            # Preserve audio from original clip
            if clip.audio:
                final_clip = final_clip.set_audio(clip.audio)

            return final_clip

        except Exception as e:
            self.log_error(f"Error applying bottom banner effect: {str(e)}")
            import traceback
            self.log_error(f"Traceback: {traceback.format_exc()}")
            # Return original clip if effect fails
            return clip
    
    def _create_banner_image(
        self, 
        width: int, 
        height: int, 
        heading: str, 
        banner_color: tuple, 
        text_color: str, 
        font_size: int
    ) -> Image.Image:
        """
        Create a banner image with text using PIL
        
        Args:
            width: Width of the banner
            height: Height of the banner
            heading: Text to display
            banner_color: RGB tuple for background color
            text_color: Color of the text
            font_size: Font size for the heading
            
        Returns:
            PIL Image with banner and text
        """
        # Create banner background
        banner = Image.new('RGB', (width, height), banner_color)
        draw = ImageDraw.Draw(banner)
        
        # Try to load a bold font
        font = self._load_font(font_size)
        
        # Wrap text if too long
        wrapped_text = self._wrap_text(heading, width, font, draw)
        
        # Get text bounding box for centering
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font, align='center')
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position to center text
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text with outline for better visibility
        outline_color = 'black' if text_color == 'white' else 'white'
        outline_width = 2
        
        # Draw outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.multiline_text(
                        (x + dx, y + dy), 
                        wrapped_text, 
                        font=font, 
                        fill=outline_color,
                        align='center'
                    )
        
        # Draw main text
        draw.multiline_text((x, y), wrapped_text, font=font, fill=text_color, align='center')
        
        return banner
    
    def _load_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        """
        Load a bold font for the banner text
        
        Args:
            font_size: Size of the font
            
        Returns:
            ImageFont object
        """
        font_paths = [
            '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        ]
        
        for font_path in font_paths:
            try:
                import os
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, font_size)
            except Exception as e:
                self.log_warning(f"Failed to load font {font_path}: {str(e)}")
                continue
        
        # Fallback to default font
        self.log_warning("Using default font")
        return ImageFont.load_default()
    
    def _wrap_text(self, text: str, max_width: int, font: ImageFont.FreeTypeFont, draw: ImageDraw.Draw) -> str:
        """
        Wrap text to fit within max_width
        
        Args:
            text: Text to wrap
            max_width: Maximum width in pixels
            font: Font to use for measuring
            draw: ImageDraw object for measuring text
            
        Returns:
            Wrapped text with newlines
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width - 40:  # 40px padding on each side
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, add it anyway
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def _create_scrolling_ticker(
        self,
        width: int,
        height: int,
        text: str,
        bg_color: tuple,
        text_color: str,
        font_size: int,
        duration: float
    ) -> VideoClip:
        """
        Create a scrolling ticker banner (news channel style) with continuous looping

        Args:
            width: Width of the ticker
            height: Height of the ticker
            text: Text to scroll (will be repeated for continuous loop)
            bg_color: RGB tuple for background color
            text_color: Color of the text
            font_size: Font size for ticker text
            duration: Duration of the ticker

        Returns:
            VideoClip with scrolling ticker effect
        """
        # Create background image
        ticker_bg = Image.new('RGB', (width, height), bg_color)
        ticker_bg_array = np.array(ticker_bg)

        # Load font for ticker
        font = self._load_font(font_size)

        # Add separator between repeated text for better readability
        separator = "  •  "
        repeated_text = text + separator

        # Create a temporary image to measure text width
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), repeated_text, font=font)
        single_text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate how many times to repeat the text to ensure smooth looping
        # We need at least 2 full repetitions visible at any time
        num_repetitions = max(3, int(width * 3 / single_text_width) + 2)
        full_text = repeated_text * num_repetitions

        # Measure full text width
        bbox = temp_draw.textbbox((0, 0), full_text, font=font)
        text_img_width = bbox[2] - bbox[0]

        # Create an image wide enough for the repeated text
        text_img = Image.new('RGBA', (text_img_width, height), (*bg_color, 255))
        text_draw = ImageDraw.Draw(text_img)

        # Calculate vertical position to center text
        y_pos = (height - text_height) // 2

        # Draw text with outline for better visibility
        outline_color = 'black' if text_color == 'white' else 'white'
        outline_width = 1

        # Draw outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    text_draw.text(
                        (10 + dx, y_pos + dy),
                        full_text,
                        font=font,
                        fill=outline_color
                    )

        # Draw main text
        text_draw.text((10, y_pos), full_text, font=font, fill=text_color)

        text_img_array = np.array(text_img)

        # Create scrolling animation with seamless looping
        def make_frame(t):
            """Generate frame at time t with scrolling effect"""
            # Calculate scroll position (pixels per second)
            scroll_speed = 100  # pixels per second
            # Use modulo with single_text_width for seamless looping
            x_offset = int(t * scroll_speed) % single_text_width

            # Create frame by cropping the scrolling text image
            frame = np.zeros((height, width, 3), dtype='uint8')

            # Fill with background color
            frame[:, :] = bg_color

            # Calculate how much of the text image to show
            if x_offset + width <= text_img_width:
                # Normal scrolling - enough text available
                frame[:, :] = text_img_array[:, x_offset:x_offset + width, :3]
            else:
                # Wrap around (shouldn't happen with enough repetitions, but just in case)
                remaining = text_img_width - x_offset
                frame[:, :remaining] = text_img_array[:, x_offset:, :3]
                if width - remaining > 0:
                    frame[:, remaining:] = text_img_array[:, :width - remaining, :3]

            return frame

        # Create VideoClip from the make_frame function
        ticker_clip = VideoClip(make_frame, duration=duration)

        return ticker_clip

    def _apply_fade_to_banner(self, banner_clip: ImageClip, duration: float) -> ImageClip:
        """
        Apply fade in/out effect to the banner

        Args:
            banner_clip: Banner clip to apply fade to
            duration: Duration of the banner

        Returns:
            Banner clip with fade effect
        """
        fade_duration = 0.5  # 0.5 seconds fade in/out

        def make_opacity_function(fade_dur, clip_dur):
            """Create opacity function for fade in/out"""
            def opacity_function(get_frame, t):
                """Calculate opacity at time t"""
                opacity = 1.0

                # Fade in
                if t < fade_dur:
                    opacity = t / fade_dur

                # Fade out
                if t > clip_dur - fade_dur:
                    time_into_fadeout = t - (clip_dur - fade_dur)
                    opacity = 1.0 - (time_into_fadeout / fade_dur)

                opacity = max(0.0, min(1.0, opacity))

                # Get the original frame and apply opacity
                frame = get_frame(t)
                return (opacity * frame).astype('uint8')

            return opacity_function

        # Apply opacity function to clip
        opacity_func = make_opacity_function(fade_duration, duration)
        banner_clip = banner_clip.fl(opacity_func)

        return banner_clip
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get default parameters for two-tier bottom banner effect

        Returns:
            Dictionary of default parameters
        """
        return {
            'heading': '',
            'summary': '',
            'banner_height': 100,
            'ticker_height': 40,
            'banner_color': (0, 51, 153),  # Navy Blue
            'ticker_color': (20, 20, 20),  # Dark Gray
            'text_color': 'white',
            'font_size': 42,
            'ticker_font_size': 24,
            'duration': 5.0
        }

