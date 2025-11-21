"""
Effects Factory - Factory pattern for creating and managing video effects
"""

from typing import Dict, Any, Optional, List
from moviepy.editor import VideoClip

from .base_effect import BaseEffect
from .ken_burns_effect import KenBurnsEffect
from .fade_text_effect import FadeTextEffect
from .logo_watermark_effect import LogoWatermarkEffect
from .background_music_effect import BackgroundMusicEffect
from .transition_effect import TransitionEffect


class EffectsFactory:
    """
    Factory class for creating and managing video effects
    
    This class provides a centralized way to register, create, and apply
    video effects in a pluggable manner.
    """
    
    # Registry of available effects
    _effects_registry: Dict[str, type] = {
        'ken_burns': KenBurnsEffect,
        'fade_text': FadeTextEffect,
        'logo_watermark': LogoWatermarkEffect,
        'background_music': BackgroundMusicEffect,
        'transition': TransitionEffect,
        # Add more effects here as they are implemented
        # 'color_grading': ColorGradingEffect,
        # etc.
    }
    
    def __init__(self, logger=None):
        """
        Initialize the effects factory
        
        Args:
            logger: Logger instance for logging
        """
        self.logger = logger
        self._active_effects: Dict[str, BaseEffect] = {}
    
    @classmethod
    def register_effect(cls, effect_name: str, effect_class: type):
        """
        Register a new effect type
        
        Args:
            effect_name: Name to register the effect under
            effect_class: Effect class (must inherit from BaseEffect)
        """
        if not issubclass(effect_class, BaseEffect):
            raise ValueError(f"Effect class must inherit from BaseEffect")
        
        cls._effects_registry[effect_name] = effect_class
    
    @classmethod
    def get_available_effects(cls) -> List[str]:
        """
        Get list of available effect names
        
        Returns:
            List of registered effect names
        """
        return list(cls._effects_registry.keys())
    
    def create_effect(self, effect_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseEffect]:
        """
        Create an effect instance
        
        Args:
            effect_name: Name of the effect to create
            config: Configuration dictionary for the effect
            
        Returns:
            Effect instance or None if effect not found
        """
        if effect_name not in self._effects_registry:
            if self.logger:
                self.logger.error(f"Effect '{effect_name}' not found in registry")
            return None
        
        effect_class = self._effects_registry[effect_name]
        effect_instance = effect_class(config=config, logger=self.logger)
        
        # Store in active effects
        self._active_effects[effect_name] = effect_instance
        
        if self.logger:
            self.logger.info(f"Created effect: {effect_name}")
        
        return effect_instance
    
    def get_effect(self, effect_name: str) -> Optional[BaseEffect]:
        """
        Get an active effect instance
        
        Args:
            effect_name: Name of the effect
            
        Returns:
            Effect instance or None if not found
        """
        return self._active_effects.get(effect_name)
    
    def apply_effect(self, effect_name: str, clip: VideoClip, 
                    config: Optional[Dict[str, Any]] = None, **kwargs) -> VideoClip:
        """
        Apply an effect to a video clip
        
        Args:
            effect_name: Name of the effect to apply
            clip: Video clip to apply effect to
            config: Configuration for the effect (if creating new instance)
            **kwargs: Additional parameters to pass to the effect
            
        Returns:
            Video clip with effect applied
        """
        # Get or create effect instance
        effect = self.get_effect(effect_name)
        if effect is None:
            effect = self.create_effect(effect_name, config)
        
        if effect is None:
            if self.logger:
                self.logger.warning(f"Could not apply effect '{effect_name}', returning original clip")
            return clip
        
        # Validate parameters
        if not effect.validate_params(**kwargs):
            if self.logger:
                self.logger.warning(f"Invalid parameters for effect '{effect_name}', returning original clip")
            return clip
        
        # Apply the effect
        try:
            return effect.apply(clip, **kwargs)
        except Exception as e:
            if self.logger:
                import traceback
                self.logger.error(f"Error applying effect '{effect_name}': {str(e)}")
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            return clip
    
    def apply_effects_chain(self, clip: VideoClip, effects_config: List[Dict[str, Any]]) -> VideoClip:
        """
        Apply a chain of effects to a video clip
        
        Args:
            clip: Video clip to apply effects to
            effects_config: List of effect configurations, each containing:
                - name: Effect name
                - config: Effect configuration (optional)
                - params: Parameters to pass to apply() (optional)
                
        Returns:
            Video clip with all effects applied in sequence
        """
        result_clip = clip
        
        for effect_cfg in effects_config:
            effect_name = effect_cfg.get('name')
            if not effect_name:
                if self.logger:
                    self.logger.warning("Effect configuration missing 'name', skipping")
                continue
            
            config = effect_cfg.get('config', {})
            params = effect_cfg.get('params', {})
            
            result_clip = self.apply_effect(effect_name, result_clip, config, **params)
        
        return result_clip
    
    def get_effect_info(self, effect_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an effect
        
        Args:
            effect_name: Name of the effect
            
        Returns:
            Dictionary containing effect information or None if not found
        """
        effect = self.get_effect(effect_name)
        if effect:
            return effect.get_effect_info()
        
        # Try to create a temporary instance to get info
        if effect_name in self._effects_registry:
            temp_effect = self._effects_registry[effect_name](logger=self.logger)
            return temp_effect.get_effect_info()
        
        return None
    
    def list_all_effects_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available effects
        
        Returns:
            Dictionary mapping effect names to their information
        """
        all_info = {}
        for effect_name in self.get_available_effects():
            info = self.get_effect_info(effect_name)
            if info:
                all_info[effect_name] = info
        
        return all_info

