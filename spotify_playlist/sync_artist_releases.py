import spotify_playlist.config as config
from db_store import load_historical_data, load_playlists_config, save_historical_data

from spotify_playlist.add_tracks_to_playlist import add_tracks_to_playlist
from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_all_artist_releases import get_all_artist_releases


def sync_artist_releases(sp):
    """Controleert gevolgde artiesten op nieuwe releases en voegt deze toe aan de doel-playlist."""
    # Laad configuratie opnieuw (kan zijn aangepast)
    playlists_config = load_playlists_config()
    config.MIJN_DOEL_PLAYLIST_ID = playlists_config.get('destination_playlist', '')
    config.BRON_PLAYLISTS = playlists_config.get('source_playlists', [])

    # Valideer configuratie
    if not config.MIJN_DOEL_PLAYLIST_ID:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen doel-playlist geconfigureerd in de database.{Colors.RESET}")
        print(f"{Colors.DIM}   Stel een doel-playlist in via het menu of vul destination_config.{Colors.RESET}")
        return

    historische_nummers = load_historical_data(config.BRON_PLAYLISTS)
    nieuwe_nummers_uris = []

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎤  Nieuwe Releases van Gevolgde Artiesten  🎤{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}\n")

    try:
        # Haal nieuwe releases op (voortgang in get_all_artist_releases)
        artist_releases = get_all_artist_releases(sp, config.ARTIST_RELEASES_DAYS_BACK)

        if artist_releases:
            # Controleer welke releases nieuw zijn (niet al in historische data)
            artist_releases_key = '__artist_releases__'
            laatst_bekende_artist_releases = historische_nummers.get(artist_releases_key, set())
            nieuwe_artist_uris = set(artist_releases.keys()) - laatst_bekende_artist_releases

            if nieuwe_artist_uris:
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╔{'═'*68}╗{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_WHITE}🎉 {len(nieuwe_artist_uris)} nieuwe releases gevonden!{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-30)}║{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╠{'═'*68}╣{Colors.RESET}")
                print(f"{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}🆕 Nieuwe releases:{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-18)}║{Colors.RESET}")
                for uri in sorted(nieuwe_artist_uris, key=lambda u: artist_releases.get(u, {}).get('name', '')):
                    release_info = artist_releases.get(uri, {})
                    if release_info:
                        release_display = (
                            f"{release_info['name']} - {release_info['artists']} "
                            f"({release_info.get('album', 'Unknown')}) - {release_info.get('release_date', '')}"
                        )
                        if len(release_display) > 60:
                            release_display = release_display[:57] + "..."
                        print(f"{Colors.BRIGHT_GREEN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.BRIGHT_WHITE}{release_display}{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-len(release_display)-8)}║{Colors.RESET}")
                print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╚{'═'*68}╝{Colors.RESET}\n")

                # Voeg toe aan lijst van nieuwe nummers
                nieuwe_nummers_uris.extend(list(nieuwe_artist_uris))

                # Update historische data
                historische_nummers[artist_releases_key] = set(artist_releases.keys())
            else:
                print(f"{Colors.DIM}🤷 Geen nieuwe releases van gevolgde artiesten gevonden.{Colors.RESET}\n")
        else:
            print(f"{Colors.DIM}🤷 Geen nieuwe releases gevonden van gevolgde artiesten.{Colors.RESET}\n")
    except SpotifyException as e:
        print(f"{Colors.BRIGHT_RED}❌ Fout bij ophalen artiest releases: {e}{Colors.RESET}")
        if e.http_status == 403:
            print(f"{Colors.BRIGHT_YELLOW}   Geen rechten om gevolgde artiesten op te halen. Controleer je scope (user-follow-read).{Colors.RESET}")
        return
    except Exception as e:
        print(f"{Colors.BRIGHT_RED}❌ Onverwachte fout bij ophalen artiest releases: {e}{Colors.RESET}")
        return

    # Voeg nieuwe releases toe aan doel-playlist
    add_tracks_to_playlist(sp, nieuwe_nummers_uris, config.MIJN_DOEL_PLAYLIST_ID)

    # Sla de status op voor de volgende keer
    save_historical_data(historische_nummers)
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ Artiest releases synchronisatie voltooid!{Colors.RESET}\n")
