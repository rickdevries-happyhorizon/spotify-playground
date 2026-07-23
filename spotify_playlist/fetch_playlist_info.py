from __future__ import annotations

from typing import Any, Dict, Iterable, List


def fetch_playlist_info(sp, playlist_id: str) -> Dict[str, Any]:
    """Look up a playlist on Spotify and return normalized metadata."""
    playlist_id = (playlist_id or "").strip()
    if not playlist_id:
        raise ValueError("Playlist ID is required")

    try:
        info = sp.playlist(playlist_id, fields="name,images")
    except Exception as exc:
        raise ValueError(f"Spotify playlist not found: {playlist_id}") from exc

    name = (info.get("name") or "").strip() or playlist_id
    images = info.get("images") or []
    artwork_url = None
    if images:
        artwork_url = images[0].get("url")

    return {
        "spotify_id": playlist_id,
        "name": name,
        "artwork_url": artwork_url,
    }


def resolve_playlist_details(sp, spotify_ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    """Resolve Spotify metadata for a unique list of playlist IDs."""
    unique_ids: List[str] = []
    for spotify_id in spotify_ids:
        spotify_id = (spotify_id or "").strip()
        if spotify_id and spotify_id not in unique_ids:
            unique_ids.append(spotify_id)

    details: Dict[str, Dict[str, Any]] = {}
    for spotify_id in unique_ids:
        details[spotify_id] = fetch_playlist_info(sp, spotify_id)
    return details
