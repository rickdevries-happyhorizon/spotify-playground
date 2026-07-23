"""MySQL persistence for playlist_sync."""
from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from normalize_track_name import normalize_track_name
from spotify_playlist.release_year import normalize_release_year
from spotify_playlist.spotify_track_energy import normalize_energy
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
    """Load source, destination, and tracking playlist Spotify IDs."""
    conn = get_connection()
    try:
        _ensure_playlist_config_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT p.spotify_id "
                "FROM destination_config dc "
                "LEFT JOIN playlist p ON p.id = dc.playlist_ref_id "
                "WHERE dc.singleton = 1 LIMIT 1"
            )
            row = cur.fetchone()
            destination = (row or {}).get("spotify_id") or ""

            cur.execute(
                "SELECT p.spotify_id "
                "FROM playlist_source ps "
                "INNER JOIN playlist p ON p.id = ps.playlist_ref_id "
                "ORDER BY ps.sort_order ASC, p.spotify_id ASC"
            )
            source_playlists = [
                r["spotify_id"] for r in cur.fetchall() if r.get("spotify_id")
            ]

            cur.execute(
                "SELECT p.spotify_id "
                "FROM playlist_tracking pt "
                "INNER JOIN playlist p ON p.id = pt.playlist_ref_id "
                "ORDER BY pt.sort_order ASC, p.spotify_id ASC"
            )
            tracking_playlists = [
                r["spotify_id"] for r in cur.fetchall() if r.get("spotify_id")
            ]

        return {
            "source_playlists": source_playlists,
            "destination_playlist": destination,
            "tracking_playlists": tracking_playlists,
        }
    except Exception as e:
        print(f"❌ Error loading playlist configuration from database: {e}")
        return {"source_playlists": [], "destination_playlist": "", "tracking_playlists": []}
    finally:
        conn.close()


def save_playlists_config(config: Dict[str, Any]) -> None:
    """Replace playlist configuration in the database."""
    conn = get_connection()
    try:
        dest = (config.get("destination_playlist") or "").strip()
        sources = config.get("source_playlists") or []
        tracking = config.get("tracking_playlists") or []

        _ensure_playlist_config_schema(conn)
        with conn.cursor() as cur:
            dest_ref_id = None
            if dest:
                dest_ref_id = _upsert_playlist_cur(cur, spotify_id=dest)
            cur.execute(
                "INSERT INTO destination_config (singleton, playlist_ref_id) VALUES (1, %s) "
                "ON DUPLICATE KEY UPDATE playlist_ref_id = VALUES(playlist_ref_id)",
                (dest_ref_id,),
            )

            cur.execute("DELETE FROM playlist_source")
            for i, spotify_id in enumerate(sources):
                spotify_id = (spotify_id or "").strip()
                if not spotify_id:
                    continue
                ref_id = _upsert_playlist_cur(cur, spotify_id=spotify_id)
                cur.execute(
                    "INSERT INTO playlist_source (sort_order, playlist_ref_id) VALUES (%s, %s)",
                    (i, ref_id),
                )

            cur.execute("DELETE FROM playlist_tracking")
            for i, spotify_id in enumerate(tracking):
                spotify_id = (spotify_id or "").strip()
                if not spotify_id:
                    continue
                ref_id = _upsert_playlist_cur(cur, spotify_id=spotify_id)
                cur.execute(
                    "INSERT INTO playlist_tracking (sort_order, playlist_ref_id) VALUES (%s, %s)",
                    (i, ref_id),
                )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Error saving playlist configuration: {e}")
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
        print(f"Error loading historical data: {e}")
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
        print("\n✅ Historical data saved to the database")
    except Exception as e:
        conn.rollback()
        print(f"Error saving historical data: {e}")
        raise
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
        print(f"Error loading tracking start date: {e}")
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
        print(f"Error saving tracking start date: {e}")
    finally:
        conn.close()


_VALID_UI_SKINS = frozenset({"neon", "simple"})


def _normalize_ui_skin(skin: Optional[str]) -> str:
    value = (skin or "neon").strip().lower()
    return value if value in _VALID_UI_SKINS else "neon"


