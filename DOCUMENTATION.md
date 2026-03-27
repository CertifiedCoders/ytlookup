# ytlookup Documentation

Production-grade guide for `ytlookup` users who want reliable, code-accurate behavior, complete response contracts, and practical async usage patterns.

---

## Table of Contents

- [What ytlookup Exposes](#what-ytlookup-exposes)
- [Install and Runtime Requirements](#install-and-runtime-requirements)
- [Quick Start](#quick-start)
- [Behavior Contract (All APIs)](#behavior-contract-all-apis)
- [Video API](#video-api)
- [Search API](#search-api)
- [Playlist API](#playlist-api)
- [Response Field Contracts](#response-field-contracts)
- [Performance Notes](#performance-notes)
- [Advanced Usage Patterns](#advanced-usage-patterns)
- [Troubleshooting](#troubleshooting)

---

## What ytlookup Exposes

`ytlookup` exports three async entry points:

| Export | Type | Purpose |
|---|---|---|
| `Video` | class | Fetch one video by URL or ID |
| `videosearch` | async function | Search YouTube videos only |
| `Playlist` | class | Fetch playlist metadata and items |

```python
from ytlookup import Video, videosearch, Playlist
```

---

## Install and Runtime Requirements

```bash
pip install ytlookup
```

- Python: `>=3.8`
- Async HTTP dependency used internally: `aiohttp`
- No API key setup required for consumers

---

## Quick Start

```python
import asyncio
from ytlookup import Video, videosearch, Playlist

async def main():
    video = await Video.get("dQw4w9WgXcQ")
    print(video["title"] if video else "Video not found")

    results = await videosearch("python async tutorial", limit=3)
    print([item["title"] for item in results])

    playlist = await Playlist.get("PLR3u2N_ix5ZV6U0lF6gqiyaSI0maRpEJQ", limit=5)
    print(playlist["title"] if playlist else "Playlist not found")

asyncio.run(main())
```

---

## Behavior Contract (All APIs)

These rules are based on the current implementation:

- All public APIs are async and must be awaited.
- Input validation errors raise `ValueError` for invalid parameters.
- Network/parsing/runtime errors are swallowed internally:
  - `Video.get(...)` returns `None`
  - `Playlist.get(...)` returns `None`
  - `videosearch(...)` returns `[]`
- Result dictionaries may have missing optional fields depending on what YouTube returns.

---

## Video API

### Signature

```python
await Video.get(url_or_id: str, fetch_extras: bool = False) -> dict | None
```

### Input Support

`Video.get()` accepts:

- Raw 11-char video IDs: `dQw4w9WgXcQ`
- Watch URLs: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Short URLs: `https://youtu.be/dQw4w9WgXcQ`
- Embed URLs: `https://www.youtube.com/embed/dQw4w9WgXcQ`
- Live URLs: `https://www.youtube.com/live/dQw4w9WgXcQ`
- Shorts URLs: `https://www.youtube.com/shorts/dQw4w9WgXcQ`

Invalid input raises:

```python
ValueError("Invalid video URL or ID: ...")
```

### Options

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `url_or_id` | `str` | required | Any supported video URL or 11-char ID |
| `fetch_extras` | `bool` | `False` | If `True`, attempts to add `publishedTime` and `likesCount` |

### Example

```python
# Fast path
video = await Video.get("dQw4w9WgXcQ")

# Enriched path (extra request to "next" endpoint)
video_full = await Video.get("dQw4w9WgXcQ", fetch_extras=True)
```

### Returned Shape

Base fields:

```json
{
  "id": "dQw4w9WgXcQ",
  "title": "Never Gonna Give You Up",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "channel": {
    "name": "Rick Astley",
    "id": "UCuAXFkgsw1L7xaCfnd5JJOw"
  },
  "isLive": false,
  "duration": {
    "seconds": 213,
    "text": "3:33"
  },
  "viewCount": {
    "text": "1,234,567 views",
    "short": "1.2M views"
  },
  "description": "...",
  "thumbnails": [
    {"url": "...", "width": 120, "height": 90}
  ],
  "keywords": ["..."]
}
```

Optional fields (only if found):

```json
{
  "publishedTime": "Oct 24, 2009",
  "likesCount": {
    "text": "18,872,033 likes",
    "short": "18.9M likes"
  }
}
```

Notes:
- If YouTube thumbnails are missing, fallback thumbnail URLs are generated.
- `likesCount` may be absent even when `fetch_extras=True` if extraction fails.

---

## Search API

### Signature

```python
await videosearch(
    query: str,
    limit: int = 10,
    language: str = "en",
    region: str = "US"
) -> list[dict]
```

### Validation

- `query` must be a non-empty `str`, else raises `ValueError`.
- `limit` must be `>= 1`, else raises `ValueError`.

### Behavior

- Searches videos only (internally sets a "videos only" filter).
- Traverses continuation tokens until:
  - requested `limit` is reached, or
  - no more pages are available.
- Deduplicates by video ID across pages.
- On internal request/parsing errors, returns `[]`.

### Example

```python
results = await videosearch(
    query="python tutorial",
    limit=10,
    language="en",
    region="US",
)
```

### Item Shape

```json
{
  "id": "video_id",
  "title": "Video Title",
  "channel": {
    "name": "Channel Name",
    "id": "UC..."
  },
  "duration": {
    "seconds": 184,
    "text": "3:04"
  },
  "viewCount": {
    "text": "1,234,567 views",
    "short": "1.2M views"
  },
  "publishedTime": "5 months ago",
  "thumbnails": [
    {"url": "...", "width": 120, "height": 90}
  ],
  "url": "https://www.youtube.com/watch?v=video_id",
  "type": "video"
}
```

---

## Playlist API

### Signature

```python
await Playlist.get(
    url_or_id: str,
    limit: int = 100,
    fetch_video_details: bool = False
) -> dict | None
```

### Input Support

`Playlist.get()` accepts:

- Playlist IDs (alphanumeric/`_`/`-`, length `>=13`)
- Playlist URLs with `list=...`

Invalid input raises:

```python
ValueError("Invalid playlist URL or ID: ...")
```

### Options

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `url_or_id` | `str` | required | Playlist ID or URL |
| `limit` | `int` | `100` | Max number of playlist videos to parse |
| `fetch_video_details` | `bool` | `False` | If `True`, fetches extra per-video details using `Video.get(video_id)` |

### Behavior

- Pulls playlist data from the InnerTube `browse` endpoint with `browseId="VL{playlist_id}"`.
- Builds each playlist video item from `playlistVideoRenderer`.
- Stops after collecting `limit` entries.
- Returns `None` on internal request/parsing errors.

When `fetch_video_details=True`, each video item is conditionally refreshed with:
- `viewCount`
- `duration`
- `thumbnails`
- `channel` (if available)

`likesCount` is only added if present in detail response; current detail path (`Video.get(..., fetch_extras=False)`) generally does not include likes.

### Example

```python
playlist = await Playlist.get(
    "https://youtube.com/playlist?list=PLR3u2N_ix5ZV6U0lF6gqiyaSI0maRpEJQ",
    limit=20,
    fetch_video_details=False,
)
```

### Returned Shape

```json
{
  "id": "PL...",
  "title": "Playlist Title",
  "videoCount": 100,
  "channel": {
    "name": "Channel Name",
    "id": "UC..."
  },
  "thumbnails": [
    {"url": "...", "width": 120, "height": 90}
  ],
  "videos": [
    {
      "id": "video_id",
      "title": "Video Title",
      "duration": {"seconds": 212, "text": "3:32"},
      "viewCount": {"text": "1,234,567 views", "short": "1.2M views"},
      "thumbnails": [{"url": "...", "width": 120, "height": 90}],
      "channel": {"name": "Channel Name", "id": "UC..."},
      "url": "https://www.youtube.com/watch?v=video_id"
    }
  ],
  "url": "https://www.youtube.com/playlist?list=PL...",
  "description": "Playlist description"
}
```

---

## Response Field Contracts

### Count Objects

Where counts are returned (`viewCount`, optional `likesCount`):

```json
{
  "text": "1,234 views",
  "short": "1.2K views"
}
```

Notes:
- For zero values, short format may be `"0"` (without label) in current formatter behavior.

### Duration Objects

```json
{
  "seconds": 213,
  "text": "3:33"
}
```

Notes:
- `text` generated by internal formatter is minute-based (`M:SS`) when synthesized.
- Parsed durations from YouTube can still appear as `H:MM:SS`.

### Thumbnail Objects

```json
{
  "url": "https://i.ytimg.com/vi/.../hqdefault.jpg",
  "width": 480,
  "height": 360
}
```

Notes:
- Query strings are stripped from thumbnail URLs.

---

## Performance Notes

| Call | Typical Request Pattern | Relative Cost |
|---|---|---|
| `Video.get(..., fetch_extras=False)` | Single `player` request | Fast |
| `Video.get(..., fetch_extras=True)` | `player` + `next` request | Medium |
| `videosearch(...)` | One or more `search` requests via continuation | Depends on `limit` |
| `Playlist.get(..., fetch_video_details=False)` | Single `browse` request | Fast/Medium |
| `Playlist.get(..., fetch_video_details=True)` | `browse` + one `Video.get` per video | High |

---

## Advanced Usage Patterns

### Concurrent Video Fetch

```python
import asyncio
from ytlookup import Video

video_ids = ["dQw4w9WgXcQ", "M7lc1UVf-VE", "aqz-KE-bpKQ"]
videos = await asyncio.gather(*(Video.get(v) for v in video_ids))
```

### Guarded Timeout

```python
import asyncio
from ytlookup import videosearch

results = await asyncio.wait_for(videosearch("python", limit=5), timeout=10)
```

### Fail-Safe Wrappers

```python
from ytlookup import Video

async def safe_video(url_or_id: str):
    try:
        return await Video.get(url_or_id)
    except ValueError:
        return None
```

---

## Troubleshooting

### `ValueError: Invalid video URL or ID`

- Ensure a valid 11-character video ID or supported YouTube URL format.

### `ValueError: Invalid playlist URL or ID`

- Ensure playlist ID is valid or URL contains `list=...`.

### Empty search results

- Query may be too narrow or region/language filters may reduce matches.
- Internal request failures also return `[]` by design.

### `None` from `Video.get()` or `Playlist.get()`

- Usually indicates request/parsing failure or unavailable content.
- Use retries with timeout control in production workflows.
