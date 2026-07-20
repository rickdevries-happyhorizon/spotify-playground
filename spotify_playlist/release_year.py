"""Helpers for parsing and extracting release years."""

from __future__ import annotations

from typing import Any


def normalize_release_year(value: int | str | None) -> int | None:
    """Normalize Spotify/YouTube release values to a four-digit year."""
    if value is None:
        return None

    if isinstance(value, int):
        year = value
    else:
        text = str(value).strip()
        if not text or len(text) < 4 or not text[:4].isdigit():
            return None
        year = int(text[:4])

    if 1900 <= year <= 2100:
        return year
    return None


def release_year_from_youtube_info(info: dict[str, Any]) -> int | None:
    """Extract a release year from a yt-dlp info dict."""
    year = normalize_release_year(info.get('release_year'))
    if year is not None:
        return year

    return normalize_release_year(info.get('release_date'))