def _ensure_app_config_table(conn) -> None:
    if _table_exists(conn, "app_config"):
        return

    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE app_config ("
            "singleton TINYINT UNSIGNED NOT NULL PRIMARY KEY, "
            "ui_skin VARCHAR(32) NOT NULL DEFAULT 'neon'"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
        )
        cur.execute(
            "INSERT INTO app_config (singleton, ui_skin) VALUES (1, 'neon')"
        )
    conn.commit()


def load_ui_skin() -> str:
    conn = get_connection()
    try:
        _ensure_app_config_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ui_skin FROM app_config WHERE singleton = 1 LIMIT 1"
            )
            row = cur.fetchone()
            return _normalize_ui_skin((row or {}).get("ui_skin"))
    except Exception as e:
        print(f"Error loading UI skin: {e}")
        return "neon"
    finally:
        conn.close()


def save_ui_skin(skin: str) -> None:
    normalized = _normalize_ui_skin(skin)
    conn = get_connection()
    try:
        _ensure_app_config_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO app_config (singleton, ui_skin) VALUES (1, %s) "
                "ON DUPLICATE KEY UPDATE ui_skin = VALUES(ui_skin)",
                (normalized,),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving UI skin: {e}")
        raise
    finally:
        conn.close()


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (table_name, column_name),
        )
        return int(cur.fetchone()["cnt"]) > 0


def _ensure_new_tracks_release_year_column(conn) -> None:
    with conn.cursor() as cur:
        if _column_exists(conn, "new_tracks", "release_year"):
            return
        after = "playlist_id" if _column_exists(conn, "new_tracks", "playlist_id") else "reference_url"
        cur.execute(
            f"ALTER TABLE new_tracks ADD COLUMN release_year SMALLINT UNSIGNED NULL "
            f"AFTER {after}"
        )
    conn.commit()


def _ensure_new_tracks_energy_column(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'new_tracks' "
            "AND COLUMN_NAME = 'energy'"
        )
        if cur.fetchone()["cnt"] == 0:
            cur.execute(
                "ALTER TABLE new_tracks ADD COLUMN energy DECIMAL(4,3) NULL "
                "AFTER release_year"
            )
    conn.commit()


def _ensure_new_tracks_copy_title_count_column(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'new_tracks' "
            "AND COLUMN_NAME = 'copy_title_count'"
        )
        if cur.fetchone()["cnt"] == 0:
            cur.execute(
                "ALTER TABLE new_tracks ADD COLUMN copy_title_count INT UNSIGNED NOT NULL DEFAULT 0 "
                "AFTER energy"
            )
    conn.commit()


def _ensure_new_tracks_image_url_column(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'new_tracks' "
            "AND COLUMN_NAME = 'image_url'"
        )
        if cur.fetchone()["cnt"] == 0:
            cur.execute(
                "ALTER TABLE new_tracks ADD COLUMN image_url TEXT NULL "
                "AFTER copy_title_count"
            )
    conn.commit()


def _ensure_playlist_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS playlist ("
            "id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "spotify_id VARCHAR(64) NULL, "
            "name VARCHAR(512) NOT NULL, "
            "artwork_url TEXT NULL, "
            "UNIQUE KEY uq_playlist_spotify_id (spotify_id), "
            "UNIQUE KEY uq_playlist_name (name(191))"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
        )
    conn.commit()
    _ensure_playlist_spotify_id_column(conn)


def _ensure_playlist_spotify_id_column(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'playlist' "
            "AND COLUMN_NAME = 'spotify_id'"
        )
        if cur.fetchone()["cnt"] == 0:
            cur.execute(
                "ALTER TABLE playlist ADD COLUMN spotify_id VARCHAR(64) NULL AFTER id"
            )
            cur.execute(
                "ALTER TABLE playlist ADD UNIQUE KEY uq_playlist_spotify_id (spotify_id)"
            )
    conn.commit()


def _table_exists(conn, table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
            (table_name,),
        )
        return int(cur.fetchone()["cnt"]) > 0


def _column_data_type(conn, table_name: str, column_name: str) -> Optional[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT DATA_TYPE FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (table_name, column_name),
        )
        row = cur.fetchone()
        return (row or {}).get("DATA_TYPE")


