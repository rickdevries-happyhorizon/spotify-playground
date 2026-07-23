#!/usr/bin/env python3
"""Look up a single Spotify playlist for the web UI."""
from __future__ import annotations

import json
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Playlist ID required"}))
        return 1

    from spotify_playlist.fetch_playlist_info import fetch_playlist_info
    from spotify_playlist.parse_spotify_playlist_id import parse_spotify_playlist_id
    from spotify_playlist.spotify_api_client import get_quiet_spotify_client

    spotify_id = parse_spotify_playlist_id(sys.argv[1])
    if not spotify_id:
        print(json.dumps({"error": "Invalid playlist ID"}))
        return 1

    try:
        sp = get_quiet_spotify_client()
        info = fetch_playlist_info(sp, spotify_id)
        print(json.dumps(info))
        return 0
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
