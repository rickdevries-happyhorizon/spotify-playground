"""Quiet Spotify client for web/API use (uses cached OAuth token)."""
from __future__ import annotations

from spotify_playlist.config import CACHE_FILE, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE
from spotify_playlist.deps import SpotifyOAuth, require_spotipy, spotipy


def get_quiet_spotify_client():
    """Return an authenticated Spotify client or raise RuntimeError."""
    require_spotipy()

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

    return spotipy.Spotify(auth_manager=auth_manager)
