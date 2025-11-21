"""
Base Effect Class - Abstract base class for all video effects
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from moviepy.editor import VideoClip, ImageClip


class BaseEffect(ABC):
    """
    Abstract base class for video effects
    
    All effects should inherit from this class and implement the apply() method
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, logger=None):
        """
        Initialize the effect
        
        Args:
            config: Configuration dictionary for the effect
            logger: Logger instance for logging
        """
        self.config = config or {}
        self.logger = logger
        self.effect_name = self.__class__.__name__
        
    @abstractmethod
    def apply(self, clip: VideoClip, **kwargs) -> VideoClip:
        """
        Apply the effect to a video clip
        
        Args:
            clip: The video clip to apply the effect to
            **kwargs: Additional parameters specific to the effect
            
        Returns:
            VideoClip with the effect applied
        """
        pass
    
    def validate_params(self, **kwargs) -> bool:
        """
        Validate effect parameters
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if parameters are valid, False otherwise
        """
        return True
    
    def get_effect_info(self) -> Dict[str, Any]:
        """
        Get information about the effect
        
        Returns:
            Dictionary containing effect metadata
        """
        return {
            'name': self.effect_name,
            'config': self.config,
            'description': self.__doc__ or 'No description available'
        }
    
    def log_info(self, message: str):
        """Log info message if logger is available"""
        if self.logger:
            self.logger.info(f"[{self.effect_name}] {message}")
    
    def log_error(self, message: str):
        """Log error message if logger is available"""
        if self.logger:
            self.logger.error(f"[{self.effect_name}] {message}")
    
    def log_warning(self, message: str):
        """Log warning message if logger is available"""
        if self.logger:
            self.logger.warning(f"[{self.effect_name}] {message}")

