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
        Generate a 45-70 word summary using LLM service

        Args:
            content: Article content to summarize
            article_id: Article identifier for logging

        Returns:
            Generated summary (45-70 words) or empty string if failed
        """
        try:
            # Simple and direct English prompt that works better with Mistral
            prompt = f"""Summarize this news article in exactly 45-70 words. Must be at least 45 words:

{content[:2000]}"""
            # Limit content to avoid token limits

            # Make request to LLM service directly (no RAG)
            payload = {
                "query": prompt,  # LLM service uses 'query' parameter
                "use_rag": False,  # Explicitly disable RAG
                "temperature": 0.3  # Lower temperature for more focused summaries
            }

            self.logger.info(f"🤖 Requesting direct LLM summary (no RAG) for article {article_id}")

            response = requests.post(
                f"{self.llm_service_url}/llm/generate",  # Direct LLM service endpoint
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
                        self.logger.info(f"✅ Generated summary for article {article_id} ({len(summary.split())} words)")
                        return summary
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
