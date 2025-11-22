"""
Create a sample logo for testing the logo watermark effect
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_logo(output_path: str, width: int = 300, height: int = 100):
    """
    Create a simple sample logo with text
    
    Args:
        output_path: Path to save the logo
        width: Width of the logo
        height: Height of the logo
    """
    # Create a new image with transparent background
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a rounded rectangle background with CNN-style red
    margin = 10
    draw.rounded_rectangle(
        [(margin, margin), (width - margin, height - margin)],
        radius=15,
        fill=(204, 0, 0, 255),  # CNN-style red (#CC0000)
        outline=(255, 255, 255, 255),
        width=3
    )

    # Load fonts
    try:
        # Try to use a bold font (similar to CNN style)
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Black.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        ]
        font_large = None
        font_small = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font_large = ImageFont.truetype(font_path, 52)  # Large font for "CNI"
                font_small = ImageFont.truetype(font_path, 18)  # Smaller font for "News"
                break
        if font_large is None:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Text lines
    text_cni = "CNI"
    text_news = "News"

    # Get text bounding boxes
    bbox_cni = draw.textbbox((0, 0), text_cni, font=font_large)
    bbox_news = draw.textbbox((0, 0), text_news, font=font_small)

    cni_width = bbox_cni[2] - bbox_cni[0]
    cni_height = bbox_cni[3] - bbox_cni[1]
    news_width = bbox_news[2] - bbox_news[0]
    news_height = bbox_news[3] - bbox_news[1]

    # Calculate total height and vertical spacing
    spacing = 5
    total_height = cni_height + spacing + news_height

    # Calculate starting Y position to center both texts vertically
    start_y = (height - total_height) // 2

    # Draw "CNI" text (centered horizontally)
    x_cni = (width - cni_width) // 2
    y_cni = start_y

    # Draw CNI with shadow
    draw.text((x_cni + 2, y_cni + 2), text_cni, font=font_large, fill=(0, 0, 0, 180))  # Shadow
    draw.text((x_cni, y_cni), text_cni, font=font_large, fill=(255, 255, 255, 255))  # Main text

    # Draw "News" text (centered horizontally, below CNI)
    x_news = (width - news_width) // 2
    y_news = y_cni + cni_height + spacing

    # Draw News with shadow
    draw.text((x_news + 2, y_news + 2), text_news, font=font_small, fill=(0, 0, 0, 180))  # Shadow
    draw.text((x_news, y_news), text_news, font=font_small, fill=(255, 255, 255, 255))  # Main text
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the logo
    img.save(output_path, 'PNG')
    print(f"✅ Sample logo created: {output_path}")
    print(f"   Size: {width}x{height}")
    print(f"   Format: PNG with transparency")

if __name__ == '__main__':
    # Create assets directory if it doesn't exist
    assets_dir = '/app/assets'
    os.makedirs(assets_dir, exist_ok=True)
    
    # Create sample logo
    logo_path = os.path.join(assets_dir, 'logo.png')
    create_sample_logo(logo_path)