def _ensure_playlist_source_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS playlist_source ("
            "sort_order INT UNSIGNED NOT NULL, "
            "playlist_ref_id INT UNSIGNED NOT NULL, "
            "PRIMARY KEY (playlist_ref_id), "
            "KEY idx_playlist_source_sort (sort_order), "
            "CONSTRAINT fk_playlist_source FOREIGN KEY (playlist_ref_id) "
            "REFERENCES playlist(id) ON DELETE CASCADE"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
        )
    conn.commit()


def _ensure_playlist_tracking_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS playlist_tracking ("
            "sort_order INT UNSIGNED NOT NULL, "
            "playlist_ref_id INT UNSIGNED NOT NULL, "
            "PRIMARY KEY (playlist_ref_id), "
            "KEY idx_playlist_tracking_sort (sort_order), "
            "CONSTRAINT fk_playlist_tracking FOREIGN KEY (playlist_ref_id) "
            "REFERENCES playlist(id) ON DELETE CASCADE"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
        )
    conn.commit()


def _ensure_destination_config_table(conn) -> None:
    if not _table_exists(conn, "destination_config"):
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE destination_config ("
                "singleton TINYINT UNSIGNED NOT NULL PRIMARY KEY, "
                "playlist_ref_id INT UNSIGNED NULL, "
                "CONSTRAINT fk_destination_playlist FOREIGN KEY (playlist_ref_id) "
                "REFERENCES playlist(id) ON DELETE SET NULL"
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
            )
            cur.execute(
                "INSERT INTO destination_config (singleton, playlist_ref_id) VALUES (1, NULL)"
            )
        conn.commit()
        return

    data_type = _column_data_type(conn, "destination_config", "playlist_id")
    if data_type in {"varchar", "char"}:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT playlist_id FROM destination_config WHERE singleton = 1 LIMIT 1"
            )
            row = cur.fetchone()
            dest_spotify = ((row or {}).get("playlist_id") or "").strip()
            dest_ref_id = None
            if dest_spotify:
                dest_ref_id = _upsert_playlist_cur(cur, spotify_id=dest_spotify)
            cur.execute(
                "CREATE TABLE destination_config_new ("
                "singleton TINYINT UNSIGNED NOT NULL PRIMARY KEY, "
                "playlist_ref_id INT UNSIGNED NULL, "
                "CONSTRAINT fk_destination_playlist_new FOREIGN KEY (playlist_ref_id) "
                "REFERENCES playlist(id) ON DELETE SET NULL"
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
            )
            cur.execute(
                "INSERT INTO destination_config_new (singleton, playlist_ref_id) VALUES (1, %s)",
                (dest_ref_id,),
            )
            cur.execute("DROP TABLE destination_config")
            cur.execute("RENAME TABLE destination_config_new TO destination_config")
        conn.commit()


def _migrate_legacy_source_tracking_table(conn, *, legacy_table: str, target_table: str) -> None:
    if not _table_exists(conn, legacy_table):
        return

    data_type = _column_data_type(conn, legacy_table, "playlist_id")
    if data_type not in {"varchar", "char"}:
        return

    ensure_target = (
        _ensure_playlist_source_table
        if target_table == "playlist_source"
        else _ensure_playlist_tracking_table
    )
    ensure_target(conn)

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT sort_order, playlist_id FROM {legacy_table} ORDER BY sort_order ASC"
        )
        rows = cur.fetchall()
        cur.execute(f"DELETE FROM {target_table}")
        for row in rows:
            spotify_id = (row.get("playlist_id") or "").strip()
            if not spotify_id:
                continue
            ref_id = _upsert_playlist_cur(cur, spotify_id=spotify_id)
            cur.execute(
                f"INSERT INTO {target_table} (sort_order, playlist_ref_id) VALUES (%s, %s)",
                (int(row["sort_order"]), ref_id),
            )
        cur.execute(f"DROP TABLE {legacy_table}")
    conn.commit()


