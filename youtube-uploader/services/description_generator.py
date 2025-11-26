"""
LLM-based YouTube Description Generator
Uses LLM to create engaging, SEO-optimized video descriptions
"""
import logging
import requests
from typing import Dict, Any, Optional


class DescriptionGenerator:
    """Generate YouTube descriptions using LLM (optional)"""

    def __init__(self, llm_service_url: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.llm_service_url = llm_service_url
        
    def generate_description(self, news_doc: Dict[str, Any]) -> str:
        """
        Generate engaging YouTube description using LLM
        
        Args:
            news_doc: MongoDB news document
            
        Returns:
            Generated description (200 words)
        """
        title = news_doc.get('title', '')
        short_summary = news_doc.get('short_summary', '')
        description = news_doc.get('description', '')
        category = news_doc.get('category', 'general')
        source = news_doc.get('source', {})
        source_name = source.get('name', 'News Source')
        
        # Build content for LLM
        content = f"Title: {title}\n\n"
        if short_summary:
            content += f"Summary: {short_summary}\n\n"
        if description:
            content += f"Details: {description[:500]}\n\n"
        
        # Create prompt for LLM
        prompt = self._build_prompt(content, category, source_name)
        
        # Call LLM service
        try:
            llm_description = self._call_llm(prompt)
            if llm_description:
                return llm_description
        except Exception as e:
            self.logger.error(f"Failed to generate LLM description: {str(e)}")
        
        # Fallback to simple description if LLM fails
        return self._build_fallback_description(news_doc)
    
    def _build_prompt(self, content: str, category: str, source_name: str) -> str:
        """Build prompt for LLM"""
        prompt = f"""You are a professional YouTube content creator specializing in news videos. Create an engaging, SEO-optimized video description for a news video.

News Content:
{content}

Category: {category}

Requirements:
1. Write EXACTLY 180-220 words (count carefully)
2. Start with a compelling hook that grabs attention in the first 2 sentences
3. Explain the key facts: who, what, when, where, why, and how
4. Use engaging language that encourages viewers to watch
5. Include relevant keywords naturally for YouTube SEO
6. Write in a professional yet conversational tone
7. Focus on the impact and significance of the news
8. Do NOT include hashtags, emojis, or calls-to-action (those will be added separately)
9. Do NOT mention word count or instructions in the output
10. Write in plain English, no markdown or formatting

Write ONLY the description itself, nothing else:"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """
        Call LLM service to generate description
        
        Args:
            prompt: Prompt for LLM
            
        Returns:
            Generated description or None if failed
        """
        try:
            response = requests.post(
                f"{self.llm_service_url}/generate",
                json={
                    "prompt": prompt,
                    "max_tokens": 500,
                    "temperature": 0.7,
                    "stop": ["\n\n\n"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Validate word count (should be around 200 words)
                word_count = len(generated_text.split())
                self.logger.info(f"Generated description: {word_count} words")
                
                if 150 <= word_count <= 300:
                    return generated_text
                else:
                    self.logger.warning(f"Description word count out of range: {word_count}")
                    return generated_text  # Return anyway, better than nothing
            else:
                self.logger.error(f"LLM service returned status {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("LLM service timeout")
            return None
        except Exception as e:
            self.logger.error(f"Error calling LLM service: {str(e)}")
            return None
    
    def _build_fallback_description(self, news_doc: Dict[str, Any]) -> str:
        """Build simple fallback description if LLM fails"""
        short_summary = news_doc.get('short_summary', '')
        description = news_doc.get('description', '')

        parts = []

        if short_summary:
            parts.append(short_summary)
        elif description:
            parts.append(description[:300])

        parts.append("\n\nStay informed with the latest news updates.")
        parts.append("This video brings you comprehensive coverage of current events and breaking news.")
        parts.append("Watch to get detailed insights and analysis of this developing story.")

        return " ".join(parts)

