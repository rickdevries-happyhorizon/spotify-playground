#!/usr/bin/env python3
"""CLI entry point for background download jobs started by the PHP web UI."""
from __future__ import annotations

import sys

from spotify_playlist.download_job_manager import get_download_job, run_download_job
from spotify_playlist.download_youtube_wav import load_tracks_from_app


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: run_web_download.py <job_id>", file=sys.stderr)
        return 1

    job_id = sys.argv[1]
    job = get_download_job(job_id)
    if job is None:
        print(f"Download job not found: {job_id}", file=sys.stderr)
        return 1

    output_dir = job.get("output_dir")
    if not output_dir:
        print(f"Download job missing output_dir: {job_id}", file=sys.stderr)
        return 1

    try:
        tracks = load_tracks_from_app()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    run_download_job(job_id, tracks, output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
