import traceback

from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_all_playlist_tracks import get_all_playlist_tracks


def add_tracks_to_playlist(sp, nieuwe_nummers_uris, doel_playlist_id):
    """Voegt tracks toe aan de doel-playlist na duplicaten controle."""
    if not nieuwe_nummers_uris:
        return

    print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}🔍  Duplicaten Controleren  🔍{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}\n")

    # Verwijder eerst duplicaten binnen de nieuwe tracks lijst zelf
    # (bijv. als dezelfde track in meerdere bron-playlists voorkomt)
    original_count = len(nieuwe_nummers_uris)
    nieuwe_nummers_uris = list(dict.fromkeys(nieuwe_nummers_uris))  # Behoudt volgorde, verwijdert duplicaten
    if len(nieuwe_nummers_uris) < original_count:
        internal_duplicates = original_count - len(nieuwe_nummers_uris)
        print(f"{Colors.BRIGHT_YELLOW}⚠️  {internal_duplicates} duplicaten verwijderd uit nieuwe tracks lijst.{Colors.RESET}")

    print(f"{Colors.DIM}⏳ Controleer {len(nieuwe_nummers_uris)} unieke nieuwe tracks tegen doel-playlist...{Colors.RESET}")
    try:
        doel_playlist_tracks = get_all_playlist_tracks(sp, doel_playlist_id)
        print(f"{Colors.BRIGHT_CYAN}   Doel-playlist bevat momenteel {Colors.BOLD}{len(doel_playlist_tracks)}{Colors.RESET}{Colors.BRIGHT_CYAN} tracks{Colors.RESET}")

        unieke_nieuwe_uris = [uri for uri in nieuwe_nummers_uris if uri not in doel_playlist_tracks]

        if len(unieke_nieuwe_uris) < len(nieuwe_nummers_uris):
            duplicates = len(nieuwe_nummers_uris) - len(unieke_nieuwe_uris)
            print(f"{Colors.BRIGHT_YELLOW}⚠️  {duplicates} nummers zitten al in de doel-playlist en worden overgeslagen.{Colors.RESET}")
        else:
            print(f"{Colors.BRIGHT_GREEN}✅ Alle {len(nieuwe_nummers_uris)} tracks zijn nieuw voor de doel-playlist{Colors.RESET}")

        nieuwe_nummers_uris = unieke_nieuwe_uris
    except Exception as e:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Kon duplicaten niet controleren: {e}{Colors.RESET}")
        print(f"{Colors.DIM}   Traceback: {type(e).__name__}: {str(e)}{Colors.RESET}")
        print(f"{Colors.DIM}   Voegt alle nummers toe (mogelijk duplicaten)...{Colors.RESET}")

    # Nummers toevoegen aan de doel-afspeellijst
    if nieuwe_nummers_uris:
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}➕  Nummers Toevoegen  ➕{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}\n")
        try:
            doel_playlist_info = sp.playlist(doel_playlist_id, fields='name')
            playlist_name = doel_playlist_info['name']
            print(f"{Colors.BRIGHT_CYAN}📝 Voegt {Colors.BOLD}{Colors.BRIGHT_WHITE}{len(nieuwe_nummers_uris)}{Colors.RESET}{Colors.BRIGHT_CYAN} unieke nummers toe aan:{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}   🎵 {playlist_name}{Colors.RESET}\n")
        except Exception:
            print(f"{Colors.BRIGHT_CYAN}📝 Voegt {Colors.BOLD}{Colors.BRIGHT_WHITE}{len(nieuwe_nummers_uris)}{Colors.RESET}{Colors.BRIGHT_CYAN} unieke nummers toe aan playlist ID: {doel_playlist_id}{Colors.RESET}\n")

        # De API kan maximaal 100 nummers per keer toevoegen
        try:
            total_added = 0
            for i in range(0, len(nieuwe_nummers_uris), 100):
                batch = nieuwe_nummers_uris[i:i + 100]
                print(f"{Colors.DIM}  ⏳ Voegt batch toe ({i+1}-{min(i+100, len(nieuwe_nummers_uris))} van {len(nieuwe_nummers_uris)})...{Colors.RESET}")
                sp.playlist_add_items(doel_playlist_id, batch)
                total_added += len(batch)
                print(f"{Colors.BRIGHT_GREEN}  ✅ Batch van {Colors.BOLD}{len(batch)}{Colors.RESET}{Colors.BRIGHT_GREEN} nummers toegevoegd.{Colors.RESET}")
            print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}╔{'═'*68}╗{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_WHITE}🎉 Totaal {total_added} nummers succesvol toegevoegd! 🎉{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-40)}║{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╚{'═'*68}╝{Colors.RESET}\n")
        except SpotifyException as e:
            print(f"{Colors.BRIGHT_RED}❌ Fout bij toevoegen nummers: {e}{Colors.RESET}")
            print(f"{Colors.DIM}   HTTP Status: {e.http_status}{Colors.RESET}")
            print(f"{Colors.DIM}   Error Code: {e.code}{Colors.RESET}")
            if e.http_status == 404:
                print(f"{Colors.BRIGHT_YELLOW}   Doel-playlist niet gevonden. Controleer de playlist ID.{Colors.RESET}")
            elif e.http_status == 403:
                print(f"{Colors.BRIGHT_YELLOW}   Geen rechten om nummers toe te voegen aan deze playlist.{Colors.RESET}")
                print(f"{Colors.DIM}   Controleer of je de juiste scope hebt (playlist-modify-public en/of playlist-modify-private){Colors.RESET}")
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Onverwachte fout bij toevoegen: {e}{Colors.RESET}")
            print(f"{Colors.DIM}   Traceback: {traceback.format_exc()}{Colors.RESET}")
    else:
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}✅  Geen Nieuwe Tracks  ✅{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")
        print(f"{Colors.DIM}Geen nieuwe nummers gevonden om toe te voegen aan de doel-afspeellijst.{Colors.RESET}\n")
