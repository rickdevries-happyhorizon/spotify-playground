"""File-backed import job tracking for web-triggered track imports."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db_store import load_playlists_config

from spotify_playlist.export_new_tracks_since_date import export_new_tracks_since_date
from spotify_playlist.spotify_api_client import get_quiet_spotify_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JOBS_DIR = PROJECT_ROOT / ".import_jobs"
_jobs_lock = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_path(job_id: str) -> Path:
    safe_id = "".join(ch for ch in job_id if ch.isalnum() or ch in "-")
    return JOBS_DIR / f"{safe_id}.json"


def _read_job_file(job_id: str) -> dict[str, Any] | None:
    path = _job_path(job_id)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_job_file(job: dict[str, Any]) -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = _job_path(job["job_id"])
    path.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")


def _snapshot_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "phase": job["phase"],
        "message": job["message"],
        "playlist_index": job.get("playlist_index"),
        "playlist_total": job.get("playlist_total"),
        "playlist_name": job.get("playlist_name"),
        "playlist_image_url": job.get("playlist_image_url"),
        "tracks_found": job.get("tracks_found"),
        "total_tracks_found": job.get("total_tracks_found"),
        "total_processed": job.get("total_processed"),
        "inserted": job.get("inserted"),
        "skipped": job.get("skipped"),
        "since_date": job.get("since_date"),
        "until_date": job.get("until_date"),
        "result": job.get("result"),
        "error": job.get("error"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
    }


def _update_job(job_id: str, **fields: Any) -> None:
    with _jobs_lock:
        job = _read_job_file(job_id)
        if not job:
            return
        job.update(fields)
        job["updated_at"] = _utc_now()
        _write_job_file(job)


def _on_progress(job_id: str, event: dict[str, Any]) -> None:
    phase = event.get("phase", "running")
    status = "error" if phase == "error" else "running"
    if phase == "done":
        status = "done"

    updates: dict[str, Any] = {
        "status": status,
        "phase": phase,
        "message": event.get("message", ""),
    }
    for key in (
        "playlist_index",
        "playlist_total",
        "playlist_name",
        "playlist_image_url",
        "tracks_found",
        "total_tracks_found",
        "total_processed",
        "inserted",
        "skipped",
        "since_date",
        "until_date",
    ):
        if key in event:
            updates[key] = event[key]

    _update_job(job_id, **updates)


def run_import_job(job_id: str, tracking_playlists: list[str]) -> None:
    """Execute the import and persist progress to the job file."""
    try:
        sp = get_quiet_spotify_client()

        def progress(event: dict[str, Any]) -> None:
            _on_progress(job_id, event)

        result = export_new_tracks_since_date(
            sp,
            tracking_playlists,
            on_progress=progress,
            quiet=True,
        )
        _update_job(
            job_id,
            status="done",
            phase="done",
            message="Import complete",
            result=result,
            inserted=result.get("inserted", 0),
            skipped=result.get("skipped", 0),
            total_processed=result.get("total_processed", 0),
            tracks_found=result.get("tracks_found", 0),
            since_date=result.get("since_date"),
            until_date=result.get("until_date"),
        )
    except Exception as exc:
        _update_job(
            job_id,
            status="error",
            phase="error",
            message=str(exc),
            error=str(exc),
        )


def create_import_job() -> tuple[str | None, str | None]:
    """Validate config, create a job file, and start a background import thread."""
    config = load_playlists_config()
    tracking_playlists = config.get("tracking_playlists") or []
    if not tracking_playlists:
        return None, "No tracking playlists configured. Add them in Settings first."

    try:
        get_quiet_spotify_client()
    except RuntimeError as exc:
        return None, str(exc)

    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "running",
        "phase": "queued",
        "message": "Preparing import…",
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "result": None,
        "error": None,
    }
    _write_job_file(job)

    thread = threading.Thread(
        target=run_import_job,
        args=(job_id, tracking_playlists),
        daemon=True,
    )
    thread.start()
    return job_id, None


def get_import_job(job_id: str) -> dict[str, Any] | None:
    job = _read_job_file(job_id)
    if not job:
        return None
    return _snapshot_job(job)
