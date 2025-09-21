"""
Controllers package for OCR Service
"""

from .base_controller import BaseController
from .ocr_controller import OCRController
from .health_controller import HealthController

__all__ = ['BaseController', 'OCRController', 'HealthController']
