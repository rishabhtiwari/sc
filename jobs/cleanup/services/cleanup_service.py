"""
Cleanup Service - Deletes old news articles and their associated files
"""

import os
import sys
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pymongo import MongoClient

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.utils.multi_tenant_db import build_multi_tenant_query


class CleanupService:
    """Service for cleaning up old news articles and their files"""

    def __init__(self, config, logger):
        """
        Initialize cleanup service

        Args:
            config: Configuration object
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.mongo_client = None
        self.news_collection = None

    def _connect_to_mongodb(self):
        """Establish MongoDB connection"""
        if not self.mongo_client:
            self.logger.info(f"🔌 Connecting to MongoDB: {self.config.NEWS_MONGODB_DATABASE}")
            self.mongo_client = MongoClient(self.config.NEWS_MONGODB_URL)
            db = self.mongo_client[self.config.NEWS_MONGODB_DATABASE]
            self.news_collection = db['news_document']
            self.logger.info("✅ MongoDB connection established")

    def cleanup_old_articles(self, retention_hours: int = None, dry_run: bool = None, customer_id: str = None) -> Dict[str, Any]:
        """
        Clean up old news articles and their associated files

        Args:
            retention_hours: Hours to retain articles (default from config)
            dry_run: If True, only preview what would be deleted (default from config)
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            Dict containing cleanup statistics
        """
        # Use config defaults if not specified
        if retention_hours is None:
            retention_hours = self.config.CLEANUP_RETENTION_HOURS
        if dry_run is None:
            dry_run = self.config.CLEANUP_DRY_RUN

        customer_info = f" for customer {customer_id}" if customer_id else ""
        self.logger.info("=" * 80)
        self.logger.info(f"🧹 Starting cleanup process{customer_info}")
        self.logger.info(f"📅 Retention period: {retention_hours} hours")
        self.logger.info(f"🔍 Dry-run mode: {dry_run}")
        self.logger.info("=" * 80)

        # Connect to MongoDB
        self._connect_to_mongodb()

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(hours=retention_hours)
        self.logger.info(f"🗓️ Cutoff date: {cutoff_date.isoformat()} (articles older than this will be deleted)")

        # Statistics
        stats = {
            'total_articles_found': 0,
            'total_articles_deleted': 0,
            'total_files_deleted': 0,
            'total_directories_deleted': 0,
            'total_space_freed_bytes': 0,
            'errors': [],
            'dry_run': dry_run,
            'retention_hours': retention_hours,
            'cutoff_date': cutoff_date.isoformat(),
            'start_time': datetime.utcnow().isoformat()
        }

        try:
            # Find old articles with multi-tenant filter
            base_query = {'created_at': {'$lt': cutoff_date}}
            query = build_multi_tenant_query(base_query, customer_id=customer_id)
            old_articles = list(self.news_collection.find(query).limit(self.config.CLEANUP_MAX_ARTICLES_PER_RUN))
            stats['total_articles_found'] = len(old_articles)

            self.logger.info(f"📊 Found {stats['total_articles_found']} articles to clean up")

            if stats['total_articles_found'] == 0:
                self.logger.info("✅ No articles to clean up")
            else:
                # Process articles in batches
                batch_size = self.config.CLEANUP_BATCH_SIZE
                for i in range(0, len(old_articles), batch_size):
                    batch = old_articles[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    total_batches = (len(old_articles) + batch_size - 1) // batch_size

                    self.logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} articles)")

                    for article in batch:
                        article_stats = self._cleanup_article(article, dry_run)

                        # Update statistics
                        if article_stats['deleted']:
                            stats['total_articles_deleted'] += 1
                        stats['total_files_deleted'] += article_stats['files_deleted']
                        stats['total_directories_deleted'] += article_stats['directories_deleted']
                        stats['total_space_freed_bytes'] += article_stats['space_freed_bytes']
                        stats['errors'].extend(article_stats['errors'])

            # Clean up temp folders
            self.logger.info("")
            self.logger.info("🗑️ Cleaning up temp folders...")
            temp_stats = self._cleanup_temp_folders(dry_run)
            stats['total_files_deleted'] += temp_stats['files_deleted']
            stats['total_space_freed_bytes'] += temp_stats['space_freed_bytes']
            stats['errors'].extend(temp_stats['errors'])

            # Log summary
            self._log_cleanup_summary(stats)

        except Exception as e:
            self.logger.error(f"❌ Cleanup process failed: {str(e)}")
            stats['errors'].append(f"Cleanup process error: {str(e)}")
        finally:
            stats['end_time'] = datetime.utcnow().isoformat()

        return stats

    def _cleanup_article(self, article: Dict, dry_run: bool) -> Dict[str, Any]:
        """
        Clean up a single article and its files

        Args:
            article: Article document from MongoDB
            dry_run: If True, only preview what would be deleted

        Returns:
            Dict containing cleanup statistics for this article
        """
        article_id = article.get('id', 'unknown')
        mongodb_id = str(article.get('_id', ''))
        article_stats = {
            'article_id': article_id,
            'deleted': False,
            'files_deleted': 0,
            'directories_deleted': 0,
            'space_freed_bytes': 0,
            'errors': []
        }

        try:
            self.logger.info(f"🗑️ Processing article: {article_id}")
            self.logger.info(f"   Title: {article.get('title', 'N/A')[:80]}")
            self.logger.info(f"   Created: {article.get('created_at', 'N/A')}")

            # Collect all file paths to delete
            files_to_delete = []
            directories_to_delete = []

            # Check for article directory in video and audio public folders
            for public_dir_name, public_dir_path in [
                ('video', self.config.VIDEO_PUBLIC_DIR),
                ('audio', self.config.AUDIO_PUBLIC_DIR)
            ]:
                article_dir = os.path.join(public_dir_path, article_id)
                if os.path.exists(article_dir) and os.path.isdir(article_dir):
                    directories_to_delete.append((public_dir_name, article_dir))

            # Check for clean_image file (stored by MongoDB _id, not article id)
            if mongodb_id and article.get('clean_image'):
                clean_image_filename = f"{mongodb_id}_cleaned.png"
                clean_image_path = os.path.join(self.config.IMAGE_PUBLIC_DIR, clean_image_filename)
                if os.path.exists(clean_image_path) and os.path.isfile(clean_image_path):
                    files_to_delete.append(('clean_image', clean_image_path))

            # Delete directories and their contents
            for dir_name, dir_path in directories_to_delete:
                dir_stats = self._delete_directory(dir_path, dir_name, dry_run)
                article_stats['files_deleted'] += dir_stats['files_deleted']
                article_stats['directories_deleted'] += dir_stats['directories_deleted']
                article_stats['space_freed_bytes'] += dir_stats['space_freed_bytes']
                article_stats['errors'].extend(dir_stats['errors'])

            # Delete individual files (like clean_image)
            for file_name, file_path in files_to_delete:
                file_stats = self._delete_file(file_path, file_name, dry_run)
                article_stats['files_deleted'] += file_stats['files_deleted']
                article_stats['space_freed_bytes'] += file_stats['space_freed_bytes']
                article_stats['errors'].extend(file_stats['errors'])

            # Delete MongoDB document
            if not dry_run:
                delete_result = self.news_collection.delete_one({'id': article_id})
                if delete_result.deleted_count > 0:
                    article_stats['deleted'] = True
                    self.logger.info(f"   ✅ Deleted MongoDB document for article: {article_id}")
                else:
                    error_msg = f"Failed to delete MongoDB document for article: {article_id}"
                    self.logger.warning(f"   ⚠️ {error_msg}")
                    article_stats['errors'].append(error_msg)
            else:
                self.logger.info(f"   [DRY-RUN] Would delete MongoDB document for article: {article_id}")
                article_stats['deleted'] = True  # Count as deleted in dry-run

        except Exception as e:
            error_msg = f"Error cleaning up article {article_id}: {str(e)}"
            self.logger.error(f"   ❌ {error_msg}")
            article_stats['errors'].append(error_msg)

        return article_stats

    def _delete_directory(self, dir_path: str, dir_name: str, dry_run: bool) -> Dict[str, Any]:
        """
        Delete a directory and all its contents

        Args:
            dir_path: Path to directory
            dir_name: Name/type of directory (for logging)
            dry_run: If True, only preview what would be deleted

        Returns:
            Dict containing deletion statistics
        """
        stats = {
            'files_deleted': 0,
            'directories_deleted': 0,
            'space_freed_bytes': 0,
            'errors': []
        }

        try:
            # Calculate directory size
            total_size = 0
            file_count = 0
            for dirpath, dirnames, filenames in os.walk(dir_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        file_size = os.path.getsize(filepath)
                        total_size += file_size
                        file_count += 1
                    except Exception as e:
                        stats['errors'].append(f"Error getting size of {filepath}: {str(e)}")

            if dry_run:
                self.logger.info(f"   [DRY-RUN] Would delete {dir_name} directory: {dir_path}")
                self.logger.info(f"   [DRY-RUN] Would delete {file_count} files ({self._format_bytes(total_size)})")
                stats['files_deleted'] = file_count
                stats['directories_deleted'] = 1
                stats['space_freed_bytes'] = total_size
            else:
                # Actually delete the directory
                shutil.rmtree(dir_path)
                self.logger.info(f"   ✅ Deleted {dir_name} directory: {dir_path}")
                self.logger.info(f"   ✅ Deleted {file_count} files ({self._format_bytes(total_size)})")
                stats['files_deleted'] = file_count
                stats['directories_deleted'] = 1
                stats['space_freed_bytes'] = total_size

        except Exception as e:
            error_msg = f"Error deleting directory {dir_path}: {str(e)}"
            self.logger.error(f"   ❌ {error_msg}")
            stats['errors'].append(error_msg)

        return stats

    def _delete_file(self, file_path: str, file_name: str, dry_run: bool) -> Dict[str, Any]:
        """
        Delete a single file

        Args:
            file_path: Path to file
            file_name: Name/type of file (for logging)
            dry_run: If True, only preview what would be deleted

        Returns:
            Dict containing deletion statistics
        """
        stats = {
            'files_deleted': 0,
            'space_freed_bytes': 0,
            'errors': []
        }

        try:
            # Get file size
            file_size = os.path.getsize(file_path)

            if dry_run:
                self.logger.info(f"   [DRY-RUN] Would delete {file_name} file: {file_path}")
                self.logger.info(f"   [DRY-RUN] Would free {self._format_bytes(file_size)}")
                stats['files_deleted'] = 1
                stats['space_freed_bytes'] = file_size
            else:
                # Actually delete the file
                os.remove(file_path)
                self.logger.info(f"   ✅ Deleted {file_name} file: {file_path}")
                self.logger.info(f"   ✅ Freed {self._format_bytes(file_size)}")
                stats['files_deleted'] = 1
                stats['space_freed_bytes'] = file_size

        except Exception as e:
            error_msg = f"Error deleting file {file_path}: {str(e)}"
            self.logger.error(f"   ❌ {error_msg}")
            stats['errors'].append(error_msg)

        return stats

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

    def _cleanup_temp_folders(self, dry_run: bool) -> Dict[str, Any]:
        """
        Clean up temporary files in temp folders and debug files

        Args:
            dry_run: If True, only preview what would be deleted

        Returns:
            Dict containing cleanup statistics
        """
        stats = {
            'files_deleted': 0,
            'space_freed_bytes': 0,
            'errors': []
        }

        # List of temp directories to clean
        temp_dirs = [
            ('audio', os.path.join(self.config.AUDIO_PUBLIC_DIR, 'temp')),
            ('video', os.path.join(self.config.VIDEO_PUBLIC_DIR, 'temp')),
            ('image', os.path.join(self.config.IMAGE_PUBLIC_DIR, 'temp'))
        ]

        for dir_name, temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                self.logger.debug(f"   ⏭️ Skipping {dir_name} temp folder (doesn't exist): {temp_dir}")
                continue

            try:
                # Get all files in temp directory
                files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]

                if not files:
                    self.logger.info(f"   ✅ {dir_name} temp folder is already clean")
                    continue

                self.logger.info(f"   🗑️ Found {len(files)} temp files in {dir_name} folder")

                # Delete each file
                files_deleted_count = 0
                space_freed = 0
                for filename in files:
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        file_size = os.path.getsize(file_path)

                        if dry_run:
                            self.logger.debug(f"      [DRY-RUN] Would delete: {filename}")
                            files_deleted_count += 1
                            space_freed += file_size
                        else:
                            os.remove(file_path)
                            files_deleted_count += 1
                            space_freed += file_size

                    except Exception as e:
                        error_msg = f"Error deleting temp file {file_path}: {str(e)}"
                        self.logger.error(f"      ❌ {error_msg}")
                        stats['errors'].append(error_msg)

                stats['files_deleted'] += files_deleted_count
                stats['space_freed_bytes'] += space_freed

                if not dry_run:
                    self.logger.info(f"   ✅ Cleaned {dir_name} temp folder: {files_deleted_count} files, {self._format_bytes(space_freed)}")
                else:
                    self.logger.info(f"   [DRY-RUN] Would clean {dir_name} temp folder: {len(files)} files")

            except Exception as e:
                error_msg = f"Error cleaning temp folder {temp_dir}: {str(e)}"
                self.logger.error(f"   ❌ {error_msg}")
                stats['errors'].append(error_msg)

        # Clean up debug_mask files in image public directory
        try:
            if os.path.exists(self.config.IMAGE_PUBLIC_DIR):
                debug_files = [f for f in os.listdir(self.config.IMAGE_PUBLIC_DIR)
                              if os.path.isfile(os.path.join(self.config.IMAGE_PUBLIC_DIR, f))
                              and f.startswith('debug_mask_')]

                if debug_files:
                    self.logger.info(f"   🗑️ Found {len(debug_files)} debug_mask files in image folder")

                    files_deleted_count = 0
                    space_freed = 0
                    for filename in debug_files:
                        file_path = os.path.join(self.config.IMAGE_PUBLIC_DIR, filename)
                        try:
                            file_size = os.path.getsize(file_path)

                            if dry_run:
                                self.logger.debug(f"      [DRY-RUN] Would delete: {filename}")
                                files_deleted_count += 1
                                space_freed += file_size
                            else:
                                os.remove(file_path)
                                files_deleted_count += 1
                                space_freed += file_size

                        except Exception as e:
                            error_msg = f"Error deleting debug_mask file {file_path}: {str(e)}"
                            self.logger.error(f"      ❌ {error_msg}")
                            stats['errors'].append(error_msg)

                    stats['files_deleted'] += files_deleted_count
                    stats['space_freed_bytes'] += space_freed

                    if not dry_run:
                        self.logger.info(f"   ✅ Cleaned debug_mask files: {files_deleted_count} files, {self._format_bytes(space_freed)}")
                    else:
                        self.logger.info(f"   [DRY-RUN] Would clean debug_mask files: {len(debug_files)} files")
                else:
                    self.logger.info(f"   ✅ No debug_mask files to clean")

        except Exception as e:
            error_msg = f"Error cleaning debug_mask files: {str(e)}"
            self.logger.error(f"   ❌ {error_msg}")
            stats['errors'].append(error_msg)

        return stats

    def _log_cleanup_summary(self, stats: Dict[str, Any]):
        """Log cleanup summary"""
        self.logger.info("=" * 80)
        self.logger.info("📊 CLEANUP SUMMARY")
        self.logger.info("=" * 80)
        self.logger.info(f"🔍 Dry-run mode: {stats['dry_run']}")
        self.logger.info(f"📅 Retention period: {stats['retention_hours']} hours")
        self.logger.info(f"🗓️ Cutoff date: {stats['cutoff_date']}")
        self.logger.info(f"📰 Articles found: {stats['total_articles_found']}")
        self.logger.info(f"🗑️ Articles deleted: {stats['total_articles_deleted']}")
        self.logger.info(f"📁 Files deleted: {stats['total_files_deleted']}")
        self.logger.info(f"📂 Directories deleted: {stats['total_directories_deleted']}")
        self.logger.info(f"💾 Space freed: {self._format_bytes(stats['total_space_freed_bytes'])}")
        self.logger.info(f"❌ Errors: {len(stats['errors'])}")

        if stats['errors']:
            self.logger.warning("⚠️ Errors encountered:")
            for error in stats['errors'][:10]:  # Show first 10 errors
                self.logger.warning(f"   - {error}")
            if len(stats['errors']) > 10:
                self.logger.warning(f"   ... and {len(stats['errors']) - 10} more errors")

        self.logger.info("=" * 80)

    def close(self):
        """Close MongoDB connection"""
        if self.mongo_client:
            self.mongo_client.close()
            self.logger.info("🔌 MongoDB connection closed")

