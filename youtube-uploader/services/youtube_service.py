"""
YouTube Upload Service
Handles video uploads to YouTube using YouTube Data API v3
"""
import os
import sys
import logging
import json
import socket
from typing import Optional, Dict, Any
from datetime import datetime
import time
from dateutil import parser

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Add parent directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.utils.multi_tenant_db import build_multi_tenant_query


class YouTubeService:
    """Service for uploading videos to YouTube"""

    def __init__(self, config, db=None):
        """
        Initialize YouTube service

        Args:
            config: Configuration object
            db: MongoDB database connection (optional)
        """
        self.config = config
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.youtube = None
        self._pending_flow = None
        
    def authenticate(self, credential_id='default-youtube-credential', customer_id=None) -> bool:
        """
        Authenticate with YouTube API using MongoDB credentials

        Args:
            credential_id: ID of the credential to use from MongoDB
            customer_id: Customer ID for multi-tenancy (optional)

        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            credentials = None

            # Try to load credentials from MongoDB if database is available
            if self.db is not None:
                self.logger.info(f"Loading YouTube credentials from MongoDB (credential_id: {credential_id}, customer_id: {customer_id})...")
                credentials_collection = self.db['youtube_credentials']

                # Get credential from database with multi-tenant filter
                base_query = {'credential_id': credential_id}
                query = build_multi_tenant_query(base_query, customer_id=customer_id)
                credential_doc = credentials_collection.find_one(query)

                # If specific credential not found, try to find any active authenticated credential for this customer
                if not credential_doc or not credential_doc.get('is_authenticated'):
                    self.logger.warning(f"⚠️ Credential '{credential_id}' not found, looking for any active credential for customer...")

                    # Look for any authenticated credential for this customer
                    fallback_query = {
                        'is_authenticated': True,
                        'is_deleted': {'$ne': True}
                    }
                    fallback_query = build_multi_tenant_query(fallback_query, customer_id=customer_id)
                    credential_doc = credentials_collection.find_one(fallback_query)

                    if credential_doc:
                        self.logger.info(f"✅ Found active credential: {credential_doc.get('name')} (ID: {credential_doc.get('credential_id')})")

                if credential_doc and credential_doc.get('is_authenticated'):
                    # Build credentials object from MongoDB data
                    creds_data = {
                        'token': credential_doc.get('access_token'),
                        'refresh_token': credential_doc.get('refresh_token'),
                        'token_uri': credential_doc.get('token_uri', 'https://oauth2.googleapis.com/token'),
                        'client_id': credential_doc.get('client_id'),
                        'client_secret': credential_doc.get('client_secret'),
                        'scopes': credential_doc.get('scopes', self.config.YOUTUBE_SCOPES)
                    }

                    # Convert token expiry to ISO string format (required by from_authorized_user_info)
                    token_expiry = credential_doc.get('token_expiry')
                    if token_expiry:
                        if isinstance(token_expiry, datetime):
                            # Convert datetime to ISO string
                            creds_data['expiry'] = token_expiry.isoformat()
                        elif isinstance(token_expiry, str):
                            # Already a string, use as-is
                            creds_data['expiry'] = token_expiry

                    credentials = Credentials.from_authorized_user_info(creds_data, self.config.YOUTUBE_SCOPES)
                    self.logger.info("✅ Loaded credentials from MongoDB")
                else:
                    self.logger.error(f"❌ No authenticated credential found in MongoDB")
                    self.logger.error("Please authenticate using the UI: YouTube Uploader → Credentials → Authenticate")
                    return False
            else:
                # Fallback to file-based credentials (legacy)
                if os.path.exists(self.config.YOUTUBE_CREDENTIALS_FILE):
                    self.logger.info("Loading existing YouTube credentials from file...")
                    with open(self.config.YOUTUBE_CREDENTIALS_FILE, 'r') as f:
                        creds_data = json.load(f)
                        credentials = Credentials.from_authorized_user_info(creds_data, self.config.YOUTUBE_SCOPES)
                else:
                    self.logger.error("❌ No credentials available. Please authenticate using the UI.")
                    return False

            # Refresh credentials if expired
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    self.logger.info("Refreshing expired credentials...")
                    try:
                        credentials.refresh(Request())

                        # Update MongoDB with new token if using MongoDB
                        if self.db is not None:
                            credentials_collection = self.db['youtube_credentials']
                            update_data = {
                                'access_token': credentials.token,
                                'token_expiry': credentials.expiry.isoformat() if credentials.expiry else None,
                                'updated_at': datetime.now()
                            }
                            # Use multi-tenant query for update
                            base_query = {'credential_id': credential_id}
                            query = build_multi_tenant_query(base_query, customer_id=customer_id)
                            credentials_collection.update_one(
                                query,
                                {'$set': update_data}
                            )
                            self.logger.info("✅ Updated refreshed token in MongoDB")
                    except Exception as refresh_error:
                        self.logger.error(f"❌ YouTube authentication failed: {str(refresh_error)}")
                        self.logger.error("Please re-authenticate using the UI: YouTube Uploader → Credentials → Re-authenticate")
                        return False
                else:
                    self.logger.error("❌ Credentials invalid and cannot be refreshed")
                    self.logger.error("Please authenticate using the UI: YouTube Uploader → Credentials → Authenticate")
                    return False
            
            # Build YouTube service with custom HTTP timeout
            # Set socket timeout to prevent hanging connections
            socket.setdefaulttimeout(600)  # 10 minutes timeout for large uploads

            # Build YouTube service with credentials
            self.youtube = build(
                self.config.YOUTUBE_API_SERVICE_NAME,
                self.config.YOUTUBE_API_VERSION,
                credentials=credentials
            )

            self.logger.info("✅ YouTube authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ YouTube authentication failed: {str(e)}")
            return False
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[list] = None,
        category_id: Optional[str] = None,
        privacy_status: Optional[str] = None,
        thumbnail_path: Optional[str] = None,
        credential_id: str = 'default-youtube-credential',
        customer_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a video to YouTube

        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID
            privacy_status: Privacy status (public, private, unlisted)
            thumbnail_path: Path to thumbnail image file (optional)
            credential_id: ID of the credential to use from MongoDB
            customer_id: Customer ID for multi-tenancy (optional)

        Returns:
            Dictionary with upload result or None if failed
        """
        try:
            if not self.youtube:
                if not self.authenticate(credential_id=credential_id, customer_id=customer_id):
                    return None
            
            # Validate video file exists
            if not os.path.exists(video_path):
                self.logger.error(f"Video file not found: {video_path}")
                return None
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title[:100],  # YouTube title max 100 chars
                    'description': description[:5000],  # YouTube description max 5000 chars
                    'tags': tags or self.config.DEFAULT_TAGS,
                    'categoryId': category_id or self.config.DEFAULT_CATEGORY_ID
                },
                'status': {
                    'privacyStatus': privacy_status or self.config.DEFAULT_PRIVACY_STATUS,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload
            media = MediaFileUpload(
                video_path,
                chunksize=self.config.CHUNK_SIZE,
                resumable=True
            )
            
            self.logger.info(f"📤 Uploading video: {title}")
            self.logger.info(f"📁 File: {video_path}")
            self.logger.info(f"🏷️ Tags ({len(tags or self.config.DEFAULT_TAGS)}): {tags or self.config.DEFAULT_TAGS}")
            
            # Execute upload with retry logic
            for attempt in range(self.config.MAX_RETRIES):
                try:
                    # Recreate media upload for each retry attempt
                    if attempt > 0:
                        self.logger.info(f"🔄 Recreating media upload for retry attempt {attempt + 1}")
                        media = MediaFileUpload(
                            video_path,
                            chunksize=self.config.CHUNK_SIZE,
                            resumable=True
                        )

                    request = self.youtube.videos().insert(
                        part='snippet,status',
                        body=body,
                        media_body=media
                    )

                    response = None
                    while response is None:
                        try:
                            status, response = request.next_chunk()
                            if status:
                                progress = int(status.progress() * 100)
                                self.logger.info(f"⏳ Upload progress: {progress}%")
                        except (BrokenPipeError, ConnectionResetError, OSError) as chunk_error:
                            # Handle broken pipe and connection errors during chunk upload
                            if attempt < self.config.MAX_RETRIES - 1:
                                self.logger.warning(f"⚠️ Connection error during upload: {str(chunk_error)}")
                                self.logger.warning(f"🔄 Retrying upload... (attempt {attempt + 2}/{self.config.MAX_RETRIES})")
                                time.sleep(2 ** attempt)  # Exponential backoff
                                raise  # Re-raise to trigger outer retry
                            else:
                                raise

                    video_id = response['id']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    self.logger.info(f"✅ Video uploaded successfully!")
                    self.logger.info(f"🔗 Video URL: {video_url}")
                    self.logger.info(f"🆔 Video ID: {video_id}")

                    # Upload thumbnail if provided
                    if thumbnail_path and os.path.exists(thumbnail_path):
                        self.logger.info(f"🖼️ Uploading thumbnail: {thumbnail_path}")
                        if self.upload_thumbnail(video_id, thumbnail_path):
                            self.logger.info("✅ Thumbnail uploaded successfully!")
                        else:
                            self.logger.warning("⚠️ Thumbnail upload failed, but video was uploaded successfully")

                    return {
                        'status': 'success',
                        'video_id': video_id,
                        'video_url': video_url,
                        'title': title,
                        'uploaded_at': datetime.utcnow().isoformat()
                    }

                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        # Retry on server errors
                        self.logger.warning(f"⚠️ Server error {e.resp.status}, retrying... (attempt {attempt + 1}/{self.config.MAX_RETRIES})")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise
                except (BrokenPipeError, ConnectionResetError, OSError) as e:
                    # Handle connection errors
                    if attempt < self.config.MAX_RETRIES - 1:
                        self.logger.warning(f"⚠️ Connection error: {str(e)}, retrying... (attempt {attempt + 1}/{self.config.MAX_RETRIES})")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        self.logger.error(f"❌ Connection error after {self.config.MAX_RETRIES} attempts: {str(e)}")
                        raise
            
            self.logger.error(f"❌ Upload failed after {self.config.MAX_RETRIES} attempts")
            return None
            
        except HttpError as e:
            self.logger.error(f"❌ YouTube API error: {e.resp.status} - {e.content}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Upload failed: {str(e)}")
            return None

    def upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """
        Upload a thumbnail for a YouTube video

        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.youtube:
                self.logger.error("YouTube service not authenticated")
                return False

            if not os.path.exists(thumbnail_path):
                self.logger.error(f"Thumbnail file not found: {thumbnail_path}")
                return False

            # Validate thumbnail file
            file_size = os.path.getsize(thumbnail_path)
            max_size = 2 * 1024 * 1024  # 2MB limit

            if file_size > max_size:
                self.logger.error(f"Thumbnail file too large: {file_size / 1024 / 1024:.2f}MB (max 2MB)")
                return False

            # Upload thumbnail
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()

            return True

        except HttpError as e:
            self.logger.error(f"❌ Thumbnail upload API error: {e.resp.status} - {e.content}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Thumbnail upload failed: {str(e)}")
            return False

    def complete_oauth_flow(self, auth_code: str) -> bool:
        """
        Complete OAuth flow with authorization code

        Args:
            auth_code: Authorization code from OAuth consent screen

        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self._pending_flow:
                # Try to restore flow from saved state
                flow_state_file = os.path.join(os.path.dirname(self.config.YOUTUBE_CREDENTIALS_FILE), 'oauth_flow_state.json')
                if not os.path.exists(flow_state_file):
                    self.logger.error("No pending OAuth flow found. Please start authentication first.")
                    return False

                with open(flow_state_file, 'r') as f:
                    flow_state = json.load(f)

                self._pending_flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.YOUTUBE_CLIENT_SECRETS_FILE,
                    flow_state['scopes']
                )
                self._pending_flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

            # Exchange authorization code for credentials
            self.logger.info("Exchanging authorization code for credentials...")
            self._pending_flow.fetch_token(code=auth_code)
            credentials = self._pending_flow.credentials

            # Save credentials
            with open(self.config.YOUTUBE_CREDENTIALS_FILE, 'w') as f:
                f.write(credentials.to_json())

            # Clean up flow state
            flow_state_file = os.path.join(os.path.dirname(self.config.YOUTUBE_CREDENTIALS_FILE), 'oauth_flow_state.json')
            if os.path.exists(flow_state_file):
                os.remove(flow_state_file)

            self._pending_flow = None

            # Build YouTube service
            self.youtube = build(
                self.config.YOUTUBE_API_SERVICE_NAME,
                self.config.YOUTUBE_API_VERSION,
                credentials=credentials
            )

            self.logger.info("✅ YouTube authentication completed successfully!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to complete OAuth flow: {str(e)}")
            return False

    def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """
        Get authenticated channel information

        Returns:
            Dictionary with channel info or None if failed
        """
        try:
            if not self.youtube:
                if not self.authenticate():
                    return None

            request = self.youtube.channels().list(
                part='snippet,statistics',
                mine=True
            )
            response = request.execute()

            if 'items' in response and len(response['items']) > 0:
                channel = response['items'][0]
                return {
                    'channel_id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description'],
                    'subscriber_count': channel['statistics'].get('subscriberCount', 0),
                    'video_count': channel['statistics'].get('videoCount', 0),
                    'view_count': channel['statistics'].get('viewCount', 0)
                }

            return None

        except Exception as e:
            self.logger.error(f"❌ Failed to get channel info: {str(e)}")
            return None

