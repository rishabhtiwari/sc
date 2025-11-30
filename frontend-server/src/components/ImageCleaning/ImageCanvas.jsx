import React, { useRef, useEffect, useState } from 'react';

/**
 * Image Canvas Component - Canvas for displaying and editing images
 */
const ImageCanvas = ({ 
  image, 
  brushSize, 
  onMaskChange,
  clearMask,
  autoDetect 
}) => {
  const imageCanvasRef = useRef(null);
  const maskCanvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Load image onto canvas
  useEffect(() => {
    console.log('[ImageCanvas] useEffect triggered, image:', image ? 'present' : 'null');
    if (!image) {
      setImageLoaded(false);
      return;
    }

    const imageCanvas = imageCanvasRef.current;
    const maskCanvas = maskCanvasRef.current;

    if (!imageCanvas || !maskCanvas) {
      console.error('[ImageCanvas] Canvas refs not available');
      return;
    }

    const imageCtx = imageCanvas.getContext('2d');
    const maskCtx = maskCanvas.getContext('2d');

    const img = new Image();
    img.onload = () => {
      console.log('[ImageCanvas] Image loaded in canvas, dimensions:', img.width, 'x', img.height);
      // Set canvas dimensions
      imageCanvas.width = img.width;
      imageCanvas.height = img.height;
      maskCanvas.width = img.width;
      maskCanvas.height = img.height;

      // Draw image
      imageCtx.drawImage(img, 0, 0);
      console.log('[ImageCanvas] Image drawn to canvas');

      // Clear mask
      maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);

      setImageLoaded(true);
    };
    img.onerror = (err) => {
      console.error('[ImageCanvas] Failed to load image in canvas:', err);
    };
    img.src = image;
  }, [image]);

  // Clear mask when requested
  useEffect(() => {
    if (clearMask && imageLoaded) {
      const maskCanvas = maskCanvasRef.current;
      const maskCtx = maskCanvas.getContext('2d');
      maskCtx.clearRect(0, 0, maskCanvas.width, maskCanvas.height);
      onMaskChange(false);
    }
  }, [clearMask, imageLoaded, onMaskChange]);

  // Auto-detect watermark
  useEffect(() => {
    if (autoDetect && imageLoaded) {
      const maskCanvas = maskCanvasRef.current;
      const maskCtx = maskCanvas.getContext('2d');
      const width = maskCanvas.width;
      const height = maskCanvas.height;

      // Clear existing mask
      maskCtx.clearRect(0, 0, width, height);

      // Draw common watermark areas (bottom-right, bottom-left, top-right)
      // Use RED color for mask - backend expects red channel
      maskCtx.fillStyle = 'rgba(255, 0, 0, 0.5)';

      // Bottom-right corner
      maskCtx.fillRect(width * 0.7, height * 0.85, width * 0.3, height * 0.15);

      // Bottom-left corner
      maskCtx.fillRect(0, height * 0.85, width * 0.3, height * 0.15);

      // Top-right corner
      maskCtx.fillRect(width * 0.7, 0, width * 0.3, height * 0.15);

      onMaskChange(true);
    }
  }, [autoDetect, imageLoaded, onMaskChange]);

  // Drawing functions
  const startDrawing = (e) => {
    setIsDrawing(true);
    draw(e);
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const draw = (e) => {
    if (!isDrawing && e.type !== 'mousedown' && e.type !== 'touchstart') return;

    const maskCanvas = maskCanvasRef.current;
    const maskCtx = maskCanvas.getContext('2d');
    const rect = maskCanvas.getBoundingClientRect();

    let x, y;
    if (e.type.startsWith('touch')) {
      const touch = e.touches[0];
      x = (touch.clientX - rect.left) * (maskCanvas.width / rect.width);
      y = (touch.clientY - rect.top) * (maskCanvas.height / rect.height);
    } else {
      x = (e.clientX - rect.left) * (maskCanvas.width / rect.width);
      y = (e.clientY - rect.top) * (maskCanvas.height / rect.height);
    }

    // Use RED color for mask - backend expects red channel
    maskCtx.fillStyle = 'rgba(255, 0, 0, 0.5)';
    maskCtx.beginPath();
    maskCtx.arc(x, y, brushSize, 0, Math.PI * 2);
    maskCtx.fill();

    onMaskChange(true);
  };

  // Get canvas data URLs
  const getCanvasData = () => {
    const imageCanvas = imageCanvasRef.current;
    const maskCanvas = maskCanvasRef.current;
    
    return {
      imageData: imageCanvas.toDataURL('image/png'),
      maskData: maskCanvas.toDataURL('image/png'),
    };
  };

  // Expose getCanvasData to parent
  useEffect(() => {
    if (imageLoaded) {
      window.getImageCanvasData = getCanvasData;
    }
  }, [imageLoaded]);

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-gray-100 rounded-lg overflow-hidden">
      {!image ? (
        <div className="text-center text-gray-400 p-8">
          <div className="text-6xl mb-4">🖼️</div>
          <p className="text-lg">No image loaded</p>
          <p className="text-sm mt-2">Click "Load Next Image" to start</p>
        </div>
      ) : (
        <div className="relative w-full h-full flex items-center justify-center p-4">
          <div className="relative" style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <canvas
              ref={imageCanvasRef}
              className="block"
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                width: 'auto',
                height: 'auto',
                objectFit: 'contain'
              }}
            />
            <canvas
              ref={maskCanvasRef}
              className="absolute cursor-crosshair"
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                width: 'auto',
                height: 'auto',
                objectFit: 'contain',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)'
              }}
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
              onTouchStart={startDrawing}
              onTouchMove={draw}
              onTouchEnd={stopDrawing}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageCanvas;

