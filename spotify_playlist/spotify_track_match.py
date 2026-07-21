"""Match local audio filenames to Spotify tracks."""

from __future__ import annotations

import re
from typing import Any

from spotify_playlist.release_year import normalize_release_year


def normalize_match_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def track_title_from_stem(stem: str) -> str:
    _, track_part = stem.split(' - ', 1)
    return track_part.strip()


def artist_names_from_track(track: dict[str, Any]) -> list[str]:
    return [artist['name'] for artist in track.get('artists', []) if artist.get('name')]


def score_track_match(track: dict[str, Any], artists: list[str], track_title: str) -> float:
    spotify_track = normalize_match_text(track.get('name', ''))
    target_track = normalize_match_text(track_title)
    if not spotify_track or not target_track:
        return 0.0

    if spotify_track == target_track:
        track_score = 1.0
    elif spotify_track in target_track or target_track in spotify_track:
        track_score = 0.85
    else:
        spotify_words = set(spotify_track.split())
        target_words = set(target_track.split())
        if not target_words:
            track_score = 0.0
        else:
            overlap = len(spotify_words & target_words) / len(target_words)
            track_score = overlap * 0.8

    spotify_artists = [normalize_match_text(name) for name in artist_names_from_track(track)]
    target_artists = [normalize_match_text(name) for name in artists if name.strip()]
    if not target_artists or not spotify_artists:
        artist_score = 0.0
    else:
        best_artist_score = 0.0
        for target_artist in target_artists:
            for spotify_artist in spotify_artists:
                if spotify_artist == target_artist:
                    best_artist_score = max(best_artist_score, 1.0)
                elif spotify_artist in target_artist or target_artist in spotify_artist:
                    best_artist_score = max(best_artist_score, 0.85)
                else:
                    target_words = set(target_artist.split())
                    spotify_words = set(spotify_artist.split())
                    if target_words:
                        overlap = len(target_words & spotify_words) / len(target_words)
                        best_artist_score = max(best_artist_score, overlap * 0.75)
        artist_score = best_artist_score

    return (track_score * 0.65) + (artist_score * 0.35)


def search_queries(artists: list[str], track_title: str) -> list[str]:
    primary_artist = artists[0]
    queries = [
        f'track:"{track_title}" artist:"{primary_artist}"',
        f'{track_title} artist:{primary_artist}',
    ]
    for artist in artists[1:3]:
        queries.append(f'track:"{track_title}" artist:"{artist}"')
    return queries


def find_spotify_track(sp, artists: list[str], stem: str) -> dict[str, Any] | None:
    """Find the best Spotify track match for a local filename."""
    track_title = track_title_from_stem(stem)
    best_track: dict[str, Any] | None = None
    best_score = 0.0

    for query in search_queries(artists, track_title):
        results = sp.search(q=query, type='track', limit=10)
        items = results.get('tracks', {}).get('items', [])
        for item in items:
            score = score_track_match(item, artists, track_title)
            if score > best_score:
                best_score = score
                best_track = item
        if best_score >= 0.9:
            break

    if best_track is None or best_score < 0.55:
        return None
    return best_track


def metadata_from_spotify_track(track: dict[str, Any]) -> dict[str, Any | None]:
    """Extract Rekordbox-relevant metadata from a Spotify track."""
    album = track.get('album') or {}
    release_date = (album.get('release_date') or '').strip()
    album_name = (album.get('name') or '').strip()
    year = normalize_release_year(release_date)

    return {
        'album': album_name or None,
        'release_date': release_date or None,
        'year': year,
    }
