"""Storage facade: MySQL persistence for playlists, tracks, and URLs."""
from __future__ import annotations

from store_common import normalize_reference_url
from mysql_store import (  # noqa: F401
    create_new_track,
    delete_new_track,
    get_connection,
    increment_new_track_copy_title_count,
    load_genre_images,
    load_historical_data,
    load_new_tracks,
    load_playlists_config,
    load_tracking_start_date,
    resolve_genre_image,
    save_genre_image,
    save_historical_data,
    save_new_tracks,
    save_playlists_config,
    save_tracking_start_date,
    strip_radio_suffixes_from_db,
    update_new_track_reference_url,
)

__all__ = [
    "create_new_track",
    "delete_new_track",
    "get_connection",
    "increment_new_track_copy_title_count",
    "load_genre_images",
    "load_historical_data",
    "load_new_tracks",
    "load_playlists_config",
    "load_tracking_start_date",
    "normalize_reference_url",
    "resolve_genre_image",
    "save_genre_image",
    "save_historical_data",
    "save_new_tracks",
    "save_playlists_config",
    "save_tracking_start_date",
    "strip_radio_suffixes_from_db",
    "update_new_track_reference_url",
]
