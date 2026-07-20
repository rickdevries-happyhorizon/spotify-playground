"""MySQL persistence for playlist_sync."""
from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from normalize_track_name import normalize_track_name
from store_common import dt_to_iso_str, normalize_reference_url, parse_datetime

try:
    import pymysql
    from pymysql.cursors import DictCursor
    from pymysql.err import IntegrityError
except ImportError:
    pymysql = None
    DictCursor = None  # type: ignore
    IntegrityError = Exception  # type: ignore


def _require_pymysql() -> None:
    if pymysql is None:
        raise ImportError(
            "PyMySQL is required for database access. Install with: pip install pymysql"
        )


def get_connection():
    """Return a new MySQL connection (caller must close or use try/finally)."""
    _require_pymysql()
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "spotify_playground"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def load_playlists_config() -> Dict[str, Any]:
    """Load source, destination, and tracking playlist IDs."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT playlist_id FROM destination_config WHERE singleton = 1 LIMIT 1"
            )
            row = cur.fetchone()
            destination = (row or {}).get("playlist_id") or ""

            cur.execute(
                "SELECT playlist_id FROM source_playlists ORDER BY sort_order ASC, playlist_id ASC"
            )
            source_playlists = [r["playlist_id"] for r in cur.fetchall()]

            cur.execute(
                "SELECT playlist_id FROM tracking_playlists ORDER BY sort_order ASC, playlist_id ASC"
            )
            tracking_playlists = [r["playlist_id"] for r in cur.fetchall()]

        return {
            "source_playlists": source_playlists,
            "destination_playlist": destination,
            "tracking_playlists": tracking_playlists,
        }
    except Exception as e:
        print(f"❌ Fout bij laden playlist configuratie uit database: {e}")
        return {"source_playlists": [], "destination_playlist": "", "tracking_playlists": []}
    finally:
        conn.close()


def save_playlists_config(config: Dict[str, Any]) -> None:
    """Replace playlist configuration in the database."""
    conn = get_connection()
    try:
        dest = config.get("destination_playlist") or ""
        sources = config.get("source_playlists") or []
        tracking = config.get("tracking_playlists") or []

        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO destination_config (singleton, playlist_id) VALUES (1, %s) "
                "ON DUPLICATE KEY UPDATE playlist_id = VALUES(playlist_id)",
                (dest,),
            )
            cur.execute("DELETE FROM source_playlists")
            for i, pid in enumerate(sources):
                cur.execute(
                    "INSERT INTO source_playlists (sort_order, playlist_id) VALUES (%s, %s)",
                    (i, pid),
                )
            cur.execute("DELETE FROM tracking_playlists")
            for i, pid in enumerate(tracking):
                cur.execute(
                    "INSERT INTO tracking_playlists (sort_order, playlist_id) VALUES (%s, %s)",
                    (i, pid),
                )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Fout bij opslaan playlist configuratie: {e}")
        raise
    finally:
        conn.close()


def load_historical_data(bron_playlists: Optional[List[str]] = None) -> Dict[str, Set[str]]:
    """Load known track URIs per playlist key (including '__artist_releases__')."""
    data: Dict[str, Set[str]] = defaultdict(set)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT playlist_key, track_uri FROM historical_tracks")
            for row in cur.fetchall():
                data[row["playlist_key"]].add(row["track_uri"])
    except Exception as e:
        print(f"Fout bij laden historische gegevens: {e}")
        if bron_playlists:
            return {pl_id: set() for pl_id in bron_playlists}
        return {}
    finally:
        conn.close()

    out: Dict[str, Set[str]] = {k: set(v) for k, v in data.items()}
    if bron_playlists:
        for pl_id in bron_playlists:
            out.setdefault(pl_id, set())
    return out


def save_historical_data(data: Dict[str, Set[str]]) -> None:
    """Persist full historical snapshot."""
    conn = get_connection()
    try:
        rows: List[tuple] = []
        for pl_key, uris in data.items():
            for uri in uris:
                rows.append((pl_key, uri))

        with conn.cursor() as cur:
            cur.execute("DELETE FROM historical_tracks")
            if rows:
                cur.executemany(
                    "INSERT INTO historical_tracks (playlist_key, track_uri) VALUES (%s, %s)",
                    rows,
                )
        conn.commit()
        print("\n✅ Historische gegevens opgeslagen in de database")
    except Exception as e:
        conn.rollback()
        print(f"Fout bij opslaan historische gegevens: {e}")
        raise
    finally:
        conn.close()


def load_play_counts() -> Dict[str, Any]:
    conn = get_connection()
    try:
        out: Dict[str, Any] = {}
        with conn.cursor() as cur:
            cur.execute(
                "SELECT track_uri, track_name, artists, play_count, first_played, last_played "
                "FROM play_counts"
            )
            for row in cur.fetchall():
                uri = row["track_uri"]
                out[uri] = {
                    "name": row["track_name"] or "Unknown",
                    "artists": row["artists"] or "",
                    "play_count": int(row["play_count"] or 0),
                    "first_played": dt_to_iso_str(row["first_played"]),
                    "last_played": dt_to_iso_str(row["last_played"]),
                }
        return out
    except Exception as e:
        print(f"Fout bij laden play counts: {e}")
        return {}
    finally:
        conn.close()


def save_play_counts(play_counts: Dict[str, Any]) -> None:
    conn = get_connection()
    try:
        rows = []
        for uri, entry in play_counts.items():
            if not isinstance(entry, dict):
                continue
            rows.append(
                (
                    uri,
                    normalize_track_name(entry.get("name", "Unknown")),
                    entry.get("artists", ""),
                    int(entry.get("play_count", 0)),
                    parse_datetime(entry.get("first_played")),
                    parse_datetime(entry.get("last_played")),
                )
            )
        with conn.cursor() as cur:
            cur.execute("DELETE FROM play_counts")
            if rows:
                cur.executemany(
                    "INSERT INTO play_counts (track_uri, track_name, artists, play_count, "
                    "first_played, last_played) VALUES (%s, %s, %s, %s, %s, %s)",
                    rows,
                )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Fout bij opslaan play counts: {e}")
    finally:
        conn.close()


def load_tracking_start_date() -> Optional[datetime]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT start_date FROM tracking_start WHERE singleton = 1 LIMIT 1"
            )
            row = cur.fetchone()
            if not row or row.get("start_date") is None:
                return None
            return parse_datetime(row["start_date"])
    except Exception as e:
        print(f"Fout bij laden tracking start datum: {e}")
        return None
    finally:
        conn.close()


def save_tracking_start_date(start_date: Any) -> None:
    conn = get_connection()
    try:
        dt = start_date
        if not isinstance(dt, datetime):
            dt = parse_datetime(start_date)
        if isinstance(dt, datetime) and dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        now = datetime.now()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tracking_start (singleton, start_date, last_updated) VALUES (1, %s, %s) "
                "ON DUPLICATE KEY UPDATE start_date = VALUES(start_date), "
                "last_updated = VALUES(last_updated)",
                (dt, now),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Fout bij opslaan tracking start datum: {e}")
    finally:
        conn.close()


def _ensure_new_tracks_genre_column(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'new_tracks' "
            "AND COLUMN_NAME = 'genre'"
        )
        if cur.fetchone()["cnt"] == 0:
            cur.execute(
                "ALTER TABLE new_tracks ADD COLUMN genre VARCHAR(512) NULL "
                "AFTER reference_url"
            )
    conn.commit()


def load_new_tracks() -> List[Dict[str, Any]]:
    """Load all new_tracks rows ordered by track name."""
    conn = get_connection()
    try:
        _ensure_new_tracks_genre_column(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, track, reference_url, genre FROM new_tracks ORDER BY track ASC"
            )
            return [
                {
                    "id": row["id"],
                    "track": row["track"],
                    "reference_url": row["reference_url"] or None,
                    "genre": row.get("genre") or None,
                }
                for row in cur.fetchall()
            ]
    finally:
        conn.close()


def update_new_track_reference_url(track_id: int, reference_url: Optional[str]) -> bool:
    """Update reference_url for a single new_tracks row. Empty string clears the URL."""
    url = normalize_reference_url(reference_url)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE new_tracks SET reference_url = %s WHERE id = %s",
                (url, track_id),
            )
            updated = cur.rowcount > 0
        conn.commit()
        return updated
    except Exception as e:
        conn.rollback()
        print(f"Fout bij bijwerken reference URL: {e}")
        raise
    finally:
        conn.close()


def delete_new_track(track_id: int) -> bool:
    """Delete a single new_tracks row."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM new_tracks WHERE id = %s", (track_id,))
            deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    except Exception as e:
        conn.rollback()
        print(f"Fout bij verwijderen track: {e}")
        raise
    finally:
        conn.close()


