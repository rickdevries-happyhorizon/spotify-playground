"""File-backed import job tracking for web-triggered track imports."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import spotify_playlist.config as config
from db_store import load_playlists_config

from spotify_playlist.export_new_tracks_since_date import export_new_tracks_since_date
from spotify_playlist.spotify_api_client import get_quiet_spotify_client
from spotify_playlist.sync_artist_releases import sync_artist_releases

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
        "artist_index": job.get("artist_index"),
        "artist_total": job.get("artist_total"),
        "artist_name": job.get("artist_name"),
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
        "artist_index",
        "artist_total",
        "artist_name",
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


def playlists_for_import(playlists_config: dict[str, Any] | None = None) -> list[str]:
    """Tracking playlists plus destination (so artist releases land in new_tracks)."""
    config_data = playlists_config if playlists_config is not None else load_playlists_config()
    playlist_ids = list(config_data.get("tracking_playlists") or [])
    destination = (config_data.get("destination_playlist") or "").strip()
    if destination and destination not in playlist_ids:
        playlist_ids = [destination, *playlist_ids]
    return playlist_ids


def run_import_job(job_id: str, tracking_playlists: list[str] | None = None) -> None:
    """Execute artist sync + playlist import and persist progress to the job file."""
    try:
        sp = get_quiet_spotify_client()

        def progress(event: dict[str, Any]) -> None:
            _on_progress(job_id, event)

        artist_result: dict[str, Any] | None = None
        if config.CHECK_ARTIST_RELEASES:
            artist_result = sync_artist_releases(sp, on_progress=progress, quiet=True)

        playlist_ids = tracking_playlists if tracking_playlists is not None else playlists_for_import()
        if not playlist_ids:
            raise RuntimeError(
                "No tracking or destination playlist configured. Add them in Settings first."
            )

        result = export_new_tracks_since_date(
            sp,
            playlist_ids,
            on_progress=progress,
            quiet=True,
        )
        if artist_result is not None:
            result["artist_sync"] = artist_result

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
    playlists_config = load_playlists_config()
    playlist_ids = playlists_for_import(playlists_config)
    if not playlist_ids:
        return None, "No tracking or destination playlist configured. Add them in Settings first."

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
        args=(job_id, playlist_ids),
        daemon=True,
    )
    thread.start()
    return job_id, None


def get_import_job(job_id: str) -> dict[str, Any] | None:
    job = _read_job_file(job_id)
    if not job:
        return None
    return _snapshot_job(job)
