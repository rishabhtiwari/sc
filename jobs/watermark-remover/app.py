#!/usr/bin/env python3
"""
IOPaint Logo/Watermark Remover API Service
Integrated Flask API that uses IOPaint library directly
"""

import os
import io
import logging
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configuration
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/output')
FLASK_PORT = int(os.getenv('FLASK_PORT', 8096))

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lazy load IOPaint model
_model = None
_device = None

def get_model():
    """Lazy load IOPaint model"""
    global _model, _device

    if _model is None:
        try:
            logger.info("🔄 Loading IOPaint LaMa model...")
            from iopaint.model import models
            import torch

            # Determine device
            _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"📱 Using device: {_device}")

            # Initialize LaMa model directly from the models registry
            # This bypasses the scan_models() check which requires downloaded models
            if "lama" not in models:
                raise ValueError("LaMa model not found in IOPaint models registry")

            lama_class = models["lama"]
            _model = lama_class(device=_device)
            logger.info("✅ IOPaint LaMa model loaded successfully!")

        except Exception as e:
            logger.error(f"❌ Failed to load IOPaint model: {e}")
            raise

    return _model


def create_mask_from_image(image, threshold=240, min_pixels=100):
    """
    Create a binary mask from image
    White/bright areas (>threshold) will be marked for removal

    Returns None if no significant bright areas are detected
    """
    # Convert to grayscale
    gray = image.convert('L')

    # Create mask: white pixels (>threshold) = areas to remove
    mask_data = np.array(gray)
    mask_array = np.where(mask_data > threshold, 255, 0).astype(np.uint8)

    # Check if mask has enough pixels
    non_zero_count = np.count_nonzero(mask_array)
    if non_zero_count < min_pixels:
        logger.warning(f"⚠️  Auto-mask only found {non_zero_count} pixels (threshold={threshold}). Trying lower threshold...")
        # Try with lower threshold
        mask_array = np.where(mask_data > 200, 255, 0).astype(np.uint8)
        non_zero_count = np.count_nonzero(mask_array)
        if non_zero_count < min_pixels:
            logger.warning(f"⚠️  Still only {non_zero_count} pixels. Returning None - please provide a custom mask.")
            return None
        logger.info(f"✅ Found {non_zero_count} pixels with threshold=200")

    mask = Image.fromarray(mask_array)
    return mask


def remove_logo_with_iopaint(image, mask=None):
    """
    Remove logo/watermark using IOPaint
    
    Args:
        image: PIL Image
        mask: PIL Image (optional) - white areas will be removed
    
    Returns:
        PIL Image with logo removed
    """
    try:
        model = get_model()
        
        # Convert image to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Create mask if not provided
        if mask is None:
            logger.info("🎭 Auto-generating mask from bright areas...")
            mask = create_mask_from_image(image)
            if mask is None:
                raise ValueError("Could not auto-generate mask. No bright areas detected. Please provide a custom mask or specify the region to remove.")
        else:
            # Ensure mask is grayscale
            if mask.mode != 'L':
                mask = mask.convert('L')

            # Resize mask to match image if needed
            if mask.size != image.size:
                mask = mask.resize(image.size, Image.LANCZOS)
        
        # Convert to numpy arrays
        image_np = np.array(image)
        mask_np = np.array(mask)
        
        # Ensure mask is binary (0 or 255)
        mask_np = np.where(mask_np > 127, 255, 0).astype(np.uint8)
        
        logger.info(f"🖼️  Processing image: {image.size}, mask non-zero pixels: {np.count_nonzero(mask_np)}")
        
        # Run inpainting
        from iopaint.schema import InpaintRequest, HDStrategy
        
        config = InpaintRequest(
            ldm_steps=25,
            ldm_sampler="plms",
            hd_strategy=HDStrategy.ORIGINAL,
            hd_strategy_crop_margin=128,
            hd_strategy_crop_trigger_size=800,
            hd_strategy_resize_limit=2048,
        )
        
        result_np = model(image_np, mask_np, config)
        
        # Convert back to PIL Image
        result = Image.fromarray(result_np)
        
        logger.info("✅ Logo removal completed successfully!")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in logo removal: {e}")
        raise


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Try to load model to verify everything is working
        get_model()
        return jsonify({
            'status': 'healthy',
            'service': 'iopaint-logo-remover',
            'model': 'lama',
            'device': str(_device) if _device else 'not_loaded'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/remove-logo', methods=['POST'])
def remove_logo():
    """
    Remove logo from a single image
    
    Form data:
        - file: Image file (required)
        - mask: Mask image file (optional) - white areas will be removed
        - auto_detect: If true and no mask provided, auto-detect bright areas (default: true)
    
    Returns:
        Cleaned image file
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Load image
        image = Image.open(file.stream)
        logger.info(f"📥 Received image: {file.filename}, size: {image.size}, mode: {image.mode}")
        
        # Load mask if provided
        mask = None
        if 'mask' in request.files:
            mask_file = request.files['mask']
            if mask_file.filename != '':
                mask = Image.open(mask_file.stream)
                logger.info(f"🎭 Received mask: {mask_file.filename}, size: {mask.size}")

        # Check for region parameter (x,y,width,height)
        elif 'region' in request.form:
            region_str = request.form['region']
            try:
                x, y, width, height = map(int, region_str.split(','))
                logger.info(f"📍 Creating mask for region: x={x}, y={y}, w={width}, h={height}")
                # Create mask for the specified region
                mask = Image.new('L', image.size, 0)
                mask_array = np.array(mask)
                mask_array[y:y+height, x:x+width] = 255
                mask = Image.fromarray(mask_array)
            except Exception as e:
                return jsonify({'error': f'Invalid region format. Use: x,y,width,height. Error: {str(e)}'}), 400

        # Process image
        result = remove_logo_with_iopaint(image, mask)
        
        # Save to bytes
        img_io = io.BytesIO()
        result.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        # Generate output filename
        original_name = secure_filename(file.filename)
        name_without_ext = os.path.splitext(original_name)[0]
        output_filename = f"{name_without_ext}_cleaned.png"
        
        logger.info(f"✅ Sending cleaned image: {output_filename}")
        
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=output_filename
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/remove-logo-batch', methods=['POST'])
def remove_logo_batch():
    """
    Remove logos from multiple images
    
    Form data:
        - files: Multiple image files
    
    Returns:
        JSON with results for each image
    """
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'Empty file list'}), 400
        
        results = []
        
        for file in files:
            try:
                # Load and process image
                image = Image.open(file.stream)
                result = remove_logo_with_iopaint(image)
                
                # Save to output directory
                original_name = secure_filename(file.filename)
                name_without_ext = os.path.splitext(original_name)[0]
                output_filename = f"{name_without_ext}_cleaned.png"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                result.save(output_path, 'PNG', quality=95)
                
                results.append({
                    'original': file.filename,
                    'output': output_filename,
                    'status': 'success',
                    'path': output_path
                })
                
                logger.info(f"✅ Processed: {file.filename} -> {output_filename}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {file.filename}: {e}")
                results.append({
                    'original': file.filename,
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'total': len(files),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'error']),
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Batch processing error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info(f"🚀 Starting IOPaint Logo Remover API on port {FLASK_PORT}...")
    logger.info(f"📁 Output directory: {OUTPUT_DIR}")
    
    app.run(
        host='0.0.0.0',
        port=FLASK_PORT,
        debug=False
    )

