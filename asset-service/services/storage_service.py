"""
MinIO Storage Service
Handles all object storage operations
"""
import logging
from typing import Optional, BinaryIO
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from config.settings import settings

logger = logging.getLogger(__name__)


class StorageService:
    """MinIO storage service for asset management"""
    
    def __init__(self):
        """Initialize MinIO client"""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            region=settings.MINIO_REGION
        )
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Ensure all required buckets exist"""
        buckets = [
            settings.AUDIO_BUCKET,
            settings.IMAGE_BUCKET,
            settings.VIDEO_BUCKET,
            settings.DOCUMENT_BUCKET,
            settings.TEMP_BUCKET
        ]
        
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
                else:
                    logger.debug(f"Bucket already exists: {bucket}")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket}: {e}")
                raise
    
    def upload_file(
        self,
        bucket: str,
        object_name: str,
        file_data: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload a file to MinIO
        
        Args:
            bucket: Bucket name
            object_name: Object key/path
            file_data: File-like object
            length: File size in bytes
            content_type: MIME type
            metadata: Optional metadata dict
            
        Returns:
            Object URL
        """
        try:
            self.client.put_object(
                bucket,
                object_name,
                file_data,
                length,
                content_type=content_type,
                metadata=metadata or {}
            )
            
            # Return the object URL
            url = f"{settings.MINIO_ENDPOINT}/{bucket}/{object_name}"
            logger.info(f"Uploaded file to {url}")
            return url
            
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def download_file(self, bucket: str, object_name: str) -> bytes:
        """
        Download a file from MinIO
        
        Args:
            bucket: Bucket name
            object_name: Object key/path
            
        Returns:
            File data as bytes
        """
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
            
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def get_presigned_url(
        self,
        bucket: str,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Get a pre-signed URL for temporary access

        Args:
            bucket: Bucket name
            object_name: Object key/path
            expires: URL expiration time

        Returns:
            Pre-signed URL with external endpoint
        """
        try:
            url = self.client.presigned_get_object(bucket, object_name, expires=expires)

            # Replace internal Docker hostname with external accessible endpoint
            # This allows browser to access the presigned URL
            if url.startswith('http://minio:9000'):
                url = url.replace('http://minio:9000', 'http://localhost:9000')
                logger.info(f"Replaced internal MinIO URL with external endpoint")
            elif url.startswith('https://minio:9000'):
                url = url.replace('https://minio:9000', 'http://localhost:9000')
                logger.info(f"Replaced internal MinIO URL with external endpoint")

            return url

        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    def delete_file(self, bucket: str, object_name: str) -> bool:
        """
        Delete a file from MinIO
        
        Args:
            bucket: Bucket name
            object_name: Object key/path
            
        Returns:
            True if successful
        """
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted file: {bucket}/{object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise
    
    def file_exists(self, bucket: str, object_name: str) -> bool:
        """Check if a file exists"""
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False


# Global storage service instance
storage_service = StorageService()

