"""
Voice Request Service - Database operations for voice generation requests
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class VoiceRequestService:
    """
    Service for managing voice generation requests in MongoDB
    """
    
    def __init__(self, mongodb_url: str, logger):
        self.mongodb_url = mongodb_url
        self.logger = logger
        self.client = None
        self.db = None
        self.collection = None
        
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_url)
            self.db = self.client.get_default_database()
            self.collection = self.db.voice_requests
            
            # Test connection
            self.client.admin.command('ping')
            self.logger.info("Connected to MongoDB for voice requests")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise Exception(f"MongoDB connection failed: {e}")
    
    def create_voice_request(self, reference_audio_path: str, text_script: str, 
                           language: str = 'en', metadata: Optional[Dict] = None) -> str:
        """
        Create a new voice generation request
        
        Args:
            reference_audio_path: Path to reference audio file
            text_script: Text to be spoken
            language: Language code
            metadata: Additional metadata
            
        Returns:
            Request ID
        """
        try:
            request_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            request_doc = {
                'request_id': request_id,
                'reference_audio_path': reference_audio_path,
                'text_script': text_script,
                'language': language,
                'generated_audio_path': None,
                'status': 'pending',
                'progress_percentage': 0,
                'progress_message': 'Request queued for processing',
                'created_at': now,
                'updated_at': now,
                'started_at': None,
                'completed_at': None,
                'error_message': None,
                'metadata': metadata or {}
            }
            
            self.collection.insert_one(request_doc)
            self.logger.info(f"Created voice request: {request_id}")
            
            return request_id
            
        except Exception as e:
            self.logger.error(f"Error creating voice request: {e}")
            raise Exception(f"Failed to create voice request: {e}")
    
    def get_voice_request(self, request_id: str) -> Optional[Dict]:
        """
        Get a voice request by ID
        
        Args:
            request_id: Request ID
            
        Returns:
            Request document or None
        """
        try:
            request_doc = self.collection.find_one({'request_id': request_id})
            
            if request_doc:
                # Remove MongoDB's _id field
                request_doc.pop('_id', None)
            
            return request_doc
            
        except Exception as e:
            self.logger.error(f"Error getting voice request {request_id}: {e}")
            return None
    
    def get_pending_requests(self, limit: int = 10) -> List[Dict]:
        """
        Get pending voice requests for processing
        
        Args:
            limit: Maximum number of requests to return
            
        Returns:
            List of pending request documents
        """
        try:
            cursor = self.collection.find(
                {'status': 'pending'}
            ).sort('created_at', 1).limit(limit)
            
            requests = []
            for doc in cursor:
                doc.pop('_id', None)  # Remove MongoDB's _id field
                requests.append(doc)
            
            return requests
            
        except Exception as e:
            self.logger.error(f"Error getting pending requests: {e}")
            return []
    
    def update_request_progress(self, request_id: str, progress_percentage: int,
                              progress_message: str = "") -> bool:
        """
        Update request progress percentage and message

        Args:
            request_id: The request ID to update
            progress_percentage: Progress percentage (0-100)
            progress_message: Optional progress message

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            update_data = {
                'progress_percentage': progress_percentage,
                'progress_message': progress_message,
                'updated_at': datetime.utcnow()
            }

            result = self.collection.update_one(
                {'request_id': request_id},
                {'$set': update_data}
            )

            if result.modified_count > 0:
                self.logger.info(f"Updated progress for request {request_id}: {progress_percentage}% - {progress_message}")
                return True
            else:
                self.logger.warning(f"No request found with ID: {request_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error updating request progress {request_id}: {e}")
            return False

    def update_request_status(self, request_id: str, status: str,
                            generated_audio_path: Optional[str] = None,
                            error_message: Optional[str] = None,
                            metadata: Optional[Dict] = None) -> bool:
        """
        Update request status and related fields
        
        Args:
            request_id: Request ID
            status: New status (pending, processing, completed, failed)
            generated_audio_path: Path to generated audio file
            error_message: Error message if failed
            metadata: Additional metadata to merge
            
        Returns:
            True if updated successfully
        """
        try:
            now = datetime.utcnow()
            update_doc = {
                'status': status,
                'updated_at': now
            }
            
            # Set timestamps based on status
            if status == 'processing':
                update_doc['started_at'] = now
            elif status in ['completed', 'failed']:
                update_doc['completed_at'] = now
            
            # Set generated audio path if provided
            if generated_audio_path:
                update_doc['generated_audio_path'] = generated_audio_path
            
            # Set error message if provided
            if error_message:
                update_doc['error_message'] = error_message
            
            # Merge metadata if provided
            if metadata:
                # Get existing metadata and merge
                existing_request = self.get_voice_request(request_id)
                if existing_request:
                    existing_metadata = existing_request.get('metadata', {})
                    existing_metadata.update(metadata)
                    update_doc['metadata'] = existing_metadata
                else:
                    update_doc['metadata'] = metadata
            
            result = self.collection.update_one(
                {'request_id': request_id},
                {'$set': update_doc}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Updated voice request {request_id} status to {status}")
                return True
            else:
                self.logger.warning(f"No voice request found with ID {request_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating voice request {request_id}: {e}")
            return False
    
    def get_request_history(self, limit: int = 50, status: Optional[str] = None) -> List[Dict]:
        """
        Get request history with optional status filter
        
        Args:
            limit: Maximum number of requests to return
            status: Optional status filter
            
        Returns:
            List of request documents
        """
        try:
            query = {}
            if status:
                query['status'] = status
            
            cursor = self.collection.find(query).sort('created_at', -1).limit(limit)
            
            requests = []
            for doc in cursor:
                doc.pop('_id', None)  # Remove MongoDB's _id field
                requests.append(doc)
            
            return requests
            
        except Exception as e:
            self.logger.error(f"Error getting request history: {e}")
            return []
    
    def get_request_stats(self) -> Dict[str, Any]:
        """
        Get statistics about voice requests
        
        Returns:
            Dictionary with request statistics
        """
        try:
            # Count by status
            pipeline = [
                {
                    '$group': {
                        '_id': '$status',
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            status_counts = {}
            for result in self.collection.aggregate(pipeline):
                status_counts[result['_id']] = result['count']
            
            # Total requests
            total_requests = self.collection.count_documents({})
            
            # Recent requests (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_requests = self.collection.count_documents({
                'created_at': {'$gte': yesterday}
            })
            
            return {
                'total_requests': total_requests,
                'recent_requests_24h': recent_requests,
                'status_counts': status_counts,
                'pending_count': status_counts.get('pending', 0),
                'processing_count': status_counts.get('processing', 0),
                'completed_count': status_counts.get('completed', 0),
                'failed_count': status_counts.get('failed', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting request stats: {e}")
            return {
                'total_requests': 0,
                'recent_requests_24h': 0,
                'status_counts': {},
                'error': str(e)
            }
    
    def cleanup_old_requests(self, max_age_days: int = 30) -> int:
        """
        Clean up old completed/failed requests
        
        Args:
            max_age_days: Maximum age of requests to keep
            
        Returns:
            Number of requests cleaned up
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
            
            result = self.collection.delete_many({
                'status': {'$in': ['completed', 'failed']},
                'completed_at': {'$lt': cutoff_date}
            })
            
            cleaned_count = result.deleted_count
            self.logger.info(f"Cleaned up {cleaned_count} old voice requests")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old requests: {e}")
            return 0
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.logger.info("Closed MongoDB connection")
