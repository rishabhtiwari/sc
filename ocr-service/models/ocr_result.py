"""
OCR Result Model
"""

import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class OCRResult:
    """
    Model for OCR processing results
    """
    text: str
    confidence_scores: List[float]
    processing_time: float
    language: str
    pages_processed: int
    status: str = "success"
    error: Optional[str] = None
    timestamp: Optional[int] = None
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = int(time.time() * 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        
        Returns:
            Dictionary representation
        """
        return asdict(self)
    
    def to_text_format(self) -> str:
        """
        Get text-only format
        
        Returns:
            Extracted text
        """
        return self.text
    
    def to_json_format(self) -> Dict[str, Any]:
        """
        Get JSON format with metadata
        
        Returns:
            Dictionary with full metadata
        """
        return self.to_dict()
    
    def to_markdown_format(self) -> str:
        """
        Get markdown format
        
        Returns:
            Text formatted as markdown
        """
        lines = self.text.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append('')
                continue
            
            # Simple heuristics for markdown formatting
            if len(line) < 50 and not line.endswith('.') and not line.endswith(','):
                # Likely a heading
                markdown_lines.append(f"## {line}")
            elif line.startswith('•') or line.startswith('-'):
                # List item
                markdown_lines.append(f"- {line[1:].strip()}")
            else:
                # Regular paragraph
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)
    
    @property
    def average_confidence(self) -> float:
        """
        Get average confidence score
        
        Returns:
            Average confidence (0.0 to 1.0)
        """
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)
    
    @property
    def character_count(self) -> int:
        """
        Get character count
        
        Returns:
            Number of characters in extracted text
        """
        return len(self.text)
    
    @property
    def word_count(self) -> int:
        """
        Get word count
        
        Returns:
            Number of words in extracted text
        """
        return len(self.text.split())
    
    @classmethod
    def create_error_result(cls, error_message: str, language: str = "en") -> 'OCRResult':
        """
        Create an error result
        
        Args:
            error_message: Error description
            language: Language code
            
        Returns:
            OCRResult with error status
        """
        return cls(
            text="",
            confidence_scores=[],
            processing_time=0.0,
            language=language,
            pages_processed=0,
            status="error",
            error=error_message
        )
