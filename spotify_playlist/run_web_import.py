#!/usr/bin/env python3
"""CLI entry point for background import jobs started by the PHP web UI."""
from __future__ import annotations

import sys

from spotify_playlist.import_job_manager import get_import_job, playlists_for_import, run_import_job


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: run_web_import.py <job_id>", file=sys.stderr)
        return 1

    job_id = sys.argv[1]
    if get_import_job(job_id) is None:
        print(f"Import job not found: {job_id}", file=sys.stderr)
        return 1

    playlist_ids = playlists_for_import()
    if not playlist_ids:
        return 1

    run_import_job(job_id, playlist_ids)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
