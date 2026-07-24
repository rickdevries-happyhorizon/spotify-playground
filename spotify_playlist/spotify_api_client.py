"""Quiet Spotify client for web/API use (uses cached OAuth token)."""
from __future__ import annotations

import threading
import time
from typing import Any

from spotify_playlist.config import CACHE_FILE, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE
from spotify_playlist.deps import SPOTIPY_AVAILABLE, SpotifyOAuth, spotipy

# Stay under Spotify's rate limit (~180 req/min for dev apps).
_DEFAULT_MIN_INTERVAL = 0.35


def apply_rate_limit(sp: Any, min_interval: float = _DEFAULT_MIN_INTERVAL) -> Any:
    """Throttle all Spotify API calls to reduce 429 rate-limit stalls."""
    lock = threading.Lock()
    last_call = 0.0
    original = sp._internal_call

    def throttled_internal_call(method, url, payload, params):
        nonlocal last_call
        with lock:
            now = time.monotonic()
            wait = min_interval - (now - last_call)
            if wait > 0:
                time.sleep(wait)
            last_call = time.monotonic()
        return original(method, url, payload, params)

    sp._internal_call = throttled_internal_call
    return sp


def get_quiet_spotify_client(*, rate_limit: bool = True):
    """Return an authenticated Spotify client or raise RuntimeError."""
    if not SPOTIPY_AVAILABLE:
        raise RuntimeError(
            "spotipy is not installed. Install dependencies with: pip install -r requirements.txt"
        )

    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_FILE,
        open_browser=False,
    )

    token_info = auth_manager.get_cached_token()
    if not token_info:
        raise RuntimeError(
            "Spotify login required. Run a CLI menu option first to authenticate."
        )

    if auth_manager.is_token_expired(token_info):
        try:
            token_info = auth_manager.refresh_access_token(token_info["refresh_token"])
        except Exception as exc:
            raise RuntimeError(
                "Spotify session expired. Run a CLI menu option to log in again."
            ) from exc

    sp = spotipy.Spotify(
        auth_manager=auth_manager,
        requests_timeout=20,
        retries=2,
        status_retries=2,
        backoff_factor=0.3,
    )
    if rate_limit:
        apply_rate_limit(sp)
    return sp
