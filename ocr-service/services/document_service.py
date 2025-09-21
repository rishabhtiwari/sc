"""
Document Service - Handles document processing and conversion
"""

import os
import time
import tempfile
import gc
from typing import Dict, Any, List
from werkzeug.datastructures import FileStorage

from .ocr_service import OCRService
from models.ocr_result import OCRResult
from models.document_info import DocumentInfo
from utils.logger import get_logger

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("⚠️ pdf2image not available. Install with: pip install pdf2image")

try:
    from docx import Document
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False
    print("⚠️ python-docx not available. Install with: pip install python-docx")


class DocumentService:
    """
    Service for handling document processing and OCR conversion
    """
    
    def __init__(self):
        """
        Initialize document service
        """
        self.ocr_service = OCRService()
        self.supported_image_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
        self.supported_document_formats = {'.pdf', '.docx'}
        
        print("📄 Document Service initialized")
    
    def is_supported_format(self, filename: str) -> bool:
        """
        Check if file format is supported
        
        Args:
            filename (str): Name of the file
            
        Returns:
            bool: True if format is supported
        """
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.supported_image_formats or ext in self.supported_document_formats
    
    def get_file_type(self, filename: str) -> str:
        """
        Get file type category
        
        Args:
            filename (str): Name of the file
            
        Returns:
            str: File type ('image', 'pdf', 'docx', 'unknown')
        """
        ext = os.path.splitext(filename.lower())[1]
        
        if ext in self.supported_image_formats:
            return 'image'
        elif ext == '.pdf':
            return 'pdf'
        elif ext == '.docx':
            return 'docx'
        else:
            return 'unknown'
    
    def process_document(self, file: FileStorage, language: str = 'en', output_format: str = 'text') -> Dict[str, Any]:
        """
        Process document and extract text using OCR
        
        Args:
            file (FileStorage): Uploaded file
            language (str): OCR language
            output_format (str): Output format ('text', 'json', 'markdown')
            
        Returns:
            Dict[str, Any]: Processing results
        """
        if not file or not file.filename:
            return {
                "status": "error",
                "error": "No file provided"
            }
        
        if not self.is_supported_format(file.filename):
            return {
                "status": "error",
                "error": f"Unsupported file format. Supported: {', '.join(self.supported_image_formats | self.supported_document_formats)}"
            }
        
        # Change OCR language if needed
        if language != self.ocr_service.lang:
            if not self.ocr_service.change_language(language):
                return {
                    "status": "error",
                    "error": f"Failed to set OCR language to: {language}"
                }
        
        file_type = self.get_file_type(file.filename)
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save uploaded file
                temp_file_path = os.path.join(temp_dir, file.filename)
                file.save(temp_file_path)
                
                print(f"📁 Saved file to: {temp_file_path}")
                
                # Process based on file type
                if file_type == 'image':
                    result = self._process_image(temp_file_path, output_format)
                elif file_type == 'pdf':
                    result = self._process_pdf(temp_file_path, temp_dir, output_format)
                elif file_type == 'docx':
                    result = self._process_docx(temp_file_path, output_format)
                else:
                    result = {
                        "status": "error",
                        "error": f"Unsupported file type: {file_type}"
                    }
                
                # Add metadata
                if result.get('status') == 'success':
                    result.update({
                        "filename": file.filename,
                        "file_type": file_type,
                        "language": language,
                        "output_format": output_format,
                        "timestamp": int(time.time() * 1000)
                    })
                
                return result
                
        except Exception as e:
            print(f"❌ Document processing error: {str(e)}")
            return {
                "status": "error",
                "error": f"Document processing failed: {str(e)}"
            }

    def _process_image(self, image_path: str, output_format: str) -> Dict[str, Any]:
        """Process single image file"""
        print(f"🖼️ Processing image: {os.path.basename(image_path)}")
        result = self.ocr_service.extract_text_from_image(image_path)
        if result['status'] == 'success':
            result['text'] = self._format_output(result['text'], output_format)
        return result

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Try to extract text directly from PDF without OCR"""
        if not PYPDF2_AVAILABLE:
            return ""

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"⚠️ Direct PDF text extraction failed: {str(e)}")
            return ""

    def _process_pdf(self, pdf_path: str, temp_dir: str, output_format: str) -> Dict[str, Any]:
        """Process PDF file - try direct text extraction first, then OCR as fallback"""
        print(f"📄 Processing PDF: {os.path.basename(pdf_path)}")

        # First, try to extract text directly from PDF (much faster and less memory)
        direct_text = self._extract_text_from_pdf(pdf_path)
        if direct_text and len(direct_text.strip()) > 10:  # If we got meaningful text
            print(f"✅ Extracted text directly from PDF (no OCR needed)")
            return {
                "status": "success",
                "text": self._format_output(direct_text, output_format),
                "confidence": 1.0,
                "method": "direct_extraction",
                "pages_processed": "all"
            }

        # Fallback to OCR if no text was found or text is too short
        print(f"📄 No extractable text found, falling back to OCR...")
        if not PDF2IMAGE_AVAILABLE:
            return {"status": "error", "error": "PDF OCR processing not available"}

        try:
            # Get page count first without loading all images
            from pdf2image import pdfinfo_from_path
            info = pdfinfo_from_path(pdf_path)
            total_pages = info["Pages"]
            print(f"📚 Processing {total_pages} pages...")

            all_text = []
            total_confidence = 0.0

            # Process pages one at a time to reduce memory usage
            for page_num in range(1, total_pages + 1):
                print(f"📄 Processing page {page_num}/{total_pages}")

                # Convert only one page at a time with lower DPI to reduce memory usage
                images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=150)
                if not images:
                    continue

                image = images[0]  # Only one image since we're processing one page
                image_path = os.path.join(temp_dir, f"page_{page_num}.png")
                image.save(image_path, 'PNG')
                print(f"🔍 Processing image: {image_path}")

                # Process this page
                page_result = self.ocr_service.extract_text_from_image(image_path)
                if page_result['status'] == 'success':
                    all_text.append(page_result['text'])
                    total_confidence += page_result.get('confidence', 0.0)

                # Clean up the image from memory and disk
                image.close()
                if os.path.exists(image_path):
                    os.remove(image_path)

                # Force garbage collection to free memory
                gc.collect()

            # Combine all text
            combined_text = '\n\n'.join(all_text)
            avg_confidence = total_confidence / total_pages if total_pages > 0 else 0.0

            return {
                "status": "success",
                "text": self._format_output(combined_text, output_format),
                "confidence": avg_confidence,
                "pages_processed": total_pages,
                "method": "ocr"
            }
        except Exception as e:
            return {"status": "error", "error": f"PDF processing failed: {str(e)}"}

    def _process_docx(self, docx_path: str, output_format: str) -> Dict[str, Any]:
        """Process DOCX file (extract existing text)"""
        if not PYTHON_DOCX_AVAILABLE:
            return {"status": "error", "error": "DOCX processing not available"}

        try:
            doc = Document(docx_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            extracted_text = '\n\n'.join(paragraphs)

            return {
                "status": "success",
                "text": self._format_output(extracted_text, output_format),
                "confidence": 1.0,
                "paragraphs": len(paragraphs),
                "method": "text_extraction"
            }
        except Exception as e:
            return {"status": "error", "error": f"DOCX processing failed: {str(e)}"}

    def _format_output(self, text: str, output_format: str) -> str:
        """Format output text according to specified format"""
        if output_format == 'json':
            import json
            return json.dumps({
                "extracted_text": text,
                "word_count": len(text.split()),
                "character_count": len(text)
            }, indent=2)
        elif output_format == 'markdown':
            lines = text.split('\n')
            markdown_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    if len(line) < 50 and not line.endswith(('.', '!', '?', ':')):
                        markdown_lines.append(f"## {line}")
                    else:
                        markdown_lines.append(line)
                else:
                    markdown_lines.append("")
            return '\n'.join(markdown_lines)
        else:
            return text
