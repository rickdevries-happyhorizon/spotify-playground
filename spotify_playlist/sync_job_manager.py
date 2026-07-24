"""File-backed sync job tracking for web-triggered source→destination sync."""

from __future__ import annotations

import fcntl
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db_store import load_artist_discovery_enabled, load_playlists_config

from spotify_playlist.spotify_api_client import get_quiet_spotify_client
from spotify_playlist.sync_playlists import sync_playlists

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JOBS_DIR = PROJECT_ROOT / ".sync_jobs"
WORKER_LOCK_PATH = JOBS_DIR / ".worker.lock"
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
    for _ in range(5):
        try:
            raw = path.read_text(encoding="utf-8")
            if raw.strip():
                return json.loads(raw)
        except (OSError, json.JSONDecodeError):
            pass
        time.sleep(0.05)
    return None


def _write_job_file(job: dict[str, Any]) -> None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = _job_path(job["job_id"])
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(job, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)


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
        "tracks_new": job.get("tracks_new"),
        "tracks_added": job.get("tracks_added"),
        "playlists_checked": job.get("playlists_checked"),
        "artist_index": job.get("artist_index"),
        "artist_total": job.get("artist_total"),
        "artist_name": job.get("artist_name"),
        "artist_releases_found": job.get("artist_releases_found"),
        "artist_releases_new": job.get("artist_releases_new"),
        "discovery_releases_found": job.get("discovery_releases_found"),
        "discovery_releases_new": job.get("discovery_releases_new"),
        "discovery_artists": job.get("discovery_artists"),
        "since_date": job.get("since_date"),
        "result": job.get("result"),
        "error": job.get("error"),
        "worker_pid": job.get("worker_pid"),
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
        "tracks_new",
        "tracks_added",
        "playlists_checked",
        "artist_index",
        "artist_total",
        "artist_name",
        "artist_releases_found",
        "artist_releases_new",
        "discovery_releases_found",
        "discovery_releases_new",
        "discovery_artists",
        "since_date",
    ):
        if key in event:
            updates[key] = event[key]

    _update_job(job_id, **updates)


def _acquire_worker_lock() -> int | None:
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    fd = os.open(WORKER_LOCK_PATH, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    os.ftruncate(fd, 0)
    os.write(fd, str(os.getpid()).encode())
    return fd


def _release_worker_lock(fd: int | None) -> None:
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def run_sync_job(job_id: str) -> None:
    """Execute source→destination sync and persist progress to the job file."""
    lock_fd = _acquire_worker_lock()
    if lock_fd is None:
        _update_job(
            job_id,
            status="error",
            phase="error",
            message="Another sync is already running",
            error="Another sync is already running",
        )
        return

    _update_job(job_id, worker_pid=os.getpid())
    try:
        sp = get_quiet_spotify_client()

        def progress(event: dict[str, Any]) -> None:
            _on_progress(job_id, event)

        result = sync_playlists(sp, on_progress=progress, quiet=True)
        _update_job(
            job_id,
            status="done",
            phase="done",
            message="Sync complete",
            result=result,
            tracks_found=result.get("tracks_found", 0),
            tracks_new=result.get("tracks_new", 0),
            tracks_added=result.get("tracks_added", 0),
            playlists_checked=result.get("playlists_checked", 0),
            playlist_total=result.get("playlist_count", 0),
            artist_releases_new=result.get("artist_releases_new", 0),
            artist_releases_found=result.get("artist_releases_found", 0),
            discovery_releases_new=result.get("discovery_releases_new", 0),
            discovery_releases_found=result.get("discovery_releases_found", 0),
            since_date=result.get("since_date"),
        )
    except Exception as exc:
        _update_job(
            job_id,
            status="error",
            phase="error",
            message=str(exc),
            error=str(exc),
        )
    finally:
        _release_worker_lock(lock_fd)


def _job_process_alive(job: dict[str, Any]) -> bool:
    pid = job.get("worker_pid")
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _mark_job_interrupted(job_id: str) -> None:
    _update_job(
        job_id,
        status="error",
        phase="error",
        message="Sync interrupted",
        error="Sync interrupted",
    )


def find_active_sync_job() -> dict[str, Any] | None:
    """Return the most recently updated running sync job, if any."""
    if not JOBS_DIR.is_dir():
        return None

    active_jobs: list[dict[str, Any]] = []
    for path in JOBS_DIR.glob("*.json"):
        if path.name.endswith(".json.tmp"):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
            if not raw.strip():
                continue
            job = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            continue
        if job.get("status") == "running":
            if not _job_process_alive(job):
                _mark_job_interrupted(job["job_id"])
                continue
            active_jobs.append(job)

    if not active_jobs:
        return None

    return max(active_jobs, key=lambda job: job.get("updated_at", ""))


def create_sync_job(*, force: bool = False) -> tuple[str | None, str | None]:
    """Validate config, create a job file, and start a background sync thread."""
    import spotify_playlist.config as app_config

    if not force:
        active_job = find_active_sync_job()
        if active_job:
            return active_job["job_id"], None

    config = load_playlists_config()
    source_playlists = config.get("source_playlists") or []
    tracking_playlists = config.get("tracking_playlists") or []
    destination = (config.get("destination_playlist") or "").strip()
    if not destination:
        return None, "No destination playlist configured. Set it in Settings first."
    discovery_enabled = load_artist_discovery_enabled() and bool(tracking_playlists)
    if not source_playlists and not app_config.CHECK_ARTIST_RELEASES and not discovery_enabled:
        return None, (
            "Nothing to sync. Add source playlists, enable followed-artist sync, "
            "or configure tracking playlists for artist discovery."
        )

    try:
        get_quiet_spotify_client()
    except RuntimeError as exc:
        return None, str(exc)

    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "running",
        "phase": "queued",
        "message": "Preparing sync…",
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "result": None,
        "error": None,
    }
    _write_job_file(job)

    thread = threading.Thread(
        target=run_sync_job,
        args=(job_id,),
        daemon=True,
    )
    thread.start()
    return job_id, None


def get_active_sync_job() -> dict[str, Any] | None:
    job = find_active_sync_job()
    if not job:
        return None
    return _snapshot_job(job)


def get_sync_job(job_id: str) -> dict[str, Any] | None:
    job = _read_job_file(job_id)
    if not job:
        return None
    return _snapshot_job(job)
