"""Routes module for template service"""

from .template_routes import template_bp, init_routes
from .health_routes import health_bp

__all__ = ['template_bp', 'health_bp', 'init_routes']

