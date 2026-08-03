#!/usr/bin/env python3
"""Fetch Spotify listening stats for the web UI."""
from __future__ import annotations

import json
import sys


def main() -> int:
    from spotify_playlist.listening_stats import fetch_listening_stats
    from spotify_playlist.spotify_api_client import get_quiet_spotify_client

    try:
        sp = get_quiet_spotify_client()
        payload = fetch_listening_stats(sp)
        print(json.dumps(payload))
        return 0
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
