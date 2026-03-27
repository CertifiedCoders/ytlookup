import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ytlookup import Playlist, Video, videosearch


def _assert_keys(payload, keys, label):
    missing = [key for key in keys if key not in payload]
    assert not missing, f"{label} missing keys: {missing}"


async def run_smoke_tests():
    video_id = "dQw4w9WgXcQ"

    print("Testing Video.get(fetch_extras=True)...")
    video_full = await Video.get(video_id, fetch_extras=True)
    assert video_full is not None, "Video.get(fetch_extras=True) returned None"
    assert video_full.get("id") == video_id, "Video ID mismatch in extras mode"
    _assert_keys(video_full, ["title", "url", "channel", "duration", "viewCount"], "Video extras mode")
    print("OK: Video.get(fetch_extras=True)")


    print("Testing videosearch()...")
    results = await videosearch("python tutorial", limit=3)
    assert isinstance(results, list), "videosearch() must return a list"
    assert len(results) > 0, "videosearch() returned no results"
    _assert_keys(results[0], ["id", "title", "url", "channel", "duration", "viewCount"], "Search result")
    print(f"OK: videosearch() ({len(results)} results)")

    print("Testing Playlist.get()...")
    playlist = await Playlist.get(
        "https://youtube.com/playlist?list=PLR3u2N_ix5ZV6U0lF6gqiyaSI0maRpEJQ",
        limit=3,
        fetch_video_details=False,
    )
    assert playlist is not None, "Playlist.get() returned None"
    assert playlist.get("id") == "PLR3u2N_ix5ZV6U0lF6gqiyaSI0maRpEJQ", "Playlist ID mismatch"
    _assert_keys(playlist, ["title", "url", "channel", "videoCount", "videos"], "Playlist")
    assert isinstance(playlist["videos"], list), "Playlist videos should be a list"
    assert len(playlist["videos"]) > 0, "Playlist videos list is empty"
    _assert_keys(playlist["videos"][0], ["id", "title", "url"], "Playlist video")
    print(f"OK: Playlist.get() ({len(playlist['videos'])} videos)")

    print("All smoke tests passed")
    return 0


def test_smoke():
    assert asyncio.run(run_smoke_tests()) == 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(run_smoke_tests()))
    except KeyboardInterrupt:
        raise SystemExit(130)
