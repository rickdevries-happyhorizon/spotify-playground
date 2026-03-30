import spotify_playlist.config as config
from db_store import load_historical_data, load_playlists_config, save_historical_data

from spotify_playlist.add_tracks_to_playlist import add_tracks_to_playlist
from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_recent_playlist_tracks import get_recent_playlist_tracks
from spotify_playlist.get_track_info import get_track_info
from spotify_playlist.loading_progress import loading_bar


def sync_playlists(sp):
    """Controleert bron-playlists op nieuwe tracks en voegt deze toe aan de doel-playlist."""
    # Laad configuratie opnieuw (kan zijn aangepast)
    playlists_config = load_playlists_config()
    config.MIJN_DOEL_PLAYLIST_ID = playlists_config.get('destination_playlist', '')
    config.BRON_PLAYLISTS = playlists_config.get('source_playlists', [])

    # Valideer configuratie
    if not config.BRON_PLAYLISTS:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen bron-playlists geconfigureerd in de database.{Colors.RESET}")
        print(f"{Colors.DIM}   Voeg bron-playlists toe via het menu (playlist configuratie) of vul de tabel source_playlists.{Colors.RESET}")
        return

    if not config.MIJN_DOEL_PLAYLIST_ID:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen doel-playlist geconfigureerd in de database.{Colors.RESET}")
        print(f"{Colors.DIM}   Stel een doel-playlist in via het menu of vul destination_config.{Colors.RESET}")
        return

    historische_nummers = load_historical_data(config.BRON_PLAYLISTS)
    nieuwe_nummers_uris = []

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🎵  Start Playlist Synchronisatie  🎵{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")

    # Doorloop elke bron-afspeellijst
    for idx, pl_id in enumerate(config.BRON_PLAYLISTS, 1):
        try:
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╔{'═'*68}╗{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}║{Colors.RESET}  {Colors.BRIGHT_WHITE}📋 Playlist {idx}/{len(config.BRON_PLAYLISTS)}{Colors.RESET}  {Colors.DIM}ID: {pl_id[:20]}...{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-45)}║{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╠{'═'*68}╣{Colors.RESET}")

            # Haal playlist naam op voor betere feedback
            try:
                playlist_info = sp.playlist(pl_id, fields='name')
                playlist_name = playlist_info['name']
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_GREEN}🎼 {playlist_name}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(playlist_name)-6)}║{Colors.RESET}")
            except Exception:
                playlist_name = "Onbekend"
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.DIM}Playlist naam niet beschikbaar{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-30)}║{Colors.RESET}")

            print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")

            # Haal alleen recent toegevoegde tracks op (laatste 7 dagen) voor snelheid
            print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_YELLOW}⏳{Colors.RESET} {Colors.DIM}Controleer tracks toegevoegd in de laatste 7 dagen...{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-50)}║{Colors.RESET}")
            with loading_bar("Recente tracks ophalen..."):
                recent_tracks = get_recent_playlist_tracks(sp, pl_id, days_back=7, return_track_info=True)
            recent_uris = set(recent_tracks.keys())
            print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_GREEN}✅{Colors.RESET} {Colors.BRIGHT_WHITE}Gevonden {Colors.BOLD}{len(recent_uris)}{Colors.RESET}{Colors.BRIGHT_WHITE} tracks toegevoegd in de laatste 7 dagen{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-60)}║{Colors.RESET}")

            # Toon recent toegevoegde tracks
            if recent_tracks:
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}📀 Recent toegevoegde tracks:{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-25)}║{Colors.RESET}")
                for uri, track_info in sorted(recent_tracks.items(), key=lambda x: x[1]['name']):
                    track_display = f"{track_info['name']} - {track_info['artists']}"
                    # Truncate if too long
                    if len(track_display) > 60:
                        track_display = track_display[:57] + "..."
                    print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.CYAN}•{Colors.RESET} {Colors.WHITE}{track_display}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(track_display)-8)}║{Colors.RESET}")

            # Bepaal welke nummers nieuw zijn (vergelijk met historische data)
            laatst_bekende_uris = historische_nummers.get(pl_id, set())
            nieuwe_uris = recent_uris - laatst_bekende_uris

            # Update historische data: voeg nieuwe tracks toe aan bestaande set
            # Dit behoudt alle historische tracks, niet alleen de laatste 7 dagen
            if nieuwe_uris:
                historische_nummers[pl_id] = laatst_bekende_uris.union(recent_uris)
            else:
                # Als er geen nieuwe tracks zijn, update alleen als we nog geen historische data hebben
                if pl_id not in historische_nummers:
                    historische_nummers[pl_id] = recent_uris

            if nieuwe_uris:
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_GREEN}🎉 {len(nieuwe_uris)} nieuwe nummers gevonden!{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-30)}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}🆕 Nieuwe tracks:{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-18)}║{Colors.RESET}")
                for uri in sorted(nieuwe_uris, key=lambda u: recent_tracks.get(u, {}).get('name', '')):
                    track_info = recent_tracks.get(uri, {})
                    if track_info:
                        track_display = f"{track_info['name']} - {track_info['artists']}"
                        if len(track_display) > 60:
                            track_display = track_display[:57] + "..."
                        print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.BRIGHT_WHITE}{track_display}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(track_display)-8)}║{Colors.RESET}")
                    else:
                        # Fallback als track info niet beschikbaar is
                        fallback_info = get_track_info(sp, uri)
                        if len(fallback_info) > 60:
                            fallback_info = fallback_info[:57] + "..."
                        print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}      {Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.WHITE}{fallback_info}{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(fallback_info)-8)}║{Colors.RESET}")
                nieuwe_nummers_uris.extend(list(nieuwe_uris))
            else:
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
                print(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.DIM}🤷 Geen nieuwe toevoegingen gevonden.{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-35)}║{Colors.RESET}")

            print(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╚{'═'*68}╝{Colors.RESET}\n")

        except SpotifyException as e:
            print(f"{Colors.BRIGHT_RED}❌ Spotify API fout bij verwerken afspeellijst {pl_id}: {e}{Colors.RESET}")
            if e.http_status == 404:
                print(f"{Colors.BRIGHT_YELLOW}   Playlist niet gevonden. Controleer of de ID correct is.{Colors.RESET}")
            elif e.http_status == 403:
                print(f"{Colors.BRIGHT_YELLOW}   Geen toegang tot deze playlist. Controleer je rechten.{Colors.RESET}")
            continue
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Fout bij verwerken afspeellijst {pl_id}: {e}{Colors.RESET}")
            continue

    # Voeg nieuwe tracks toe aan doel-playlist
    add_tracks_to_playlist(sp, nieuwe_nummers_uris, config.MIJN_DOEL_PLAYLIST_ID)

    # Sla de status op voor de volgende keer
    save_historical_data(historische_nummers)
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ Playlist synchronisatie voltooid!{Colors.RESET}\n")
