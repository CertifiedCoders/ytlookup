"""
Request handlers for YouTube API communication
"""

import aiohttp
from typing import Dict, Any, Optional
from .formatting import (
    duration_text_to_seconds,
    format_count,
    get_text,
    normalize_thumbnails,
    parse_int_from_text,
)


class RequestHandler:
    """Handles HTTP requests to YouTube's InnerTube API"""
    
    BASE_URL = "https://www.youtube.com/youtubei/v1"
    
    # YouTube InnerTube API key (public, used by YouTube web client)
    API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    
    # Client context for InnerTube API  
    # Using WEB client for search/browse (most stable)
    CONTEXT = {
        "client": {
            "clientName": "WEB",
            "clientVersion": "2.20231219.01.00",
            "hl": "en",
            "gl": "US",
        }
    }
    
    @staticmethod
    async def make_request(
        endpoint: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Make async request to YouTube InnerTube API
        
        Args:
            endpoint: API endpoint (search, browse, player, etc.)
            data: Request payload (will be merged with context)
            context: Optional client context override
            timeout: Request timeout in seconds
            
        Returns:
            JSON response as dictionary or None on error
        """
        url = f"{RequestHandler.BASE_URL}/{endpoint}"
        params = {"key": RequestHandler.API_KEY}
        
        # Add videoId to params for player endpoint
        if endpoint == "player" and "videoId" in data:
            params["videoId"] = data["videoId"]
            params["contentCheckOk"] = "true"
            params["racyCheckOk"] = "true"
        
        # Build request payload - context must be inside the JSON body
        context_data = context or RequestHandler.CONTEXT
        request_context: Dict[str, Any] = {}
        for key, value in context_data.items():
            if key == "client" and isinstance(value, dict):
                request_context[key] = value.copy()
            else:
                request_context[key] = value
        request_data = {"context": request_context}
        request_data.update(data)
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    params=params,
                    headers=headers,
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Request failed with status {response.status}")
                        return None
        except aiohttp.ClientError as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None


class ComponentHandler:
    """Handles parsing of YouTube response components"""
    
    @staticmethod
    def extract_video_renderer(renderer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract video information from videoRenderer component"""
        try:
            video_id = renderer.get("videoId")
            if not video_id:
                return None
            
            # Extract title
            title = get_text(renderer.get("title", {}))
            
            # Extract channel
            channel_runs = renderer.get("ownerText", {}).get("runs", [])
            channel = channel_runs[0].get("text", "") if channel_runs else ""
            channel_id = channel_runs[0].get("navigationEndpoint", {}).get("browseEndpoint", {}).get("browseId", "") if channel_runs else ""
            
            # Extract duration
            duration_text = get_text(renderer.get("lengthText", {}))
            duration_seconds = duration_text_to_seconds(duration_text)
            
            # Extract views
            view_count_text = get_text(renderer.get("viewCountText", {}))
            view_count_value = parse_int_from_text(view_count_text) or 0
            
            # Extract publish time
            publish_time = get_text(renderer.get("publishedTimeText", {}))
            
            # Extract thumbnails
            thumbnails = renderer.get("thumbnail", {}).get("thumbnails", [])
            thumbnail_items = normalize_thumbnails(thumbnails)
            
            return {
                "id": video_id,
                "title": title,
                "channel": {
                    "name": channel,
                    "id": channel_id
                },
                "duration": {
                    "seconds": duration_seconds,
                    "text": duration_text,
                },
                "viewCount": format_count(view_count_value, "views"),
                "publishedTime": publish_time,
                "thumbnails": thumbnail_items,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "type": "video"
            }
        except Exception as e:
            print(f"Error extracting video renderer: {e}")
            return None
