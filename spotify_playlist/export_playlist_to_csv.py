import os
import csv

from spotify_playlist.deps import SpotifyException


def export_playlist_to_csv(sp, playlist_id, output_file=None):
    """Exporteert een playlist naar een CSV bestand."""
    try:
        # Haal playlist informatie op
        playlist_info = sp.playlist(playlist_id, fields='name,owner')
        playlist_name = playlist_info['name']
        print(f"\n📋 Exporteer playlist: {playlist_name}")

        # Genereer bestandsnaam als niet opgegeven
        if not output_file:
            # Maak bestandsnaam veilig voor bestandssysteem
            safe_name = "".join(c for c in playlist_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            output_file = f"playlist_{safe_name}_{playlist_id[:8]}.csv"

        # Haal alle tracks op met volledige informatie
        tracks_data = []
        results = sp.playlist_items(playlist_id, fields='items.track,next', limit=100)

        while results:
            for item in results['items']:
                track = item.get('track')
                if track and track.get('uri'):
                    # Haal volledige track informatie op
                    try:
                        full_track = sp.track(track['id'])
                        artists = ', '.join([artist['name'] for artist in full_track.get('artists', [])])
                        track_name = full_track.get('name', 'Unknown')

                        tracks_data.append({
                            'Track': f"{artists} - {track_name}"
                        })
                    except Exception:
                        # Fallback als volledige track info niet beschikbaar is
                        artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
                        track_name = track.get('name', 'Unknown')

                        tracks_data.append({
                            'Track': f"{artists} - {track_name}"
                        })

            results = sp.next(results) if results.get('next') else None

        # Schrijf naar CSV
        if tracks_data:
            # Sorteer tracks alfabetisch
            tracks_data = sorted(tracks_data, key=lambda x: x['Track'].lower())
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Track']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for i, row in enumerate(tracks_data):
                    writer.writerow(row)
                    if (i + 1) % 5 == 0:
                        writer.writerow(dict.fromkeys(fieldnames, ''))  # Lege regel na elke 5 rijen

            print(f"✅ {len(tracks_data)} tracks geëxporteerd naar: {output_file}")
            print(f"   Bestandslocatie: {os.path.abspath(output_file)}")
        else:
            print("⚠️  Geen tracks gevonden in deze playlist.")

    except SpotifyException as e:
        print(f"❌ Fout bij exporteren playlist: {e}")
        if e.http_status == 404:
            print("   Playlist niet gevonden. Controleer of de playlist ID correct is.")
        elif e.http_status == 403:
            print("   Geen toegang tot deze playlist. Controleer je rechten.")
    except Exception as e:
        print(f"❌ Onverwachte fout bij exporteren: {e}")
