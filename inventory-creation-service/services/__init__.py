"""
Services package for inventory-creation-service

Contains Flask Blueprints for different content types:
- product_service: Product-specific API endpoints
- public_service: Public file serving endpoints
- prompt_template_service: Prompt template management API endpoints
- content_generation_service: Generic LLM content generation endpoints
- (future) blog_service: Blog content API endpoints
- (future) social_media_service: Social media content API endpoints
"""

from .product_service import product_bp, init_product_service
from .public_service import public_bp, init_public_service
from .prompt_template_service import prompt_template_bp, init_prompt_template_service
from .content_generation_service import content_generation_bp, init_content_generation_service

__all__ = [
    'product_bp',
    'public_bp',
    'prompt_template_bp',
    'content_generation_bp',
    'init_product_service',
    'init_public_service',
    'init_prompt_template_service',
    'init_content_generation_service'
]

