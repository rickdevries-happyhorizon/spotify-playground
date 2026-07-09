"""Shared helpers for storage backends (MySQL and text file)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse


def dt_to_iso_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat() + ("Z" if value.tzinfo is None else "")
    return str(value)


def parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


def normalize_reference_url(url: Optional[str]) -> Optional[str]:
    """Normalize reference URLs. YouTube links are stripped to watch?v=VIDEO_ID only."""
    if url is None:
        return None

    cleaned = url.strip()
    if not cleaned:
        return None

    parsed = urlparse(cleaned)
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]

    video_id: Optional[str] = None
    if host in ("youtube.com", "m.youtube.com", "music.youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith("/shorts/"):
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) >= 2 and parts[0] == "shorts":
                video_id = parts[1]
    elif host == "youtu.be":
        video_id = parsed.path.lstrip("/").split("/")[0] or None

    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"

    return cleaned
