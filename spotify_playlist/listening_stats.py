"""Aggregate Spotify listening stats from recently played and top endpoints."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

MAX_RECENT_PAGES = 80


def _parse_played_at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _period_start(period: str) -> datetime:
    now = datetime.now(timezone.utc)
    if period == "week":
        return now - timedelta(days=7)
    if period == "month":
        return now - timedelta(days=30)
    if period == "year":
        return datetime(now.year, 1, 1, tzinfo=timezone.utc)
    raise ValueError(f"Unknown period: {period}")


def _aggregate_recently_played(
    sp: Any,
    since: datetime,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], int]:
    track_counts: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "track": None})
    artist_counts: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "artist": None})
    total_ms = 0
    before: int | None = None

    for _ in range(MAX_RECENT_PAGES):
        kwargs: dict[str, Any] = {"limit": 50}
        if before is not None:
            kwargs["before"] = before

        result = sp.current_user_recently_played(**kwargs)
        items = result.get("items") or []
        if not items:
            break

        stop = False
        for item in items:
            played_at = item.get("played_at")
            if not played_at:
                continue

            played_dt = _parse_played_at(played_at)
            if played_dt < since:
                stop = True
                break

            track = item.get("track")
            if not track or track.get("is_local") or not track.get("id"):
                continue

            track_id = track["id"]
            track_counts[track_id]["count"] += 1
            track_counts[track_id]["track"] = track

            for artist in track.get("artists") or []:
                artist_id = artist.get("id")
                if not artist_id:
                    continue
                artist_counts[artist_id]["count"] += 1
                artist_counts[artist_id]["artist"] = artist

            total_ms += int(track.get("duration_ms") or 0)

        if stop:
            break

        cursors = result.get("cursors") or {}
        next_before = cursors.get("before")
        if not next_before:
            break
        before = int(next_before)

    return track_counts, artist_counts, total_ms


def _format_top_tracks(track_counts: dict[str, dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    ranked = sorted(track_counts.values(), key=lambda entry: entry["count"], reverse=True)[:limit]
    formatted: list[dict[str, Any]] = []

    for entry in ranked:
        track = entry["track"]
        if not track:
            continue
        images = (track.get("album") or {}).get("images") or []
        formatted.append(
            {
                "id": track.get("id"),
                "name": track.get("name"),
                "artists": [artist.get("name") for artist in track.get("artists") or [] if artist.get("name")],
                "image_url": images[0]["url"] if images else None,
                "spotify_url": (track.get("external_urls") or {}).get("spotify"),
                "play_count": entry["count"],
            }
        )

    return formatted


def _format_top_artists(artist_counts: dict[str, dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    ranked = sorted(artist_counts.values(), key=lambda entry: entry["count"], reverse=True)[:limit]
    formatted: list[dict[str, Any]] = []

    for entry in ranked:
        artist = entry["artist"]
        if not artist:
            continue
        images = artist.get("images") or []
        formatted.append(
            {
                "id": artist.get("id"),
                "name": artist.get("name"),
                "image_url": images[0]["url"] if images else None,
                "spotify_url": (artist.get("external_urls") or {}).get("spotify"),
                "play_count": entry["count"],
            }
        )

    return formatted


def _format_top_items(items: list[dict[str, Any]], *, kind: str, limit: int = 10) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []

    for index, item in enumerate(items[:limit], start=1):
        if kind == "track":
            images = (item.get("album") or {}).get("images") or []
            formatted.append(
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "artists": [artist.get("name") for artist in item.get("artists") or [] if artist.get("name")],
                    "image_url": images[0]["url"] if images else None,
                    "spotify_url": (item.get("external_urls") or {}).get("spotify"),
                    "rank": index,
                }
            )
            continue

        images = item.get("images") or []
        formatted.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "image_url": images[0]["url"] if images else None,
                "spotify_url": (item.get("external_urls") or {}).get("spotify"),
                "rank": index,
            }
        )

    return formatted


def _load_top_from_api(
    sp: Any,
    time_range: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tracks_result = sp.current_user_top_tracks(limit=10, time_range=time_range)
    artists_result = sp.current_user_top_artists(limit=10, time_range=time_range)
    tracks = _format_top_items(tracks_result.get("items") or [], kind="track")
    artists = _format_top_items(artists_result.get("items") or [], kind="artist")
    return tracks, artists


def _load_week_from_recently_played(sp: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    since = _period_start("week")
    track_counts, artist_counts, _ = _aggregate_recently_played(sp, since)
    tracks = _format_top_tracks(track_counts)
    artists = _format_top_artists(artist_counts)

    if tracks or artists:
        return tracks, artists, "recently_played"

    tracks, artists = _load_top_from_api(sp, "short_term")
    return tracks, artists, "spotify_top"


def fetch_listening_stats(sp: Any) -> dict[str, Any]:
    """Return top tracks/artists for week, month, and year."""
    week_tracks, week_artists, week_source = _load_week_from_recently_played(sp)
    month_tracks, month_artists = _load_top_from_api(sp, "medium_term")
    year_tracks, year_artists = _load_top_from_api(sp, "long_term")

    return {
        "periods": {
            "week": {
                "tracks": week_tracks,
                "artists": week_artists,
                "source": week_source,
            },
            "month": {
                "tracks": month_tracks,
                "artists": month_artists,
                "source": "spotify_top",
            },
            "year": {
                "tracks": year_tracks,
                "artists": year_artists,
                "source": "spotify_top",
            },
        },
    }
