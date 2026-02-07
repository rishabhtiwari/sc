"""
LLM-based YouTube Title Generator
Uses LLM to create engaging, clickable video titles
"""
import logging
import requests
from typing import Dict, Any, Optional


class TitleGenerator:
    """Generate YouTube titles using LLM"""
    
    def __init__(self, llm_service_url: str = "http://ichat-llm-service:8083"):
        self.logger = logging.getLogger(__name__)
        self.llm_service_url = llm_service_url
        
    def generate_title(self, news_doc: Dict[str, Any]) -> str:
        """
        Generate engaging YouTube title using LLM
        
        Args:
            news_doc: MongoDB news document
            
        Returns:
            Generated title (max 100 characters)
        """
        original_title = news_doc.get('title', '')
        short_summary = news_doc.get('short_summary', '')
        category = news_doc.get('category', 'general')
        
        # Build content for LLM
        content = f"Original Title: {original_title}\n"
        if short_summary:
            content += f"Summary: {short_summary}\n"
        
        # Create prompt for LLM
        prompt = self._build_prompt(content, category)
        
        # Call LLM service
        try:
            llm_title = self._call_llm(prompt)
            if llm_title:
                # Ensure it's within YouTube's 100 char limit
                if len(llm_title) > 100:
                    llm_title = llm_title[:97] + '...'
                return llm_title
        except Exception as e:
            self.logger.error(f"Failed to generate LLM title: {str(e)}")
        
        # Fallback to enhanced original title
        return self._build_fallback_title(news_doc)
    
    def _build_prompt(self, content: str, category: str) -> str:
        """Build prompt for LLM"""
        
        # Category-specific guidance
        category_guidance = {
            'business': 'Focus on financial impact, market movements, or economic significance',
            'entertainment': 'Highlight celebrity names, drama, or exclusive content',
            'health': 'Emphasize health benefits, risks, or breakthrough discoveries',
            'science': 'Focus on innovation, discovery, or technological advancement',
            'sports': 'Highlight teams, players, scores, or dramatic moments',
            'technology': 'Focus on innovation, new features, or tech impact',
            'politics': 'Highlight key figures, policy changes, or political drama'
        }
        
        guidance = category_guidance.get(category, 'Focus on the most newsworthy aspect')
        
        prompt = f"""You are a professional YouTube content creator specializing in news videos. Create an engaging, clickable title for a news video.

News Information:
{content}

Category: {category}
Guidance: {guidance}

Requirements:
1. Maximum 100 characters (count carefully)
2. Make it engaging and clickable (use power words)
3. Front-load the most important keywords
4. Use title case (capitalize major words)
5. Include numbers if relevant (e.g., "Top 5", "₹1000 Crore")
6. Add emotional triggers where appropriate (Breaking, Shocking, Exclusive, etc.)
7. Be accurate - don't exaggerate or mislead
8. Do NOT use clickbait or false information
9. Do NOT include emojis (those will be added separately)
10. Do NOT mention character count in the output

Examples of good titles:
- "Breaking: Stock Market Crashes 500 Points Amid Global Concerns"
- "India Wins Cricket World Cup Final in Thrilling Last-Over Finish"
- "New AI Technology Detects Cancer with 99% Accuracy"
- "₹10,000 Crore Scam Exposed: Top Officials Under Investigation"

Write ONLY the title itself, nothing else:"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """
        Call LLM service to generate title
        
        Args:
            prompt: Prompt for LLM
            
        Returns:
            Generated title or None if failed
        """
        try:
            response = requests.post(
                f"{self.llm_service_url}/generate",
                json={
                    "prompt": prompt,
                    "max_tokens": 50,
                    "temperature": 0.8,  # Higher temperature for more creative titles
                    "stop": ["\n"]
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_title = result.get('response', '').strip()
                
                # Remove quotes if LLM added them
                generated_title = generated_title.strip('"\'')
                
                # Validate length
                if len(generated_title) <= 100 and len(generated_title) > 10:
                    self.logger.info(f"Generated title: {generated_title} ({len(generated_title)} chars)")
                    return generated_title
                else:
                    self.logger.warning(f"Title length out of range: {len(generated_title)} chars")
                    if len(generated_title) > 100:
                        return generated_title[:97] + '...'
                    return None
            else:
                self.logger.error(f"LLM service returned status {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("LLM service timeout")
            return None
        except Exception as e:
            self.logger.error(f"Error calling LLM service: {str(e)}")
            return None
    
    def _build_fallback_title(self, news_doc: Dict[str, Any]) -> str:
        """Build enhanced fallback title if LLM fails"""
        original_title = news_doc.get('title', 'Untitled')
        category = news_doc.get('category', 'general')
        
        # Truncate if too long (leave room for prefix)
        max_title_length = 90
        if len(original_title) > max_title_length:
            original_title = original_title[:max_title_length] + '...'
        
        # Add category emoji prefix
        category_prefixes = {
            'business': '💼',
            'entertainment': '🎬',
            'health': '🏥',
            'science': '🔬',
            'sports': '⚽',
            'technology': '💻',
            'politics': '🏛️'
        }
        
        prefix = category_prefixes.get(category, '📰')
        
        # Build final title
        final_title = f"{prefix} {original_title}"
        
        # Ensure within YouTube's 100 char limit
        if len(final_title) > 100:
            final_title = final_title[:97] + '...'
        
        return final_title

