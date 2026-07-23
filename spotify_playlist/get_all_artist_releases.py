from spotify_playlist.get_artist_new_releases import get_artist_new_releases
from spotify_playlist.get_followed_artists import get_followed_artists
from spotify_playlist.loading_progress import loading_bar, tqdm


def get_all_artist_releases(sp, days_back=30):
    """Fetches new releases from all followed artists."""
    print(f"\n🎵 Checking new releases from followed artists (last {days_back} days)...")

    # Fetch followed artists
    try:
        with loading_bar("Fetching followed artists..."):
            artist_ids = get_followed_artists(sp)
        print(f"   Found {len(artist_ids)} followed artists")
    except Exception as e:
        print(f"❌ Could not fetch followed artists: {e}")
        return {}

    all_new_releases = {}

    # Fetch new releases for each artist
    for artist_id in tqdm(artist_ids, desc="Checking releases", unit="artist"):
        try:
            artist_info = sp.artist(artist_id)
            artist_name = artist_info['name']

            releases = get_artist_new_releases(sp, artist_id, days_back)
            if releases:
                tqdm.write(f"   ✅ {artist_name}: {len(releases)} new releases found")
                all_new_releases.update(releases)
        except Exception as e:
            tqdm.write(f"   ⚠️  Error checking artist {artist_id}: {e}")
            continue

    print(f"\n   Total {len(all_new_releases)} new releases found from {len(artist_ids)} artists")
    return all_new_releases
