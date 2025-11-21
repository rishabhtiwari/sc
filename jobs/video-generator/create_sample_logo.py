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

    # Draw a rounded rectangle background with TOI-style red
    margin = 10
    draw.rounded_rectangle(
        [(margin, margin), (width - margin, height - margin)],
        radius=15,
        fill=(220, 20, 30, 255),  # TOI-style red (similar to #DC143C crimson)
        outline=(255, 255, 255, 255),
        width=3
    )
    
    # Add text
    try:
        # Try to use a nice font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "CNI News"
    
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculate position to center text
    x = (width - text_width) // 2
    y = (height - text_height) // 2 - 5
    
    # Draw text with shadow
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 180))  # Shadow
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))  # Main text
    
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

