from spotify_playlist.get_artist_new_releases import get_artist_new_releases
from spotify_playlist.get_followed_artists import get_followed_artists


def get_all_artist_releases(sp, days_back=30):
    """Haalt nieuwe releases op van alle gevolgde artiesten."""
    print(f"\n🎵 Controleer nieuwe releases van gevolgde artiesten (laatste {days_back} dagen)...")

    # Haal gevolgde artiesten op
    try:
        artist_ids = get_followed_artists(sp)
        print(f"   Gevonden {len(artist_ids)} gevolgde artiesten")
    except Exception as e:
        print(f"❌ Kon gevolgde artiesten niet ophalen: {e}")
        return {}

    all_new_releases = {}
    checked_count = 0

    # Haal nieuwe releases op voor elke artiest
    for artist_id in artist_ids:
        try:
            artist_info = sp.artist(artist_id)
            artist_name = artist_info['name']
            checked_count += 1

            if checked_count % 10 == 0:
                print(f"   Gecontroleerd {checked_count}/{len(artist_ids)} artiesten...")

            releases = get_artist_new_releases(sp, artist_id, days_back)
            if releases:
                print(f"   ✅ {artist_name}: {len(releases)} nieuwe releases gevonden")
                all_new_releases.update(releases)
        except Exception as e:
            print(f"   ⚠️  Fout bij controleren artiest {artist_id}: {e}")
            continue

    print(f"\n   Totaal {len(all_new_releases)} nieuwe releases gevonden van {checked_count} artiesten")
    return all_new_releases
