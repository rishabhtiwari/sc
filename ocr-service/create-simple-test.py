#!/usr/bin/env python3
"""
Simple test file creator for OCR service testing
Creates a basic test image with text using system tools
"""

import os
import subprocess
import sys

def create_test_image():
    """Create a simple test image with text using ImageMagick or system tools"""

    # Ensure test-files directory exists
    os.makedirs("test-files", exist_ok=True)

    # Text to put in the image
    test_text = "Hello World!\nThis is a test document\nfor OCR processing."

    # Try to create image using ImageMagick (if available)
    try:
        cmd = [
            "convert",
            "-size", "400x200",
            "-background", "white",
            "-fill", "black",
            "-font", "Arial",
            "-pointsize", "20",
            "-gravity", "center",
            f"caption:{test_text}",
            "test-files/sample.png"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Test image created successfully using ImageMagick")
            return True

    except FileNotFoundError:
        print("⚠️  ImageMagick not found, trying alternative method...")

    # Alternative: Create a simple text file that can be converted
    try:
        # Create a simple HTML file that can be screenshot
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 24px;
                    padding: 50px;
                    background: white;
                    color: black;
                }}
            </style>
        </head>
        <body>
            <div>{test_text.replace(chr(10), '<br>')}</div>
        </body>
        </html>
        """

        with open("test-files/sample.html", "w") as f:
            f.write(html_content)

        print("✅ Created HTML test file: test-files/sample.html")
        print("💡 You can manually convert this to PNG using a browser screenshot")
        return True

    except Exception as e:
        print(f"❌ Failed to create test files: {e}")
        return False

def create_sample_pdf():
    """Create a simple PDF using system tools if available"""
    try:
        # Try using wkhtmltopdf if available
        if os.path.exists("test-files/sample.html"):
            cmd = ["wkhtmltopdf", "test-files/sample.html", "test-files/sample.pdf"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PDF test file created: test-files/sample.pdf")
                return True
    except:
        pass

    print("💡 PDF creation requires wkhtmltopdf. Install with: brew install wkhtmltopdf")
    return False

def main():
    """Main function to create test files"""
    print("🔧 Creating test files for OCR service...")

    success = create_test_image()
    create_sample_pdf()

    if success:
        print("\n📁 Test files created in test-files/ directory")
        print("🧪 You can now test the OCR service with:")
        print("   curl -X POST http://localhost:8081/convert \\")
        print("     -F \"file=@test-files/sample.png\" \\")
        print("     -F \"output_format=json\" \\")
        print("     -F \"language=en\"")
    else:
        print("\n❌ Failed to create test files")
        print("💡 Try installing ImageMagick: brew install imagemagick")

if __name__ == "__main__":
    main()