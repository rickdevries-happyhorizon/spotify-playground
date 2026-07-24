#!/usr/bin/env python3
"""CLI entry point for background sync jobs started by the PHP web UI."""
from __future__ import annotations

import sys

from spotify_playlist.sync_job_manager import get_sync_job, run_sync_job


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: run_web_sync.py <job_id>", file=sys.stderr)
        return 1

    job_id = sys.argv[1]
    if get_sync_job(job_id) is None:
        print(f"Sync job not found: {job_id}", file=sys.stderr)
        return 1

    run_sync_job(job_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
