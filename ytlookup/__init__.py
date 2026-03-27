"""
ytlookup - Blazing-Fast Async YouTube Search Library
Fast, simple, and efficient async library for YouTube video and playlist searches.
"""

from .search import videosearch
from .video import Video
from .playlist import Playlist

__version__ = "1.0.0"
__author__ = "Certified Coders"
__license__ = "MIT"

__all__ = [
    "videosearch",
    "Video",
    "Playlist",
]