def _ensure_playlist_config_schema(conn) -> None:
    _ensure_playlist_table(conn)
    _ensure_destination_config_table(conn)
    _migrate_legacy_source_tracking_table(
        conn, legacy_table="source_playlists", target_table="playlist_source"
    )
    _migrate_legacy_source_tracking_table(
        conn, legacy_table="tracking_playlists", target_table="playlist_tracking"
    )
    _ensure_playlist_source_table(conn)
    _ensure_playlist_tracking_table(conn)


def _ensure_new_tracks_playlist_id_column(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'new_tracks' "
            "AND COLUMN_NAME = 'playlist_id'"
        )
        if cur.fetchone()["cnt"] == 0:
            try:
                cur.execute(
                    "ALTER TABLE new_tracks ADD COLUMN playlist_id INT UNSIGNED NULL "
                    "AFTER reference_url"
                )
                cur.execute(
                    "ALTER TABLE new_tracks ADD KEY idx_new_tracks_playlist (playlist_id)"
                )
            except Exception as e:
                if "Duplicate column name" not in str(e):
                    raise
    conn.commit()


def _ensure_new_tracks_playlist_fk(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM information_schema.TABLE_CONSTRAINTS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'new_tracks' "
            "AND CONSTRAINT_NAME = 'fk_new_tracks_playlist'"
        )
        if cur.fetchone()["cnt"] == 0:
            cur.execute(
                "ALTER TABLE new_tracks ADD CONSTRAINT fk_new_tracks_playlist "
                "FOREIGN KEY (playlist_id) REFERENCES playlist(id) ON DELETE SET NULL"
            )
    conn.commit()


def _backfill_playlist_artwork(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE playlist p "
            "INNER JOIN ("
            "  SELECT nt.playlist_id, MIN(nt.id) AS first_id "
            "  FROM new_tracks nt "
            "  WHERE nt.image_url IS NOT NULL AND nt.playlist_id IS NOT NULL "
            "  GROUP BY nt.playlist_id"
            ") picked ON picked.playlist_id = p.id "
            "INNER JOIN new_tracks nt ON nt.id = picked.first_id "
            "SET p.artwork_url = nt.image_url "
            "WHERE p.artwork_url IS NULL OR TRIM(p.artwork_url) = ''"
        )
    conn.commit()


def _migrate_legacy_genre_data(conn) -> None:
    """Move legacy genre column values into playlist rows before dropping genre."""
    if not _column_exists(conn, "new_tracks", "genre"):
        return

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM new_tracks "
            "WHERE genre IS NOT NULL AND TRIM(genre) != '' AND playlist_id IS NULL"
        )
        pending = int(cur.fetchone()["cnt"])

        _ensure_genre_images_table(conn)
        cur.execute("SELECT genre, image_url FROM genre_images")
        for row in cur.fetchall():
            genre = (row.get("genre") or "").strip()
            image_url = (row.get("image_url") or "").strip()
            if genre:
                _upsert_playlist_cur(cur, name=genre, artwork_url=image_url or None)

        if pending > 0:
            cur.execute(
                "SELECT DISTINCT genre FROM new_tracks "
                "WHERE genre IS NOT NULL AND TRIM(genre) != ''"
            )
            for row in cur.fetchall():
                genre = (row.get("genre") or "").strip()
                if genre:
                    _upsert_playlist_cur(cur, name=genre)

            cur.execute(
                "UPDATE new_tracks nt "
                "INNER JOIN playlist p ON p.name = nt.genre "
                "SET nt.playlist_id = p.id "
                "WHERE nt.playlist_id IS NULL AND nt.genre IS NOT NULL"
            )
    conn.commit()
    _backfill_playlist_artwork(conn)


def _drop_new_tracks_genre_column(conn) -> None:
    if not _column_exists(conn, "new_tracks", "genre"):
        return
    _migrate_legacy_genre_data(conn)
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE new_tracks DROP COLUMN genre")
    conn.commit()


