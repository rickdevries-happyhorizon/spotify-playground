from datetime import datetime

from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException


def get_playlist_tracks_since_date(sp, playlist_id, since_date, return_track_info=False, debug=False):
    """Haalt tracks op die sinds een specifieke datum zijn toegevoegd aan de playlist.

    Args:
        sp: Spotify client
        playlist_id: ID van de playlist
        since_date: datetime object - alleen tracks toegevoegd na deze datum
        return_track_info: Als True, retourneert ook track informatie (naam, artiesten, added_at)
        debug: Als True, toon debug informatie

    Returns:
        Als return_track_info=False: set van track URIs
        Als return_track_info=True: dict met URI als key en {'name': ..., 'artists': ..., 'added_at': ...} als value
    """
    track_data = {} if return_track_info else set()
    items_without_added_at = 0
    items_processed = 0

    try:
        # Haal playlist items op met added_at datum
        # Let op: added_at is alleen beschikbaar voor playlists die je bezit of waar je collaborator bent
        results = sp.playlist_items(
            playlist_id,
            fields='items.added_at,items.track.uri,items.track.name,items.track.artists,items.track.id,next',
            limit=100,
        )

        if debug:
            print(f"{Colors.DIM}   Debug: API response keys: {list(results.keys()) if results else 'None'}{Colors.RESET}")
            if results and 'items' in results:
                print(f"{Colors.DIM}   Debug: Aantal items in eerste batch: {len(results['items'])}{Colors.RESET}")
                if len(results['items']) > 0:
                    first_item = results['items'][0]
                    print(f"{Colors.DIM}   Debug: Eerste item keys: {list(first_item.keys())}{Colors.RESET}")
                    print(f"{Colors.DIM}   Debug: Eerste item added_at: {first_item.get('added_at', 'NIET AANWEZIG')}{Colors.RESET}")

        while results:
            for item in results['items']:
                items_processed += 1

                # Controleer of track bestaat
                track = item.get('track')
                if not track or not track.get('uri'):
                    if debug:
                        print(f"{Colors.DIM}   Debug: Item {items_processed} heeft geen track of URI{Colors.RESET}")
                    continue

                # Controleer wanneer de track is toegevoegd
                added_at_str = item.get('added_at')

                if not added_at_str:
                    items_without_added_at += 1
                    if debug and items_without_added_at <= 3:
                        track_name = track.get('name', 'Unknown')
                        print(f"{Colors.BRIGHT_YELLOW}   ⚠️  Track '{track_name}' heeft geen added_at veld{Colors.RESET}")
                        print(f"{Colors.DIM}      Dit kan betekenen dat je geen rechten hebt om deze informatie te zien{Colors.RESET}")
                    # Als geen added_at, neem de track op (voor veiligheid)
                    uri = track['uri']
                    if return_track_info:
                        artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
                        track_data[uri] = {
                            'name': track.get('name', 'Unknown'),
                            'artists': artists,
                            'added_at': None  # Geen datum beschikbaar
                        }
                    else:
                        track_data.add(uri)
                    continue

                try:
                    # Parse de ISO 8601 datum
                    added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                    # Converteer naar local timezone voor vergelijking
                    if added_at.tzinfo:
                        added_at = added_at.astimezone().replace(tzinfo=None)

                    if debug and len(track_data) < 5:
                        track_name = track.get('name', 'Unknown')
                        print(
                            f"{Colors.DIM}   Debug: Track '{track_name}' - added_at: "
                            f"{added_at.strftime('%Y-%m-%d %H:%M:%S')}, since_date: "
                            f"{since_date.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}"
                        )

                    # Alleen tracks die na of gelijk aan de since_date zijn toegevoegd
                    # Let op: we stoppen NIET vroegtijdig omdat de volgorde niet altijd perfect is
                    if added_at >= since_date:
                        uri = track['uri']
                        if return_track_info:
                            artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
                            track_data[uri] = {
                                'name': track.get('name', 'Unknown'),
                                'artists': artists,
                                'added_at': added_at_str
                            }
                        else:
                            track_data.add(uri)

                except (ValueError, AttributeError) as e:
                    if debug:
                        print(f"{Colors.BRIGHT_YELLOW}   ⚠️  Kon datum niet parsen: {added_at_str} - {e}{Colors.RESET}")
                    # Als parsing mislukt, negeer deze track
                    continue

            if results:
                results = sp.next(results) if results.get('next') else None

        if debug:
            print(f"{Colors.DIM}   Debug: Totaal items verwerkt: {items_processed}, zonder added_at: {items_without_added_at}{Colors.RESET}")

        return track_data
    except SpotifyException as e:
        print(f"❌ Spotify API fout bij ophalen tracks: {e}")
        if e.http_status == 403:
            print(f"{Colors.BRIGHT_YELLOW}   ⚠️  Geen toegang tot added_at informatie. Mogelijk geen rechten voor deze playlist.{Colors.RESET}")
        raise
    except Exception as e:
        print(f"❌ Onverwachte fout bij ophalen tracks: {e}")
        raise
