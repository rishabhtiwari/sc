#!/usr/bin/env python3
"""
IOPaint UI Service with MongoDB Integration
Provides a web UI for manually removing watermarks from news images
"""

import os
import io
import sys
import logging
import base64
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import cv2
from pymongo import MongoClient
from bson import ObjectId
import requests
from typing import Optional, Dict, Any

# Add current directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.utils.multi_tenant_db import (
    build_multi_tenant_query,
    prepare_update_document,
    extract_user_context_from_headers
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# MongoDB configuration
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://ichat-mongodb:27017/news')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/output')
FLASK_PORT = int(os.getenv('FLASK_PORT', 8096))

# Global variables
_model = None
_device = None
_mongo_client = None
_news_collection = None


def get_mongo_client():
    """Get MongoDB client (lazy loaded)"""
    global _mongo_client, _news_collection

    if _mongo_client is None:
        try:
            logger.info(f"🔌 Connecting to MongoDB: {MONGODB_URL}")
            _mongo_client = MongoClient(MONGODB_URL)
            _news_collection = _mongo_client.get_database().news_document
            # Test connection
            _mongo_client.admin.command('ping')
            logger.info("✅ MongoDB connected successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    return _news_collection


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

            # Log GPU info if available
            if torch.cuda.is_available():
                logger.info(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
                logger.info(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            else:
                logger.warning("⚠️  CUDA not available, using CPU (will be slower)")

            # Initialize LaMa model directly from the models registry
            if "lama" not in models:
                raise ValueError("LaMa model not found in IOPaint models registry")

            lama_class = models["lama"]
            _model = lama_class(device=_device)
            logger.info("✅ IOPaint LaMa model loaded successfully!")

        except Exception as e:
            logger.error(f"❌ Failed to load IOPaint model: {e}")
            raise

    return _model


def remove_watermark(image_np, mask_np):
    """
    Remove watermark using IOPaint

    Args:
        image_np: numpy array of image (RGB, uint8)
        mask_np: numpy array of mask (grayscale, 255=remove, 0=keep, uint8)

    Returns:
        numpy array of cleaned image (RGB, uint8)
    """
    try:
        model = get_model()

        from iopaint.schema import InpaintRequest, HDStrategy

        # Ensure proper data types
        if image_np.dtype != np.uint8:
            image_np = np.clip(image_np, 0, 255).astype(np.uint8)

        if mask_np.dtype != np.uint8:
            mask_np = np.clip(mask_np, 0, 255).astype(np.uint8)

        # Ensure mask is binary (0 or 255)
        mask_np = np.where(mask_np > 127, 255, 0).astype(np.uint8)

        # Dilate the mask very slightly to include edge pixels
        # This helps the model understand the surrounding background better
        kernel_size = 3  # Minimal dilation to capture immediate edge context
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        mask_np = cv2.dilate(mask_np, kernel, iterations=1)

        logger.info(f"🔧 Input - Image shape: {image_np.shape}, dtype: {image_np.dtype}")
        logger.info(
            f"🔧 Input - Mask shape: {mask_np.shape}, dtype: {mask_np.dtype}, unique values: {np.unique(mask_np)}")

        # Save debug mask to verify the area being processed
        try:
            debug_mask_path = f"/app/output/debug_mask_dilated_{int(time.time())}.png"
            Image.fromarray(mask_np).save(debug_mask_path)
            logger.info(f"💾 Debug mask saved to: {debug_mask_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not save debug mask: {e}")

        # Configure IOPaint for LaMa model (context-aware inpainting)
        # LaMa doesn't use ldm_steps/ldm_sampler - those are for diffusion models
        config = InpaintRequest(
            hd_strategy=HDStrategy.CROP,  # Crop strategy for better local context
            hd_strategy_crop_margin=256,  # Larger margin to capture more background context
            hd_strategy_crop_trigger_size=800,  # Process larger areas with cropping
            hd_strategy_resize_limit=2048,
        )

        # Process with IOPaint (LaMa model)
        logger.info("🎨 Running LaMa inpainting with background context awareness...")
        result_np = model(image_np, mask_np, config)

        logger.info(f"🔧 Output - Result shape: {result_np.shape}, dtype: {result_np.dtype}")

        # Ensure result is uint8
        if result_np.dtype != np.uint8:
            result_np = np.clip(result_np, 0, 255).astype(np.uint8)

        # Apply Gaussian blur to mask edges for smoother blending
        mask_blurred = cv2.GaussianBlur(mask_np, (5, 5), 0)
        mask_3ch_smooth = np.stack([mask_blurred] * 3, axis=2) / 255.0

        # Blend: use inpainted result where mask is white, original image where mask is black
        final_result = (result_np * mask_3ch_smooth + image_np * (1 - mask_3ch_smooth)).astype(np.uint8)

        logger.info(f"✅ Watermark removal complete! Final shape: {final_result.shape}")

        return final_result

    except Exception as e:
        logger.error(f"❌ Error in watermark removal: {e}", exc_info=True)
        raise


# HTML Template for the UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>IOPaint - Watermark Remover</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 24px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .stats {
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 12px;
            color: #6c757d;
            margin-top: 4px;
        }
        .content {
            display: flex;
            height: calc(100vh - 250px);
        }
        .canvas-area {
            flex: 1;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: auto;
            min-height: 0;
        }
        #canvas-container {
            position: relative;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            /* Checkered background to show transparency */
            background-image:
                linear-gradient(45deg, #ccc 25%, transparent 25%),
                linear-gradient(-45deg, #ccc 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, #ccc 75%),
                linear-gradient(-45deg, transparent 75%, #ccc 75%);
            background-size: 20px 20px;
            background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
            background-color: #f8f9fa;
            max-width: calc(100% - 40px);
            max-height: calc(100% - 40px);
            display: inline-block;
            overflow: hidden;
        }
        #image-canvas {
            display: block;
            cursor: crosshair;
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            max-width: 100%;
            max-height: calc(100vh - 350px);
            width: auto;
            height: auto;
            object-fit: contain;
        }
        #image-canvas:hover {
            opacity: 0.95;
        }
        #mask-canvas {
            display: block;
            position: absolute;
            top: 0;
            left: 0;
            pointer-events: none;
            max-width: 100%;
            max-height: calc(100vh - 350px);
            width: auto;
            height: auto;
        }
        .controls {
            width: 300px;
            padding: 20px;
            border-left: 1px solid #e9ecef;
            overflow-y: auto;
        }
        .control-group {
            margin-bottom: 24px;
        }
        .control-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #495057;
            font-size: 14px;
        }
        .btn {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 8px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background: #c82333;
        }
        .btn-info {
            background: #17a2b8;
            color: white;
        }
        .btn-info:hover {
            background: #138496;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        input[type="range"] {
            width: 100%;
        }
        .brush-size-display {
            text-align: center;
            font-size: 12px;
            color: #6c757d;
            margin-top: 4px;
        }
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255,255,255,0.95);
            padding: 24px 48px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: none;
        }
        .loading.active {
            display: block;
        }

        /* Toast notifications */
        .toast {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #333;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-size: 14px;
            font-weight: 500;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            z-index: 10000;
            max-width: 400px;
        }
        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }
        .toast-success {
            background: #10b981;
        }
        .toast-error {
            background: #ef4444;
        }
        .toast-info {
            background: #3b82f6;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 12px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .image-info {
            background: #e7f3ff;
            padding: 12px;
            border-radius: 6px;
            font-size: 13px;
            margin-bottom: 16px;
        }
        .image-info strong {
            color: #0066cc;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 IOPaint Watermark Remover</h1>
            <p>Paint over watermarks to remove them from news images</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value" id="total-images">-</div>
                <div class="stat-label">Total Images</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="cleaned-images">-</div>
                <div class="stat-label">Cleaned</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="skipped-images" style="color: #dc3545;">-</div>
                <div class="stat-label">Skipped</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="pending-images">-</div>
                <div class="stat-label">Pending</div>
            </div>
        </div>
        
        <div class="content">
            <div class="canvas-area">
                <div id="canvas-container">
                    <canvas id="image-canvas"></canvas>
                    <canvas id="mask-canvas"></canvas>
                </div>
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <div>Processing...</div>
                </div>
            </div>
            
            <div class="controls">
                <div class="image-info" id="image-info" style="display:none;">
                    <strong>Current Image:</strong><br>
                    <span id="image-title">-</span>
                </div>

                <div id="instructions" style="display:none; padding: 12px; background: #e7f3ff; border-radius: 6px; margin-bottom: 16px; font-size: 13px; color: #004085;">
                    <strong>📝 Instructions:</strong><br>
                    • <strong>No watermark?</strong> Click "Save & Mark Done" directly<br>
                    • <strong>Has watermark?</strong> Paint over it, then click "Remove Watermark"<br>
                    • Use brush size slider or "Auto-detect" button
                </div>

                <div class="control-group">
                    <label>Brush Size</label>
                    <input type="range" id="brush-size" min="5" max="100" value="20">
                    <div class="brush-size-display"><span id="brush-size-value">20</span>px</div>
                </div>
                
                <div class="control-group">
                    <button class="btn btn-primary" id="load-next-btn">📥 Load Next Image</button>
                    <button class="btn btn-info" id="auto-detect-btn" disabled>🔍 Auto-detect Watermark</button>
                    <button class="btn btn-secondary" id="clear-mask-btn" disabled>🗑️ Clear Mask</button>
                    <button class="btn btn-primary" id="process-btn" disabled>✨ Remove Watermark</button>
                    <button class="btn btn-success" id="save-btn" disabled>💾 Save & Mark Done</button>
                    <button class="btn btn-danger" id="skip-btn" disabled>⏭️ Skip This Image</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Canvas setup
        const imageCanvas = document.getElementById('image-canvas');
        const maskCanvas = document.getElementById('mask-canvas');
        const imageCtx = imageCanvas.getContext('2d');
        const maskCtx = maskCanvas.getContext('2d');

        let currentImage = null;
        let currentDocId = null;
        let isDrawing = false;
        let brushSize = 20;
        let processedImage = null;

        // Position mask canvas over image canvas
        maskCanvas.style.position = 'absolute';
        maskCanvas.style.top = '0';
        maskCanvas.style.left = '0';
        maskCanvas.style.pointerEvents = 'none';

        // Make image canvas interactive
        imageCanvas.style.cursor = 'crosshair';
        
        // Brush size control
        document.getElementById('brush-size').addEventListener('input', (e) => {
            brushSize = parseInt(e.target.value);
            document.getElementById('brush-size-value').textContent = brushSize;
        });
        
        // Drawing on mask
        imageCanvas.addEventListener('mousedown', startDrawing);
        imageCanvas.addEventListener('mousemove', draw);
        imageCanvas.addEventListener('mouseup', stopDrawing);
        imageCanvas.addEventListener('mouseleave', stopDrawing);
        
        function startDrawing(e) {
            if (!currentImage) {
                console.log('⚠️ No image loaded yet');
                return;
            }
            isDrawing = true;
            console.log('🖌️ Started drawing');
            draw(e);
        }
        
        function draw(e) {
            if (!isDrawing) return;

            const rect = imageCanvas.getBoundingClientRect();
            const scaleX = imageCanvas.width / rect.width;
            const scaleY = imageCanvas.height / rect.height;

            const x = (e.clientX - rect.left) * scaleX;
            const y = (e.clientY - rect.top) * scaleY;

            // Draw on mask canvas
            maskCtx.fillStyle = 'rgba(255, 0, 0, 0.5)';
            maskCtx.beginPath();
            maskCtx.arc(x, y, brushSize / 2, 0, Math.PI * 2);
            maskCtx.fill();

            document.getElementById('process-btn').disabled = false;
        }
        
        function stopDrawing() {
            isDrawing = false;
        }
        
        // Load next image
        document.getElementById('load-next-btn').addEventListener('click', loadNextImage);
        
        async function loadNextImage() {
            console.log('🔄 Loading next image...');
            showLoading(true);
            try {
                // Pass current image ID to exclude it from results
                const url = currentDocId ? `/api/next-image?exclude_id=${currentDocId}` : '/api/next-image';
                const response = await fetch(url);
                console.log('📡 Response status:', response.status);

                // Parse JSON response first (even for errors)
                const data = await response.json();
                console.log('📦 Response data:', data);

                // Check for errors (including 404)
                if (!response.ok || data.error) {
                    showToast(data.error || 'Failed to load image', 'info');
                    showLoading(false);
                    // Disable buttons when no images available
                    document.getElementById('auto-detect-btn').disabled = true;
                    document.getElementById('clear-mask-btn').disabled = true;
                    document.getElementById('skip-btn').disabled = true;
                    document.getElementById('process-btn').disabled = true;
                    document.getElementById('save-btn').disabled = true;
                    return;
                }

                currentDocId = data.doc_id;
                currentImage = new Image();
                currentImage.crossOrigin = 'anonymous';

                currentImage.onerror = () => {
                    console.error('❌ Failed to load image from:', data.image_url);
                    alert('Failed to load image');
                    showLoading(false);
                };

                currentImage.onload = () => {
                    // Calculate display size to fit within viewport
                    const maxWidth = window.innerWidth - 400; // Account for controls sidebar
                    const maxHeight = window.innerHeight - 350; // Account for header and stats

                    let displayWidth = currentImage.width;
                    let displayHeight = currentImage.height;

                    // Scale down if image is too large
                    if (displayWidth > maxWidth || displayHeight > maxHeight) {
                        const widthRatio = maxWidth / displayWidth;
                        const heightRatio = maxHeight / displayHeight;
                        const ratio = Math.min(widthRatio, heightRatio);

                        displayWidth = Math.floor(displayWidth * ratio);
                        displayHeight = Math.floor(displayHeight * ratio);
                    }

                    // Set canvas to actual image size (for processing)
                    imageCanvas.width = currentImage.width;
                    imageCanvas.height = currentImage.height;
                    maskCanvas.width = currentImage.width;
                    maskCanvas.height = currentImage.height;

                    // Set display size (CSS)
                    imageCanvas.style.width = displayWidth + 'px';
                    imageCanvas.style.height = displayHeight + 'px';
                    maskCanvas.style.width = displayWidth + 'px';
                    maskCanvas.style.height = displayHeight + 'px';

                    // Draw image
                    imageCtx.drawImage(currentImage, 0, 0);

                    // Clear mask
                    maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);

                    // Update UI
                    document.getElementById('image-info').style.display = 'block';
                    document.getElementById('image-title').textContent = data.title;
                    document.getElementById('instructions').style.display = 'block';
                    document.getElementById('auto-detect-btn').disabled = false;
                    document.getElementById('clear-mask-btn').disabled = false;
                    document.getElementById('skip-btn').disabled = false;
                    document.getElementById('process-btn').disabled = true; // Disabled until user draws
                    processedImage = null;
                    document.getElementById('save-btn').disabled = false; // Enable save for original image

                    showLoading(false);

                    console.log('✅ Image loaded. Canvas size:', imageCanvas.width, 'x', imageCanvas.height);
                    console.log('✅ Display size:', displayWidth, 'x', displayHeight);
                    console.log('✅ You can now draw on the canvas to mark watermarks.');
                };
                currentImage.src = data.image_url;
                
            } catch (error) {
                console.error('Error loading image:', error);
                alert('Failed to load image');
                showLoading(false);
            }
        }
        
        // Auto-detect watermark (mark common watermark areas)
        document.getElementById('auto-detect-btn').addEventListener('click', () => {
            if (!currentImage) return;

            const width = maskCanvas.width;
            const height = maskCanvas.height;

            // Clear existing mask
            maskCtx.clearRect(0, 0, width, height);

            // Mark common watermark locations with semi-transparent red
            maskCtx.fillStyle = 'rgba(255, 0, 0, 0.5)';

            // Bottom-right corner (most common)
            const cornerSize = Math.min(width * 0.2, height * 0.15);
            maskCtx.fillRect(width - cornerSize, height - cornerSize, cornerSize, cornerSize);

            // Bottom-left corner
            maskCtx.fillRect(0, height - cornerSize, cornerSize, cornerSize);

            // Top-right corner
            maskCtx.fillRect(width - cornerSize, 0, cornerSize, cornerSize);

            // Enable process button
            document.getElementById('process-btn').disabled = false;

            alert('Auto-detected common watermark areas. You can paint additional areas or clear and draw manually.');
        });

        // Clear mask
        document.getElementById('clear-mask-btn').addEventListener('click', () => {
            maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
            // Disable process button since mask is now empty
            document.getElementById('process-btn').disabled = true;
            console.log('🗑️ Mask cleared');
        });
        
        // Process image
        document.getElementById('process-btn').addEventListener('click', processImage);
        
        async function processImage() {
            if (!currentImage || !currentDocId) return;

            // Check if mask has any content
            const maskImageData = maskCtx.getImageData(0, 0, maskCanvas.width, maskCanvas.height);
            const maskPixels = maskImageData.data;
            let hasContent = false;

            // Check if any pixel has non-zero alpha (meaning something was drawn)
            for (let i = 3; i < maskPixels.length; i += 4) {
                if (maskPixels[i] > 0) {
                    hasContent = true;
                    break;
                }
            }

            if (!hasContent) {
                alert('Please mark the watermark areas first!\\n\\nYou can:\\n- Click and drag to paint over watermarks\\n- Or click Auto-detect Watermark button');
                return;
            }

            console.log('✅ Mask has content, proceeding with processing...');

            showLoading(true);
            try {
                // Get mask data
                const maskData = maskCanvas.toDataURL('image/png');
                const imageData = imageCanvas.toDataURL('image/png');

                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        doc_id: currentDocId,
                        image_data: imageData,
                        mask_data: maskData
                    })
                });

                const data = await response.json();

                if (data.error) {
                    alert(data.error);
                    return;
                }

                // Display processed image
                processedImage = new Image();
                processedImage.onload = () => {
                    imageCtx.drawImage(processedImage, 0, 0);
                    maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
                    document.getElementById('save-btn').disabled = false;
                    showLoading(false);
                };
                processedImage.src = 'data:image/png;base64,' + data.result_image;

            } catch (error) {
                console.error('Error processing image:', error);
                alert('Failed to process image');
                showLoading(false);
            }
        }
        
        // Save and mark done
        document.getElementById('save-btn').addEventListener('click', saveImage);
        
        async function saveImage() {
            if (!currentDocId) return;

            // If no processed image, save the original image
            let imageToSave;
            if (processedImage) {
                imageToSave = processedImage.src;
                console.log('💾 Saving processed image...');
            } else if (currentImage) {
                // Convert current canvas to data URL
                imageToSave = imageCanvas.toDataURL('image/png');
                console.log('💾 Saving original image (no edits made)...');
            } else {
                showToast('No image to save', 'error');
                return;
            }

            showLoading(true);
            try {
                const response = await fetch('/api/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        doc_id: currentDocId,
                        image_data: imageToSave
                    })
                });

                const data = await response.json();

                if (data.error) {
                    showToast(data.error, 'error');
                    showLoading(false);
                    return;
                }

                showToast('Image saved successfully!', 'success');
                updateStats();
                loadNextImage();

            } catch (error) {
                console.error('Error saving image:', error);
                showToast('Failed to save image', 'error');
                showLoading(false);
            }
        }
        
        // Skip image
        document.getElementById('skip-btn').addEventListener('click', async () => {
            if (!currentDocId) {
                showToast('No image loaded to skip', 'error');
                return;
            }

            showLoading(true);
            try {
                const response = await fetch('/api/skip', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ doc_id: currentDocId })
                });

                const data = await response.json();

                if (data.error) {
                    showToast(data.error, 'error');
                    showLoading(false);
                    return;
                }

                showToast('Image skipped successfully!', 'success');
                updateStats();
                loadNextImage();

            } catch (error) {
                console.error('Error skipping image:', error);
                showToast('Failed to skip image', 'error');
                showLoading(false);
            }
        });
        
        // Update stats
        async function updateStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();

                document.getElementById('total-images').textContent = data.total;
                document.getElementById('cleaned-images').textContent = data.cleaned;
                document.getElementById('skipped-images').textContent = data.skipped || 0;
                document.getElementById('pending-images').textContent = data.pending;
            } catch (error) {
                console.error('Error updating stats:', error);
            }
        }
        
        function showLoading(show) {
            document.getElementById('loading').classList.toggle('active', show);
        }

        // Toast notification function
        function showToast(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);

            // Trigger animation
            setTimeout(() => toast.classList.add('show'), 10);

            // Remove after 3 seconds
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        // Initialize
        updateStats();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Serve the main UI"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about images (only counts images with valid short_summary)"""
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        collection = get_mongo_client()

        # Build base match query with multi-tenant filter
        base_match = {
            'image': {'$ne': None},
            'short_summary': {'$ne': None, '$ne': ''}
        }
        match_query = build_multi_tenant_query(base_match, customer_id=customer_id)

        # Count only images that have valid short_summary (min 30 words)
        # Use aggregation to filter by word count
        pipeline_total = [
            {
                '$match': match_query
            },
            {
                '$addFields': {
                    'word_count': {
                        '$size': {
                            '$split': [
                                {'$trim': {'input': '$short_summary'}},
                                ' '
                            ]
                        }
                    }
                }
            },
            {
                '$match': {
                    'word_count': {'$gte': 30}  # Minimum 30 words requirement
                }
            },
            {
                '$count': 'total'
            }
        ]

        # Build match query for cleaned images
        cleaned_match = {
            'image': {'$ne': None},
            'clean_image': {'$ne': None},
            'short_summary': {'$ne': None, '$ne': ''}
        }
        cleaned_match_query = build_multi_tenant_query(cleaned_match, customer_id=customer_id)

        pipeline_cleaned = [
            {
                '$match': cleaned_match_query
            },
            {
                '$addFields': {
                    'word_count': {
                        '$size': {
                            '$split': [
                                {'$trim': {'input': '$short_summary'}},
                                ' '
                            ]
                        }
                    }
                }
            },
            {
                '$match': {
                    'word_count': {'$gte': 30}  # Minimum 30 words requirement
                }
            },
            {
                '$count': 'total'
            }
        ]

        # Build match query for skipped images
        skipped_match = {
            'image': {'$ne': None},
            'watermark_skipped': True,
            'short_summary': {'$ne': None, '$ne': ''}
        }
        skipped_match_query = build_multi_tenant_query(skipped_match, customer_id=customer_id)

        # Count skipped images (with watermark_skipped: true)
        pipeline_skipped = [
            {
                '$match': skipped_match_query
            },
            {
                '$addFields': {
                    'word_count': {
                        '$size': {
                            '$split': [
                                {'$trim': {'input': '$short_summary'}},
                                ' '
                            ]
                        }
                    }
                }
            },
            {
                '$match': {
                    'word_count': {'$gte': 30}  # Minimum 30 words requirement
                }
            },
            {
                '$count': 'total'
            }
        ]

        total_result = list(collection.aggregate(pipeline_total))
        cleaned_result = list(collection.aggregate(pipeline_cleaned))
        skipped_result = list(collection.aggregate(pipeline_skipped))

        total = total_result[0]['total'] if total_result else 0
        cleaned = cleaned_result[0]['total'] if cleaned_result else 0
        skipped = skipped_result[0]['total'] if skipped_result else 0
        pending = total - cleaned - skipped  # Exclude both cleaned and skipped from pending

        return jsonify({
            'total': total,
            'cleaned': cleaned,
            'skipped': skipped,
            'pending': pending
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/images', methods=['GET'])
def list_images():
    """List all images with pagination and filtering"""
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        collection = get_mongo_client()

        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status_filter = request.args.get('status', 'all')  # all, pending, cleaned, skipped

        skip = (page - 1) * limit

        # Build match criteria
        match_criteria = {
            'image': {'$ne': None},
            'short_summary': {'$ne': None, '$ne': ''},
            'status': {'$ne': 'dont_process'}
        }

        # Apply status filter
        if status_filter == 'pending':
            match_criteria['clean_image'] = None
            match_criteria['watermark_skipped'] = {'$ne': True}
        elif status_filter == 'cleaned':
            match_criteria['clean_image'] = {'$ne': None}
        elif status_filter == 'skipped':
            match_criteria['watermark_skipped'] = True

        # Apply multi-tenant filter
        match_criteria = build_multi_tenant_query(match_criteria, customer_id=customer_id)

        # Build aggregation pipeline
        pipeline = [
            {'$match': match_criteria},
            {
                '$addFields': {
                    'word_count': {
                        '$size': {
                            '$split': [
                                {'$trim': {'input': '$short_summary'}},
                                ' '
                            ]
                        }
                    }
                }
            },
            {
                '$match': {
                    'word_count': {'$gte': 30}  # Minimum 30 words requirement
                }
            },
            {'$sort': {'created_at': -1}},  # Sort by most recently created
            {
                '$facet': {
                    'metadata': [{'$count': 'total'}],
                    'data': [
                        {'$skip': skip},
                        {'$limit': limit},
                        {
                            '$project': {
                                '_id': 1,
                                'title': 1,
                                'image': 1,
                                'clean_image': 1,
                                'watermark_skipped': 1,
                                'created_at': 1,
                                'word_count': 1
                            }
                        }
                    ]
                }
            }
        ]

        results = list(collection.aggregate(pipeline))

        if not results or not results[0]['data']:
            return jsonify({
                'images': [],
                'total': 0,
                'page': page,
                'limit': limit,
                'total_pages': 0
            })

        total = results[0]['metadata'][0]['total'] if results[0]['metadata'] else 0
        images = results[0]['data']

        # Format response
        formatted_images = []
        for doc in images:
            doc_id = str(doc['_id'])
            status = 'cleaned' if doc.get('clean_image') else ('skipped' if doc.get('watermark_skipped') else 'pending')

            formatted_images.append({
                'id': doc_id,
                'title': doc.get('title', 'Untitled'),
                'status': status,
                'image_url': f'/api/proxy-image/{doc_id}',
                'cleaned_image_url': f'/api/cleaned-image/{doc_id}' if doc.get('clean_image') else None,
                'created_at': doc.get('created_at').isoformat() if doc.get('created_at') else None,
                'word_count': doc.get('word_count', 0)
            })

        return jsonify({
            'images': formatted_images,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })
    except Exception as e:
        logger.error(f"Error listing images: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/next-image', methods=['GET'])
def get_next_image():
    """Get next image that needs cleaning (sorted by most recent first)"""
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        collection = get_mongo_client()

        # Get optional exclude_id parameter to skip current image
        exclude_id = request.args.get('exclude_id')

        # Find first document with:
        # 1. Has image but no clean_image
        # 2. Has short_summary field that is not empty/null
        # 3. short_summary has at least 30 words (minimum requirement)
        # 4. Not marked as skipped
        # 5. Status is not 'dont_process'
        # 6. Not the currently displayed image (if exclude_id provided)
        # Sorted by created_at descending (most recent first)

        # Build match criteria
        match_criteria = {
            'image': {'$ne': None},
            'clean_image': None,
            'short_summary': {'$ne': None, '$ne': ''},
            'watermark_skipped': {'$ne': True},
            'status': {'$ne': 'dont_process'}
        }

        # Exclude current image if provided
        if exclude_id:
            try:
                match_criteria['_id'] = {'$ne': ObjectId(exclude_id)}
                logger.info(f"🔍 Excluding current image from query: {exclude_id}")
            except Exception as e:
                logger.warning(f"⚠️ Invalid exclude_id format: {exclude_id}, error: {e}")

        # Apply multi-tenant filter
        match_criteria = build_multi_tenant_query(match_criteria, customer_id=customer_id)

        # Use aggregation pipeline to filter by word count
        pipeline = [
            {
                '$match': match_criteria
            },
            {
                '$addFields': {
                    'word_count': {
                        '$size': {
                            '$split': [
                                {'$trim': {'input': '$short_summary'}},
                                ' '
                            ]
                        }
                    }
                }
            },
            {
                '$match': {
                    'word_count': {'$gte': 30}  # Minimum 30 words requirement
                }
            },
            {
                '$sort': {'created_at': -1}  # Most recent first
            },
            {
                '$limit': 1
            }
        ]

        results = list(collection.aggregate(pipeline))

        if not results:
            return jsonify({
                'error': 'No more images to clean! All images either lack proper short_summary (min 30 words) or are already cleaned.'}), 404

        doc = results[0]
        word_count = doc.get('word_count', 0)
        logger.info(
            f"📸 Loading image: {doc.get('title', 'Untitled')} (created: {doc.get('created_at')}, short_summary: {word_count} words)")

        return jsonify({
            'doc_id': str(doc['_id']),
            'title': doc.get('title', 'Untitled'),
            'image_url': f'/api/proxy-image/{str(doc["_id"])}',  # Use proxy endpoint
            'original_image_url': doc.get('image')  # Original image URL from database
        })
    except Exception as e:
        logger.error(f"Error getting next image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/proxy-image/<doc_id>', methods=['GET'])
def proxy_image(doc_id):
    """Proxy external images to avoid CORS issues"""
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        collection = get_mongo_client()

        # Get document with multi-tenant filter
        base_query = {'_id': ObjectId(doc_id)}
        query = build_multi_tenant_query(base_query, customer_id=customer_id)
        doc = collection.find_one(query)
        if not doc or 'image' not in doc:
            return jsonify({'error': 'Image not found'}), 404

        image_url = doc['image']

        # Download image with proper headers to avoid 403 errors
        logger.info(f"📥 Proxying image from: {image_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': image_url,
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(image_url, timeout=30, headers=headers)
        response.raise_for_status()

        # Return image with proper content type
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        return send_file(
            io.BytesIO(response.content),
            mimetype=content_type,
            as_attachment=False
        )

    except Exception as e:
        logger.error(f"Error proxying image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/process', methods=['POST'])
def process_image():
    """Process image to remove watermark"""
    try:
        data = request.json
        doc_id = data['doc_id']
        image_data = data['image_data']
        mask_data = data['mask_data']

        logger.info(f"🔄 Processing image for doc_id: {doc_id}")

        # Decode base64 images
        image_bytes = base64.b64decode(image_data.split(',')[1])
        mask_bytes = base64.b64decode(mask_data.split(',')[1])

        # Load images
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        mask_img = Image.open(io.BytesIO(mask_bytes)).convert('RGBA')

        logger.info(f"📐 Image size: {image.size}, Mask size: {mask_img.size}")

        # Convert mask to grayscale and extract red channel (our mask color)
        # The mask canvas has red semi-transparent marks, we need to convert to binary
        mask_np = np.array(mask_img)

        # Extract red channel and alpha channel
        red_channel = mask_np[:, :, 0]  # Red channel
        alpha_channel = mask_np[:, :, 3]  # Alpha channel

        # Create binary mask: white (255) where there's red color, black (0) elsewhere
        # Combine red and alpha to detect painted areas
        binary_mask = np.where((red_channel > 100) & (alpha_channel > 0), 255, 0).astype(np.uint8)

        non_zero_pixels = np.count_nonzero(binary_mask)
        logger.info(
            f"🎭 Mask stats - min: {binary_mask.min()}, max: {binary_mask.max()}, non-zero pixels: {non_zero_pixels}")

        # Validate that mask has content
        if non_zero_pixels == 0:
            logger.warning("⚠️ Mask is empty - no watermark areas marked!")
            return jsonify({'error': 'Please mark the watermark areas before processing'}), 400

        # Convert image to numpy
        image_np = np.array(image)

        logger.info(f"🖼️ Image array shape: {image_np.shape}, dtype: {image_np.dtype}")
        logger.info(f"🎭 Mask array shape: {binary_mask.shape}, dtype: {binary_mask.dtype}")

        # Ensure image is uint8
        if image_np.dtype != np.uint8:
            image_np = (image_np * 255).astype(np.uint8)

        # Debug: Save mask to verify what we're processing
        try:
            debug_mask_path = f'/app/output/debug_mask_{doc_id}.png'
            Image.fromarray(binary_mask).save(debug_mask_path)
            logger.info(f"🐛 Debug mask saved to: {debug_mask_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not save debug mask: {e}")

        # Process with IOPaint
        result_np = remove_watermark(image_np, binary_mask)

        logger.info(f"✅ Processing complete, result shape: {result_np.shape}")

        # Ensure result is uint8
        if result_np.dtype != np.uint8:
            result_np = np.clip(result_np, 0, 255).astype(np.uint8)

        # Convert back to image (RGBA for transparency support)
        if result_np.shape[2] == 4:
            # RGBA image with transparency
            result_image = Image.fromarray(result_np, mode='RGBA')
            logger.info("📸 Created RGBA image with transparency")
        else:
            # RGB image
            result_image = Image.fromarray(result_np, mode='RGB')
            logger.info("📸 Created RGB image")

        # Encode to base64 as PNG (supports transparency)
        output = io.BytesIO()
        result_image.save(output, format='PNG')
        output.seek(0)
        result_base64 = base64.b64encode(output.read()).decode('utf-8')

        return jsonify({
            'result_image': result_base64
        })
    except Exception as e:
        logger.error(f"❌ Error processing image: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/save', methods=['POST'])
def save_image():
    """Save cleaned image and update MongoDB"""
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        data = request.json
        doc_id = data['doc_id']
        image_data = data['image_data']

        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes))

        # Ensure output directory exists
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            logger.info(f"📁 Output directory ensured: {OUTPUT_DIR}")
        except Exception as dir_error:
            logger.error(f"❌ Failed to create output directory {OUTPUT_DIR}: {dir_error}")
            raise

        # Save to file
        filename = f"{doc_id}_cleaned.png"
        filepath = os.path.join(OUTPUT_DIR, filename)

        try:
            image.save(filepath, 'PNG')
            logger.info(f"💾 Image saved to: {filepath}")
        except Exception as save_error:
            logger.error(f"❌ Failed to save image to {filepath}: {save_error}")
            raise

        # Update MongoDB with multi-tenant filter
        collection = get_mongo_client()

        # Prepare update data with audit tracking
        update_data = {
            'clean_image': filepath,
            'clean_image_updated_at': datetime.utcnow()
        }
        prepare_update_document(update_data, user_id=user_id or 'system')

        base_query = {'_id': ObjectId(doc_id)}
        query = build_multi_tenant_query(base_query, customer_id=customer_id)

        collection.update_one(query, {'$set': update_data})

        logger.info(f"✅ Saved cleaned image and updated MongoDB: {filepath}")

        return jsonify({
            'success': True,
            'filepath': filepath
        })
    except Exception as e:
        logger.error(f"❌ Error saving image: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/replace-image', methods=['POST'])
def replace_image():
    """Replace the original image URL for an article"""
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        data = request.json
        doc_id = data.get('doc_id')
        new_image_url = data.get('image_url')

        if not doc_id:
            return jsonify({'error': 'doc_id is required'}), 400

        if not new_image_url:
            return jsonify({'error': 'image_url is required'}), 400

        collection = get_mongo_client()

        # Prepare update data with audit tracking
        update_data = {
            'image': new_image_url,
            'image_updated_at': datetime.utcnow()
        }
        prepare_update_document(update_data, user_id=user_id or 'system')

        # Update document with new image URL and multi-tenant filter
        base_query = {'_id': ObjectId(doc_id)}
        query = build_multi_tenant_query(base_query, customer_id=customer_id)

        result = collection.update_one(query, {'$set': update_data})

        if result.matched_count == 0:
            return jsonify({'error': 'Document not found'}), 404

        logger.info(f"✓ Image URL replaced for doc_id: {doc_id}")
        return jsonify({
            'success': True,
            'message': 'Image URL replaced successfully',
            'image_url': f'/api/proxy-image/{doc_id}'
        })
    except Exception as e:
        logger.error(f"Error replacing image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/skip', methods=['POST'])
def skip_image():
    """Skip an image (mark it as skipped so it won't be shown again)"""
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')
        user_id = user_context.get('user_id')

        data = request.json
        doc_id = data.get('doc_id')

        if not doc_id:
            return jsonify({'error': 'doc_id is required'}), 400

        collection = get_mongo_client()

        # Prepare update data with audit tracking
        update_data = {
            'watermark_skipped': True,
            'watermark_skipped_at': datetime.now()
        }
        prepare_update_document(update_data, user_id=user_id or 'system')

        # Update document to mark as skipped with multi-tenant filter
        base_query = {'_id': ObjectId(doc_id)}
        query = build_multi_tenant_query(base_query, customer_id=customer_id)

        result = collection.update_one(query, {'$set': update_data})

        if result.matched_count == 0:
            return jsonify({'error': 'Document not found'}), 404

        logger.info(f"✓ Image skipped: {doc_id}")
        return jsonify({'success': True, 'message': 'Image skipped successfully'})

    except Exception as e:
        logger.error(f"Error skipping image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/cleaned-image/<doc_id>', methods=['GET'])
def get_cleaned_image(doc_id):
    """Get cleaned image for a news article by document ID"""
    try:
        # Extract user context from headers for multi-tenancy
        user_context = extract_user_context_from_headers(request.headers)
        customer_id = user_context.get('customer_id')

        collection = get_mongo_client()

        # Get document with multi-tenant filter
        base_query = {'_id': ObjectId(doc_id)}
        query = build_multi_tenant_query(base_query, customer_id=customer_id)
        doc = collection.find_one(query)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404

        # Check if cleaned image exists
        if 'clean_image' not in doc or not doc['clean_image']:
            return jsonify({'error': 'No cleaned image available for this document'}), 404

        # Get the cleaned image file path
        filepath = doc['clean_image']

        # Check if file exists
        if not os.path.exists(filepath):
            logger.error(f"Cleaned image file not found: {filepath}")
            return jsonify({'error': 'Cleaned image file not found on disk'}), 404

        # Return the image file
        return send_file(
            filepath,
            mimetype='image/png',
            as_attachment=False,
            download_name=f"{doc_id}_cleaned.png"
        )

    except Exception as e:
        logger.error(f"Error retrieving cleaned image: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB
        get_mongo_client()

        # Check model
        get_model()

        return jsonify({
            'status': 'healthy',
            'service': 'iopaint-ui',
            'model': 'lama',
            'device': str(_device) if _device else 'not_loaded',
            'mongodb': 'connected'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    logger.info(f"🚀 Starting IOPaint UI Service on port {FLASK_PORT}...")
    logger.info(f"📁 Output directory: {OUTPUT_DIR}")
    logger.info(f"🔌 MongoDB URL: {MONGODB_URL}")

    app.run(
        host='0.0.0.0',
        port=FLASK_PORT,
        debug=False
    )
