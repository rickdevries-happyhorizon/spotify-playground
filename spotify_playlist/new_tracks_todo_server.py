"""Browser UI for managing new_tracks reference URLs."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from db_store import (
    create_new_track,
    delete_new_track,
    increment_new_track_copy_title_count,
    load_genre_images,
    load_new_tracks,
    load_ui_skin,
    normalize_reference_url,
    resolve_genre_image,
    update_new_track_reference_url,
)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_PORT = int(os.environ.get("NEW_TRACKS_TODO_PORT", "5050"))


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(TEMPLATE_DIR),
        static_folder=str(STATIC_DIR),
    )

    def _render_page():
        return render_template("new_tracks_todo.html", ui_skin=load_ui_skin())

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

        try:
            created = create_new_track(track, reference_url)
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