def _merge_playlist_rows(cur, *, from_id: int, to_id: int) -> None:
    """Move references from one playlist row to another and delete the duplicate."""
    if from_id == to_id:
        return

    cur.execute(
        "SELECT spotify_id, artwork_url FROM playlist WHERE id = %s",
        (to_id,),
    )
    target = cur.fetchone()
    cur.execute(
        "SELECT spotify_id, artwork_url FROM playlist WHERE id = %s",
        (from_id,),
    )
    source = cur.fetchone()
    if not target or not source:
        return

    updates: List[str] = []
    params: List[Any] = []
    source_sid = (source.get("spotify_id") or "").strip() or None
    target_sid = (target.get("spotify_id") or "").strip() or None
    if source_sid and not target_sid:
        cur.execute(
            "UPDATE playlist SET spotify_id = NULL WHERE id = %s",
            (from_id,),
        )
        cur.execute(
            "UPDATE playlist SET spotify_id = %s WHERE id = %s",
            (source_sid, to_id),
        )
    if not (target.get("artwork_url") or "").strip() and (source.get("artwork_url") or "").strip():
        cur.execute(
            "UPDATE playlist SET artwork_url = %s WHERE id = %s",
            (source["artwork_url"].strip(), to_id),
        )

    cur.execute(
        "UPDATE destination_config SET playlist_ref_id = %s "
        "WHERE playlist_ref_id = %s",
        (to_id, from_id),
    )

    for table in ("playlist_source", "playlist_tracking"):
        cur.execute(
            f"SELECT 1 FROM {table} WHERE playlist_ref_id = %s LIMIT 1",
            (to_id,),
        )
        if cur.fetchone():
            cur.execute(
                f"DELETE FROM {table} WHERE playlist_ref_id = %s",
                (from_id,),
            )
        else:
            cur.execute(
                f"UPDATE {table} SET playlist_ref_id = %s WHERE playlist_ref_id = %s",
                (to_id, from_id),
            )

    cur.execute(
        "UPDATE new_tracks SET playlist_id = %s WHERE playlist_id = %s",
        (to_id, from_id),
    )
    cur.execute("DELETE FROM playlist WHERE id = %s", (from_id,))


def _upsert_playlist_cur(
    cur,
    *,
    name: Optional[str] = None,
    artwork_url: Optional[str] = None,
    spotify_id: Optional[str] = None,
) -> int:
    playlist_name = (name or "").strip() or None
    sid = (spotify_id or "").strip() or None
    url = (artwork_url or "").strip() or None

    if sid:
        cur.execute(
            "SELECT id, name, artwork_url FROM playlist WHERE spotify_id = %s",
            (sid,),
        )
        row = cur.fetchone()
        if row:
            playlist_id = int(row["id"])
            updates: List[str] = []
            params: List[Any] = []
            if (
                playlist_name
                and playlist_name != row["name"]
                and not (sid and playlist_name == sid)
            ):
                cur.execute(
                    "SELECT id FROM playlist WHERE name = %s AND id != %s LIMIT 1",
                    (playlist_name, playlist_id),
                )
                existing = cur.fetchone()
                if existing:
                    _merge_playlist_rows(
                        cur, from_id=playlist_id, to_id=int(existing["id"])
                    )
                    return int(existing["id"])
                updates.append("name = %s")
                params.append(playlist_name)
            if url and url != (row.get("artwork_url") or ""):
                updates.append("artwork_url = %s")
                params.append(url)
            if updates:
                params.append(playlist_id)
                cur.execute(
                    f"UPDATE playlist SET {', '.join(updates)} WHERE id = %s",
                    params,
                )
            return playlist_id

        if playlist_name:
            cur.execute(
                "SELECT id, artwork_url FROM playlist "
                "WHERE name = %s AND (spotify_id IS NULL OR spotify_id = '')",
                (playlist_name,),
            )
            row = cur.fetchone()
            if row:
                playlist_id = int(row["id"])
                updates = ["spotify_id = %s"]
                params: List[Any] = [sid]
                if url and url != (row.get("artwork_url") or ""):
                    updates.append("artwork_url = %s")
                    params.append(url)
                params.append(playlist_id)
                cur.execute(
                    f"UPDATE playlist SET {', '.join(updates)} WHERE id = %s",
                    params,
                )
                return playlist_id

    if playlist_name:
        cur.execute(
            "SELECT id, spotify_id, artwork_url FROM playlist WHERE name = %s",
            (playlist_name,),
        )
        row = cur.fetchone()
        if row:
            playlist_id = int(row["id"])
            updates: List[str] = []
            params: List[Any] = []
            if sid and sid != (row.get("spotify_id") or ""):
                updates.append("spotify_id = %s")
                params.append(sid)
            if url and url != (row.get("artwork_url") or ""):
                updates.append("artwork_url = %s")
                params.append(url)
            if updates:
                params.append(playlist_id)
                cur.execute(
                    f"UPDATE playlist SET {', '.join(updates)} WHERE id = %s",
                    params,
                )
            return playlist_id

    if sid:
        cur.execute(
            "INSERT INTO playlist (spotify_id, name, artwork_url) VALUES (%s, %s, %s)",
            (sid, playlist_name or sid, url),
        )
        return int(cur.lastrowid)

    if playlist_name:
        cur.execute(
            "INSERT INTO playlist (name, artwork_url) VALUES (%s, %s)",
            (playlist_name, url),
        )
        return int(cur.lastrowid)

    raise ValueError("Playlist name or spotify_id is required")


