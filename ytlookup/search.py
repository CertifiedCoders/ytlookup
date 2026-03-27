"""
Video search functionality
"""

from typing import List, Dict, Any, Tuple
from .handlers import RequestHandler, ComponentHandler


def _collect_search_nodes(data: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Collect video renderers and continuation tokens from search response"""
    video_renderers: List[Dict[str, Any]] = []
    continuation_tokens: List[str] = []
    stack: List[Any] = [data]

    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "videoRenderer" in node and isinstance(node["videoRenderer"], dict):
                video_renderers.append(node["videoRenderer"])

            token = (node.get("continuationCommand", {}) or {}).get("token")
            if isinstance(token, str) and token:
                continuation_tokens.append(token)

            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)

    return video_renderers, continuation_tokens


async def videosearch(
    query: str,
    limit: int = 10,
    language: str = "en",
    region: str = "US"
) -> List[Dict[str, Any]]:
    """
    Search for videos on YouTube (fast mode - no extra API calls per video)
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 10)
        language: Language code (default: "en")
        region: Region code (default: "US")
    
    Returns:
        List of video dictionaries with basic info from search results
    """
    
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
    
    if limit < 1:
        raise ValueError("Limit must be at least 1")
    
    search_context = {
        "client": {
            **RequestHandler.CONTEXT.get("client", {}),
            "hl": language,
            "gl": region,
        }
    }
    
    request_data = {
        "query": query,
        "params": "EgIQAQ%3D%3D"  # Filter for videos only
    }
    
    results = []
    continuation_token = None
    
    try:
        while len(results) < limit:
            if continuation_token:
                request_data = {"continuation": continuation_token}
            
            response = await RequestHandler.make_request("search", request_data, context=search_context)
            
            if not response:
                break
            
            video_renderers, continuation_tokens = _collect_search_nodes(response)

            existing_ids = {video.get("id") for video in results}
            for renderer in video_renderers:
                if len(results) >= limit:
                    break
                video = ComponentHandler.extract_video_renderer(renderer)
                if video and video.get("id") not in existing_ids:
                    results.append(video)
                    existing_ids.add(video.get("id"))

            # Find next continuation token
            next_token = None
            for token in continuation_tokens:
                if token != continuation_token:
                    next_token = token
                    break
            continuation_token = next_token

            if not continuation_token and len(results) < limit:
                break
        
        return results[:limit]
    
    except Exception as e:
        print(f"Search error: {e}")
        return []