def strip_radio_suffixes_from_db() -> tuple[int, int, int]:
    """Remove radio edit/mix suffixes from new_tracks and play_counts."""
    conn = get_connection()
    new_tracks_updated = 0
    new_tracks_deleted = 0
    play_counts_updated = 0
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, track, reference_url FROM new_tracks "
                "WHERE LOWER(track) LIKE '%radio edit%' OR LOWER(track) LIKE '%radio mix%'"
            )
            for row in cur.fetchall():
                normalized = normalize_track_name(row["track"])
                if normalized == row["track"]:
                    continue

                cur.execute(
                    "SELECT id, reference_url FROM new_tracks WHERE track = %s AND id != %s LIMIT 1",
                    (normalized, row["id"]),
                )
                existing = cur.fetchone()
                if existing:
                    if row["reference_url"] and not existing["reference_url"]:
                        cur.execute(
                            "UPDATE new_tracks SET reference_url = %s WHERE id = %s",
                            (row["reference_url"], existing["id"]),
                        )
                    cur.execute("DELETE FROM new_tracks WHERE id = %s", (row["id"],))
                    new_tracks_deleted += 1
                else:
                    cur.execute(
                        "UPDATE new_tracks SET track = %s WHERE id = %s",
                        (normalized, row["id"]),
                    )
                    new_tracks_updated += 1

            cur.execute(
                "SELECT track_uri, track_name FROM play_counts "
                "WHERE LOWER(track_name) LIKE '%radio edit%' OR LOWER(track_name) LIKE '%radio mix%'"
            )
            for row in cur.fetchall():
                normalized = normalize_track_name(row["track_name"])
                if normalized == row["track_name"]:
                    continue
                cur.execute(
                    "UPDATE play_counts SET track_name = %s WHERE track_uri = %s",
                    (normalized, row["track_uri"]),
                )
                play_counts_updated += 1

        conn.commit()
        return new_tracks_updated, new_tracks_deleted, play_counts_updated
    except Exception as e:
        conn.rollback()
        print(f"Fout bij opschonen radio edit/mix suffixen: {e}")
        raise
    finally:
        conn.close()


