<div align="center">

# 🎵 ytlookup

### *Blazing-fast async YouTube search library*

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/CertifiedCoders/ytlookup?style=for-the-badge&logo=github)](https://github.com/CertifiedCoders/ytlookup)
[![PyPI Version](https://img.shields.io/pypi/v/ytlookup?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/ytlookup/)


</div>

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

## ✨ Why ytlookup?

- ⚡ **Blazing fast:** Typical response time is around **50-100ms** with optimized InnerTube requests.
- 🔐 **No API key needed:** Zero setup, no quotas, and no external credential configuration.
- 🎯 **Simple developer experience:** Clean async API with typed return structures and predictable fields.
- 🚀 **Production-ready by design:** Includes robust parsing, fallback handling, and stable response formatting.
- 🐍 **Modern Python support:** Works on **Python 3.8-3.14** with a minimal dependency footprint (`aiohttp`).

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

## 📦 Installation

### Quick Install

```bash
pip install ytlookup
```

### From Source

```bash
git clone https://github.com/CertifiedCoders/ytlookup
cd ytlookup
pip install -e .
```

**Requirements:** Python 3.8+ and `aiohttp`

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

## 🚀 Quick Start

### Get Video Information (Fast Mode)

```python
import asyncio
from ytlookup import Video

async def main():
    # Lightning fast - ~50ms response time! ⚡
    video = await Video.get("dQw4w9WgXcQ")
    
    print(f"📹 {video['title']}")
    print(f"👤 {video['channel']['name']}")
    print(f"👁️  {video['viewCount']['short']}")
    print(f"⏱️  {video['duration']['text']}")

asyncio.run(main())
```

### Get Complete Information (With Extras)

```python
import asyncio
from ytlookup import Video

async def main():
    # Includes publishedTime and may include likes (~500ms)
    video = await Video.get("dQw4w9WgXcQ", fetch_extras=True)
    if not video:
        print("Video not found")
        return

    print(f"📅 Published: {video.get('publishedTime', 'N/A')}")
    likes = video.get("likesCount", {}).get("short", "N/A")
    print(f"👍 Likes: {likes}")

asyncio.run(main())
```

### Search YouTube Videos

```python
import asyncio
from ytlookup import videosearch

async def main():
    # Search with metadata
    videos = await videosearch("Python tutorial", limit=5)

    for video in videos:
        print(f"🎬 {video['title']}")
        print(f"   📊 {video['viewCount']['short']} • {video['duration']['text']}")
        print(f"   🔗 {video['url']}\n")

asyncio.run(main())
```

### Get Playlist Information

```python
import asyncio
from ytlookup import Playlist

async def main():
    # Fetch playlist with videos
    playlist = await Playlist.get("PLxxx...", limit=10)
    if not playlist:
        print("Playlist not found")
        return

    print(f"📋 {playlist['title']}")
    print(f"🎬 {playlist['videoCount']} videos")
    print(f"👤 {playlist['channel']['name']}")

    for video in playlist['videos']:
        print(f"  • {video['title']}")

asyncio.run(main())
```

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

## 📚 Detailed Guide

For complete API contracts, response shapes, and advanced usage patterns, see [`DOCUMENTATION.md`](DOCUMENTATION.md).

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

## 🛠️ Requirements

### Minimal Dependencies

- **Python:** 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- **aiohttp:** >= 3.8.0

That's it! No complex dependencies.

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

## 🤝 Contributing

Contributions are welcome and appreciated.

### Quick Start

1. Fork this repository
2. Create a branch (`git checkout -b feature/your-change`)
3. Make your changes and test locally
4. Commit with a clear message
5. Open a Pull Request

### Not sure where to start?

- Found a bug? Open an issue: [GitHub Issues](https://github.com/CertifiedCoders/ytlookup/issues)
- Have a feature idea? Share it in [GitHub Issues](https://github.com/CertifiedCoders/ytlookup/issues)
- Want to improve docs or examples? PRs are always welcome

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Copyright © 2026 CertifiedCoders**

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

### 🔖 Credits & Acknowledgments

- **Special thanks** to [alexmercerind](https://github.com/alexmercerind) for [youtube-search-python](https://github.com/alexmercerind/youtube-search-python)
- **Special thanks** to [aiohttp](https://github.com/aio-libs/aiohttp)
- Crafted with passion by [CertifiedCoders](https://github.com/CertifiedCoders)
- Special thanks to all contributors and users of ytlookup