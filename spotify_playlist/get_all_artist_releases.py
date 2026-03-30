from spotify_playlist.get_artist_new_releases import get_artist_new_releases
from spotify_playlist.get_followed_artists import get_followed_artists
from spotify_playlist.loading_progress import loading_bar, tqdm


def get_all_artist_releases(sp, days_back=30):
    """Haalt nieuwe releases op van alle gevolgde artiesten."""
    print(f"\n🎵 Controleer nieuwe releases van gevolgde artiesten (laatste {days_back} dagen)...")

    # Haal gevolgde artiesten op
    try:
        with loading_bar("Gevolgde artiesten ophalen..."):
            artist_ids = get_followed_artists(sp)
        print(f"   Gevonden {len(artist_ids)} gevolgde artiesten")
    except Exception as e:
        print(f"❌ Kon gevolgde artiesten niet ophalen: {e}")
        return {}

    all_new_releases = {}

    # Haal nieuwe releases op voor elke artiest
    for artist_id in tqdm(artist_ids, desc="Releases controleren", unit="artiest"):
        try:
            artist_info = sp.artist(artist_id)
            artist_name = artist_info['name']

            releases = get_artist_new_releases(sp, artist_id, days_back)
            if releases:
                tqdm.write(f"   ✅ {artist_name}: {len(releases)} nieuwe releases gevonden")
                all_new_releases.update(releases)
        except Exception as e:
            tqdm.write(f"   ⚠️  Fout bij controleren artiest {artist_id}: {e}")
            continue

    print(f"\n   Totaal {len(all_new_releases)} nieuwe releases gevonden van {len(artist_ids)} artiesten")
    return all_new_releases
