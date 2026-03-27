import re
from typing import Any, Dict, List, Optional


def get_text(data: Any) -> str:
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return ""
    simple = data.get("simpleText")
    if isinstance(simple, str):
        return simple
    runs = data.get("runs", [])
    if not isinstance(runs, list):
        return ""
    return "".join(run.get("text", "") for run in runs if isinstance(run, dict))


def parse_int_from_text(text: str) -> Optional[int]:
    match = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*([KMB])?", text or "", re.IGNORECASE)
    if not match:
        return None
    number = float(match.group(1).replace(",", ""))
    suffix = (match.group(2) or "").upper()
    multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(suffix, 1)
    return int(number * multiplier)


def duration_text_to_seconds(duration_text: str) -> int:
    if not duration_text:
        return 0
    parts = duration_text.split(":")
    if not all(part.isdigit() for part in parts):
        return 0
    total = 0
    for part in parts:
        total = total * 60 + int(part)
    return total


def seconds_to_duration_text(seconds: int) -> str:
    minutes, secs = divmod(max(seconds, 0), 60)
    return f"{minutes}:{secs:02d}"


def format_compact_number(value: int) -> str:
    if value >= 1_000_000_000:
        compact = f"{value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        compact = f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        compact = f"{value / 1_000:.1f}K"
    else:
        return str(value)
    return compact.replace(".0B", "B").replace(".0M", "M").replace(".0K", "K")


def format_count(value: int, label: str) -> Dict[str, str]:
    short = format_compact_number(value)
    if value > 0:
        short = f"{short} {label}"
    return {
        "text": f"{value:,} {label}",
        "short": short,
    }


def normalize_thumbnails(thumbnails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output = []
    for thumb in thumbnails or []:
        url = thumb.get("url", "")
        output.append({
            "url": url.split("?")[0] if isinstance(url, str) else "",
            "width": int(thumb.get("width", 0) or 0),
            "height": int(thumb.get("height", 0) or 0),
        })
    return output

