from typing import Any, Callable

from spotify_playlist.get_artist_new_releases import get_artist_new_releases
from spotify_playlist.get_followed_artists import get_followed_artists
from spotify_playlist.loading_progress import loading_bar, tqdm

ProgressCallback = Callable[[dict[str, Any]], None]


def _load_artist_names(
    sp,
    artist_ids: list[str],
    on_report: Callable[..., None] | None = None,
    artist_total: int = 0,
) -> dict[str, str]:
    names: dict[str, str] = {}
    batch_total = max(1, (len(artist_ids) + 49) // 50)
    for batch_index, batch_start in enumerate(range(0, len(artist_ids), 50), start=1):
        if on_report:
            on_report(
                phase="artists_start",
                message=f"Loading artist names ({batch_index}/{batch_total})…",
                artist_index=0,
                artist_total=artist_total,
            )
        batch = artist_ids[batch_start : batch_start + 50]
        response = sp.artists(batch)
        for artist in response.get("artists") or []:
            if artist and artist.get("id"):
                names[artist["id"]] = artist.get("name") or artist["id"]
    return names


def get_all_artist_releases(
    sp,
    days_back=30,
    on_progress: ProgressCallback | None = None,
    quiet: bool = False,
):
    """Fetches new releases from all followed artists."""

    def log(message: str = "") -> None:
        if not quiet:
            print(message)

    def report(**payload: Any) -> None:
        if on_progress:
            on_progress(payload)

    log(f"\n🎵 Checking new releases from followed artists (last {days_back} days)...")

    try:
        if quiet:
            artist_ids = get_followed_artists(sp)
        else:
            with loading_bar("Fetching followed artists..."):
                artist_ids = get_followed_artists(sp)
        log(f"   Found {len(artist_ids)} followed artists")
        report(
            phase="artists_start",
            message=f"Found {len(artist_ids)} followed artists",
            artist_index=0,
            artist_total=len(artist_ids),
        )
    except Exception as e:
        log(f"❌ Could not fetch followed artists: {e}")
        raise

    artist_total = len(artist_ids)
    artist_names = _load_artist_names(
        sp,
        artist_ids,
        on_report=report,
        artist_total=artist_total,
    )

    all_new_releases = {}
    iterator = artist_ids
    if not quiet:
        iterator = tqdm(artist_ids, desc="Checking releases", unit="artist")

    for index, artist_id in enumerate(iterator, start=1):
        artist_name = artist_names.get(artist_id, artist_id[:8])
        try:
            report(
                phase="artists_scanning",
                message=f"Checking {artist_name} ({index}/{artist_total})",
                artist_index=index,
                artist_total=artist_total,
                artist_name=artist_name,
                playlist_name=artist_name,
            )
            releases = get_artist_new_releases(sp, artist_id, days_back)
            if releases:
                if not quiet:
                    writer = getattr(iterator, "write", print)
                    writer(f"   ✅ {artist_name}: {len(releases)} new releases found")
                all_new_releases.update(releases)
        except Exception as e:
            if not quiet:
                writer = getattr(iterator, "write", print)
                writer(f"   ⚠️  Error checking artist {artist_id}: {e}")
            continue

    log(f"\n   Total {len(all_new_releases)} new releases found from {artist_total} artists")
    report(
        phase="artists_done",
        message=f"Found {len(all_new_releases)} releases from {artist_total} artists",
        artist_index=artist_total,
        artist_total=artist_total,
        releases_found=len(all_new_releases),
    )
    return all_new_releases
