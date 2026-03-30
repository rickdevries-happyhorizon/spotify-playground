import sys
from datetime import datetime

from db_store import (
    load_playlists_config,
    save_playlists_config,
    load_tracking_start_date,
    save_tracking_start_date,
)

import spotify_playlist.config as config
from spotify_playlist.colors import Colors
from spotify_playlist.export_new_tracks_since_date import export_new_tracks_since_date
from spotify_playlist.export_playlist_to_csv import export_playlist_to_csv
from spotify_playlist.get_spotify_client import get_spotify_client
from spotify_playlist.manage_playlists_config import manage_playlists_config
from spotify_playlist.run_export_new_tracks import run_export_new_tracks
from spotify_playlist.show_menu import show_menu
from spotify_playlist.show_top_tracks import show_top_tracks
from spotify_playlist.sync_artist_releases import sync_artist_releases
from spotify_playlist.sync_playlists import sync_playlists


def main():
    """Hoofdfunctie met menu systeem."""
    # Check voor command-line argumenten
    if len(sys.argv) > 1:
        if sys.argv[1] == '--export' or sys.argv[1] == '-e':
            # Voer export direct uit
            run_export_new_tracks()
            return
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("\n🎵 Spotify Playlist Manager")
            print("=" * 60)
            print("\nGebruik:")
            print("  python playlist_sync.py              - Start interactief menu")
            print("  python playlist_sync.py --export    - Exporteer nieuwe tracks direct")
            print("  python playlist_sync.py -e          - Zelfde als --export")
            print("  python playlist_sync.py --help      - Toon deze help")
            print("\nOpties:")
            print("  --export, -e    Voer export nieuwe tracks uit met opgeslagen instellingen")
            print("  --help, -h      Toon deze help tekst")
            print()
            return

    while True:
        choice = show_menu()

        if choice == 0:
            print("\n👋 Tot ziens!")
            break
        elif choice == 1:
            # Synchroniseer alleen playlists
            sp = get_spotify_client()
            sync_playlists(sp)
        elif choice == 2:
            # Haal alleen nieuwe releases op van gevolgde artiesten
            sp = get_spotify_client()
            sync_artist_releases(sp)
        elif choice == 3:
            # Synchroniseer alles (playlists + artiest releases)
            sp = get_spotify_client()
            sync_playlists(sp)
            if config.CHECK_ARTIST_RELEASES:
                sync_artist_releases(sp)
        elif choice == 4:
            # Exporteer playlist naar CSV
            sp = get_spotify_client()

            print("\n📥 Exporteer Playlist naar CSV")
            print("-" * 60)

            while True:
                try:
                    playlist_id = input("\nVoer de playlist ID in (of 'q' om terug te gaan): ").strip()

                    if playlist_id.lower() == 'q':
                        break

                    if not playlist_id:
                        print("❌ Playlist ID mag niet leeg zijn.")
                        continue

                    # Optioneel: vraag om bestandsnaam
                    output_file = input("Bestandsnaam (Enter voor automatisch): ").strip()
                    if not output_file:
                        output_file = None

                    export_playlist_to_csv(sp, playlist_id, output_file)

                    # Vraag of gebruiker nog een playlist wil exporteren
                    again = input("\nNog een playlist exporteren? (j/n): ").strip().lower()
                    if again != 'j':
                        break

                except KeyboardInterrupt:
                    print("\n\nTerug naar hoofdmenu...")
                    break
                except Exception as e:
                    print(f"❌ Fout: {e}")
        elif choice == 5:
            # Toon meest beluisterde tracks
            sp = get_spotify_client()
            show_top_tracks(sp)
        elif choice == 6:
            # Beheer playlist configuratie
            manage_playlists_config()
        elif choice == 7:
            # Exporteer nieuwe tracks sinds datum naar CSV
            sp = get_spotify_client()

            print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}📥  Exporteer Nieuwe Tracks Sinds Datum  📥{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")

            # Laad configuratie
            playlists_config = load_playlists_config()
            tracking_playlists = playlists_config.get('tracking_playlists', [])

            # Vraag welke playlists te gebruiken
            print(f"{Colors.BRIGHT_WHITE}Huidige tracking playlists ({len(tracking_playlists)}):{Colors.RESET}")
            if tracking_playlists:
                for idx, pl_id in enumerate(tracking_playlists, 1):
                    try:
                        playlist_info = sp.playlist(pl_id, fields='name')
                        playlist_name = playlist_info['name']
                        print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                    except Exception:
                        print(f"  {idx}. {Colors.DIM}{pl_id} (niet gevonden){Colors.RESET}")
            else:
                print(f"  {Colors.DIM}(geen playlists geconfigureerd){Colors.RESET}")

            print(f"\n{Colors.BRIGHT_CYAN}Opties:{Colors.RESET}")
            if tracking_playlists:
                print(f"  {Colors.BRIGHT_GREEN}u.{Colors.RESET} Gebruik tracking playlists ({len(tracking_playlists)} playlists)")
            print(f"  {Colors.BRIGHT_BLUE}m.{Colors.RESET} Handmatig playlist ID's invoeren")
            print(f"  {Colors.BRIGHT_MAGENTA}c.{Colors.RESET} Beheer tracking playlists")
            print(f"  {Colors.DIM}q.{Colors.RESET} Terug naar hoofdmenu")

            option = None
            while True:
                try:
                    option = input(f"\n{Colors.BRIGHT_CYAN}Voer je keuze in ({'u/' if tracking_playlists else ''}m/c/q): {Colors.RESET}").strip().lower()

                    if option == 'q':
                        break
                    elif option == 'u' and tracking_playlists:
                        selected_playlists = tracking_playlists
                        break
                    elif option == 'm':
                        # Handmatig playlist ID's invoeren
                        print(f"\n{Colors.BRIGHT_WHITE}Voer playlist ID's in (gescheiden door komma's):{Colors.RESET}")
                        playlist_input = input(f"{Colors.BRIGHT_CYAN}Playlist ID's: {Colors.RESET}").strip()
                        selected_playlists = [pl_id.strip() for pl_id in playlist_input.split(',') if pl_id.strip()]
                        if not selected_playlists:
                            print(f"{Colors.BRIGHT_RED}❌ Geen playlist ID's ingevoerd.{Colors.RESET}")
                            continue

                        # Vraag of gebruiker deze playlists wil opslaan
                        save_option = input(f"{Colors.BRIGHT_CYAN}Wil je deze playlists opslaan voor volgende keer? (j/n): {Colors.RESET}").strip().lower()
                        if save_option == 'j':
                            # Voeg nieuwe playlists toe aan tracking_playlists (zonder duplicaten)
                            playlists_config = load_playlists_config()
                            tracking_playlists = playlists_config.get('tracking_playlists', [])
                            for pl_id in selected_playlists:
                                if pl_id not in tracking_playlists:
                                    tracking_playlists.append(pl_id)
                            playlists_config['tracking_playlists'] = tracking_playlists
                            save_playlists_config(playlists_config)
                            print(f"{Colors.BRIGHT_GREEN}✅ {len(selected_playlists)} playlist(s) opgeslagen!{Colors.RESET}")
                        break
                    elif option == 'c':
                        # Beheer tracking playlists
                        while True:
                            playlists_config = load_playlists_config()
                            tracking_playlists = playlists_config.get('tracking_playlists', [])

                            print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
                            print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}⚙️  Beheer Tracking Playlists  ⚙️{Colors.RESET}")
                            print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")

                            print(f"{Colors.BRIGHT_WHITE}Huidige tracking playlists ({len(tracking_playlists)}):{Colors.RESET}")
                            if tracking_playlists:
                                for idx, pl_id in enumerate(tracking_playlists, 1):
                                    try:
                                        playlist_info = sp.playlist(pl_id, fields='name')
                                        playlist_name = playlist_info['name']
                                        print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                                    except Exception:
                                        print(f"  {idx}. {Colors.DIM}{pl_id} (niet gevonden){Colors.RESET}")
                            else:
                                print(f"  {Colors.DIM}(geen){Colors.RESET}")

                            print(f"\n{Colors.BRIGHT_WHITE}Wat wil je doen?{Colors.RESET}")
                            print(f"  {Colors.BRIGHT_GREEN}1.{Colors.RESET} Voeg playlist toe")
                            print(f"  {Colors.BRIGHT_RED}2.{Colors.RESET} Verwijder playlist")
                            print(f"  {Colors.DIM}0.{Colors.RESET} Terug")

                            try:
                                action = input(f"\n{Colors.BRIGHT_CYAN}Voer je keuze in (0-2): {Colors.RESET}").strip()

                                if action == '0':
                                    break
                                elif action == '1':
                                    # Voeg playlist toe
                                    playlist_id = input(f"{Colors.BRIGHT_GREEN}Voer playlist ID in om toe te voegen: {Colors.RESET}").strip()
                                    if playlist_id and playlist_id not in tracking_playlists:
                                        try:
                                            playlist_info = sp.playlist(playlist_id, fields='name')
                                            playlist_name = playlist_info['name']
                                            print(f"{Colors.BRIGHT_CYAN}   Gevonden: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")
                                            confirm = input(f"{Colors.BRIGHT_GREEN}Toevoegen? (j/n): {Colors.RESET}").strip().lower()
                                            if confirm == 'j':
                                                tracking_playlists.append(playlist_id)
                                                playlists_config['tracking_playlists'] = tracking_playlists
                                                save_playlists_config(playlists_config)
                                                print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{playlist_name}' toegevoegd!{Colors.RESET}\n")
                                            else:
                                                print(f"{Colors.DIM}Geannuleerd.{Colors.RESET}\n")
                                        except Exception as e:
                                            print(f"{Colors.BRIGHT_YELLOW}⚠️  Kon playlist niet verifiëren: {e}{Colors.RESET}")
                                            confirm = input(f"{Colors.BRIGHT_YELLOW}Toch toevoegen? (j/n): {Colors.RESET}").strip().lower()
                                            if confirm == 'j':
                                                tracking_playlists.append(playlist_id)
                                                playlists_config['tracking_playlists'] = tracking_playlists
                                                save_playlists_config(playlists_config)
                                                print(f"{Colors.BRIGHT_GREEN}✅ Playlist toegevoegd!{Colors.RESET}\n")
                                    elif playlist_id in tracking_playlists:
                                        print(f"{Colors.BRIGHT_YELLOW}⚠️  Deze playlist staat al in de lijst.{Colors.RESET}\n")
                                    else:
                                        print(f"{Colors.BRIGHT_RED}❌ Ongeldige playlist ID.{Colors.RESET}\n")

                                elif action == '2':
                                    # Verwijder playlist
                                    if not tracking_playlists:
                                        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen playlists om te verwijderen.{Colors.RESET}\n")
                                        continue

                                    print(f"{Colors.BRIGHT_RED}Welke playlist wil je verwijderen?{Colors.RESET}")
                                    playlist_names = {}
                                    for idx, pl_id in enumerate(tracking_playlists, 1):
                                        try:
                                            playlist_info = sp.playlist(pl_id, fields='name')
                                            playlist_name = playlist_info['name']
                                            playlist_names[pl_id] = playlist_name
                                            print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                                        except Exception:
                                            print(f"  {idx}. {Colors.DIM}{pl_id} (niet gevonden){Colors.RESET}")

                                    try:
                                        idx = int(input(f"{Colors.BRIGHT_RED}Voer nummer in (1-{len(tracking_playlists)}): {Colors.RESET}").strip())
                                        if 1 <= idx <= len(tracking_playlists):
                                            removed_id = tracking_playlists.pop(idx - 1)
                                            removed_name = playlist_names.get(removed_id, removed_id)
                                            playlists_config['tracking_playlists'] = tracking_playlists
                                            save_playlists_config(playlists_config)
                                            if removed_name != removed_id:
                                                print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_name}' verwijderd!{Colors.RESET}\n")
                                            else:
                                                print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_id}' verwijderd!{Colors.RESET}\n")
                                        else:
                                            print(f"{Colors.BRIGHT_RED}❌ Ongeldig nummer.{Colors.RESET}\n")
                                    except ValueError:
                                        print(f"{Colors.BRIGHT_RED}❌ Voer een geldig nummer in.{Colors.RESET}\n")

                                else:
                                    print(f"{Colors.BRIGHT_RED}❌ Ongeldige keuze.{Colors.RESET}\n")

                            except KeyboardInterrupt:
                                print(f"\n\n{Colors.DIM}Terug...{Colors.RESET}")
                                break
                            except Exception as e:
                                print(f"{Colors.BRIGHT_RED}❌ Fout: {e}{Colors.RESET}\n")

                        # Na beheer, vraag of gebruiker wil doorgaan
                        continue_option = input(f"\n{Colors.BRIGHT_CYAN}Wil je doorgaan met exporteren? (j/n): {Colors.RESET}").strip().lower()
                        if continue_option != 'j':
                            break
                        # Herlaad configuratie na beheer
                        playlists_config = load_playlists_config()
                        tracking_playlists = playlists_config.get('tracking_playlists', [])
                        if not tracking_playlists:
                            print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen tracking playlists geconfigureerd.{Colors.RESET}")
                            break
                        selected_playlists = tracking_playlists
                        break
                    else:
                        print(f"{Colors.BRIGHT_RED}❌ Ongeldige keuze.{Colors.RESET}")

                except KeyboardInterrupt:
                    print(f"\n\n{Colors.DIM}Terug naar hoofdmenu...{Colors.RESET}")
                    break

            if option == 'q':
                continue

            if 'selected_playlists' not in locals():
                continue

            # Toon huidige start datum en vraag om datum instellingen
            saved_start_date = load_tracking_start_date()
            today = datetime.now()

            print(f"\n{Colors.BRIGHT_WHITE}Datum instellingen:{Colors.RESET}")
            if saved_start_date:
                print(f"{Colors.DIM}   Huidige start datum: {saved_start_date.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
                print(f"{Colors.DIM}   Vandaag: {today.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
                print(f"{Colors.DIM}   Er worden tracks gecontroleerd tussen deze twee datums.{Colors.RESET}")
            else:
                print(f"{Colors.DIM}   Geen start datum ingesteld. Standaard: 7 dagen terug.{Colors.RESET}")

            print(f"\n{Colors.BRIGHT_CYAN}Opties:{Colors.RESET}")
            print(f"  {Colors.BRIGHT_GREEN}1.{Colors.RESET} Gebruik opgeslagen start datum ({saved_start_date.strftime('%Y-%m-%d') if saved_start_date else '7 dagen terug'})")
            print(f"  {Colors.BRIGHT_BLUE}2.{Colors.RESET} Stel nieuwe start datum in")

            since_date = None
            date_option = None
            while True:
                try:
                    date_option = input(f"\n{Colors.BRIGHT_CYAN}Voer je keuze in (1/2): {Colors.RESET}").strip()

                    if date_option == '1':
                        # Gebruik opgeslagen start datum
                        since_date = None  # Wordt in functie geladen
                        break
                    elif date_option == '2':
                        # Vraag om nieuwe start datum
                        date_str = input(f"{Colors.BRIGHT_CYAN}Voer nieuwe start datum in (YYYY-MM-DD): {Colors.RESET}").strip()
                        try:
                            since_date = datetime.strptime(date_str, '%Y-%m-%d')
                            # Sla de nieuwe start datum op
                            save_tracking_start_date(since_date)
                            print(f"{Colors.BRIGHT_GREEN}✅ Start datum ingesteld op: {since_date.strftime('%Y-%m-%d')}{Colors.RESET}")
                            break
                        except ValueError:
                            print(f"{Colors.BRIGHT_RED}❌ Ongeldige datum formaat. Gebruik YYYY-MM-DD{Colors.RESET}")
                            continue
                    else:
                        print(f"{Colors.BRIGHT_RED}❌ Ongeldige keuze. Voer 1 of 2 in.{Colors.RESET}")

                except KeyboardInterrupt:
                    print(f"\n\n{Colors.DIM}Geannuleerd...{Colors.RESET}")
                    break

            if date_option is None or (date_option == '2' and since_date is None):
                continue

            # Vraag om bestandsnaam (optioneel)
            output_file = input(f"\n{Colors.BRIGHT_CYAN}Bestandsnaam (Enter voor automatisch): {Colors.RESET}").strip()
            if not output_file:
                output_file = None

            # Exporteer nieuwe tracks
            export_new_tracks_since_date(sp, selected_playlists, since_date, output_file)
