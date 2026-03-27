"""
Video information retrieval
"""

from typing import Dict, Any, Optional
from .handlers import RequestHandler
from .formatting import format_count, seconds_to_duration_text, normalize_thumbnails, get_text
import re


class Video:
    """Class for fetching video information"""

    @staticmethod
    def extract_video_id(url_or_id: str) -> Optional[str]:
        """Extract video ID from URL or return ID if already provided"""
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
            return url_or_id
        
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/live/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None

    @staticmethod
    async def get(url_or_id: str, fetch_extras: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get video information
        
        Args:
            url_or_id: YouTube video URL or video ID
            fetch_extras: If True, fetches publishedTime and likes (slower)
                          Default: False (fast mode - ~44ms)
            
        Returns:
            Dictionary with video information
            - Always: title, channel, views, duration, thumbnails, description, keywords
            - With fetch_extras=True: + publishedTime, likesCount
        """
        video_id = Video.extract_video_id(url_or_id)
        if not video_id:
            raise ValueError(f"Invalid video URL or ID: {url_or_id}")
        
        context = {
            "client": {
                "clientName": "ANDROID_TESTSUITE",
                "clientVersion": "1.9",
                "androidSdkVersion": 30,
            }
        }

        try:
            response = await RequestHandler.make_request("player", {"videoId": video_id}, context=context)
            
            if not response or "videoDetails" not in response:
                return None

            video_details = response["videoDetails"]
            
            # Safe int conversion (handle string or int)
            try:
                duration_seconds = int(video_details.get("lengthSeconds", 0) or 0)
            except (ValueError, TypeError):
                duration_seconds = 0
            
            try:
                view_count = int(video_details.get("viewCount", 0) or 0)
            except (ValueError, TypeError):
                view_count = 0
            
            # Fetch extras (publishedTime + likes) if requested
            published_time = None
            like_count = None
            
            if fetch_extras:
                try:
                    next_response = await RequestHandler.make_request("next", {"videoId": video_id})
                    if next_response:
                        contents = (next_response.get("contents", {})
                            .get("twoColumnWatchNextResults", {})
                            .get("results", {})
                            .get("results", {})
                            .get("contents", []))
                        
                        if contents:
                            primary_info = contents[0].get("videoPrimaryInfoRenderer", {})
                            
                            # Extract both publishedTime and likes from same response
                            published_time = get_text(primary_info.get("dateText", {}))
                            like_count = Video._extract_likes(next_response)
                except:
                    pass
            
            # Process thumbnails
            thumbs = normalize_thumbnails(video_details.get("thumbnail", {}).get("thumbnails", []))
            if not thumbs:
                thumbs = [
                    {"url": f"https://img.youtube.com/vi/{video_id}/default.jpg", "width": 120, "height": 90},
                    {"url": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg", "width": 320, "height": 180},
                    {"url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg", "width": 480, "height": 360},
                    {"url": f"https://img.youtube.com/vi/{video_id}/sddefault.jpg", "width": 640, "height": 480},
                ]
            
            # Build result
            result = {
                "id": video_id,
                "title": video_details.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "channel": {
                    "name": video_details.get("author", ""),
                    "id": video_details.get("channelId", "")
                },
                "isLive": video_details.get("isLiveContent", False),
                "duration": {
                    "seconds": duration_seconds,
                    "text": seconds_to_duration_text(duration_seconds),
                },
                "viewCount": format_count(view_count, "views"),
                "description": video_details.get("shortDescription", ""),
                "thumbnails": thumbs,
                "keywords": video_details.get("keywords", []),
            }
            
            if published_time:
                result["publishedTime"] = published_time
            
            if like_count:
                result["likesCount"] = format_count(like_count, "likes")
            
            return result
            
        except Exception as e:
            print(f"Video.get() error: {e}")
            return None

    @staticmethod
    def _extract_likes(next_response: Optional[Dict[str, Any]]) -> Optional[int]:
        """Extract like count from next endpoint response"""
        if not next_response:
            return None
        
        try:
            contents = (next_response.get("contents", {})
                .get("twoColumnWatchNextResults", {})
                .get("results", {})
                .get("results", {})
                .get("contents", [{}]))
            
            primary_info = contents[0].get("videoPrimaryInfoRenderer", {}) if contents else {}
            buttons = (primary_info.get("videoActions", {})
                .get("menuRenderer", {})
                .get("topLevelButtons", []))

            for button in buttons:
                # Try new structure (2024+): segmentedLikeDislikeButtonViewModel
                segmented = button.get("segmentedLikeDislikeButtonViewModel", {})
                if segmented:
                    like_button = (segmented.get("likeButtonViewModel", {})
                        .get("likeButtonViewModel", {})
                        .get("toggleButtonViewModel", {})
                        .get("toggleButtonViewModel", {})
                        .get("defaultButtonViewModel", {})
                        .get("buttonViewModel", {}))
                    
                    if like_button:
                        # Try accessibilityText (most accurate)
                        accessibility_text = like_button.get("accessibilityText", "")
                        match = re.search(r"([\d,]+)", accessibility_text)
                        if match:
                            return int(match.group(1).replace(",", ""))
                        
                        # Fallback: try title (short format like "18M")
                        # We'll skip this as it's less accurate
                
                # Try old structure (legacy): toggleButtonRenderer
                toggle = button.get("toggleButtonRenderer")
                if toggle and toggle.get("defaultIcon", {}).get("iconType") == "LIKE":
                    label = (toggle.get("defaultText", {})
                        .get("accessibility", {})
                        .get("accessibilityData", {})
                        .get("label", ""))
                    match = re.search(r"([\d,]+)", label)
                    if match:
                        return int(match.group(1).replace(",", ""))
        except:
            pass
        
        return None
