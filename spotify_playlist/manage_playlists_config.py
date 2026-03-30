from db_store import load_playlists_config, save_playlists_config

from spotify_playlist.colors import Colors
from spotify_playlist.get_playlist_name import get_playlist_name
from spotify_playlist.get_spotify_client import get_spotify_client
from spotify_playlist.parse_spotify_playlist_id import parse_spotify_playlist_id


def manage_playlists_config():
    """Beheert de playlist configuratie via een interactief menu."""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}⚙️  Playlist Configuratie Beheer  ⚙️{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")
    print(
        f"{Colors.DIM}Tip: bij playlist-ID kun je ook een Spotify-link plakken (open.spotify.com of spotify:playlist:…).{Colors.RESET}\n"
    )

    # Authenticeer voor het ophalen van playlist namen
    sp = None
    try:
        sp = get_spotify_client()
    except Exception:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Kan niet authenticeren. Playlist namen worden niet getoond.{Colors.RESET}\n")

    while True:
        # Laad huidige configuratie
        config = load_playlists_config()
        source_playlists = config.get('source_playlists', [])
        destination_playlist = config.get('destination_playlist', '')

        print(f"{Colors.BRIGHT_WHITE}Huidige configuratie:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_CYAN}Bron-playlists ({len(source_playlists)}):{Colors.RESET}")
        if source_playlists:
            for idx, pl_id in enumerate(source_playlists, 1):
                if sp:
                    playlist_name = get_playlist_name(sp, pl_id)
                    if playlist_name:
                        print(f"    {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                    else:
                        print(f"    {idx}. {Colors.DIM}{pl_id} (niet gevonden){Colors.RESET}")
                else:
                    print(f"    {idx}. {pl_id}")
        else:
            print(f"    {Colors.DIM}(geen){Colors.RESET}")

        print(f"\n  {Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET}")
        if destination_playlist:
            if sp:
                playlist_name = get_playlist_name(sp, destination_playlist)
                if playlist_name:
                    print(f"    {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({destination_playlist}){Colors.RESET}")
                else:
                    print(f"    {Colors.DIM}{destination_playlist} (niet gevonden){Colors.RESET}")
            else:
                print(f"    {destination_playlist}")
        else:
            print(f"    {Colors.DIM}(niet ingesteld){Colors.RESET}")

        print(f"\n{Colors.BRIGHT_WHITE}Wat wil je doen?{Colors.RESET}")
        print(f"  {Colors.BRIGHT_GREEN}1.{Colors.RESET} Voeg bron-playlist toe")
        print(f"  {Colors.BRIGHT_RED}2.{Colors.RESET} Verwijder bron-playlist")
        print(f"  {Colors.BRIGHT_BLUE}3.{Colors.RESET} Stel doel-playlist in")
        print(f"  {Colors.BRIGHT_YELLOW}4.{Colors.RESET} Toon alle playlists")
        print(f"  {Colors.DIM}0.{Colors.RESET} Terug naar hoofdmenu")
        print(f"\n{Colors.DIM}{'-'*70}{Colors.RESET}")

        try:
            action = input(f"{Colors.BRIGHT_CYAN}Voer je keuze in (0-4): {Colors.RESET}").strip()

            if action == '0':
                break
            elif action == '1':
                # Voeg bron-playlist toe
                raw = input(f"{Colors.BRIGHT_GREEN}Voer playlist ID of Spotify-link in om toe te voegen: {Colors.RESET}").strip()
                playlist_id = parse_spotify_playlist_id(raw)
                if playlist_id and playlist_id not in source_playlists:
                    # Probeer playlist naam op te halen
                    playlist_name = None
                    if sp:
                        print(f"{Colors.DIM}⏳ Playlist informatie ophalen...{Colors.RESET}")
                        playlist_name = get_playlist_name(sp, playlist_id)

                    if playlist_name:
                        print(f"{Colors.BRIGHT_CYAN}   Gevonden: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")
                        confirm = input(f"{Colors.BRIGHT_GREEN}Toevoegen? (j/n): {Colors.RESET}").strip().lower()
                        if confirm != 'j':
                            print(f"{Colors.DIM}Geannuleerd.{Colors.RESET}\n")
                            continue

                    source_playlists.append(playlist_id)
                    config['source_playlists'] = source_playlists
                    save_playlists_config(config)

                    if playlist_name:
                        print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{playlist_name}' toegevoegd!{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_GREEN}✅ Playlist toegevoegd!{Colors.RESET}\n")
                elif playlist_id in source_playlists:
                    playlist_name = None
                    if sp:
                        playlist_name = get_playlist_name(sp, playlist_id)
                    if playlist_name:
                        print(f"{Colors.BRIGHT_YELLOW}⚠️  Deze playlist ({playlist_name}) staat al in de lijst.{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_YELLOW}⚠️  Deze playlist staat al in de lijst.{Colors.RESET}\n")
                else:
                    print(f"{Colors.BRIGHT_RED}❌ Ongeldige playlist ID.{Colors.RESET}\n")

            elif action == '2':
                # Verwijder bron-playlist
                if not source_playlists:
                    print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen playlists om te verwijderen.{Colors.RESET}\n")
                    continue

                print(f"{Colors.BRIGHT_RED}Welke playlist wil je verwijderen?{Colors.RESET}")
                playlist_names = {}
                for idx, pl_id in enumerate(source_playlists, 1):
                    if sp:
                        playlist_name = get_playlist_name(sp, pl_id)
                        if playlist_name:
                            playlist_names[pl_id] = playlist_name
                            print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                        else:
                            print(f"  {idx}. {Colors.DIM}{pl_id} (niet gevonden){Colors.RESET}")
                    else:
                        print(f"  {idx}. {pl_id}")

                try:
                    idx = int(input(f"{Colors.BRIGHT_RED}Voer nummer in (1-{len(source_playlists)}): {Colors.RESET}").strip())
                    if 1 <= idx <= len(source_playlists):
                        removed_id = source_playlists.pop(idx - 1)
                        removed_name = playlist_names.get(removed_id, removed_id)
                        config['source_playlists'] = source_playlists
                        save_playlists_config(config)
                        if removed_name != removed_id:
                            print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_name}' verwijderd!{Colors.RESET}\n")
                        else:
                            print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_id}' verwijderd!{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_RED}❌ Ongeldig nummer.{Colors.RESET}\n")
                except ValueError:
                    print(f"{Colors.BRIGHT_RED}❌ Voer een geldig nummer in.{Colors.RESET}\n")

            elif action == '3':
                # Stel doel-playlist in
                raw = input(f"{Colors.BRIGHT_BLUE}Voer doel-playlist ID of Spotify-link in: {Colors.RESET}").strip()
                playlist_id = parse_spotify_playlist_id(raw)
                if playlist_id:
                    # Probeer playlist naam op te halen
                    playlist_name = None
                    if sp:
                        print(f"{Colors.DIM}⏳ Playlist informatie ophalen...{Colors.RESET}")
                        playlist_name = get_playlist_name(sp, playlist_id)
                        if playlist_name:
                            print(f"{Colors.BRIGHT_CYAN}   Gevonden: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")

                    config['destination_playlist'] = playlist_id
                    save_playlists_config(config)

                    if playlist_name:
                        print(f"{Colors.BRIGHT_GREEN}✅ Doel-playlist ingesteld: '{playlist_name}'!{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_GREEN}✅ Doel-playlist ingesteld!{Colors.RESET}\n")
                else:
                    print(f"{Colors.BRIGHT_RED}❌ Ongeldige playlist ID.{Colors.RESET}\n")

            elif action == '4':
                # Toon alle playlists (met namen als mogelijk)
                print(f"\n{Colors.BRIGHT_CYAN}Alle geconfigureerde playlists:{Colors.RESET}\n")

                if destination_playlist:
                    if sp:
                        dest_name = get_playlist_name(sp, destination_playlist)
                        if dest_name:
                            print(f"{Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET} {Colors.BRIGHT_WHITE}{dest_name}{Colors.RESET} {Colors.DIM}({destination_playlist}){Colors.RESET}")
                        else:
                            print(f"{Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET} {Colors.DIM}{destination_playlist} (niet gevonden){Colors.RESET}")
                    else:
                        print(f"{Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET} {destination_playlist}")
                else:
                    print(f"{Colors.BRIGHT_GREEN}Doel-playlist:{Colors.RESET} {Colors.DIM}(niet ingesteld){Colors.RESET}")

                print(f"\n{Colors.BRIGHT_CYAN}Bron-playlists ({len(source_playlists)}):{Colors.RESET}")
                if source_playlists:
                    for idx, pl_id in enumerate(source_playlists, 1):
                        if sp:
                            playlist_name = get_playlist_name(sp, pl_id)
                            if playlist_name:
                                print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                            else:
                                print(f"  {idx}. {Colors.DIM}{pl_id} (niet gevonden){Colors.RESET}")
                        else:
                            print(f"  {idx}. {pl_id}")
                else:
                    print(f"  {Colors.DIM}(geen){Colors.RESET}")

                input(f"\n{Colors.DIM}Druk Enter om door te gaan...{Colors.RESET}")
                print()

            else:
                print(f"{Colors.BRIGHT_RED}❌ Ongeldige keuze.{Colors.RESET}\n")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.DIM}Terug naar hoofdmenu...{Colors.RESET}")
            break
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Fout: {e}{Colors.RESET}\n")
