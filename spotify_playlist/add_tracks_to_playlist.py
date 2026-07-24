import traceback

from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_all_playlist_tracks import get_all_playlist_tracks
from spotify_playlist.loading_progress import loading_bar, tqdm


def add_tracks_to_playlist(sp, nieuwe_nummers_uris, doel_playlist_id, quiet: bool = False):
    """Adds tracks to the destination playlist after duplicate checking."""
    if not nieuwe_nummers_uris:
        return

    def log(message: str = "") -> None:
        if not quiet:
            print(message)

    log(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}")
    log(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}🔍  Checking Duplicates  🔍{Colors.RESET}")
    log(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}\n")

    # Remove duplicates within the new tracks list first
    # (e.g. when the same track appears in multiple source playlists)
    original_count = len(nieuwe_nummers_uris)
    nieuwe_nummers_uris = list(dict.fromkeys(nieuwe_nummers_uris))  # Preserves order, removes duplicates
    if len(nieuwe_nummers_uris) < original_count:
        internal_duplicates = original_count - len(nieuwe_nummers_uris)
        log(f"{Colors.BRIGHT_YELLOW}⚠️  {internal_duplicates} duplicates removed from new tracks list.{Colors.RESET}")

    log(f"{Colors.DIM}⏳ Checking {len(nieuwe_nummers_uris)} unique new tracks against destination playlist...{Colors.RESET}")
    try:
        if quiet:
            doel_playlist_tracks = get_all_playlist_tracks(sp, doel_playlist_id)
        else:
            with loading_bar("Fetching destination playlist..."):
                doel_playlist_tracks = get_all_playlist_tracks(sp, doel_playlist_id)
        log(
            f"{Colors.BRIGHT_CYAN}   Destination playlist currently contains "
            f"{Colors.BOLD}{len(doel_playlist_tracks)}{Colors.RESET}{Colors.BRIGHT_CYAN} tracks{Colors.RESET}"
        )

        unieke_nieuwe_uris = [uri for uri in nieuwe_nummers_uris if uri not in doel_playlist_tracks]

        if len(unieke_nieuwe_uris) < len(nieuwe_nummers_uris):
            duplicates = len(nieuwe_nummers_uris) - len(unieke_nieuwe_uris)
            log(
                f"{Colors.BRIGHT_YELLOW}⚠️  {duplicates} tracks are already in the destination "
                f"playlist and will be skipped.{Colors.RESET}"
            )
        else:
            log(
                f"{Colors.BRIGHT_GREEN}✅ All {len(nieuwe_nummers_uris)} tracks are new "
                f"for the destination playlist{Colors.RESET}"
            )

        nieuwe_nummers_uris = unieke_nieuwe_uris
    except Exception as e:
        log(f"{Colors.BRIGHT_YELLOW}⚠️  Could not check duplicates: {e}{Colors.RESET}")
        log(f"{Colors.DIM}   Traceback: {type(e).__name__}: {str(e)}{Colors.RESET}")
        log(f"{Colors.DIM}   Adding all tracks (possible duplicates)...{Colors.RESET}")

    # Add tracks to the destination playlist
    if nieuwe_nummers_uris:
        log(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}")
        log(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}➕  Adding Tracks  ➕{Colors.RESET}")
        log(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}\n")
        try:
            doel_playlist_info = sp.playlist(doel_playlist_id, fields='name')
            playlist_name = doel_playlist_info['name']
            log(
                f"{Colors.BRIGHT_CYAN}📝 Adding {Colors.BOLD}{Colors.BRIGHT_WHITE}"
                f"{len(nieuwe_nummers_uris)}{Colors.RESET}{Colors.BRIGHT_CYAN} unique tracks to:{Colors.RESET}"
            )
            log(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}   🎵 {playlist_name}{Colors.RESET}\n")
        except Exception:
            log(
                f"{Colors.BRIGHT_CYAN}📝 Adding {Colors.BOLD}{Colors.BRIGHT_WHITE}"
                f"{len(nieuwe_nummers_uris)}{Colors.RESET}{Colors.BRIGHT_CYAN} unique tracks to "
                f"playlist ID: {doel_playlist_id}{Colors.RESET}\n"
            )

        # The API can add at most 100 tracks at a time
        try:
            total_added = 0
            batch_starts = list(range(0, len(nieuwe_nummers_uris), 100))
            batch_iter = batch_starts if quiet else tqdm(batch_starts, desc="Adding to playlist", unit="batch")
            for i in batch_iter:
                batch = nieuwe_nummers_uris[i : i + 100]
                sp.playlist_add_items(doel_playlist_id, batch)
                total_added += len(batch)
            log(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}╔{'═'*68}╗{Colors.RESET}")
            log(
                f"{Colors.BOLD}{Colors.BRIGHT_GREEN}║{Colors.RESET}  "
                f"{Colors.BOLD}{Colors.BRIGHT_WHITE}🎉 Successfully added {total_added} tracks! 🎉"
                f"{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-40)}║{Colors.RESET}"
            )
            log(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╚{'═'*68}╝{Colors.RESET}\n")
        except SpotifyException as e:
            log(f"{Colors.BRIGHT_RED}❌ Error adding tracks: {e}{Colors.RESET}")
            log(f"{Colors.DIM}   HTTP Status: {e.http_status}{Colors.RESET}")
            log(f"{Colors.DIM}   Error Code: {e.code}{Colors.RESET}")
            if e.http_status == 404:
                log(f"{Colors.BRIGHT_YELLOW}   Destination playlist not found. Check the playlist ID.{Colors.RESET}")
            elif e.http_status == 403:
                log(f"{Colors.BRIGHT_YELLOW}   No permission to add tracks to this playlist.{Colors.RESET}")
                log(
                    f"{Colors.DIM}   Check that you have the correct scope "
                    f"(playlist-modify-public and/or playlist-modify-private){Colors.RESET}"
                )
        except Exception as e:
            log(f"{Colors.BRIGHT_RED}❌ Unexpected error while adding tracks: {e}{Colors.RESET}")
            log(f"{Colors.DIM}   Traceback: {traceback.format_exc()}{Colors.RESET}")
    else:
        log(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
        log(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}✅  No New Tracks  ✅{Colors.RESET}")
        log(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")
        log(f"{Colors.DIM}No new tracks found to add to the destination playlist.{Colors.RESET}\n")