def upsert_playlist(
    name: str,
    artwork_url: Optional[str] = None,
    *,
    spotify_id: Optional[str] = None,
) -> int:
    """Create or update a playlist row and return its id."""
    conn = get_connection()
    try:
        _ensure_playlist_table(conn)
        with conn.cursor() as cur:
            playlist_id = _upsert_playlist_cur(
                cur,
                name=name,
                artwork_url=artwork_url,
                spotify_id=spotify_id,
            )
        conn.commit()
        return playlist_id
    except Exception as e:
        conn.rollback()
        print(f"Error upserting playlist: {e}")
        raise
    finally:
        conn.close()


def backfill_playlist_names(sp) -> int:
    """Set playlist.name from Spotify where name was stored as the Spotify ID."""
    from spotify_playlist.get_playlist_name import get_playlist_name

    conn = get_connection()
    updated = 0
    try:
        _ensure_playlist_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, spotify_id FROM playlist "
                "WHERE spotify_id IS NOT NULL AND TRIM(spotify_id) != '' "
                "AND name = spotify_id"
            )
            rows = cur.fetchall()
            for row in rows:
                sid = (row.get("spotify_id") or "").strip()
                if not sid:
                    continue
                playlist_name = get_playlist_name(sp, sid)
                if not playlist_name or playlist_name == sid:
                    continue
                row_id = int(row["id"])
                cur.execute(
                    "SELECT id FROM playlist WHERE name = %s AND id != %s LIMIT 1",
                    (playlist_name, row_id),
                )
                existing = cur.fetchone()
                if existing:
                    _merge_playlist_rows(
                        cur, from_id=row_id, to_id=int(existing["id"])
                    )
                else:
                    cur.execute(
                        "UPDATE playlist SET name = %s WHERE id = %s",
                        (playlist_name, row_id),
                    )
                updated += 1
        conn.commit()
        return updated
    except Exception as e:
        conn.rollback()
        print(f"Error backfilling playlist names: {e}")
        raise
    finally:
        conn.close()


def load_playlists() -> List[Dict[str, Any]]:
    """Load all playlists with artwork URLs."""
    conn = get_connection()
    try:
        _ensure_playlist_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, spotify_id, name, artwork_url FROM playlist ORDER BY name ASC"
            )
            return [
                {
                    "id": int(row["id"]),
                    "spotify_id": row.get("spotify_id") or None,
                    "name": row["name"],
                    "artwork_url": row.get("artwork_url") or None,
                }
                for row in cur.fetchall()
            ]
    finally:
        conn.close()


def _ensure_genre_images_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS genre_images ("
            "genre VARCHAR(512) NOT NULL PRIMARY KEY, "
            "image_url TEXT NOT NULL"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
        )
    conn.commit()


def _ensure_new_tracks_columns(conn) -> None:
    _ensure_playlist_table(conn)
    _ensure_new_tracks_playlist_id_column(conn)
    _ensure_new_tracks_release_year_column(conn)
    _ensure_new_tracks_energy_column(conn)
    _ensure_new_tracks_copy_title_count_column(conn)
    _ensure_new_tracks_image_url_column(conn)
    _ensure_genre_images_table(conn)
    try:
        _ensure_new_tracks_playlist_fk(conn)
    except Exception:
        conn.rollback()
    _drop_new_tracks_genre_column(conn)
    _backfill_playlist_artwork(conn)


