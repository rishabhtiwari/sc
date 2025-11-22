"""
Thumbnail Generation Service - Creates YouTube-style thumbnails for merged videos
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from typing import Dict, Optional, Tuple
import textwrap


class ThumbnailService:
    """Service for generating professional YouTube-style thumbnails"""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.thumbnail_width = 1280
        self.thumbnail_height = 720
        
    def generate_thumbnail(
        self,
        background_image_path: Optional[str],
        title: str,
        subtitle: Optional[str] = None,
        output_path: str = None,
        news_thumbnails: Optional[list] = None
    ) -> str:
        """
        Generate a professional YouTube-style thumbnail with split design

        Args:
            background_image_path: Path to background image (optional, not used in split design)
            title: Main title text (will be overridden to "TOP 20 NEWS")
            subtitle: Optional subtitle text
            output_path: Where to save the thumbnail
            news_thumbnails: List of paths to news thumbnail images

        Returns:
            Path to generated thumbnail
        """
        try:
            self.logger.info(f"🎨 Generating split-design thumbnail...")

            # Create split design thumbnail
            thumbnail = self._create_split_design(news_thumbnails or [])

            # Save thumbnail
            if not output_path:
                output_path = os.path.join(
                    self.config.get('public_dir', '/app/public'),
                    'thumbnail.jpg'
                )

            thumbnail.save(output_path, 'JPEG', quality=95)
            self.logger.info(f"✅ Thumbnail saved: {output_path}")

            return output_path

        except Exception as e:
            self.logger.error(f"❌ Thumbnail generation failed: {str(e)}")
            raise
    
    def _create_split_design(self, news_thumbnails: list) -> Image.Image:
        """
        Create a split design thumbnail similar to YouTube news style:
        - Left 25%: Red background with "TOP 20 NEWS" text
        - Right 75%: 2-3 news thumbnails merged together with CNI logo in top-right corner
        """
        # Create base canvas
        canvas = Image.new('RGB', (self.thumbnail_width, self.thumbnail_height), (255, 255, 255))

        # Split point (25% for left, 75% for right)
        split_x = int(self.thumbnail_width * 0.25)

        # LEFT 25%: Red background with text (matching YouTube style)
        left_width = split_x
        left_half = Image.new('RGB', (left_width, self.thumbnail_height), (220, 20, 60))  # Crimson red

        # Add "TOP 20 NEWS" text on left half
        left_half = self._add_left_text(left_half)

        # Paste left half onto canvas
        canvas.paste(left_half, (0, 0))

        # RIGHT 75%: News thumbnails
        right_width = self.thumbnail_width - split_x
        right_half = self._create_news_thumbnails_collage(news_thumbnails, right_width)

        # Paste right half onto canvas
        canvas.paste(right_half, (split_x, 0))

        # Add CNI logo to top-right corner of entire thumbnail (on the right section)
        canvas = self._add_logo_to_thumbnail(canvas)

        return canvas

    def _add_logo_to_thumbnail(self, canvas: Image.Image) -> Image.Image:
        """Add CNI logo to the top-right corner of the entire thumbnail"""
        try:
            logo_path = '/app/assets/logo.png'
            if not os.path.exists(logo_path):
                self.logger.warning(f"⚠️ Logo not found at {logo_path}")
                return canvas

            # Load logo
            logo = Image.open(logo_path)

            # Calculate logo size - 9.2% of thumbnail width (increased by 15% from 8%)
            thumbnail_width = canvas.size[0]
            logo_width = int(thumbnail_width * 0.092)  # 9.2% of total thumbnail width
            logo_height = int(logo.height * (logo_width / logo.width))

            # Resize logo
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)

            # Position logo at top-right corner of entire thumbnail
            x = thumbnail_width - logo_width - 30  # 30px margin from right edge
            y = 30  # 30px from top

            # Paste logo with transparency
            if logo.mode == 'RGBA':
                canvas.paste(logo, (x, y), logo)
            else:
                canvas.paste(logo, (x, y))

            return canvas

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to add logo to thumbnail: {str(e)}")
            return canvas

    def _add_left_text(self, img: Image.Image) -> Image.Image:
        """Add 'TOP 20 NEWS' text to left half - YouTube style"""
        draw = ImageDraw.Draw(img)

        # Load bold font
        try:
            font_large = None
            font_small = None
            font_paths = [
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_large = ImageFont.truetype(font_path, 95)
                    font_small = ImageFont.truetype(font_path, 50)
                    break

            if not font_large:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Text lines - matching YouTube style
        line1 = "TOP 20"
        line2 = "NEWS"

        # Calculate positions (centered)
        width = img.size[0]
        height = img.size[1]

        # Get text sizes
        bbox1 = draw.textbbox((0, 0), line1, font=font_small)
        bbox2 = draw.textbbox((0, 0), line2, font=font_large)

        text_width1 = bbox1[2] - bbox1[0]
        text_width2 = bbox2[2] - bbox2[0]

        text_height1 = bbox1[3] - bbox1[1]
        text_height2 = bbox2[3] - bbox2[1]

        # Calculate vertical spacing
        total_height = text_height1 + text_height2 + 20  # 20px spacing
        start_y = (height - total_height) // 2

        # Draw "TOP 20" (smaller, at top)
        x1 = (width - text_width1) // 2
        y1 = start_y

        # Simple shadow for depth
        draw.text((x1 + 3, y1 + 3), line1, font=font_small, fill=(0, 0, 0, 128))
        draw.text((x1, y1), line1, font=font_small, fill=(255, 255, 255))

        # Draw "NEWS" (larger, below)
        x2 = (width - text_width2) // 2
        y2 = y1 + text_height1 + 20

        # Simple shadow for depth
        draw.text((x2 + 3, y2 + 3), line2, font=font_large, fill=(0, 0, 0, 128))
        draw.text((x2, y2), line2, font=font_large, fill=(255, 255, 255))

        return img

    def _create_news_thumbnails_collage(self, news_thumbnails: list, collage_width: int) -> Image.Image:
        """Create a collage of 2-3 news thumbnails on the right side"""

        # If we have news thumbnails, use them; otherwise create placeholder
        if news_thumbnails and len(news_thumbnails) > 0:
            # Take up to 3 thumbnails
            thumbnails_to_use = news_thumbnails[:3]

            # Create collage
            collage = Image.new('RGB', (collage_width, self.thumbnail_height), (30, 30, 30))

            if len(thumbnails_to_use) == 1:
                # Single image - fill entire right side
                img = self._load_and_resize_thumbnail(thumbnails_to_use[0], collage_width, self.thumbnail_height)
                collage.paste(img, (0, 0))
            elif len(thumbnails_to_use) == 2:
                # Two images - stack vertically
                img_height = self.thumbnail_height // 2
                img1 = self._load_and_resize_thumbnail(thumbnails_to_use[0], collage_width, img_height)
                img2 = self._load_and_resize_thumbnail(thumbnails_to_use[1], collage_width, img_height)
                collage.paste(img1, (0, 0))
                collage.paste(img2, (0, img_height))
            else:
                # Three images - one on top, two on bottom
                top_height = self.thumbnail_height // 2
                bottom_height = self.thumbnail_height // 2
                bottom_width = collage_width // 2

                img1 = self._load_and_resize_thumbnail(thumbnails_to_use[0], collage_width, top_height)
                img2 = self._load_and_resize_thumbnail(thumbnails_to_use[1], bottom_width, bottom_height)
                img3 = self._load_and_resize_thumbnail(thumbnails_to_use[2], bottom_width, bottom_height)

                collage.paste(img1, (0, 0))
                collage.paste(img2, (0, top_height))
                collage.paste(img3, (bottom_width, top_height))

            return collage
        else:
            # No thumbnails - create gradient placeholder
            placeholder = Image.new('RGB', (collage_width, self.thumbnail_height))
            draw = ImageDraw.Draw(placeholder)

            # Red gradient for news theme
            for y in range(self.thumbnail_height):
                r = int(139 + (220 - 139) * (y / self.thumbnail_height))
                g = int(0 + (20 - 0) * (y / self.thumbnail_height))
                b = int(0 + (60 - 0) * (y / self.thumbnail_height))
                draw.rectangle([(0, y), (collage_width, y + 1)], fill=(r, g, b))

            return placeholder

    def _load_and_resize_thumbnail(self, image_path: str, target_width: int, target_height: int) -> Image.Image:
        """Load and resize a thumbnail image to fit target dimensions"""
        try:
            img = Image.open(image_path)

            # Resize and crop to fit
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height

            if img_ratio > target_ratio:
                # Image is wider - crop width
                new_width = int(img.height * target_ratio)
                left = (img.width - new_width) // 2
                img = img.crop((left, 0, left + new_width, img.height))
            else:
                # Image is taller - crop height
                new_height = int(img.width / target_ratio)
                top = (img.height - new_height) // 2
                img = img.crop((0, top, img.width, top + new_height))

            # Resize to exact dimensions
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            return img

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to load thumbnail {image_path}: {str(e)}")
            # Return solid color placeholder
            return Image.new('RGB', (target_width, target_height), (50, 50, 50))

    def _create_from_background(self, image_path: str) -> Image.Image:
        """Create thumbnail from background image"""
        try:
            img = Image.open(image_path)
            
            # Resize and crop to thumbnail dimensions
            img_ratio = img.width / img.height
            target_ratio = self.thumbnail_width / self.thumbnail_height
            
            if img_ratio > target_ratio:
                # Image is wider - crop width
                new_width = int(img.height * target_ratio)
                left = (img.width - new_width) // 2
                img = img.crop((left, 0, left + new_width, img.height))
            else:
                # Image is taller - crop height
                new_height = int(img.width / target_ratio)
                top = (img.height - new_height) // 2
                img = img.crop((0, top, img.width, top + new_height))
            
            # Resize to exact dimensions
            img = img.resize((self.thumbnail_width, self.thumbnail_height), Image.Resampling.LANCZOS)
            
            # Enhance image
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)
            
            # Apply slight blur for background effect
            img = img.filter(ImageFilter.GaussianBlur(radius=2))
            
            return img
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to load background image: {str(e)}")
            return self._create_gradient_background()
    
    def _create_gradient_background(self) -> Image.Image:
        """Create a gradient background (red to dark red for news theme)"""
        img = Image.new('RGB', (self.thumbnail_width, self.thumbnail_height))
        draw = ImageDraw.Draw(img)
        
        # Create red gradient (news theme)
        for y in range(self.thumbnail_height):
            # Gradient from dark red to red
            r = int(139 + (220 - 139) * (y / self.thumbnail_height))
            g = int(0 + (20 - 0) * (y / self.thumbnail_height))
            b = int(0 + (60 - 0) * (y / self.thumbnail_height))
            draw.rectangle([(0, y), (self.thumbnail_width, y + 1)], fill=(r, g, b))
        
        return img
    
    def _add_overlay(self, img: Image.Image, opacity: float = 0.5) -> Image.Image:
        """Add gradient overlay for better text visibility and professional look"""
        img = img.convert('RGBA')

        # Create gradient overlay (dark at top and bottom, lighter in middle)
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        height = img.size[1]
        for y in range(height):
            # Stronger darkness at top and bottom
            if y < height * 0.3:
                # Top gradient
                alpha = int(255 * opacity * (1 - y / (height * 0.3)) * 0.8)
            elif y > height * 0.7:
                # Bottom gradient
                alpha = int(255 * opacity * ((y - height * 0.7) / (height * 0.3)) * 0.8)
            else:
                # Middle section - lighter
                alpha = int(255 * opacity * 0.4)

            draw.rectangle([(0, y), (img.size[0], y + 1)], fill=(0, 0, 0, alpha))

        img = Image.alpha_composite(img, overlay)
        return img.convert('RGB')
    
    def _add_title_text(self, img: Image.Image, title: str) -> Image.Image:
        """Add main title text with bold styling and professional effects"""
        draw = ImageDraw.Draw(img)

        # Try to load a bold font, fallback to default
        try:
            # Try common system fonts - larger size for impact
            font_size = 90
            font_paths = [
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            ]

            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break

            if not font:
                font = ImageFont.load_default()

        except Exception as e:
            self.logger.warning(f"⚠️ Font loading failed: {str(e)}")
            font = ImageFont.load_default()

        # Wrap text to fit width
        max_width = self.thumbnail_width - 120  # More padding
        wrapped_lines = self._wrap_text(title, font, max_width, draw)

        # Calculate total text height
        line_height = font_size + 15
        total_height = len(wrapped_lines) * line_height

        # Start position (centered vertically, slightly higher)
        y = (self.thumbnail_height - total_height) // 2 - 20

        # Draw each line with enhanced shadow and outline
        for line in wrapped_lines:
            # Get text bounding box
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (self.thumbnail_width - text_width) // 2

            # Add colored background bar for each line (semi-transparent red)
            padding = 20
            img_rgba = img.convert('RGBA')
            bar_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            bar_draw = ImageDraw.Draw(bar_overlay)
            bar_draw.rectangle(
                [
                    (x - padding, y - padding // 2),
                    (x + text_width + padding, y + text_height + padding // 2)
                ],
                fill=(220, 20, 60, 180)  # Red with transparency
            )
            img = Image.alpha_composite(img_rgba, bar_overlay).convert('RGB')
            draw = ImageDraw.Draw(img)

            # Draw thick black outline for better visibility
            outline_offset = 6
            for dx in range(-outline_offset, outline_offset + 1):
                for dy in range(-outline_offset, outline_offset + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))

            # Draw main text (bright yellow for news theme - high contrast)
            draw.text((x, y), line, font=font, fill=(255, 255, 0))

            y += line_height

        return img
    
    def _add_subtitle_text(self, img: Image.Image, subtitle: str) -> Image.Image:
        """Add subtitle text with professional styling"""
        draw = ImageDraw.Draw(img)

        try:
            font_size = 45
            font_paths = [
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            ]

            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break

            if not font:
                font = ImageFont.load_default()

        except Exception:
            font = ImageFont.load_default()

        # Position at bottom
        bbox = draw.textbbox((0, 0), subtitle, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.thumbnail_width - text_width) // 2
        y = self.thumbnail_height - 120

        # Add background bar
        padding = 15
        img_rgba = img.convert('RGBA')
        bar_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar_overlay)
        bar_draw.rectangle(
            [
                (x - padding, y - padding // 2),
                (x + text_width + padding, y + text_height + padding // 2)
            ],
            fill=(0, 0, 0, 200)  # Black with transparency
        )
        img = Image.alpha_composite(img_rgba, bar_overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        # Draw with thick outline
        outline_offset = 3
        for dx in range(-outline_offset, outline_offset + 1):
            for dy in range(-outline_offset, outline_offset + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), subtitle, font=font, fill=(0, 0, 0))

        # Draw subtitle in white
        draw.text((x, y), subtitle, font=font, fill=(255, 255, 255))

        return img
    
    def _add_branding(self, img: Image.Image) -> Image.Image:
        """Add branding elements with professional news badge"""
        draw = ImageDraw.Draw(img)

        # Add "BREAKING NEWS" badge at top-left
        badge_text = "BREAKING NEWS"

        try:
            font_size = 42
            font_paths = [
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            ]

            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break

            if not font:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # Draw badge background
        bbox = draw.textbbox((0, 0), badge_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        badge_x = 40
        badge_y = 40
        padding = 20

        # Red badge background with gradient effect
        img_rgba = img.convert('RGBA')
        badge_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        badge_draw = ImageDraw.Draw(badge_overlay)

        # Draw badge rectangle
        badge_draw.rectangle(
            [
                (badge_x - padding, badge_y - padding),
                (badge_x + text_width + padding, badge_y + text_height + padding)
            ],
            fill=(220, 20, 60, 255),  # Bright red
            outline=(255, 255, 255, 255),
            width=4
        )

        img = Image.alpha_composite(img_rgba, badge_overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        # Badge text with outline
        outline_offset = 2
        for dx in range(-outline_offset, outline_offset + 1):
            for dy in range(-outline_offset, outline_offset + 1):
                if dx != 0 or dy != 0:
                    draw.text((badge_x + dx, badge_y + dy), badge_text, font=font, fill=(0, 0, 0))

        # Badge text in white
        draw.text((badge_x, badge_y), badge_text, font=font, fill=(255, 255, 255))

        return img
    
    def _add_border(self, img: Image.Image) -> Image.Image:
        """Add border/frame effect"""
        draw = ImageDraw.Draw(img)
        
        # Draw thick border
        border_width = 8
        draw.rectangle(
            [(0, 0), (self.thumbnail_width - 1, self.thumbnail_height - 1)],
            outline=(255, 255, 255),
            width=border_width
        )
        
        return img
    
    def _wrap_text(self, text: str, font, max_width: int, draw) -> list:
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to 3 lines max
        if len(lines) > 3:
            lines = lines[:3]
            lines[2] = lines[2][:50] + '...'
        
        return lines

