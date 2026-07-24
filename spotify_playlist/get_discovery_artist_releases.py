from typing import Any, Callable

from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_artist_new_releases import get_artist_new_releases
from spotify_playlist.get_followed_artists import get_followed_artists
from spotify_playlist.get_playlist_artist_counts import (
    get_playlist_artist_counts,
    load_artist_genres,
    top_genres_from_artists,
)
from spotify_playlist.loading_progress import loading_bar, tqdm

ProgressCallback = Callable[[dict[str, Any]], None]


def _try_related_artists(sp, artist_id: str) -> list[dict[str, Any]] | None:
    """Return related artists, or None when the endpoint is unavailable."""
    try:
        response = sp.artist_related_artists(artist_id)
        return list(response.get("artists") or [])
    except SpotifyException as exc:
        if getattr(exc, "http_status", None) in (403, 404):
            return None
        return []
    except Exception:
        return []


def _search_artists_by_genre(sp, genre: str, *, limit: int = 20) -> list[dict[str, Any]]:
    try:
        response = sp.search(q=f'genre:"{genre}"', type="artist", limit=limit)
    except Exception:
        return []
    items = ((response.get("artists") or {}).get("items")) or []
    return [artist for artist in items if artist and artist.get("id")]


def discover_candidate_artists(
    sp,
    seed_artist_ids: list[str],
    *,
    exclude_artist_ids: set[str],
    max_candidates: int = 40,
    max_related_seeds: int = 15,
    max_genres: int = 8,
) -> list[dict[str, Any]]:
    """Find artists similar to the seed set, excluding already-known artists."""
    candidates: dict[str, dict[str, Any]] = {}
    related_available = True

    for artist_id in seed_artist_ids[:max_related_seeds]:
        if not related_available:
            break
        related = _try_related_artists(sp, artist_id)
        if related is None:
            related_available = False
            break
        for artist in related:
            candidate_id = artist.get("id")
            if not candidate_id or candidate_id in exclude_artist_ids:
                continue
            previous = candidates.get(candidate_id)
            popularity = int(artist.get("popularity") or 0)
            if previous is None or popularity > int(previous.get("popularity") or 0):
                candidates[candidate_id] = {
                    "id": candidate_id,
                    "name": artist.get("name") or candidate_id,
                    "popularity": popularity,
                }

    genres_by_artist = load_artist_genres(sp, seed_artist_ids[:50])
    for genre in top_genres_from_artists(seed_artist_ids, genres_by_artist, limit=max_genres):
        for artist in _search_artists_by_genre(sp, genre):
            candidate_id = artist.get("id")
            if not candidate_id or candidate_id in exclude_artist_ids:
                continue
            previous = candidates.get(candidate_id)
            popularity = int(artist.get("popularity") or 0)
            if previous is None or popularity > int(previous.get("popularity") or 0):
                candidates[candidate_id] = {
                    "id": candidate_id,
                    "name": artist.get("name") or candidate_id,
                    "popularity": popularity,
                }

    ranked = sorted(
        candidates.values(),
        key=lambda item: (-int(item.get("popularity") or 0), item.get("name") or ""),
    )
    return ranked[:max_candidates]


def get_discovery_artist_releases(
    sp,
    tracking_playlist_ids: list[str],
    days_back: int = 7,
    *,
    max_seed_artists: int = 25,
    max_candidates: int = 40,
    max_tracks_per_playlist: int = 150,
    on_progress: ProgressCallback | None = None,
    quiet: bool = False,
) -> dict[str, dict[str, Any]]:
    """Discover new artists from tracking-playlist taste and fetch recent releases."""

    def log(message: str = "") -> None:
        if not quiet:
            print(message)

    def report(**payload: Any) -> None:
        if on_progress:
            on_progress(payload)

    if not tracking_playlist_ids:
        log("   No tracking playlists configured for artist discovery.")
        return {}

    report(
        phase="discovery_start",
        message="Building taste profile from tracking playlists…",
    )
    log("\n🔎 Discovering new artists from tracking playlists...")

    if quiet:
        artist_counts = get_playlist_artist_counts(
            sp,
            tracking_playlist_ids,
            max_tracks_per_playlist=max_tracks_per_playlist,
        )
    else:
        with loading_bar("Analyzing tracking playlists..."):
            artist_counts = get_playlist_artist_counts(
                sp,
                tracking_playlist_ids,
                max_tracks_per_playlist=max_tracks_per_playlist,
            )

    seed_artist_ids = [artist_id for artist_id, _ in artist_counts.most_common(max_seed_artists)]
    if not seed_artist_ids:
        log("   No artists found in tracking playlists.")
        report(phase="discovery_done", message="No seed artists found", discovery_artists=0)
        return {}

    log(f"   Taste seeds: {len(seed_artist_ids)} artists from {len(tracking_playlist_ids)} playlists")

    try:
        followed_ids = set(get_followed_artists(sp))
    except Exception:
        followed_ids = set()

    exclude_ids = set(artist_counts) | followed_ids
    report(
        phase="discovery_candidates",
        message="Finding similar artists…",
        discovery_seed_artists=len(seed_artist_ids),
    )

    if quiet:
        candidates = discover_candidate_artists(
            sp,
            seed_artist_ids,
            exclude_artist_ids=exclude_ids,
            max_candidates=max_candidates,
        )
    else:
        with loading_bar("Finding similar artists..."):
            candidates = discover_candidate_artists(
                sp,
                seed_artist_ids,
                exclude_artist_ids=exclude_ids,
                max_candidates=max_candidates,
            )

    if not candidates:
        log("   No new artists discovered.")
        report(phase="discovery_done", message="No new artists discovered", discovery_artists=0)
        return {}

    log(f"   Checking releases from {len(candidates)} discovered artists")
    report(
        phase="discovery_scanning",
        message=f"Checking {len(candidates)} discovered artists…",
        artist_index=0,
        artist_total=len(candidates),
        discovery_artists=len(candidates),
    )

    all_new_releases: dict[str, dict[str, Any]] = {}
    iterator = candidates if quiet else tqdm(candidates, desc="Discovery releases", unit="artist")
    for index, artist in enumerate(iterator, start=1):
        artist_id = artist["id"]
        artist_name = artist.get("name") or artist_id[:8]
        try:
            report(
                phase="discovery_scanning",
                message=f"Checking {artist_name} ({index}/{len(candidates)})",
                artist_index=index,
                artist_total=len(candidates),
                artist_name=artist_name,
                playlist_name=artist_name,
                discovery_artists=len(candidates),
            )
            releases = get_artist_new_releases(sp, artist_id, days_back)
            if releases:
                if not quiet:
                    writer = getattr(iterator, "write", print)
                    writer(f"   ✅ {artist_name}: {len(releases)} new releases found")
                all_new_releases.update(releases)
        except Exception as exc:
            if not quiet:
                writer = getattr(iterator, "write", print)
                writer(f"   ⚠️  Error checking artist {artist_id}: {exc}")
            continue

    log(
        f"\n   Total {len(all_new_releases)} discovery releases from "
        f"{len(candidates)} artists"
    )
    report(
        phase="discovery_done",
        message=(
            f"Found {len(all_new_releases)} discovery release"
            f"{'' if len(all_new_releases) == 1 else 's'} "
            f"from {len(candidates)} artists"
        ),
        artist_index=len(candidates),
        artist_total=len(candidates),
        discovery_artists=len(candidates),
        discovery_releases_found=len(all_new_releases),
    )
    return all_new_releases
