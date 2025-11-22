"""
Logo Service - Generate CNI logo similar to CNN style
"""
import os
from PIL import Image, ImageDraw, ImageFont
import logging


class LogoService:
    """Service for generating CNI logo in CNN style"""
    
    def __init__(self):
        self.logger = logging.getLogger('video-generator')
    
    def generate_cni_logo(self, output_path: str, size: int = 500) -> str:
        """
        Generate CNI logo similar to CNN style
        
        Args:
            output_path: Path where logo should be saved
            size: Size of the logo (square)
            
        Returns:
            Path to generated logo
        """
        try:
            self.logger.info(f"🎨 Generating CNI logo (size: {size}x{size})...")
            
            # Create canvas with red background (CNN red: #CC0000)
            logo = Image.new('RGB', (size, size), (204, 0, 0))
            draw = ImageDraw.Draw(logo)
            
            # Load bold font for "CNI" text
            font = self._load_bold_font(size)
            
            # Text to draw
            text = "CNI"
            
            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position to center text
            x = (size - text_width) // 2
            y = (size - text_height) // 2
            
            # Draw white text (CNN style)
            draw.text((x, y), text, font=font, fill=(255, 255, 255))
            
            # Save logo
            logo.save(output_path, 'PNG', quality=95)
            self.logger.info(f"✅ CNI logo generated: {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ Logo generation failed: {str(e)}")
            raise
    
    def _load_bold_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load bold font for logo text"""
        # Calculate font size (approximately 60% of canvas size for 3 letters)
        font_size = int(size * 0.5)
        
        # Try to load system fonts
        font_paths = [
            '/System/Library/Fonts/Supplemental/Arial Black.ttf',
            '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, font_size)
                except Exception:
                    continue
        
        # Fallback to default font
        self.logger.warning("⚠️ Could not load system font, using default")
        return ImageFont.load_default()
    
    def generate_cni_logo_with_border(self, output_path: str, size: int = 500, border_width: int = 10) -> str:
        """
        Generate CNI logo with white border (alternative style)
        
        Args:
            output_path: Path where logo should be saved
            size: Size of the logo (square)
            border_width: Width of white border
            
        Returns:
            Path to generated logo
        """
        try:
            self.logger.info(f"🎨 Generating CNI logo with border (size: {size}x{size})...")
            
            # Create canvas with white background
            logo = Image.new('RGB', (size, size), (255, 255, 255))
            draw = ImageDraw.Draw(logo)
            
            # Draw red rectangle (leaving border)
            draw.rectangle(
                [(border_width, border_width), (size - border_width, size - border_width)],
                fill=(204, 0, 0)
            )
            
            # Load bold font for "CNI" text
            font = self._load_bold_font(size - 2 * border_width)
            
            # Text to draw
            text = "CNI"
            
            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Calculate position to center text
            x = (size - text_width) // 2
            y = (size - text_height) // 2
            
            # Draw white text
            draw.text((x, y), text, font=font, fill=(255, 255, 255))
            
            # Save logo
            logo.save(output_path, 'PNG', quality=95)
            self.logger.info(f"✅ CNI logo with border generated: {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ Logo generation failed: {str(e)}")
            raise

