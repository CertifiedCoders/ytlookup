"""
Playlist information retrieval using InnerTube API only
"""

import asyncio
from typing import Dict, Any, Optional, List
from .handlers import RequestHandler
from .video import Video
from .formatting import (
    duration_text_to_seconds,
    format_count,
    get_text,
    normalize_thumbnails,
    parse_int_from_text,
    seconds_to_duration_text,
)
import re


class Playlist:
    """Class for fetching playlist information and videos"""
    
    @staticmethod
    def extract_playlist_id(url_or_id: str) -> Optional[str]:
        """
        Extract playlist ID from URL or return ID if already provided
        
        Args:
            url_or_id: YouTube playlist URL or playlist ID
            
        Returns:
            Playlist ID or None if invalid
        """
        # If it looks like a playlist ID (starts with PL, typically 34 chars)
        if re.match(r'^[A-Za-z0-9_-]+$', url_or_id) and len(url_or_id) >= 13:
            return url_or_id
        
        # Extract from URL
        patterns = [
            r'list=([A-Za-z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        
        return None

    @staticmethod
    def _extract_main_fields(response: Dict[str, Any]) -> Dict[str, Any]:
        fields: Dict[str, Any] = {}
        sidebar_items = (response.get("sidebar", {})
            .get("playlistSidebarRenderer", {})
            .get("items", []))
        primary = {}
        secondary = {}
        for item in sidebar_items:
            if "playlistSidebarPrimaryInfoRenderer" in item:
                primary = item["playlistSidebarPrimaryInfoRenderer"]
            if "playlistSidebarSecondaryInfoRenderer" in item:
                secondary = item["playlistSidebarSecondaryInfoRenderer"]

        title = get_text(primary.get("title", {}))
        if title:
            fields["title"] = title

        video_count = None
        for stat in primary.get("stats", []):
            stat_text = get_text(stat)
            if "video" in stat_text.lower():
                video_count = parse_int_from_text(stat_text)
                if video_count is not None:
                    break
        if video_count is not None:
            fields["videoCount"] = video_count

        description = get_text(primary.get("description", {}))
        if description:
            fields["description"] = description

        thumbnails = normalize_thumbnails(
            primary.get("thumbnailRenderer", {})
            .get("playlistVideoThumbnailRenderer", {})
            .get("thumbnail", {})
            .get("thumbnails", [])
        )
        if not thumbnails:
            thumbnails = normalize_thumbnails(
                response.get("metadata", {})
                .get("playlistMetadataRenderer", {})
                .get("thumbnail", {})
                .get("thumbnails", [])
            )
        if thumbnails:
            fields["thumbnails"] = thumbnails

        owner = (secondary.get("videoOwner", {})
            .get("videoOwnerRenderer", {}))
        channel_name = get_text(owner.get("title", {}))
        channel_id = (owner.get("navigationEndpoint", {})
            .get("browseEndpoint", {})
            .get("browseId", ""))
        if channel_name or channel_id:
            fields["channel"] = {}
            if channel_name:
                fields["channel"]["name"] = channel_name
            if channel_id:
                fields["channel"]["id"] = channel_id

        return fields

    @staticmethod
    def _build_video_item(video_renderer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        video_id = video_renderer.get("videoId", "")
        if not video_id:
            return None

        title = get_text(video_renderer.get("title", {}))
        duration_text = get_text(video_renderer.get("lengthText", {}))
        
        # Safe int conversion
        try:
            duration_seconds = int(video_renderer.get("lengthSeconds", 0) or 0)
        except (ValueError, TypeError):
            duration_seconds = 0
        
        if duration_seconds == 0:
            duration_seconds = duration_text_to_seconds(duration_text)
        if not duration_text:
            duration_text = seconds_to_duration_text(duration_seconds)

        channel_runs = video_renderer.get("shortBylineText", {}).get("runs", [])
        channel_name = channel_runs[0].get("text", "") if channel_runs else ""
        channel_id = (channel_runs[0].get("navigationEndpoint", {})
            .get("browseEndpoint", {})
            .get("browseId", "")) if channel_runs else ""
        channel = {}
        if channel_name:
            channel["name"] = channel_name
        if channel_id:
            channel["id"] = channel_id

        thumbs = normalize_thumbnails(video_renderer.get("thumbnail", {}).get("thumbnails", []))
        if not thumbs:
            thumbs = normalize_thumbnails([
                {"url": f"https://img.youtube.com/vi/{video_id}/default.jpg", "width": 120, "height": 90},
                {"url": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg", "width": 320, "height": 180},
                {"url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg", "width": 480, "height": 360},
                {"url": f"https://img.youtube.com/vi/{video_id}/sddefault.jpg", "width": 640, "height": 480},
                {"url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg", "width": 1280, "height": 720},
            ])

        view_text_candidates = [
            get_text(video_renderer.get("viewCountText", {})),
            get_text(video_renderer.get("shortViewCountText", {})),
            get_text(video_renderer.get("videoInfo", {})),
        ]
        view_count = 0
        for candidate in view_text_candidates:
            parsed = parse_int_from_text(candidate)
            if parsed is not None:
                view_count = parsed
                break

        item: Dict[str, Any] = {
            "id": video_id,
            "title": title,
            "duration": {
                "seconds": duration_seconds,
                "text": duration_text,
            },
            "viewCount": format_count(view_count, "views"),
            "thumbnails": thumbs,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
        if channel:
            item["channel"] = channel
        return item
    
    @staticmethod
    async def get(url_or_id: str, limit: int = 100, fetch_video_details: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get playlist information including videos (fast mode - no extra API calls)
        
        Args:
            url_or_id: YouTube playlist URL or playlist ID
            limit: Maximum number of videos to fetch (default: 100)
            fetch_video_details: If True, fetches detailed info for each video (SLOW! adds ~0.1s per video)
            
        Returns:
            Dictionary with playlist information from InnerTube browse endpoint
        """
        
        playlist_id = Playlist.extract_playlist_id(url_or_id)
        if not playlist_id:
            raise ValueError(f"Invalid playlist URL or ID: {url_or_id}")
        
        request_data = {"browseId": f"VL{playlist_id}"}
        
        try:
            response = await RequestHandler.make_request("browse", request_data)
            
            if not response:
                return None
            
            videos = []
            tabs = response.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [])
            
            for tab in tabs:
                tab_renderer = tab.get("tabRenderer", {})
                if not tab_renderer:
                    continue
                
                content = tab_renderer.get("content", {})
                section_list = content.get("sectionListRenderer", {})
                contents = section_list.get("contents", [])
                
                for content_item in contents:
                    item_section = content_item.get("itemSectionRenderer", {})
                    if not item_section:
                        continue
                    
                    playlist_contents = item_section.get("contents", [])
                    for playlist_content in playlist_contents:
                        playlist_renderer = playlist_content.get("playlistVideoListRenderer", {})
                        if not playlist_renderer:
                            continue
                        
                        video_items = playlist_renderer.get("contents", [])
                        
                        for item in video_items:
                            if len(videos) >= limit:
                                break
                            video_renderer = item.get("playlistVideoRenderer", {})
                            if not video_renderer:
                                continue
                            video_data = Playlist._build_video_item(video_renderer)
                            if video_data:
                                videos.append(video_data)
                    if len(videos) >= limit:
                        break
                if len(videos) >= limit:
                    break
            
            videos = videos[:limit]

            if fetch_video_details and videos:
                details = await asyncio.gather(
                    *(Video.get(video["id"]) for video in videos),
                    return_exceptions=True
                )
                for index, detail in enumerate(details):
                    if not isinstance(detail, dict):
                        continue
                    videos[index]["viewCount"] = detail.get("viewCount", videos[index]["viewCount"])
                    videos[index]["duration"] = detail.get("duration", videos[index]["duration"])
                    videos[index]["thumbnails"] = detail.get("thumbnails", videos[index]["thumbnails"])
                    if "channel" in detail and isinstance(detail["channel"], dict):
                        videos[index]["channel"] = detail["channel"]
                    likes_count = detail.get("likesCount", {})
                    if likes_count and likes_count.get("text"):
                        videos[index]["likesCount"] = likes_count

            main_fields = Playlist._extract_main_fields(response)
            result: Dict[str, Any] = {"id": playlist_id}
            if "title" in main_fields:
                result["title"] = main_fields["title"]
            if "videoCount" in main_fields:
                result["videoCount"] = main_fields["videoCount"]
            if "channel" in main_fields:
                result["channel"] = main_fields["channel"]
            if "thumbnails" in main_fields:
                result["thumbnails"] = main_fields["thumbnails"]
            result["videos"] = videos
            result["url"] = f"https://www.youtube.com/playlist?list={playlist_id}"
            if "description" in main_fields:
                result["description"] = main_fields["description"]
            return result
            
        except Exception as e:
            print(f"Playlist.get() error: {e}")
            return None
