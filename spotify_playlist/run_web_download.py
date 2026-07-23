#!/usr/bin/env python3
"""CLI entry point for background download jobs started by the PHP web UI."""
from __future__ import annotations

import sys

from spotify_playlist.download_job_manager import get_download_job, run_download_job, _update_job
from spotify_playlist.download_youtube_wav import load_tracks_from_app


def _fail_job(job_id: str, message: str) -> int:
    _update_job(
        job_id,
        status="error",
        phase="error",
        message=message,
        error=message,
    )
    print(message, file=sys.stderr)
    return 1


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
        return _fail_job(job_id, "Download job missing output directory.")

    try:
        tracks = load_tracks_from_app()
    except ValueError as exc:
        return _fail_job(job_id, str(exc))
    except Exception as exc:
        return _fail_job(job_id, f"Could not load tracks from database: {exc}")

    run_download_job(job_id, tracks, output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
