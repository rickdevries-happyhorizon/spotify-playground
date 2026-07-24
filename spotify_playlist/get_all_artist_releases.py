from typing import Any, Callable

from spotify_playlist.get_artist_new_releases import get_artist_new_releases
from spotify_playlist.get_followed_artists import get_followed_artists
from spotify_playlist.loading_progress import loading_bar, tqdm

ProgressCallback = Callable[[dict[str, Any]], None]


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
            artists = get_followed_artists(sp)
        else:
            with loading_bar("Fetching followed artists..."):
                artists = get_followed_artists(sp)
        log(f"   Found {len(artists)} followed artists")
        report(
            phase="artists_start",
            message=f"Found {len(artists)} followed artists",
            artist_index=0,
            artist_total=len(artists),
        )
    except Exception as e:
        log(f"❌ Could not fetch followed artists: {e}")
        raise

    all_new_releases = {}
    artist_total = len(artists)
    iterator = artists
    if not quiet:
        iterator = tqdm(artists, desc="Checking releases", unit="artist")

    for index, artist in enumerate(iterator, start=1):
        artist_id = artist["id"]
        artist_name = artist["name"]
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
        phase="artists_scanning",
        message=f"Found {len(all_new_releases)} releases from {artist_total} artists",
        artist_index=artist_total,
        artist_total=artist_total,
        releases_found=len(all_new_releases),
    )
    return all_new_releases
