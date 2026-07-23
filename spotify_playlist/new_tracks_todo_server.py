"""Browser UI for managing new_tracks reference URLs."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from db_store import (
    create_new_track,
    delete_new_track,
    get_connection,
    increment_new_track_copy_title_count,
    load_genre_images,
    load_locale,
    load_new_tracks,
    load_playlists_config,
    load_sync_start_date,
    load_tracking_start_date,
    load_ui_skin,
    normalize_reference_url,
    resolve_genre_image,
    save_locale,
    save_playlists_config,
    save_sync_start_date,
    save_tracking_start_date,
    save_ui_skin,
    update_new_track_reference_url,
)
from spotify_playlist.i18n import gettext as translate, locale_html_lang, load_catalog
from spotify_playlist.fetch_playlist_info import resolve_playlist_details
from spotify_playlist.import_job_manager import create_import_job, get_import_job
from spotify_playlist.parse_spotify_playlist_id import parse_spotify_playlist_id
from spotify_playlist.spotify_api_client import get_quiet_spotify_client

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_PORT = int(os.environ.get("NEW_TRACKS_TODO_PORT", "5050"))
_VALID_UI_SKINS = frozenset({"light", "dark", "colorful"})
_VALID_LOCALES = frozenset({"en", "nl", "brab"})


def _playlist_names_by_spotify_id(spotify_ids: list[str]) -> dict[str, str]:
    unique_ids = [spotify_id for spotify_id in dict.fromkeys(spotify_ids) if spotify_id]
    if not unique_ids:
        return {}

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            placeholders = ", ".join(["%s"] * len(unique_ids))
            cur.execute(
                f"SELECT spotify_id, name FROM playlist WHERE spotify_id IN ({placeholders})",
                unique_ids,
            )
            return {
                row["spotify_id"]: row["name"]
                for row in cur.fetchall()
                if row.get("spotify_id") and row.get("name")
            }
    finally:
        conn.close()


def _format_playlist_entry(spotify_id: str, names: dict[str, str]) -> dict[str, str | None]:
    return {
        "spotify_id": spotify_id,
        "name": names.get(spotify_id),
    }


def _build_settings_payload() -> dict:
    config = load_playlists_config()
    destination = (config.get("destination_playlist") or "").strip()
    source_playlists = config.get("source_playlists") or []
    tracking_playlists = config.get("tracking_playlists") or []
    start_date = load_tracking_start_date()
    sync_start_date = load_sync_start_date()

    all_ids: list[str] = []
    if destination:
        all_ids.append(destination)
    all_ids.extend(source_playlists)
    all_ids.extend(tracking_playlists)
    names = _playlist_names_by_spotify_id(all_ids)

    return {
        "ui_skin": load_ui_skin(),
        "locale": load_locale(),
        "destination_playlist": _format_playlist_entry(destination, names)
        if destination
        else None,
        "source_playlists": [
            _format_playlist_entry(spotify_id, names) for spotify_id in source_playlists
        ],
        "tracking_playlists": [
            _format_playlist_entry(spotify_id, names) for spotify_id in tracking_playlists
        ],
        "tracking_start_date": start_date.strftime("%Y-%m-%d") if start_date else None,
        "sync_start_date": sync_start_date.strftime("%Y-%m-%d") if sync_start_date else None,
    }


def _collect_config_spotify_ids(config: dict) -> list[str]:
    ids: list[str] = []
    destination = (config.get("destination_playlist") or "").strip()
    if destination:
        ids.append(destination)
    for spotify_id in config.get("source_playlists") or []:
        spotify_id = (spotify_id or "").strip()
        if spotify_id and spotify_id not in ids:
            ids.append(spotify_id)
    for spotify_id in config.get("tracking_playlists") or []:
        spotify_id = (spotify_id or "").strip()
        if spotify_id and spotify_id not in ids:
            ids.append(spotify_id)
    return ids


def _resolve_playlist_details_for_config(config: dict) -> dict:
    spotify_ids = _collect_config_spotify_ids(config)
    if not spotify_ids:
        return {}
    try:
        sp = get_quiet_spotify_client()
    except RuntimeError as exc:
        raise ValueError(str(exc)) from exc
    try:
        return resolve_playlist_details(sp, spotify_ids)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


def _parse_playlist_list(values: list, field_name: str) -> list[str] | tuple[None, str]:
    parsed: list[str] = []
    for item in values:
        if not isinstance(item, str):
            return None, f"{field_name} items must be strings"
        spotify_id = parse_spotify_playlist_id(item)
        if not spotify_id:
            return None, f"Invalid playlist in {field_name}: {item}"
        if spotify_id not in parsed:
            parsed.append(spotify_id)
    return parsed, ""


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
        static_folder=str(STATIC_DIR),
    )

    def _render_page():
        locale = load_locale()
        return render_template(
            "new_tracks_todo.html",
            ui_skin=load_ui_skin(),
            locale=locale_html_lang(locale),
            locale_code=locale,
            translations_json=json.dumps(load_catalog(locale), ensure_ascii=False),
            _=lambda msgid: translate(msgid, locale),
        )

    @app.get("/")
    def index():
        return _render_page()

    @app.get("/api/genres")
    def list_genres():
        try:
            tracks = load_new_tracks()
            genre_images = load_genre_images()
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        counts: dict[str, int] = {}
        for track in tracks:
            name = (track.get("genre") or "").strip()
            key = name or "__uncategorized__"
            counts[key] = counts.get(key, 0) + 1

        genres = []
        for key in sorted(counts, key=lambda k: (k == "__uncategorized__", k.lower())):
            slug = "Uncategorized" if key == "__uncategorized__" else key
            label = "Uncategorized" if key == "__uncategorized__" else key
            image_url = None if key == "__uncategorized__" else resolve_genre_image(
                slug,
                genre_images=genre_images,
                tracks=tracks,
            )
            genres.append(
                {
                    "slug": slug,
                    "label": label,
                    "track_count": counts[key],
                    "image_url": image_url,
                }
            )

        return jsonify({"genres": genres, "total": len(tracks)})

    @app.get("/api/tracks")
    def list_tracks():
        genre = request.args.get("genre")
        try:
            tracks = load_new_tracks()
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        if genre:
            if genre == "Uncategorized":
                tracks = [t for t in tracks if not (t.get("genre") or "").strip()]
            else:
                tracks = [
                    t for t in tracks if (t.get("genre") or "").strip() == genre
                ]

        with_url = [t for t in tracks if t.get("reference_url")]
        without_url = [t for t in tracks if not t.get("reference_url")]
        genre_image_url = resolve_genre_image(genre, tracks=tracks) if genre else None
        return jsonify(
            {
                "with_url": with_url,
                "without_url": without_url,
                "total": len(tracks),
                "genre": genre,
                "genre_image_url": genre_image_url,
            }
        )

    @app.post("/api/tracks")
    def create_track():
        data = request.get_json(silent=True) or {}
        track = data.get("track")
        if not isinstance(track, str) or not track.strip():
            return jsonify({"error": "track is required"}), 400

        reference_url = data.get("reference_url")
        if reference_url is not None and not isinstance(reference_url, str):
            return jsonify({"error": "reference_url must be a string or null"}), 400

        genre = data.get("genre")
        if genre is not None and not isinstance(genre, str):
            return jsonify({"error": "genre must be a string or null"}), 400
        if genre == "Uncategorized":
            genre = None

        try:
            created = create_new_track(track, reference_url, genre=genre)
        except ValueError as e:
            status = 409 if "already exists" in str(e).lower() else 400
            return jsonify({"error": str(e)}), status

        return jsonify({**created, "has_url": bool(created.get("reference_url"))}), 201

    @app.patch("/api/tracks/<int:track_id>")
    def patch_track(track_id: int):
        data = request.get_json(silent=True) or {}
        if "reference_url" not in data:
            return jsonify({"error": "reference_url is required"}), 400

        reference_url = data.get("reference_url")
        if reference_url is not None and not isinstance(reference_url, str):
            return jsonify({"error": "reference_url must be a string or null"}), 400

        if not update_new_track_reference_url(track_id, reference_url):
            return jsonify({"error": "Track not found"}), 404

        url = normalize_reference_url(reference_url)
        return jsonify(
            {
                "id": track_id,
                "reference_url": url,
                "has_url": bool(url),
            }
        )

    @app.post("/api/tracks/<int:track_id>/copy-title")
    def record_copy_title(track_id: int):
        try:
            count = increment_new_track_copy_title_count(track_id)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        if count is None:
            return jsonify({"error": "Track not found"}), 404

        return jsonify({"id": track_id, "copy_title_count": count})

    @app.delete("/api/tracks/<int:track_id>")
    def remove_track(track_id: int):
        if not delete_new_track(track_id):
            return jsonify({"error": "Track not found"}), 404
        return jsonify({"id": track_id, "deleted": True})

    @app.get("/api/playlists/lookup")
    def lookup_playlist():
        raw_id = request.args.get("id", "")
        if not isinstance(raw_id, str) or not raw_id.strip():
            return jsonify({"error": "id is required"}), 400

        spotify_id = parse_spotify_playlist_id(raw_id)
        if not spotify_id:
            return jsonify({"error": "Invalid playlist ID"}), 400

        names = _playlist_names_by_spotify_id([spotify_id])
        if spotify_id in names and names[spotify_id] != spotify_id:
            return jsonify({"spotify_id": spotify_id, "name": names[spotify_id]})

        try:
            sp = get_quiet_spotify_client()
            info = resolve_playlist_details(sp, [spotify_id]).get(spotify_id)
            if info:
                return jsonify({"spotify_id": spotify_id, "name": info.get("name")})
        except (RuntimeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify({"spotify_id": spotify_id, "name": names.get(spotify_id)})

    @app.post("/api/import/tracks")
    def start_track_import():
        job_id, error = create_import_job()
        if error:
            status = 400
            if "Spotify" in error or "token" in error.lower() or "login" in error.lower():
                status = 401
            return jsonify({"error": error}), status
        return jsonify({"job_id": job_id}), 202

    @app.get("/api/import/tracks/<job_id>")
    def track_import_status(job_id: str):
        job = get_import_job(job_id)
        if not job:
            return jsonify({"error": "Import job not found"}), 404
        return jsonify(job)

    @app.get("/api/settings")
    def get_settings():
        try:
            return jsonify(_build_settings_payload())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.patch("/api/settings")
    def patch_settings():
        data = request.get_json(silent=True) or {}

        if "ui_skin" in data:
            skin = data.get("ui_skin")
            if not isinstance(skin, str):
                return jsonify({"error": "ui_skin must be a string"}), 400
            normalized = skin.strip().lower()
            if normalized == "neon":
                normalized = "colorful"
            elif normalized == "simple":
                normalized = "light"
            if normalized not in _VALID_UI_SKINS:
                return jsonify({"error": "ui_skin must be 'light', 'dark', or 'colorful'"}), 400
            try:
                save_ui_skin(normalized)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        if "locale" in data:
            locale = data.get("locale")
            if not isinstance(locale, str):
                return jsonify({"error": "locale must be a string"}), 400
            normalized = locale.strip().lower()
            if normalized not in _VALID_LOCALES:
                return jsonify({"error": "locale must be 'en', 'nl', or 'brab'"}), 400
            try:
                save_locale(normalized)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        config = load_playlists_config()
        config_changed = False

        if "destination_playlist" in data:
            destination = data.get("destination_playlist")
            if destination is None or destination == "":
                config["destination_playlist"] = ""
            elif isinstance(destination, str):
                spotify_id = parse_spotify_playlist_id(destination)
                if not spotify_id:
                    return jsonify({"error": "Invalid destination playlist"}), 400
                config["destination_playlist"] = spotify_id
            else:
                return jsonify({"error": "destination_playlist must be a string or null"}), 400
            config_changed = True

        if "source_playlists" in data:
            source_playlists = data.get("source_playlists")
            if not isinstance(source_playlists, list):
                return jsonify({"error": "source_playlists must be an array"}), 400
            parsed, error = _parse_playlist_list(source_playlists, "source_playlists")
            if error:
                return jsonify({"error": error}), 400
            config["source_playlists"] = parsed
            config_changed = True

        if "tracking_playlists" in data:
            tracking_playlists = data.get("tracking_playlists")
            if not isinstance(tracking_playlists, list):
                return jsonify({"error": "tracking_playlists must be an array"}), 400
            parsed, error = _parse_playlist_list(tracking_playlists, "tracking_playlists")
            if error:
                return jsonify({"error": error}), 400
            config["tracking_playlists"] = parsed
            config_changed = True

        if config_changed:
            try:
                playlist_details = _resolve_playlist_details_for_config(config)
                save_playlists_config(config, playlist_details=playlist_details)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        if "sync_start_date" in data:
            sync_start_date = data.get("sync_start_date")
            if sync_start_date is None or sync_start_date == "":
                try:
                    save_sync_start_date(None)
                except Exception as e:
                    return jsonify({"error": str(e)}), 500
            elif isinstance(sync_start_date, str):
                try:
                    save_sync_start_date(sync_start_date.strip())
                except Exception as e:
                    return jsonify({"error": str(e)}), 400
            else:
                return jsonify({"error": "sync_start_date must be a string or null"}), 400

        if "tracking_start_date" in data:
            tracking_start_date = data.get("tracking_start_date")
            if tracking_start_date is None or tracking_start_date == "":
                try:
                    save_tracking_start_date(None)
                except Exception as e:
                    return jsonify({"error": str(e)}), 500
            elif isinstance(tracking_start_date, str):
                try:
                    save_tracking_start_date(tracking_start_date.strip())
                except Exception as e:
                    return jsonify({"error": str(e)}), 400
            else:
                return jsonify({"error": "tracking_start_date must be a string or null"}), 400

        try:
            return jsonify(_build_settings_payload())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.get("/<path:genre>")
    def genre_page(genre: str):
        if genre.startswith("api/") or genre.startswith("static/"):
            from flask import abort

            abort(404)
        return _render_page()

    return app


def run_server(port: int = DEFAULT_PORT) -> None:
    from spotify_playlist.is_port_available import is_port_available

    try:
        tracks = load_new_tracks()
    except ImportError as e:
        print(f"❌ {e}")
        print("   Install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Could not connect to the database: {e}")
        print(
            "   Check MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, and MYSQL_DATABASE."
        )
        sys.exit(1)

    if not is_port_available(port):
        print(f"❌ Port {port} is already in use.")
        sys.exit(1)

    with_url = sum(1 for t in tracks if t.get("reference_url"))
    without_url = len(tracks) - with_url
    print(f"📀 {len(tracks)} tracks loaded ({with_url} with URL, {without_url} without)")

    app = create_app()
    print(f"🌐 New tracks to-do: http://127.0.0.1:{port}/")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    run_server()
