"""
OCR Service - Handles Paddle OCR operations
"""

import os
import time
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("⚠️ PaddleOCR not available. Install with: pip install paddleocr")


class OCRService:
    """
    Service for handling OCR operations using PaddleOCR
    """
    
    def __init__(self, use_gpu: bool = False, lang: str = 'en'):
        """
        Initialize OCR service
        
        Args:
            use_gpu (bool): Whether to use GPU acceleration
            lang (str): Language for OCR recognition
        """
        self.use_gpu = use_gpu
        self.lang = lang
        self.ocr_engine = None
        
        if PADDLEOCR_AVAILABLE:
            try:
                print(f"🔧 Initializing PaddleOCR (GPU: {use_gpu}, Language: {lang})...")
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=lang,
                    use_gpu=use_gpu,
                    show_log=False
                )
                print("✅ PaddleOCR initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize PaddleOCR: {e}")
                self.ocr_engine = None
        else:
            print("❌ PaddleOCR not available")
    
    def health_check(self) -> bool:
        """
        Check if OCR service is healthy
        
        Returns:
            bool: True if service is healthy
        """
        return PADDLEOCR_AVAILABLE and self.ocr_engine is not None
    
    def extract_text_from_image(self, image_path: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Extract text from image using OCR
        
        Args:
            image_path (str): Path to the image file
            confidence_threshold (float): Minimum confidence for text detection
            
        Returns:
            Dict[str, Any]: OCR results with text and metadata
        """
        if not self.health_check():
            return {
                "status": "error",
                "error": "OCR service not available",
                "text": "",
                "confidence": 0.0
            }
        
        try:
            print(f"🔍 Processing image: {image_path}")
            start_time = time.time()
            
            # Run OCR
            result = self.ocr_engine.ocr(image_path, cls=True)
            
            processing_time = time.time() - start_time
            print(f"⏱️ OCR processing completed in {processing_time:.2f}s")
            
            # Parse results
            extracted_text = []
            total_confidence = 0.0
            valid_detections = 0
            
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], tuple) else str(line[1])
                        confidence = line[1][1] if isinstance(line[1], tuple) and len(line[1]) > 1 else 1.0
                        
                        if confidence >= confidence_threshold:
                            extracted_text.append(text)
                            total_confidence += confidence
                            valid_detections += 1
            
            # Calculate average confidence
            avg_confidence = total_confidence / valid_detections if valid_detections > 0 else 0.0
            
            final_text = '\n'.join(extracted_text)
            
            print(f"📝 Extracted {len(final_text)} characters with {avg_confidence:.2f} confidence")
            
            return {
                "status": "success",
                "text": final_text,
                "confidence": avg_confidence,
                "processing_time": processing_time,
                "detections": valid_detections,
                "language": self.lang
            }
            
        except Exception as e:
            print(f"❌ OCR processing error: {str(e)}")
            return {
                "status": "error",
                "error": f"OCR processing failed: {str(e)}",
                "text": "",
                "confidence": 0.0
            }
    
    def extract_text_from_multiple_images(self, image_paths: List[str], confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Extract text from multiple images
        
        Args:
            image_paths (List[str]): List of image file paths
            confidence_threshold (float): Minimum confidence for text detection
            
        Returns:
            Dict[str, Any]: Combined OCR results
        """
        if not image_paths:
            return {
                "status": "error",
                "error": "No images provided",
                "text": "",
                "confidence": 0.0
            }
        
        print(f"📚 Processing {len(image_paths)} images...")
        
        all_text = []
        total_confidence = 0.0
        successful_extractions = 0
        
        for i, image_path in enumerate(image_paths):
            print(f"📄 Processing image {i+1}/{len(image_paths)}: {os.path.basename(image_path)}")
            
            result = self.extract_text_from_image(image_path, confidence_threshold)
            
            if result['status'] == 'success' and result['text'].strip():
                all_text.append(result['text'])
                total_confidence += result['confidence']
                successful_extractions += 1
            else:
                print(f"⚠️ Failed to extract text from {image_path}: {result.get('error', 'Unknown error')}")
        
        # Calculate overall confidence
        avg_confidence = total_confidence / successful_extractions if successful_extractions > 0 else 0.0
        
        combined_text = '\n\n'.join(all_text)
        
        print(f"✅ Successfully processed {successful_extractions}/{len(image_paths)} images")
        
        return {
            "status": "success" if successful_extractions > 0 else "error",
            "text": combined_text,
            "confidence": avg_confidence,
            "processed_images": successful_extractions,
            "total_images": len(image_paths),
            "language": self.lang
        }
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages
        
        Returns:
            List[str]: List of supported language codes
        """
        return ['en', 'ch', 'fr', 'german', 'korean', 'japan']
    
    def change_language(self, new_lang: str) -> bool:
        """
        Change OCR language
        
        Args:
            new_lang (str): New language code
            
        Returns:
            bool: True if language changed successfully
        """
        if new_lang not in self.get_supported_languages():
            print(f"❌ Unsupported language: {new_lang}")
            return False
        
        try:
            print(f"🔄 Changing OCR language to: {new_lang}")
            self.lang = new_lang
            self.ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang=new_lang,
                use_gpu=self.use_gpu,
                show_log=False
            )
            print(f"✅ Language changed to: {new_lang}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to change language: {e}")
            return False
