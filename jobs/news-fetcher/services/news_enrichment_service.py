"""
News Enrichment Service - Enriches news articles with LLM-generated summaries
"""

import requests
from datetime import datetime
from typing import Dict, List, Any
from pymongo import MongoClient

from config.settings import ArticleStatus


class NewsEnrichmentService:
    """Service to enrich news articles with AI-generated summaries"""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger

        # MongoDB connection for news database
        self.news_client = MongoClient(config.NEWS_MONGODB_URL)
        self.news_db = self.news_client[config.NEWS_MONGODB_DATABASE]
        self.news_collection = self.news_db['news_document']

        # LLM service configuration - direct service communication
        self.llm_service_url = getattr(config, 'LLM_SERVICE_URL', 'http://ichat-llm-service:8083')
        self.llm_timeout = getattr(config, 'LLM_TIMEOUT', 30)

    def enrich_news_articles(self, job_id: str, **kwargs) -> Dict[str, Any]:
        """
        Main enrichment task - processes articles with status='progress'
        
        Args:
            job_id: Job identifier for tracking
            **kwargs: Additional parameters
            
        Returns:
            Dict with enrichment results
        """
        results = {
            'job_id': job_id,
            'total_articles_found': 0,
            'articles_processed': 0,
            'articles_enriched': 0,
            'articles_failed': 0,
            'errors': []
        }

        try:
            # Step 1: Fetch all articles with status='progress'
            articles = list(self.news_collection.find({
                'status': ArticleStatus.PROGRESS.value,
                '$or': [
                    {'short_summary': {'$exists': False}},
                    {'short_summary': ''},
                    {'short_summary': None}
                ]
            }))

            results['total_articles_found'] = len(articles)
            self.logger.info(f"📰 Found {len(articles)} articles to enrich for job {job_id}")

            if not articles:
                self.logger.info(f"✅ No articles found for enrichment in job {job_id}")
                return results

            # Step 2: Process each article
            for article in articles:
                try:
                    article_id = article.get('id', 'unknown')
                    self.logger.info(f"🔍 Processing article: {article_id}")

                    # Step 3: Get content field data
                    content = article.get('content', '')
                    if not content:
                        # Fallback to description if content is empty
                        content = article.get('description', '')

                    if not content:
                        self.logger.warning(f"⚠️ Article {article_id} has no content or description to summarize")
                        results['articles_failed'] += 1
                        continue

                    # Step 4: Generate 45-70 word summary using LLM
                    summary = self._generate_summary(content, article_id)

                    if summary:
                        # Step 5: Store summary in short_summary field
                        update_result = self.news_collection.update_one(
                            {'id': article_id},
                            {
                                '$set': {
                                    'short_summary': summary,
                                    'status': ArticleStatus.COMPLETED.value,  # Step 6: Mark as completed
                                    'updated_at': datetime.utcnow(),
                                    'enriched_at': datetime.utcnow()
                                }
                            }
                        )

                        if update_result.modified_count > 0:
                            results['articles_enriched'] += 1
                            self.logger.info(f"✅ Article {article_id} enriched and marked as completed")
                        else:
                            results['articles_failed'] += 1
                            self.logger.error(f"❌ Failed to update article {article_id} in database")
                    else:
                        results['articles_failed'] += 1
                        self.logger.error(f"❌ Failed to generate summary for article {article_id}")

                    results['articles_processed'] += 1

                except Exception as e:
                    results['articles_failed'] += 1
                    error_msg = f"Error processing article {article.get('id', 'unknown')}: {str(e)}"
                    results['errors'].append(error_msg)
                    self.logger.error(error_msg)
                    continue

            self.logger.info(
                f"🏁 Enrichment completed for job {job_id}: {results['articles_enriched']} enriched, {results['articles_failed']} failed")

        except Exception as e:
            error_msg = f"Error in news enrichment for job {job_id}: {str(e)}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)

        return results

    def _generate_summary(self, content: str, article_id: str) -> str:
        """
        Generate a 45-70 word summary using LLM service with retry logic

        Args:
            content: Article content to summarize
            article_id: Article identifier for logging

        Returns:
            Generated summary (45-70 words) or empty string if failed
        """
        max_retries = 2  # Try up to 2 times

        for attempt in range(max_retries):
            try:
                # Enhanced prompt with stronger emphasis on word count
                # On retry, make the prompt even more explicit
                if attempt == 0:
                    prompt = f"""You are a professional news editor. Create a news summary following these STRICT requirements:

CRITICAL REQUIREMENTS:
1. Write EXACTLY 45-70 words - this is MANDATORY
2. Count every single word to ensure you meet this requirement
3. If your summary is less than 45 words, ADD MORE DETAILS
4. If your summary is more than 70 words, REMOVE LESS IMPORTANT DETAILS

CONTENT RULES:
- Write in plain, everyday English
- Use complete, grammatically correct sentences
- Include key facts: who, what, when, where, why
- Write ONLY the summary - no titles, labels, or explanations
- Never use code, markdown, bullets, or special formatting

Article to summarize:
{content[:2000]}

Write your 45-70 word summary now:"""
                else:
                    # More aggressive prompt for retry
                    prompt = f"""IMPORTANT: Your previous summary was TOO SHORT. You MUST write MORE words.

Create a detailed news summary with EXACTLY 50-65 words (count carefully!).

MANDATORY RULES:
- Write AT LEAST 50 words - this is CRITICAL
- Include MORE details: background, context, implications
- Use complete sentences with proper grammar
- Write ONLY the summary text - no labels or formatting

Article:
{content[:2000]}

Write your 50-65 word detailed summary:"""

                # Make request to LLM service directly (no RAG)
                payload = {
                    "query": prompt,
                    "use_rag": False,
                    "detect_code": False,
                    "temperature": 0.6 if attempt == 0 else 0.7,  # Higher temp on retry for more output
                    "max_tokens": 200  # More tokens on retry
                }

                attempt_label = f"(attempt {attempt + 1}/{max_retries})" if max_retries > 1 else ""
                self.logger.info(f"🤖 Requesting direct LLM summary {attempt_label} for article {article_id}")

                response = requests.post(
                    f"{self.llm_service_url}/llm/generate",
                    json=payload,
                    timeout=self.llm_timeout,
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'success':
                        # LLM service returns response in 'response' field
                        summary = result.get('response', '').strip()
                        if not summary and 'data' in result:
                            # Fallback to 'data' field structure
                            summary = result['data'].get('generated_text', '').strip()

                        if summary:
                            # Post-process to ensure it's not code
                            cleaned_summary = self._clean_summary(summary)
                            if cleaned_summary:
                                word_count = len(cleaned_summary.split())
                                self.logger.info(f"✅ Generated summary for article {article_id} ({word_count} words)")
                                return cleaned_summary
                            else:
                                self.logger.warning(
                                    f"⚠️ Summary validation failed for article {article_id} on attempt {attempt + 1}")
                                if attempt < max_retries - 1:
                                    self.logger.info(f"🔄 Retrying summary generation...")
                                    continue
                                else:
                                    self.logger.error(
                                        f"❌ Summary contained code/invalid content for article {article_id}")
                        else:
                            self.logger.error(f"❌ Empty summary received for article {article_id}")
                    else:
                        self.logger.error(f"❌ LLM service returned error for article {article_id}: {result}")
                else:
                    self.logger.error(
                        f"❌ LLM service request failed for article {article_id}: {response.status_code} - {response.text}")

            except requests.exceptions.Timeout:
                self.logger.error(f"⏰ LLM service timeout for article {article_id}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"🌐 LLM service request error for article {article_id}: {str(e)}")
            except Exception as e:
                self.logger.error(f"💥 Unexpected error generating summary for article {article_id}: {str(e)}")

        self.logger.error(f"❌ Failed to generate summary for article {article_id} after {max_retries} attempts")
        return ""

    def _clean_summary(self, summary: str) -> str:
        """
        Clean and validate summary to ensure it's proper text, not code

        Args:
            summary: Raw summary from LLM

        Returns:
            Cleaned summary or empty string if invalid
        """
        try:
            # Remove any markdown code blocks
            import re

            # Remove code blocks (```python, ```javascript, etc.)
            summary = re.sub(r'```[\w]*\n.*?\n```', '', summary, flags=re.DOTALL)
            summary = re.sub(r'`.*?`', '', summary)  # Remove inline code

            # Check for code-like patterns that shouldn't be in news summaries
            code_indicators = [
                'def ', 'function ', 'class ', 'import ', 'from ',
                'return ', 'print(', 'console.log', '#!/usr/bin',
                'if __name__', 'try:', 'except:', 'raise ',
                'Args:', 'Returns:', 'Parameters:', '"""', "'''",
                'def summarize', 'def get_', 'def fetch_'
            ]

            # If summary contains multiple code indicators, reject it
            code_count = sum(1 for indicator in code_indicators if indicator in summary.lower())
            if code_count >= 2:
                self.logger.warning(f"⚠️ Summary rejected: contains {code_count} code indicators")
                return ""

            # Clean up the summary
            summary = summary.strip()

            # Remove common code artifacts
            summary = re.sub(r'\n\s*\n', ' ', summary)  # Multiple newlines
            summary = re.sub(r'\s+', ' ', summary)  # Multiple spaces

            # Ensure it starts with a capital letter and ends with punctuation
            if summary and not summary[0].isupper():
                summary = summary[0].upper() + summary[1:]

            if summary and summary[-1] not in '.!?':
                summary += '.'

            # Check word count (should be 45-70 words, but accept 40-90 to be flexible)
            word_count = len(summary.split())
            if word_count < 40:  # Too short, likely not a proper summary
                self.logger.warning(f"⚠️ Summary too short: {word_count} words (minimum 40 required)")
                return ""

            if word_count > 90:  # Too long (increased from 80 to reduce false rejections)
                self.logger.warning(f"⚠️ Summary too long: {word_count} words (maximum 90 allowed)")
                return ""

            return summary

        except Exception as e:
            self.logger.error(f"💥 Error cleaning summary: {str(e)}")
            return ""

    def get_enrichment_status(self) -> Dict[str, Any]:
        """
        Get current enrichment status and statistics
        
        Returns:
            Dict with enrichment statistics
        """
        try:
            total_articles = self.news_collection.count_documents({})
            progress_articles = self.news_collection.count_documents({'status': ArticleStatus.PROGRESS.value})
            completed_articles = self.news_collection.count_documents({'status': ArticleStatus.COMPLETED.value})
            enriched_articles = self.news_collection.count_documents({
                'short_summary': {'$exists': True, '$ne': '', '$ne': None}
            })

            return {
                'total_articles': total_articles,
                'progress_articles': progress_articles,
                'completed_articles': completed_articles,
                'enriched_articles': enriched_articles,
                'pending_enrichment': progress_articles,
                'enrichment_rate': round((enriched_articles / total_articles * 100), 2) if total_articles > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Error getting enrichment status: {str(e)}")
            return {'error': str(e)}
