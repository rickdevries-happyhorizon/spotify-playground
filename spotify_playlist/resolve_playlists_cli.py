#!/usr/bin/env python3
"""Resolve Spotify metadata for a list of playlist IDs (JSON array on stdin)."""
from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        raw = sys.stdin.read()
        spotify_ids = json.loads(raw) if raw.strip() else []
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON input"}))
        return 1

    if not isinstance(spotify_ids, list):
        print(json.dumps({"error": "Input must be a JSON array"}))
        return 1

    from spotify_playlist.fetch_playlist_info import resolve_playlist_details
    from spotify_playlist.spotify_api_client import get_quiet_spotify_client

    try:
        sp = get_quiet_spotify_client()
        details = resolve_playlist_details(sp, spotify_ids)
        print(json.dumps(details))
        return 0
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
