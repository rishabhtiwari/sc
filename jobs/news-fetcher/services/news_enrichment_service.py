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
        self.config_collection = self.news_db['enrichment_config']

        # LLM service configuration - direct service communication
        self.llm_service_url = getattr(config, 'LLM_SERVICE_URL', 'http://ichat-llm-service:8083')
        self.llm_timeout = getattr(config, 'LLM_TIMEOUT', 30)

    def enrich_news_articles(self, job_id: str, **kwargs) -> Dict[str, Any]:
        """
        Main enrichment task - processes articles with status='progress'

        Args:
            job_id: Job identifier for tracking
            **kwargs: Additional parameters (customer_id, user_id)

        Returns:
            Dict with enrichment results
        """
        from common.utils.multi_tenant_db import build_multi_tenant_query

        # Extract customer_id and user_id from kwargs
        customer_id = kwargs.get('customer_id')
        user_id = kwargs.get('user_id')

        results = {
            'job_id': job_id,
            'total_articles_found': 0,
            'articles_processed': 0,
            'articles_enriched': 0,
            'articles_failed': 0,
            'errors': []
        }

        try:
            # Step 1: Fetch all articles with status='progress' for this customer, sorted by newest first
            base_query = {
                'status': ArticleStatus.PROGRESS.value,
                '$or': [
                    {'short_summary': {'$exists': False}},
                    {'short_summary': ''},
                    {'short_summary': None}
                ]
            }

            # Add customer_id filter for multi-tenancy
            query = build_multi_tenant_query(base_query, customer_id=customer_id)

            articles = list(self.news_collection.find(query).sort('publishedAt', -1))  # Sort by publishedAt descending (newest first)

            results['total_articles_found'] = len(articles)
            self.logger.info(f"📰 Found {len(articles)} articles to enrich for job {job_id} (processing newest first)")

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

                    # Step 3.5: Clean content to remove word/char count annotations
                    content = self._clean_content(content)
                    self.logger.info(f"🧹 Cleaned content for article {article_id}")

                    # Step 4: Generate 40-75 word summary using LLM
                    summary = self._generate_summary(content, article_id)

                    if summary:
                        # Step 5: Store summary in short_summary field
                        # Use customer_id filter to ensure we only update articles for this customer
                        update_query = build_multi_tenant_query({'id': article_id}, customer_id=customer_id)

                        update_result = self.news_collection.update_one(
                            update_query,
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
        Generate a 40-75 word summary using LLM service with retry logic

        Args:
            content: Article content to summarize
            article_id: Article identifier for logging

        Returns:
            Generated summary (40-75 words) or empty string if failed
        """
        # Load configuration from database
        enrichment_config = self.config_collection.find_one({'config_type': 'enrichment'})

        # Use config values or fallback to defaults
        max_retries = enrichment_config.get('max_retries', 2) if enrichment_config else 2
        content_max_chars = enrichment_config.get('content_max_chars', 2000) if enrichment_config else 2000

        for attempt in range(max_retries):
            try:
                # Get prompt templates from config
                if attempt == 0:
                    prompt_template = enrichment_config.get('prompt_template', '') if enrichment_config else ''
                    temperature = enrichment_config.get('temperature', 0.6) if enrichment_config else 0.6
                else:
                    prompt_template = enrichment_config.get('retry_prompt_template', '') if enrichment_config else ''
                    temperature = enrichment_config.get('retry_temperature', 0.7) if enrichment_config else 0.7

                # Format prompt with content
                prompt = prompt_template.replace('{content}', content[:content_max_chars])

                # Get max_tokens from config
                max_tokens = enrichment_config.get('max_tokens', 200) if enrichment_config else 200

                # Make request to LLM service directly (no RAG)
                payload = {
                    "query": prompt,
                    "use_rag": False,
                    "detect_code": False,
                    "temperature": temperature,
                    "max_tokens": max_tokens
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

    def _clean_content(self, content: str) -> str:
        """
        Clean content by removing word/character count annotations

        Removes patterns like:
        - "... [4771 chars]" at the end of content
        - "[1200 words]", "[1200 characters]" anywhere in content

        Args:
            content: Raw content from news article

        Returns:
            Cleaned content without word/char count annotations
        """
        import re

        # Remove patterns like "... [4771 chars]" at the end
        # Pattern: optional "..." followed by space, bracket, digits, space, "chars", bracket
        content = re.sub(r'\.\.\.\s*\[\s*\d+\s+chars?\s*\]\s*$', '', content, flags=re.IGNORECASE)

        # Remove any remaining patterns like [1200 chars], [1200 words], [1200 characters]
        content = re.sub(r'\[\s*\d+\s+(?:word|char|character)s?\s*\]', '', content, flags=re.IGNORECASE)

        # Also remove patterns at the end like "1200 words" or "1200 characters" without brackets
        content = re.sub(r'\s*\d+\s+(?:word|char|character)s?\s*$', '', content, flags=re.IGNORECASE)

        return content.strip()

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

            # Check word count using configurable limits
            enrichment_config = self.config_collection.find_one({'config_type': 'enrichment'})
            min_word_count = enrichment_config.get('min_word_count', 30) if enrichment_config else 30
            max_word_count = enrichment_config.get('max_word_count', 100) if enrichment_config else 100

            word_count = len(summary.split())
            if word_count < min_word_count:  # Too short, likely not a proper summary
                self.logger.warning(f"⚠️ Summary too short: {word_count} words (minimum {min_word_count} required)")
                return ""

            if word_count > max_word_count:  # Too long
                self.logger.warning(f"⚠️ Summary too long: {word_count} words (maximum {max_word_count} allowed)")
                return ""

            return summary

        except Exception as e:
            self.logger.error(f"💥 Error cleaning summary: {str(e)}")
            return ""

    def get_enrichment_status(self, customer_id: str = None) -> Dict[str, Any]:
        """
        Get current enrichment status and statistics

        Args:
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            Dict with enrichment statistics
        """
        try:
            from common.utils.multi_tenant_db import build_multi_tenant_query

            # Build queries with customer_id filter
            base_query = {}
            query = build_multi_tenant_query(base_query, customer_id=customer_id)

            total_articles = self.news_collection.count_documents(query)

            progress_query = build_multi_tenant_query({'status': ArticleStatus.PROGRESS.value}, customer_id=customer_id)
            progress_articles = self.news_collection.count_documents(progress_query)

            completed_query = build_multi_tenant_query({'status': ArticleStatus.COMPLETED.value}, customer_id=customer_id)
            completed_articles = self.news_collection.count_documents(completed_query)

            # Enriched articles = articles with non-empty short_summary
            # Use $and with $nin to properly check for non-null and non-empty
            enriched_query = build_multi_tenant_query({
                'short_summary': {
                    '$exists': True,
                    '$nin': [None, '']
                }
            }, customer_id=customer_id)
            enriched_articles = self.news_collection.count_documents(enriched_query)

            # Pending enrichment = total - enriched (simpler and more reliable)
            pending_enrichment = total_articles - enriched_articles

            self.logger.info(f"📊 Enrichment stats (customer_id: {customer_id}) - Total: {total_articles}, Enriched: {enriched_articles}, Pending: {pending_enrichment}, Progress: {progress_articles}, Completed: {completed_articles}")

            return {
                'total_articles': total_articles,
                'progress_articles': progress_articles,
                'completed_articles': completed_articles,
                'enriched_articles': enriched_articles,
                'pending_enrichment': pending_enrichment,
                'enrichment_rate': round((enriched_articles / total_articles * 100), 2) if total_articles > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Error getting enrichment status: {str(e)}")
            return {'error': str(e)}