def _resolve_playlist_id_from_entry(cur, entry: Dict[str, Any]) -> Optional[int]:
    playlist_id = entry.get("playlist_id")
    if playlist_id is not None:
        return int(playlist_id)
    genre_value = (entry.get("genre") or "").strip() or None
    if genre_value:
        return _upsert_playlist_cur(cur, name=genre_value)
    return None


_NEW_TRACKS_SELECT = (
    "SELECT nt.id, nt.track, nt.reference_url, nt.playlist_id, nt.release_year, nt.energy, "
    "nt.copy_title_count, nt.image_url, p.name AS genre, "
    "p.artwork_url AS playlist_artwork_url "
    "FROM new_tracks nt "
    "LEFT JOIN playlist p ON p.id = nt.playlist_id "
)


def _row_to_track(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "track": row["track"],
        "reference_url": row["reference_url"] or None,
        "playlist_id": row.get("playlist_id") or None,
        "genre": row.get("genre") or None,
        "release_year": row.get("release_year") or None,
        "energy": float(row["energy"]) if row.get("energy") is not None else None,
        "copy_title_count": int(row.get("copy_title_count") or 0),
        "image_url": row.get("image_url") or None,
        "playlist_artwork_url": row.get("playlist_artwork_url") or None,
    }


def load_new_tracks() -> List[Dict[str, Any]]:
    """Load all new_tracks rows ordered by track name."""
    conn = get_connection()
    try:
        _ensure_new_tracks_columns(conn)
        with conn.cursor() as cur:
            cur.execute(_NEW_TRACKS_SELECT + "ORDER BY nt.track ASC")
            return [_row_to_track(row) for row in cur.fetchall()]
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
        print(f"Error updating reference URL: {e}")
        raise
    finally:
        conn.close()


def increment_new_track_copy_title_count(track_id: int) -> Optional[int]:
    """Increment copy_title_count for a track. Returns new count or None if not found."""
    conn = get_connection()
    try:
        _ensure_new_tracks_columns(conn)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE new_tracks SET copy_title_count = copy_title_count + 1 WHERE id = %s",
                (track_id,),
            )
            if cur.rowcount == 0:
                conn.rollback()
                return None
            cur.execute(
                "SELECT copy_title_count FROM new_tracks WHERE id = %s",
                (track_id,),
            )
            row = cur.fetchone()
        conn.commit()
        return int(row["copy_title_count"]) if row else None
    except Exception as e:
        conn.rollback()
        print(f"Error incrementing copy title count: {e}")
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
        print(f"Error deleting track: {e}")
        raise
    finally:
        conn.close()


def strip_radio_suffixes_from_db() -> tuple[int, int]:
    """Remove radio edit/mix suffixes from new_tracks."""
    conn = get_connection()
    new_tracks_updated = 0
    new_tracks_deleted = 0
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

        conn.commit()
        return new_tracks_updated, new_tracks_deleted
    except Exception as e:
        conn.rollback()
        print(f"Error cleaning radio edit/mix suffixes: {e}")
        raise
    finally:
        conn.close()


def create_new_track(
    track: str,
    reference_url: Optional[str] = None,
    genre: Optional[str] = None,
    energy: Optional[float] = None,
) -> Dict[str, Any]:
    """Insert a single new_tracks row. Raises ValueError if track is empty or already exists."""
    track_name = normalize_track_name((track or "").strip())
    if not track_name:
        raise ValueError("Track name is required")

    url = normalize_reference_url(reference_url)
    genre_value = (genre or "").strip() or None
    energy_value = normalize_energy(energy)
    conn = get_connection()
    try:
        _ensure_new_tracks_columns(conn)
        with conn.cursor() as cur:
            playlist_id = None
            if genre_value:
                playlist_id = _upsert_playlist_cur(cur, name=genre_value)
            cur.execute(
                "INSERT INTO new_tracks (track, reference_url, playlist_id, release_year, energy) "
                "VALUES (%s, %s, %s, NULL, %s)",
                (track_name, url, playlist_id, energy_value),
            )
            track_id = cur.lastrowid
        conn.commit()
        return {
            "id": track_id,
            "track": track_name,
            "reference_url": url,
            "playlist_id": playlist_id,
            "genre": genre_value,
            "energy": energy_value,
            "copy_title_count": 0,
            "image_url": None,
        }
    except IntegrityError as e:
        conn.rollback()
        raise ValueError("Track already exists") from e
    except Exception as e:
        conn.rollback()
        print(f"Error adding track: {e}")
        raise
    finally:
        conn.close()


