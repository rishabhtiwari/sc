#!/usr/bin/env python3
"""
Create a simple test image with text for OCR testing
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image():
    # Create a white image
    width, height = 800, 400
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a system font, fallback to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Add text content
    text_lines = [
        "OCR Test Document",
        "",
        "This is a sample document for testing",
        "the Paddle OCR Document Converter Service.",
        "",
        "Features:",
        "• Multi-language support",
        "• PDF and image processing",
        "• JSON, text, and markdown output",
        "",
        "Contact: support@ichat.com",
        "Date: September 21, 2025"
    ]
    
    y_position = 30
    for i, line in enumerate(text_lines):
        if i == 0:  # Title
            draw.text((50, y_position), line, fill='black', font=title_font)
            y_position += 50
        else:
            draw.text((50, y_position), line, fill='black', font=font)
            y_position += 30
    
    # Save the image
    output_path = "test-files/sample-text.png"
    image.save(output_path)
    print(f"✅ Test image created: {output_path}")
    return output_path

if __name__ == "__main__":
    create_test_image()
