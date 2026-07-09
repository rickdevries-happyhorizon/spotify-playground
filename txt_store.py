"""Text-file persistence for playlist_sync (JSON in a .txt file, no MySQL required)."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from normalize_track_name import normalize_track_name
from store_common import dt_to_iso_str, normalize_reference_url, parse_datetime

DEFAULT_STORAGE_FILE = Path(__file__).resolve().parent / "data" / "store.txt"


def storage_path() -> Path:
    raw = os.environ.get("STORAGE_FILE", "").strip()
    if raw:
        return Path(os.path.expanduser(raw)).resolve()
    return DEFAULT_STORAGE_FILE


def _default_store() -> Dict[str, Any]:
    return {
        "playlists_config": {
            "source_playlists": [],
            "destination_playlist": "",
            "tracking_playlists": [],
        },
        "historical_tracks": {},
        "play_counts": {},
        "tracking_start": {"start_date": None, "last_updated": None},
        "new_tracks": [],
        "next_new_track_id": 1,
    }


def _merge_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    defaults = _default_store()
    merged = defaults.copy()
    merged.update(data)

    for key in ("playlists_config", "historical_tracks", "play_counts", "tracking_start"):
        if not isinstance(merged.get(key), dict):
            merged[key] = defaults[key]
        else:
            section = defaults[key].copy()
            section.update(merged[key])
            merged[key] = section

    if not isinstance(merged.get("new_tracks"), list):
        merged["new_tracks"] = []

    next_id = merged.get("next_new_track_id")
    if not isinstance(next_id, int) or next_id < 1:
        max_id = max((track.get("id", 0) for track in merged["new_tracks"]), default=0)
        merged["next_new_track_id"] = max_id + 1

    return merged


def _load_store() -> Dict[str, Any]:
    path = storage_path()
    if not path.is_file():
        return _default_store()

    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Ongeldig opslagbestand: {path}")
    return _merge_defaults(data)


def _save_store(data: Dict[str, Any]) -> None:
    path = storage_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def load_playlists_config() -> Dict[str, Any]:
    """Load source, destination, and tracking playlist IDs."""
    try:
        store = _load_store()
        config = store["playlists_config"]
        return {
            "source_playlists": list(config.get("source_playlists") or []),
            "destination_playlist": config.get("destination_playlist") or "",
            "tracking_playlists": list(config.get("tracking_playlists") or []),
        }
    except Exception as e:
        print(f"❌ Fout bij laden playlist configuratie uit bestand: {e}")
        return {"source_playlists": [], "destination_playlist": "", "tracking_playlists": []}


def save_playlists_config(config: Dict[str, Any]) -> None:
    """Replace playlist configuration in the text store."""
    try:
        store = _load_store()
        store["playlists_config"] = {
            "source_playlists": list(config.get("source_playlists") or []),
            "destination_playlist": config.get("destination_playlist") or "",
            "tracking_playlists": list(config.get("tracking_playlists") or []),
        }
        _save_store(store)
    except Exception as e:
        print(f"❌ Fout bij opslaan playlist configuratie: {e}")
        raise


def load_historical_data(bron_playlists: Optional[List[str]] = None) -> Dict[str, Set[str]]:
    """Load known track URIs per playlist key (including '__artist_releases__')."""
    try:
        store = _load_store()
        raw = store.get("historical_tracks") or {}
        out: Dict[str, Set[str]] = {
            key: set(value or [])
            for key, value in raw.items()
            if isinstance(value, list)
        }
    except Exception as e:
        print(f"Fout bij laden historische gegevens: {e}")
        if bron_playlists:
            return {pl_id: set() for pl_id in bron_playlists}
        return {}

    if bron_playlists:
        for pl_id in bron_playlists:
            out.setdefault(pl_id, set())
    return out


def save_historical_data(data: Dict[str, Set[str]]) -> None:
    """Persist full historical snapshot."""
    try:
        store = _load_store()
        store["historical_tracks"] = {
            pl_key: sorted(uris)
            for pl_key, uris in data.items()
        }
        _save_store(store)
        print(f"\n✅ Historische gegevens opgeslagen in {storage_path()}")
    except Exception as e:
        print(f"Fout bij opslaan historische gegevens: {e}")
        raise


def load_play_counts() -> Dict[str, Any]:
    try:
        store = _load_store()
        raw = store.get("play_counts") or {}
        out: Dict[str, Any] = {}
        for uri, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            out[uri] = {
                "name": entry.get("name") or "Unknown",
                "artists": entry.get("artists") or "",
                "play_count": int(entry.get("play_count") or 0),
                "first_played": entry.get("first_played"),
                "last_played": entry.get("last_played"),
            }
        return out
    except Exception as e:
        print(f"Fout bij laden play counts: {e}")
        return {}


def save_play_counts(play_counts: Dict[str, Any]) -> None:
    try:
        store = _load_store()
        out: Dict[str, Any] = {}
        for uri, entry in play_counts.items():
            if not isinstance(entry, dict):
                continue
            out[uri] = {
                "name": normalize_track_name(entry.get("name", "Unknown")),
                "artists": entry.get("artists", ""),
                "play_count": int(entry.get("play_count", 0)),
                "first_played": dt_to_iso_str(entry.get("first_played")),
                "last_played": dt_to_iso_str(entry.get("last_played")),
            }
        store["play_counts"] = out
        _save_store(store)
    except Exception as e:
        print(f"Fout bij opslaan play counts: {e}")


def load_tracking_start_date() -> Optional[datetime]:
    try:
        store = _load_store()
        value = (store.get("tracking_start") or {}).get("start_date")
        return parse_datetime(value)
    except Exception as e:
        print(f"Fout bij laden tracking start datum: {e}")
        return None


def save_tracking_start_date(start_date: Any) -> None:
    try:
        dt = start_date
        if not isinstance(dt, datetime):
            dt = parse_datetime(start_date)
        if isinstance(dt, datetime) and dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)

        store = _load_store()
        store["tracking_start"] = {
            "start_date": dt_to_iso_str(dt),
            "last_updated": dt_to_iso_str(datetime.now()),
        }
        _save_store(store)
    except Exception as e:
        print(f"Fout bij opslaan tracking start datum: {e}")


def load_new_tracks() -> List[Dict[str, Any]]:
    """Load all new_tracks rows ordered by track name."""
    store = _load_store()
    tracks = [
        {
            "id": int(track["id"]),
            "track": track["track"],
            "reference_url": track.get("reference_url") or None,
        }
        for track in store["new_tracks"]
        if isinstance(track, dict) and "id" in track and "track" in track
    ]
    tracks.sort(key=lambda row: row["track"].casefold())
    return tracks


def update_new_track_reference_url(track_id: int, reference_url: Optional[str]) -> bool:
    """Update reference_url for a single new_tracks row."""
    url = normalize_reference_url(reference_url)
    store = _load_store()
    updated = False
    for track in store["new_tracks"]:
        if track.get("id") == track_id:
            track["reference_url"] = url
            updated = True
            break

    if updated:
        _save_store(store)
    return updated


def delete_new_track(track_id: int) -> bool:
    """Delete a single new_tracks row."""
    store = _load_store()
    before = len(store["new_tracks"])
    store["new_tracks"] = [
        track for track in store["new_tracks"]
        if track.get("id") != track_id
    ]
    deleted = len(store["new_tracks"]) < before
    if deleted:
        _save_store(store)
    return deleted


def strip_radio_suffixes_from_db() -> tuple[int, int, int]:
    """Remove radio edit/mix suffixes from new_tracks and play_counts."""
    store = _load_store()
    new_tracks_updated = 0
    new_tracks_deleted = 0
    play_counts_updated = 0

    tracks = store["new_tracks"]
    kept: List[Dict[str, Any]] = []
    by_name: Dict[str, Dict[str, Any]] = {}

    for track in tracks:
        normalized = normalize_track_name(track.get("track", ""))
        if normalized != track.get("track"):
            existing = by_name.get(normalized)
            if existing:
                if track.get("reference_url") and not existing.get("reference_url"):
                    existing["reference_url"] = track["reference_url"]
                new_tracks_deleted += 1
                continue
            track["track"] = normalized
            new_tracks_updated += 1

        if track["track"] in by_name:
            existing = by_name[track["track"]]
            if track.get("reference_url") and not existing.get("reference_url"):
                existing["reference_url"] = track["reference_url"]
            new_tracks_deleted += 1
            continue

        by_name[track["track"]] = track
        kept.append(track)

    store["new_tracks"] = kept

    play_counts = store.get("play_counts") or {}
    for uri, entry in play_counts.items():
        if not isinstance(entry, dict):
            continue
        normalized = normalize_track_name(entry.get("name", ""))
        if normalized != entry.get("name"):
            entry["name"] = normalized
            play_counts_updated += 1

    store["play_counts"] = play_counts
    _save_store(store)
    return new_tracks_updated, new_tracks_deleted, play_counts_updated


def create_new_track(track: str, reference_url: Optional[str] = None) -> Dict[str, Any]:
    """Insert a single new_tracks row. Raises ValueError if track is empty or already exists."""
    track_name = normalize_track_name((track or "").strip())
    if not track_name:
        raise ValueError("Track name is required")

    url = normalize_reference_url(reference_url)
    store = _load_store()
    for existing in store["new_tracks"]:
        if existing.get("track") == track_name:
            raise ValueError("Track already exists")

    track_id = store["next_new_track_id"]
    store["next_new_track_id"] = track_id + 1
    created = {"id": track_id, "track": track_name, "reference_url": url}
    store["new_tracks"].append(created)
    _save_store(store)
    return created


def save_new_tracks(tracks: List[Dict[str, Any]], replace: bool = False) -> tuple[int, int]:
    """Persist tracks (new.numbers shape: track + reference_url)."""
    if not tracks:
        return 0, 0

    store = _load_store()
    rows: List[tuple[str, Optional[str]]] = []
    seen_in_batch: set[str] = set()
    total_valid = 0

    for entry in tracks:
        track_display = normalize_track_name(
            entry.get("track") or entry.get("Track") or ""
        )
        if not track_display:
            continue
        total_valid += 1
        if track_display in seen_in_batch:
            continue
        seen_in_batch.add(track_display)
        rows.append((track_display, normalize_reference_url(entry.get("reference_url"))))

    if not rows:
        return 0, total_valid

    if replace:
        store["new_tracks"] = []
        store["next_new_track_id"] = 1

    existing = {track["track"] for track in store["new_tracks"]}
    inserted = 0
    for track_name, url in rows:
        if track_name in existing:
            continue
        track_id = store["next_new_track_id"]
        store["next_new_track_id"] = track_id + 1
        store["new_tracks"].append(
            {"id": track_id, "track": track_name, "reference_url": url}
        )
        existing.add(track_name)
        inserted += 1

    _save_store(store)
    skipped = 0 if replace else total_valid - inserted
    return inserted, skipped