def save_new_tracks(tracks: List[Dict[str, Any]], replace: bool = False) -> tuple[int, int]:
    """Persist tracks (track + reference_url, optional genre, release_year, energy)."""
    if not tracks:
        return 0, 0

    conn = get_connection()
    try:
        _ensure_new_tracks_columns(conn)
        rows = []
        seen_in_batch: set[str] = set()
        total_valid = 0
        with conn.cursor() as cur:
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
                release_year = normalize_release_year(entry.get("release_year"))
                energy = normalize_energy(entry.get("energy"))
                image_url = (entry.get("image_url") or "").strip() or None
                playlist_id = _resolve_playlist_id_from_entry(cur, entry)
                rows.append(
                    (
                        track_display,
                        normalize_reference_url(entry.get("reference_url")),
                        playlist_id,
                        release_year,
                        energy,
                        image_url,
                    )
                )

            if not rows:
                return 0, total_valid

            insert_sql = (
                "INSERT INTO new_tracks (track, reference_url, playlist_id, release_year, energy, image_url) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            )
            if replace:
                cur.execute("DELETE FROM new_tracks")
                cur.executemany(insert_sql, rows)
                inserted = len(rows)
            else:
                cur.execute("SELECT track FROM new_tracks")
                existing = {row["track"] for row in cur.fetchall()}
                new_rows = [row for row in rows if row[0] not in existing]
                if new_rows:
                    cur.executemany(insert_sql, new_rows)
                inserted = len(new_rows)
        conn.commit()
        skipped = 0 if replace else total_valid - inserted
        return inserted, skipped
    except Exception as e:
        conn.rollback()
        print(f"Error saving new tracks: {e}")
        raise
    finally:
        conn.close()


def load_genre_images() -> Dict[str, str]:
    """Load playlist cover art URLs keyed by playlist name."""
    conn = get_connection()
    try:
        _ensure_playlist_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, artwork_url FROM playlist WHERE artwork_url IS NOT NULL"
            )
            return {
                row["name"]: row["artwork_url"]
                for row in cur.fetchall()
                if row.get("name") and row.get("artwork_url")
            }
    finally:
        conn.close()


def save_genre_image(genre: str, image_url: Optional[str]) -> None:
    """Persist cover art for a playlist (by name)."""
    genre_name = (genre or "").strip()
    url = (image_url or "").strip()
    if not genre_name or not url:
        return
    upsert_playlist(genre_name, url)


def resolve_genre_image(
    genre: str,
    *,
    genre_images: Optional[Dict[str, str]] = None,
    tracks: Optional[List[Dict[str, Any]]] = None,
) -> Optional[str]:
    """Return playlist artwork, falling back to the first track image in that playlist."""
    genre_name = (genre or "").strip()
    if not genre_name:
        return None

    images = genre_images if genre_images is not None else load_genre_images()
    if genre_name in images:
        return images[genre_name]

    conn = get_connection()
    try:
        _ensure_playlist_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT artwork_url FROM playlist WHERE name = %s LIMIT 1",
                (genre_name,),
            )
            row = cur.fetchone()
            if row and row.get("artwork_url"):
                return row["artwork_url"]
    finally:
        conn.close()

    if tracks is None:
        tracks = load_new_tracks()
    for track in tracks:
        if (track.get("genre") or "").strip() != genre_name:
            continue
        artwork = track.get("playlist_artwork_url") or track.get("image_url")
        if artwork:
            return artwork
    return None
