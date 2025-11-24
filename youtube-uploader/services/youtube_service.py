"""
YouTube Upload Service
Handles video uploads to YouTube using YouTube Data API v3
"""
import os
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
import time

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class YouTubeService:
    """Service for uploading videos to YouTube"""
    
    def __init__(self, config):
        """
        Initialize YouTube service

        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.youtube = None
        self._pending_flow = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with YouTube API
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            credentials = None
            
            # Load existing credentials if available
            if os.path.exists(self.config.YOUTUBE_CREDENTIALS_FILE):
                self.logger.info("Loading existing YouTube credentials...")
                with open(self.config.YOUTUBE_CREDENTIALS_FILE, 'r') as f:
                    creds_data = json.load(f)
                    credentials = Credentials.from_authorized_user_info(creds_data, self.config.YOUTUBE_SCOPES)
            
            # Refresh or get new credentials
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    self.logger.info("Refreshing expired credentials...")
                    credentials.refresh(Request())
                else:
                    self.logger.info("Getting new credentials...")
                    if not os.path.exists(self.config.YOUTUBE_CLIENT_SECRETS_FILE):
                        self.logger.error(f"Client secrets file not found: {self.config.YOUTUBE_CLIENT_SECRETS_FILE}")
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.config.YOUTUBE_CLIENT_SECRETS_FILE,
                        self.config.YOUTUBE_SCOPES
                    )

                    # Use console-based OAuth flow for Docker environment
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    auth_url, _ = flow.authorization_url(prompt='consent')

                    self.logger.info("=" * 80)
                    self.logger.info("🔐 YOUTUBE AUTHENTICATION REQUIRED")
                    self.logger.info("=" * 80)
                    self.logger.info("")
                    self.logger.info("Please visit this URL to authorize the application:")
                    self.logger.info("")
                    self.logger.info(f"    {auth_url}")
                    self.logger.info("")
                    self.logger.info("After authorization, you will receive an authorization code.")
                    self.logger.info("Please enter the code using the following command:")
                    self.logger.info("")
                    self.logger.info("    curl -X POST http://localhost:8097/api/oauth-callback \\")
                    self.logger.info("         -H 'Content-Type: application/json' \\")
                    self.logger.info("         -d '{\"code\": \"YOUR_AUTH_CODE_HERE\"}'")
                    self.logger.info("")
                    self.logger.info("=" * 80)

                    # Save the flow state for later use
                    flow_state = {
                        'auth_url': auth_url,
                        'client_config': flow.client_config,
                        'scopes': self.config.YOUTUBE_SCOPES
                    }

                    flow_state_file = os.path.join(os.path.dirname(self.config.YOUTUBE_CREDENTIALS_FILE), 'oauth_flow_state.json')
                    with open(flow_state_file, 'w') as f:
                        json.dump(flow_state, f)

                    # Store flow instance for callback
                    self._pending_flow = flow

                    return False  # Authentication pending
                
                # Save credentials for future use
                with open(self.config.YOUTUBE_CREDENTIALS_FILE, 'w') as f:
                    f.write(credentials.to_json())
                self.logger.info("Credentials saved successfully")
            
            # Build YouTube service
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
        thumbnail_path: Optional[str] = None
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

        Returns:
            Dictionary with upload result or None if failed
        """
        try:
            if not self.youtube:
                if not self.authenticate():
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
            
            # Execute upload with retry logic
            for attempt in range(self.config.MAX_RETRIES):
                try:
                    request = self.youtube.videos().insert(
                        part='snippet,status',
                        body=body,
                        media_body=media
                    )
                    
                    response = None
                    while response is None:
                        status, response = request.next_chunk()
                        if status:
                            progress = int(status.progress() * 100)
                            self.logger.info(f"⏳ Upload progress: {progress}%")
                    
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
                        self.logger.warning(f"Server error, retrying... (attempt {attempt + 1}/{self.config.MAX_RETRIES})")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
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

