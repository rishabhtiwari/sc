"""
MinIO Initialization Script
Creates required buckets and sets policies
"""
import os
import sys
from minio import Minio
from minio.error import S3Error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Buckets to create
BUCKETS = [
    "audio-assets",
    "image-assets",
    "video-assets",
    "document-assets"
]


def init_minio():
    """Initialize MinIO buckets"""
    try:
        # Create MinIO client
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        
        logger.info(f"Connected to MinIO at {MINIO_ENDPOINT}")
        
        # Create buckets
        for bucket_name in BUCKETS:
            try:
                if not client.bucket_exists(bucket_name):
                    client.make_bucket(bucket_name)
                    logger.info(f"✅ Created bucket: {bucket_name}")
                else:
                    logger.info(f"✓ Bucket already exists: {bucket_name}")
                    
                # Set bucket policy (public read for now - adjust as needed)
                # For production, you should use pre-signed URLs instead
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                        }
                    ]
                }
                
                import json
                client.set_bucket_policy(bucket_name, json.dumps(policy))
                logger.info(f"✅ Set policy for bucket: {bucket_name}")
                
            except S3Error as e:
                logger.error(f"❌ Error with bucket {bucket_name}: {e}")
                
        logger.info("MinIO initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize MinIO: {e}")
        return False


if __name__ == "__main__":
    success = init_minio()
    sys.exit(0 if success else 1)

