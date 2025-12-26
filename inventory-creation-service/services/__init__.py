"""
Services package for inventory-creation-service

Contains Flask Blueprints for different content types:
- product_service: Product-specific API endpoints
- public_service: Public file serving endpoints
- (future) blog_service: Blog content API endpoints
- (future) social_media_service: Social media content API endpoints
"""

from .product_service import product_bp, init_product_service
from .public_service import public_bp, init_public_service

__all__ = [
    'product_bp',
    'public_bp',
    'init_product_service',
    'init_public_service'
]

