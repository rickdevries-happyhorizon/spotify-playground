from collections import Counter

from spotify_playlist.deps import SpotifyException


def get_playlist_artist_counts(
    sp,
    playlist_ids: list[str],
    *,
    max_tracks_per_playlist: int = 150,
) -> Counter[str]:
    """Count artist IDs appearing in the given playlists (newest tracks first)."""
    counts: Counter[str] = Counter()
    for playlist_id in playlist_ids:
        if not playlist_id:
            continue
        try:
            fetched = 0
            results = sp.playlist_items(
                playlist_id,
                fields="items.track.artists.id,next",
                limit=min(100, max_tracks_per_playlist),
            )
            while results and fetched < max_tracks_per_playlist:
                items = results.get("items") or []
                for item in items:
                    if fetched >= max_tracks_per_playlist:
                        break
                    track = item.get("track") or {}
                    artists = track.get("artists") or []
                    for artist in artists:
                        artist_id = artist.get("id")
                        if artist_id:
                            counts[artist_id] += 1
                    fetched += 1
                if fetched >= max_tracks_per_playlist or not results.get("next"):
                    break
                results = sp.next(results)
        except SpotifyException:
            continue
        except Exception:
            continue
    return counts


def load_artist_genres(sp, artist_ids: list[str]) -> dict[str, list[str]]:
    """Batch-load genres for artist IDs."""
    genres_by_artist: dict[str, list[str]] = {}
    for batch_start in range(0, len(artist_ids), 50):
        batch = artist_ids[batch_start : batch_start + 50]
        try:
            response = sp.artists(batch)
        except Exception:
            continue
        for artist in response.get("artists") or []:
            if not artist or not artist.get("id"):
                continue
            genres_by_artist[artist["id"]] = list(artist.get("genres") or [])
    return genres_by_artist


def top_genres_from_artists(
    artist_ids: list[str],
    genres_by_artist: dict[str, list[str]],
    *,
    limit: int = 10,
) -> list[str]:
    """Rank genres by how often they appear among the given artists."""
    genre_counts: Counter[str] = Counter()
    for artist_id in artist_ids:
        for genre in genres_by_artist.get(artist_id, []):
            if genre:
                genre_counts[genre] += 1
    return [genre for genre, _ in genre_counts.most_common(limit)]
