from datetime import datetime

from db_store import (
    load_playlists_config,
    load_tracking_start_date,
    save_playlists_config,
    save_tracking_start_date,
)

from spotify_playlist.action_sound import play_selection
from spotify_playlist.colors import Colors
from spotify_playlist.export_new_tracks_since_date import export_new_tracks_since_date


def run_import_new_tracks_menu(sp) -> None:
    """Interactive flow to import new playlist tracks into the database."""
    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}📥  Import New Tracks Since Date  📥{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}\n")

    playlists_config = load_playlists_config()
    tracking_playlists = playlists_config.get('tracking_playlists', [])

    print(f"{Colors.BRIGHT_WHITE}Current tracking playlists ({len(tracking_playlists)}):{Colors.RESET}")
    if tracking_playlists:
        for idx, pl_id in enumerate(tracking_playlists, 1):
            try:
                playlist_info = sp.playlist(pl_id, fields='name')
                playlist_name = playlist_info['name']
                print(f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} {Colors.DIM}({pl_id}){Colors.RESET}")
            except Exception:
                print(f"  {idx}. {Colors.DIM}{pl_id} (not found){Colors.RESET}")
    else:
        print(f"  {Colors.DIM}(no playlists configured){Colors.RESET}")

    print(f"\n{Colors.BRIGHT_CYAN}Options:{Colors.RESET}")
    if tracking_playlists:
        print(f"  {Colors.BRIGHT_GREEN}u.{Colors.RESET} Use tracking playlists ({len(tracking_playlists)} playlists)")
    print(f"  {Colors.BRIGHT_BLUE}m.{Colors.RESET} Enter playlist IDs manually")
    print(f"  {Colors.BRIGHT_MAGENTA}c.{Colors.RESET} Manage tracking playlists")
    print(f"  {Colors.DIM}q.{Colors.RESET} Back to main menu")

    option = None
    selected_playlists = None
    while True:
        try:
            option = input(
                f"\n{Colors.BRIGHT_CYAN}Enter your choice ({'u/' if tracking_playlists else ''}m/c/q): {Colors.RESET}"
            ).strip().lower()

            if option == 'q':
                break
            if option == 'u' and tracking_playlists:
                play_selection()
                selected_playlists = tracking_playlists
                break
            if option == 'm':
                play_selection()
                print(f"\n{Colors.BRIGHT_WHITE}Enter playlist IDs (comma-separated):{Colors.RESET}")
                playlist_input = input(f"{Colors.BRIGHT_CYAN}Playlist IDs: {Colors.RESET}").strip()
                selected_playlists = [pl_id.strip() for pl_id in playlist_input.split(',') if pl_id.strip()]
                if not selected_playlists:
                    print(f"{Colors.BRIGHT_RED}❌ No playlist IDs entered.{Colors.RESET}")
                    continue

                save_option = input(
                    f"{Colors.BRIGHT_CYAN}Save these playlists for next time? (y/n): {Colors.RESET}"
                ).strip().lower()
                if save_option == 'y':
                    playlists_config = load_playlists_config()
                    tracking_playlists = playlists_config.get('tracking_playlists', [])
                    for pl_id in selected_playlists:
                        if pl_id not in tracking_playlists:
                            tracking_playlists.append(pl_id)
                    playlists_config['tracking_playlists'] = tracking_playlists
                    save_playlists_config(playlists_config)
                    print(f"{Colors.BRIGHT_GREEN}✅ Saved {len(selected_playlists)} playlist(s)!{Colors.RESET}")
                break
            if option == 'c':
                play_selection()
                while True:
                    playlists_config = load_playlists_config()
                    tracking_playlists = playlists_config.get('tracking_playlists', [])

                    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
                    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}⚙️  Manage Tracking Playlists  ⚙️{Colors.RESET}")
                    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}\n")

                    print(f"{Colors.BRIGHT_WHITE}Current tracking playlists ({len(tracking_playlists)}):{Colors.RESET}")
                    if tracking_playlists:
                        for idx, pl_id in enumerate(tracking_playlists, 1):
                            try:
                                playlist_info = sp.playlist(pl_id, fields='name')
                                playlist_name = playlist_info['name']
                                print(
                                    f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} "
                                    f"{Colors.DIM}({pl_id}){Colors.RESET}"
                                )
                            except Exception:
                                print(f"  {idx}. {Colors.DIM}{pl_id} (not found){Colors.RESET}")
                    else:
                        print(f"  {Colors.DIM}(none){Colors.RESET}")

                    print(f"\n{Colors.BRIGHT_WHITE}What would you like to do?{Colors.RESET}")
                    print(f"  {Colors.BRIGHT_GREEN}1.{Colors.RESET} Add playlist")
                    print(f"  {Colors.BRIGHT_RED}2.{Colors.RESET} Remove playlist")
                    print(f"  {Colors.DIM}0.{Colors.RESET} Back")

                    try:
                        action = input(f"\n{Colors.BRIGHT_CYAN}Enter your choice (0-2): {Colors.RESET}").strip()

                        if action == '0':
                            break
                        if action == '1':
                            play_selection()
                            playlist_id = input(
                                f"{Colors.BRIGHT_GREEN}Enter playlist ID to add: {Colors.RESET}"
                            ).strip()
                            if playlist_id and playlist_id not in tracking_playlists:
                                try:
                                    playlist_info = sp.playlist(playlist_id, fields='name')
                                    playlist_name = playlist_info['name']
                                    print(
                                        f"{Colors.BRIGHT_CYAN}   Found: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}"
                                    )
                                    confirm = input(f"{Colors.BRIGHT_GREEN}Add it? (y/n): {Colors.RESET}").strip().lower()
                                    if confirm == 'y':
                                        tracking_playlists.append(playlist_id)
                                        playlists_config['tracking_playlists'] = tracking_playlists
                                        save_playlists_config(playlists_config)
                                        print(
                                            f"{Colors.BRIGHT_GREEN}✅ Playlist '{playlist_name}' added!{Colors.RESET}\n"
                                        )
                                    else:
                                        print(f"{Colors.DIM}Cancelled.{Colors.RESET}\n")
                                except Exception as exc:
                                    print(f"{Colors.BRIGHT_YELLOW}⚠️  Could not verify playlist: {exc}{Colors.RESET}")
                                    confirm = input(
                                        f"{Colors.BRIGHT_YELLOW}Add anyway? (y/n): {Colors.RESET}"
                                    ).strip().lower()
                                    if confirm == 'y':
                                        tracking_playlists.append(playlist_id)
                                        playlists_config['tracking_playlists'] = tracking_playlists
                                        save_playlists_config(playlists_config)
                                        print(f"{Colors.BRIGHT_GREEN}✅ Playlist added!{Colors.RESET}\n")
                            elif playlist_id in tracking_playlists:
                                print(f"{Colors.BRIGHT_YELLOW}⚠️  This playlist is already in the list.{Colors.RESET}\n")
                            else:
                                print(f"{Colors.BRIGHT_RED}❌ Invalid playlist ID.{Colors.RESET}\n")
                        elif action == '2':
                            play_selection()
                            if not tracking_playlists:
                                print(f"{Colors.BRIGHT_YELLOW}⚠️  No playlists to remove.{Colors.RESET}\n")
                                continue

                            print(f"{Colors.BRIGHT_RED}Which playlist do you want to remove?{Colors.RESET}")
                            playlist_names = {}
                            for idx, pl_id in enumerate(tracking_playlists, 1):
                                try:
                                    playlist_info = sp.playlist(pl_id, fields='name')
                                    playlist_name = playlist_info['name']
                                    playlist_names[pl_id] = playlist_name
                                    print(
                                        f"  {idx}. {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET} "
                                        f"{Colors.DIM}({pl_id}){Colors.RESET}"
                                    )
                                except Exception:
                                    print(f"  {idx}. {Colors.DIM}{pl_id} (not found){Colors.RESET}")

                            try:
                                idx = int(
                                    input(
                                        f"{Colors.BRIGHT_RED}Enter number (1-{len(tracking_playlists)}): {Colors.RESET}"
                                    ).strip()
                                )
                                if 1 <= idx <= len(tracking_playlists):
                                    removed_id = tracking_playlists.pop(idx - 1)
                                    removed_name = playlist_names.get(removed_id, removed_id)
                                    playlists_config['tracking_playlists'] = tracking_playlists
                                    save_playlists_config(playlists_config)
                                    if removed_name != removed_id:
                                        print(
                                            f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_name}' removed!{Colors.RESET}\n"
                                        )
                                    else:
                                        print(
                                            f"{Colors.BRIGHT_GREEN}✅ Playlist '{removed_id}' removed!{Colors.RESET}\n"
                                        )
                                else:
                                    print(f"{Colors.BRIGHT_RED}❌ Invalid number.{Colors.RESET}\n")
                            except ValueError:
                                print(f"{Colors.BRIGHT_RED}❌ Enter a valid number.{Colors.RESET}\n")
                        else:
                            print(f"{Colors.BRIGHT_RED}❌ Invalid choice.{Colors.RESET}\n")

                    except KeyboardInterrupt:
                        print(f"\n\n{Colors.DIM}Back...{Colors.RESET}")
                        break
                    except Exception as exc:
                        print(f"{Colors.BRIGHT_RED}❌ Error: {exc}{Colors.RESET}\n")

                continue_option = input(
                    f"\n{Colors.BRIGHT_CYAN}Continue importing? (y/n): {Colors.RESET}"
                ).strip().lower()
                if continue_option != 'y':
                    break
                playlists_config = load_playlists_config()
                tracking_playlists = playlists_config.get('tracking_playlists', [])
                if not tracking_playlists:
                    print(f"{Colors.BRIGHT_YELLOW}⚠️  No tracking playlists configured.{Colors.RESET}")
                    break
                selected_playlists = tracking_playlists
                break
            print(f"{Colors.BRIGHT_RED}❌ Invalid choice.{Colors.RESET}")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.DIM}Back to main menu...{Colors.RESET}")
            return

    if option == 'q' or selected_playlists is None:
        return

    saved_start_date = load_tracking_start_date()
    today = datetime.now()

    print(f"\n{Colors.BRIGHT_WHITE}Date settings:{Colors.RESET}")
    if saved_start_date:
        print(f"{Colors.DIM}   Current start date: {saved_start_date.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.DIM}   Today: {today.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.DIM}   Tracks will be checked between these two dates.{Colors.RESET}")
    else:
        print(f"{Colors.DIM}   No start date set. Default: 7 days ago.{Colors.RESET}")

    print(f"\n{Colors.BRIGHT_CYAN}Options:{Colors.RESET}")
    print(
        f"  {Colors.BRIGHT_GREEN}1.{Colors.RESET} Use saved start date "
        f"({saved_start_date.strftime('%Y-%m-%d') if saved_start_date else '7 days ago'})"
    )
    print(f"  {Colors.BRIGHT_BLUE}2.{Colors.RESET} Set a new start date")

    since_date = None
    date_option = None
    while True:
        try:
            date_option = input(f"\n{Colors.BRIGHT_CYAN}Enter your choice (1/2): {Colors.RESET}").strip()

            if date_option == '1':
                play_selection()
                since_date = None
                break
            if date_option == '2':
                play_selection()
                date_str = input(f"{Colors.BRIGHT_CYAN}Enter new start date (YYYY-MM-DD): {Colors.RESET}").strip()
                try:
                    since_date = datetime.strptime(date_str, '%Y-%m-%d')
                    save_tracking_start_date(since_date)
                    print(
                        f"{Colors.BRIGHT_GREEN}✅ Start date set to: {since_date.strftime('%Y-%m-%d')}{Colors.RESET}"
                    )
                    break
                except ValueError:
                    print(f"{Colors.BRIGHT_RED}❌ Invalid date format. Use YYYY-MM-DD{Colors.RESET}")
                    continue
            print(f"{Colors.BRIGHT_RED}❌ Invalid choice. Enter 1 or 2.{Colors.RESET}")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.DIM}Cancelled...{Colors.RESET}")
            return

    if date_option is None or (date_option == '2' and since_date is None):
        return

    export_new_tracks_since_date(sp, selected_playlists, since_date)
