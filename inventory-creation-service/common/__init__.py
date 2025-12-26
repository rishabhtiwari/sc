"""
Common utilities and base classes for inventory creation service
"""

from .utils import (
    serialize_document,
    strip_markdown_for_tts,
    parse_ai_summary_to_sections,
    get_smart_audio_config,
    get_section_speed,
    distribute_media_across_sections,
    convert_audio_url_to_proxy
)

from .base_content_generator import BaseContentGenerator

__all__ = [
    'serialize_document',
    'strip_markdown_for_tts',
    'parse_ai_summary_to_sections',
    'get_smart_audio_config',
    'get_section_speed',
    'distribute_media_across_sections',
    'convert_audio_url_to_proxy',
    'BaseContentGenerator'
]

