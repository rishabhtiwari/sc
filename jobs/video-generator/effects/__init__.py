"""
Video Effects Module - Pluggable effects system for video generation
"""

from .base_effect import BaseEffect
from .ken_burns_effect import KenBurnsEffect
from .fade_text_effect import FadeTextEffect
from .effects_factory import EffectsFactory

__all__ = ['BaseEffect', 'KenBurnsEffect', 'FadeTextEffect', 'EffectsFactory']

