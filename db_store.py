"""Storage facade: MySQL (default) or text file, selected via STORAGE_BACKEND."""
from __future__ import annotations

import os

from store_common import normalize_reference_url

_BACKEND = os.environ.get("STORAGE_BACKEND", "mysql").strip().lower()

if _BACKEND in ("txt", "text", "file"):
    from txt_store import (  # noqa: F401
        create_new_track,
        delete_new_track,
        load_historical_data,
        load_new_tracks,
        load_play_counts,
        load_playlists_config,
        load_tracking_start_date,
        save_historical_data,
        save_new_tracks,
        save_play_counts,
        save_playlists_config,
        save_tracking_start_date,
        storage_path,
        strip_radio_suffixes_from_db,
        update_new_track_reference_url,
    )
else:
    from mysql_store import (  # noqa: F401
        create_new_track,
        delete_new_track,
        get_connection,
        load_historical_data,
        load_new_tracks,
        load_play_counts,
        load_playlists_config,
        load_tracking_start_date,
        save_historical_data,
        save_new_tracks,
        save_play_counts,
        save_playlists_config,
        save_tracking_start_date,
        strip_radio_suffixes_from_db,
        update_new_track_reference_url,
    )

__all__ = [
    "create_new_track",
    "delete_new_track",
    "load_historical_data",
    "load_new_tracks",
    "load_play_counts",
    "load_playlists_config",
    "load_tracking_start_date",
    "normalize_reference_url",
    "save_historical_data",
    "save_new_tracks",
    "save_play_counts",
    "save_playlists_config",
    "save_tracking_start_date",
    "strip_radio_suffixes_from_db",
    "update_new_track_reference_url",
]

if _BACKEND not in ("txt", "text", "file"):
    __all__.append("get_connection")
