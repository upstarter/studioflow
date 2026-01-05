"""
YouTube API integration module
Ported from sf-youtube for upload, analytics, and optimization
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class YouTubeAPIService:
    """YouTube Data API v3 integration for upload and management"""

    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/youtube.readonly'
    ]

    def __init__(self):
        self.service = None
        self.credentials = None
        self.config_dir = Path.home() / '.studioflow' / 'youtube'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.api_available = self._check_api_libraries()

    def _check_api_libraries(self) -> bool:
        """Check if YouTube API libraries are installed"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            return True
        except ImportError:
            return False

    def authenticate(self) -> bool:
        """Authenticate with YouTube Data API v3"""
        if not self.api_available:
            return False

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None
            token_file = self.config_dir / 'token.json'
            credentials_file = self.config_dir / 'credentials.json'

            # Check for existing token
            if token_file.exists():
                creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)

            # Refresh or obtain new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not credentials_file.exists():
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_file), self.SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save credentials for next run
                token_file.write_text(creds.to_json())

            self.credentials = creds
            self.service = build('youtube', 'v3', credentials=creds)
            return True

        except Exception:
            return False

    def upload_video(self,
                     video_path: Path,
                     title: str,
                     description: str,
                     tags: List[str] = None,
                     category_id: str = "22",  # 22 = People & Blogs
                     privacy: str = "private",
                     thumbnail_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Upload video to YouTube with metadata

        Args:
            video_path: Path to video file
            title: Video title (max 100 chars)
            description: Video description (max 5000 chars)
            tags: List of tags
            category_id: YouTube category ID
            privacy: Privacy status (private/unlisted/public)
            thumbnail_path: Optional thumbnail image

        Returns:
            Dict with upload result including video ID and URL
        """
        if not self.authenticate():
            return {
                "success": False,
                "error": "Authentication failed. Please set up YouTube API credentials."
            }

        try:
            from googleapiclient.http import MediaFileUpload

            body = {
                'snippet': {
                    'title': title[:100],  # YouTube title limit
                    'description': description[:5000],  # YouTube description limit
                    'tags': tags or [],
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy,
                    'selfDeclaredMadeForKids': False
                }
            }

            # Create media upload object
            media = MediaFileUpload(
                str(video_path),
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )

            # Execute upload
            request = self.service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()

            video_id = response.get('id')
            video_url = f"https://youtube.com/watch?v={video_id}"

            # Upload thumbnail if provided
            if thumbnail_path and thumbnail_path.exists():
                self._upload_thumbnail(video_id, thumbnail_path)

            return {
                'success': True,
                'id': video_id,
                'url': video_url,
                'title': title,
                'status': privacy
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _upload_thumbnail(self, video_id: str, thumbnail_path: Path) -> bool:
        """Upload custom thumbnail for video"""
        try:
            from googleapiclient.http import MediaFileUpload

            media = MediaFileUpload(
                str(thumbnail_path),
                mimetype='image/jpeg'
            )

            self.service.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()

            return True
        except:
            return False

    def get_upload_defaults(self) -> Dict[str, Any]:
        """Get optimized default settings for YouTube uploads"""
        return {
            "title_max_length": 100,
            "description_max_length": 5000,
            "tags_max": 500,  # Total character count for all tags
            "thumbnail_size": (1280, 720),
            "thumbnail_formats": ["jpg", "jpeg", "png", "gif"],
            "categories": {
                "1": "Film & Animation",
                "2": "Cars & Vehicles",
                "10": "Music",
                "15": "Pets & Animals",
                "17": "Sports",
                "19": "Travel & Events",
                "20": "Gaming",
                "22": "People & Blogs",
                "23": "Comedy",
                "24": "Entertainment",
                "25": "News & Politics",
                "26": "How-to & Style",
                "27": "Education",
                "28": "Science & Technology"
            },
            "optimal_upload_times": {
                "weekday": ["14:00", "15:00", "16:00"],  # 2-4 PM
                "weekend": ["09:00", "10:00", "11:00"]   # 9-11 AM
            }
        }

    def update_video_metadata(self,
                              video_id: str,
                              title: Optional[str] = None,
                              description: Optional[str] = None,
                              tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update existing video metadata"""
        if not self.authenticate():
            return {"success": False, "error": "Authentication failed"}

        try:
            # Get current video data
            video_response = self.service.videos().list(
                part="snippet",
                id=video_id
            ).execute()

            if not video_response.get("items"):
                return {"success": False, "error": "Video not found"}

            snippet = video_response["items"][0]["snippet"]

            # Update fields if provided
            if title:
                snippet["title"] = title[:100]
            if description:
                snippet["description"] = description[:5000]
            if tags:
                snippet["tags"] = tags

            # Update video
            update_response = self.service.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": snippet
                }
            ).execute()

            return {
                "success": True,
                "video_id": video_id,
                "updated_fields": {
                    "title": title is not None,
                    "description": description is not None,
                    "tags": tags is not None
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_channel_analytics(self) -> Dict[str, Any]:
        """Get channel analytics and insights"""
        if not self.authenticate():
            return {"success": False, "error": "Authentication failed"}

        try:
            # Get channel data
            channels_response = self.service.channels().list(
                part="statistics,snippet",
                mine=True
            ).execute()

            if not channels_response.get("items"):
                return {"success": False, "error": "No channel found"}

            channel = channels_response["items"][0]
            statistics = channel["statistics"]
            snippet = channel["snippet"]

            return {
                "success": True,
                "channel_id": channel["id"],
                "channel_title": snippet["title"],
                "statistics": {
                    "subscribers": int(statistics.get("subscriberCount", 0)),
                    "total_views": int(statistics.get("viewCount", 0)),
                    "total_videos": int(statistics.get("videoCount", 0))
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_competitors(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for competitor videos to analyze"""
        if not self.authenticate():
            return []

        try:
            search_response = self.service.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=max_results,
                order="viewCount"
            ).execute()

            videos = []
            for item in search_response.get("items", []):
                snippet = item["snippet"]
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": snippet["title"],
                    "channel": snippet["channelTitle"],
                    "published": snippet["publishedAt"],
                    "thumbnail": snippet["thumbnails"]["high"]["url"]
                })

            return videos

        except:
            return []