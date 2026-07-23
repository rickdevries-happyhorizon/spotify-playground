from db_store import load_playlists_config, save_playlists_config, upsert_playlist

from spotify_playlist.action_sound import play_action_done, play_selection
from spotify_playlist.colors import Colors
from spotify_playlist.get_playlist_name import get_playlist_name
from spotify_playlist.get_spotify_client import get_spotify_client
from spotify_playlist.loading_progress import loading_bar
from spotify_playlist.parse_spotify_playlist_id import parse_spotify_playlist_id


def manage_playlists_config():
    """Manages playlist configuration via an interactive menu."""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}⚙️  Playlist Configuration  ⚙️{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")
    print(
        f"{Colors.DIM}Tip: for playlist ID you can also paste a Spotify link (open.spotify.com or spotify:playlist:…).{Colors.RESET}\n"
    )

    # Authenticate before fetching playlist names
    sp = None
    try:
        sp = get_spotify_client()
    except Exception:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Cannot authenticate. Playlist names will not be shown.{Colors.RESET}\n")

    while True:
        # Load current configuration
        config = load_playlists_config()
        source_playlists = config.get('source_playlists', [])
        destination_playlist = config.get('destination_playlist', '')

        print(f"{Colors.BRIGHT_WHITE}Current configuration:{Colors.RESET}")
        print(f"  {Colors.BRIGHT_CYAN}Source playlists ({len(source_playlists)}):{Colors.RESET}")
        if source_playlists:
            for idx, pl_id in enumerate(source_playlists, 1):
                if sp:
                    playlist_name = get_playlist_name(sp, pl_id)
                    if playlist_name:
                        print(f"    {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                    else:
                        print(f"    {idx}. {Colors.DIM}{pl_id} (not found){Colors.RESET}")
                else:
                    print(f"    {idx}. {pl_id}")
        else:
            print(f"    {Colors.DIM}(none){Colors.RESET}")

        print(f"\n  {Colors.BRIGHT_GREEN}Destination playlist:{Colors.RESET}")
        if destination_playlist:
            if sp:
                playlist_name = get_playlist_name(sp, destination_playlist)
                if playlist_name:
                    print(f"    {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({destination_playlist}){Colors.RESET}")
                else:
                    print(f"    {Colors.DIM}{destination_playlist} (not found){Colors.RESET}")
            else:
                print(f"    {destination_playlist}")
        else:
            print(f"    {Colors.DIM}(not set){Colors.RESET}")

        print(f"\n{Colors.BRIGHT_WHITE}What would you like to do?{Colors.RESET}")
        print(f"  {Colors.BRIGHT_GREEN}1.{Colors.RESET} Add source playlist")
        print(f"  {Colors.BRIGHT_RED}2.{Colors.RESET} Remove source playlist")
        print(f"  {Colors.BRIGHT_BLUE}3.{Colors.RESET} Set destination playlist")
        print(f"  {Colors.BRIGHT_YELLOW}4.{Colors.RESET} Show all playlists")
        print(f"  {Colors.DIM}0.{Colors.RESET} Back to main menu")
        print(f"\n{Colors.DIM}{'-'*70}{Colors.RESET}")

        try:
            action = input(f"{Colors.BRIGHT_CYAN}Enter your choice (0-4): {Colors.RESET}").strip()

            if action == '0':
                break
            if action in ('1', '2', '3', '4'):
                play_selection()
            if action == '1':
                # Add source playlist
                raw = input(f"{Colors.BRIGHT_GREEN}Enter playlist ID or Spotify link to add: {Colors.RESET}").strip()
                playlist_id = parse_spotify_playlist_id(raw)
                if playlist_id and playlist_id not in source_playlists:
                    # Try to fetch playlist name
                    playlist_name = None
                    if sp:
                        with loading_bar("Fetching playlist info..."):
                            playlist_name = get_playlist_name(sp, playlist_id)

                    if playlist_name:
                        print(f"{Colors.BRIGHT_CYAN}   Found: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")
                        confirm = input(f"{Colors.BRIGHT_GREEN}Add? (y/n): {Colors.RESET}").strip().lower()
                        if confirm != 'y':
                            print(f"{Colors.DIM}Cancelled.{Colors.RESET}\n")
                            continue

                    source_playlists.append(playlist_id)
                    config['source_playlists'] = source_playlists
                    if playlist_name:
                        upsert_playlist(playlist_name, spotify_id=playlist_id)
                    save_playlists_config(config)

                    if playlist_name:
                        print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{playlist_name}' added!{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_GREEN}✅ Playlist added!{Colors.RESET}\n")
                    play_action_done()
                elif playlist_id in source_playlists:
                    playlist_name = None
                    if sp:
                        playlist_name = get_playlist_name(sp, playlist_id)
                    if playlist_name:
                        print(f"{Colors.BRIGHT_YELLOW}⚠️  This playlist ({playlist_name}) is already in the list.{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_YELLOW}⚠️  This playlist is already in the list.{Colors.RESET}\n")
                else:
                    print(f"{Colors.BRIGHT_RED}❌ Invalid playlist ID.{Colors.RESET}\n")

            elif action == '2':
                # Remove source playlist
                if not source_playlists:
                    print(f"{Colors.BRIGHT_YELLOW}⚠️  No playlists to remove.{Colors.RESET}\n")
                    continue

                print(f"{Colors.BRIGHT_RED}Which playlist would you like to remove?{Colors.RESET}")
                playlist_names = {}
                for idx, pl_id in enumerate(source_playlists, 1):
                    if sp:
                        playlist_name = get_playlist_name(sp, pl_id)
                        if playlist_name:
                            playlist_names[pl_id] = playlist_name
                            print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                        else:
                            print(f"  {idx}. {Colors.DIM}{pl_id} (not found){Colors.RESET}")
                    else:
                        print(f"  {idx}. {pl_id}")

                try:
                    idx = int(input(f"{Colors.BRIGHT_RED}Enter number (1-{len(source_playlists)}): {Colors.RESET}").strip())
                    if 1 <= idx <= len(source_playlists):
                        removed_id = source_playlists.pop(idx - 1)
                        removed_name = playlist_names.get(removed_id, removed_id)
                        config['source_playlists'] = source_playlists
                        save_playlists_config(config)
                        if removed_name != removed_id:
                            print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_name}' removed!{Colors.RESET}\n")
                        else:
                            print(f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_id}' removed!{Colors.RESET}\n")
                        play_action_done()
                    else:
                        print(f"{Colors.BRIGHT_RED}❌ Invalid number.{Colors.RESET}\n")
                except ValueError:
                    print(f"{Colors.BRIGHT_RED}❌ Enter a valid number.{Colors.RESET}\n")

            elif action == '3':
                # Set destination playlist
                raw = input(f"{Colors.BRIGHT_BLUE}Enter destination playlist ID or Spotify link: {Colors.RESET}").strip()
                playlist_id = parse_spotify_playlist_id(raw)
                if playlist_id:
                    # Try to fetch playlist name
                    playlist_name = None
                    if sp:
                        with loading_bar("Fetching playlist info..."):
                            playlist_name = get_playlist_name(sp, playlist_id)
                        if playlist_name:
                            print(f"{Colors.BRIGHT_CYAN}   Found: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")

                    config['destination_playlist'] = playlist_id
                    if playlist_name:
                        upsert_playlist(playlist_name, spotify_id=playlist_id)
                    save_playlists_config(config)

                    if playlist_name:
                        print(f"{Colors.BRIGHT_GREEN}✅ Destination playlist set: '{playlist_name}'!{Colors.RESET}\n")
                    else:
                        print(f"{Colors.BRIGHT_GREEN}✅ Destination playlist set!{Colors.RESET}\n")
                    play_action_done()
                else:
                    print(f"{Colors.BRIGHT_RED}❌ Invalid playlist ID.{Colors.RESET}\n")

            elif action == '4':
                # Show all playlists (with names when possible)
                print(f"\n{Colors.BRIGHT_CYAN}All configured playlists:{Colors.RESET}\n")

                if destination_playlist:
                    if sp:
                        dest_name = get_playlist_name(sp, destination_playlist)
                        if dest_name:
                            print(f"{Colors.BRIGHT_GREEN}Destination playlist:{Colors.RESET} {Colors.BRIGHT_WHITE}{dest_name}{Colors.RESET} {Colors.DIM}({destination_playlist}){Colors.RESET}")
                        else:
                            print(f"{Colors.BRIGHT_GREEN}Destination playlist:{Colors.RESET} {Colors.DIM}{destination_playlist} (not found){Colors.RESET}")
                    else:
                        print(f"{Colors.BRIGHT_GREEN}Destination playlist:{Colors.RESET} {destination_playlist}")
                else:
                    print(f"{Colors.BRIGHT_GREEN}Destination playlist:{Colors.RESET} {Colors.DIM}(not set){Colors.RESET}")

                print(f"\n{Colors.BRIGHT_CYAN}Source playlists ({len(source_playlists)}):{Colors.RESET}")
                if source_playlists:
                    for idx, pl_id in enumerate(source_playlists, 1):
                        if sp:
                            playlist_name = get_playlist_name(sp, pl_id)
                            if playlist_name:
                                print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
                            else:
                                print(f"  {idx}. {Colors.DIM}{pl_id} (not found){Colors.RESET}")
                        else:
                            print(f"  {idx}. {pl_id}")
                else:
                    print(f"  {Colors.DIM}(none){Colors.RESET}")

                input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")
                print()

            else:
                print(f"{Colors.BRIGHT_RED}❌ Invalid choice.{Colors.RESET}\n")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.DIM}Back to main menu...{Colors.RESET}")
            break
        except Exception as e:
            print(f"{Colors.BRIGHT_RED}❌ Error: {e}{Colors.RESET}\n")