def create_new_track(
    track: str,
    reference_url: Optional[str] = None,
    genre: Optional[str] = None,
) -> Dict[str, Any]:
    """Insert a single new_tracks row. Raises ValueError if track is empty or already exists."""
    track_name = normalize_track_name((track or "").strip())
    if not track_name:
        raise ValueError("Track name is required")

    url = normalize_reference_url(reference_url)
    genre_value = (genre or "").strip() or None
    conn = get_connection()
    try:
        _ensure_new_tracks_genre_column(conn)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO new_tracks (track, reference_url, genre) VALUES (%s, %s, %s)",
                (track_name, url, genre_value),
            )
            track_id = cur.lastrowid
        conn.commit()
        return {
            "id": track_id,
            "track": track_name,
            "reference_url": url,
            "genre": genre_value,
        }
    except IntegrityError as e:
        conn.rollback()
        raise ValueError("Track already exists") from e
    except Exception as e:
        conn.rollback()
        print(f"Fout bij toevoegen track: {e}")
        raise
    finally:
        conn.close()


def save_new_tracks(tracks: List[Dict[str, Any]], replace: bool = False) -> tuple[int, int]:
    """Persist tracks (new.numbers shape: track + reference_url)."""
    if not tracks:
        return 0, 0

    conn = get_connection()
    try:
        _ensure_new_tracks_genre_column(conn)
        rows = []
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
            genre_value = (entry.get("genre") or "").strip() or None
            rows.append(
                (
                    track_display,
                    normalize_reference_url(entry.get("reference_url")),
                    genre_value,
                )
            )

        if not rows:
            return 0, total_valid

        with conn.cursor() as cur:
            if replace:
                cur.execute("DELETE FROM new_tracks")
                cur.executemany(
                    "INSERT INTO new_tracks (track, reference_url, genre) VALUES (%s, %s, %s)",
                    rows,
                )
                inserted = len(rows)
            else:
                cur.execute("SELECT track FROM new_tracks")
                existing = {row["track"] for row in cur.fetchall()}
                new_rows = [row for row in rows if row[0] not in existing]
                if new_rows:
                    cur.executemany(
                        "INSERT INTO new_tracks (track, reference_url, genre) VALUES (%s, %s, %s)",
                        new_rows,
                    )
                inserted = len(new_rows)
        conn.commit()
        skipped = 0 if replace else total_valid - inserted
        return inserted, skipped
    except Exception as e:
        conn.rollback()
        print(f"Fout bij opslaan nieuwe tracks: {e}")
        raise
    finally:
        conn.close()
