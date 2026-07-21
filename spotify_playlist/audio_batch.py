"""Shared helpers for batch audio file processing."""

from __future__ import annotations

import os
import time
import urllib.error
from datetime import datetime, timezone

from spotify_playlist.deps import SpotifyException

AUDIO_EXTENSIONS = ('.wav', '.aiff', '.aif')
DEFAULT_MUSIC_DIR = '/Volumes/ShortJack/music'
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')


def discover_audio_files(directory: str) -> list[str]:
    audio_files: list[str] = []
    for root, _dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.startswith('._'):
                continue
            if not filename.lower().endswith(AUDIO_EXTENSIONS):
                continue
            audio_files.append(os.path.join(root, filename))
    return sorted(audio_files)


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def spotify_call_with_retry(callable_fn, *, max_attempts: int = 5):
    delay = 1.0
    last_exc: Exception | None = None
    for _attempt in range(max_attempts):
        try:
            return callable_fn()
        except SpotifyException as exc:
            last_exc = exc
            message = str(exc).lower()
            if '429' in message or 'rate limit' in message:
                time.sleep(delay)
                delay = min(delay * 2, 30.0)
                continue
            raise
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 429:
                time.sleep(delay)
                delay = min(delay * 2, 30.0)
                continue
            raise
    if last_exc is not None:
        raise last_exc
    raise RuntimeError('Spotify call failed without exception')
