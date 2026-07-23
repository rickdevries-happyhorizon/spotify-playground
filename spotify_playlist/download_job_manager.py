"""File-backed download job tracking for web-triggered AIFF downloads."""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from spotify_playlist.config import YOUTUBE_DOWNLOAD_DIR
from spotify_playlist.download_youtube_wav import download_youtube_tracks, load_tracks_from_app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JOBS_DIR = PROJECT_ROOT / ".download_jobs"
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
        "track_index": job.get("track_index"),
        "track_total": job.get("track_total"),
        "track_name": job.get("track_name"),
        "success_count": job.get("success_count"),
        "error_count": job.get("error_count"),
        "last_error": job.get("last_error"),
        "output_dir": job.get("output_dir"),
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
        "track_index",
        "track_total",
        "track_name",
        "success_count",
        "error_count",
        "last_error",
    ):
        if key in event:
            updates[key] = event[key]

    _update_job(job_id, **updates)


def _resolve_output_dir() -> tuple[str | None, str | None]:
    raw_dir = (YOUTUBE_DOWNLOAD_DIR or "").strip()
    if not raw_dir:
        return None, "No download directory configured. Set YOUTUBE_DOWNLOAD_DIR in config.py."

    directory = os.path.abspath(os.path.expanduser(raw_dir))
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as exc:
        return None, f"Could not create download directory: {exc}"

    return directory, None


def resolve_output_dir() -> tuple[str | None, str | None]:
    """Return the configured download directory, or an error message."""
    return _resolve_output_dir()


def run_download_job(job_id: str, tracks: list[dict], output_dir: str) -> None:
    """Execute the download and persist progress to the job file."""
    try:
        def progress(event: dict[str, Any]) -> None:
            _on_progress(job_id, event)

        success_count, error_count = download_youtube_tracks(
            tracks,
            output_dir,
            overwrite=False,
            tag_metadata=True,
            on_progress=progress,
        )
        final_job = _read_job_file(job_id) or {}
        last_error = final_job.get("last_error")
        if success_count == 0 and error_count > 0:
            message = last_error or "No tracks were downloaded."
            _update_job(
                job_id,
                status="error",
                phase="error",
                message=message,
                error=message,
                success_count=success_count,
                error_count=error_count,
                result={
                    "success_count": success_count,
                    "error_count": error_count,
                    "output_dir": output_dir,
                },
            )
            return

        _update_job(
            job_id,
            status="done",
            phase="done",
            message="Download complete",
            success_count=success_count,
            error_count=error_count,
            result={
                "success_count": success_count,
                "error_count": error_count,
                "output_dir": output_dir,
            },
        )
    except Exception as exc:
        _update_job(
            job_id,
            status="error",
            phase="error",
            message=str(exc),
            error=str(exc),
        )


def create_download_job() -> tuple[str | None, str | None]:
    """Validate config, create a job file, and start a background download thread."""
    output_dir, error = _resolve_output_dir()
    if error:
        return None, error

    try:
        tracks = load_tracks_from_app()
    except ValueError as exc:
        return None, str(exc)
    except Exception as exc:
        return None, f"Could not load tracks from database: {exc}"

    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "running",
        "phase": "queued",
        "message": "Preparing download…",
        "track_total": len(tracks),
        "output_dir": output_dir,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "result": None,
        "error": None,
    }
    _write_job_file(job)

    thread = threading.Thread(
        target=run_download_job,
        args=(job_id, tracks, output_dir),
        daemon=True,
    )
    thread.start()
    return job_id, None


def get_download_job(job_id: str) -> dict[str, Any] | None:
    job = _read_job_file(job_id)
    if not job:
        return None
    return _snapshot_job(job)
