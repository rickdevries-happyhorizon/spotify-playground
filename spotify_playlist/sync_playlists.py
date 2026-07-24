from typing import Any, Callable

import spotify_playlist.config as config
from db_store import (
    backfill_playlist_names,
    load_artist_discovery_enabled,
    load_historical_data,
    load_playlists_config,
    load_sync_start_date,
    resolve_sync_days_back,
    resolve_sync_since_date,
    save_historical_data,
)

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.add_tracks_to_playlist import add_tracks_to_playlist
from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_all_artist_releases import get_all_artist_releases
from spotify_playlist.get_discovery_artist_releases import get_discovery_artist_releases
from spotify_playlist.get_recent_playlist_tracks import get_recent_playlist_tracks
from spotify_playlist.get_track_info import get_track_info
from spotify_playlist.loading_progress import loading_bar

ProgressCallback = Callable[[dict[str, Any]], None]
ARTIST_RELEASES_KEY = "__artist_releases__"
ARTIST_DISCOVERY_KEY = "__artist_discovery__"


def _all_historical_uris(historical: dict[str, set[str]]) -> set[str]:
    known: set[str] = set()
    for uris in historical.values():
        known |= uris
    return known


def sync_playlists(
    sp,
    on_progress: ProgressCallback | None = None,
    quiet: bool = False,
    include_artist_releases: bool | None = None,
    include_artist_discovery: bool | None = None,
) -> dict[str, Any]:
    """Checks followed artists, discovery, and source playlists; adds new tracks to destination."""
    result: dict[str, Any] = {
        "playlist_count": 0,
        "playlists_checked": 0,
        "tracks_found": 0,
        "tracks_new": 0,
        "tracks_added": 0,
        "artist_releases_found": 0,
        "artist_releases_new": 0,
        "discovery_artists": 0,
        "discovery_releases_found": 0,
        "discovery_releases_new": 0,
        "artists_checked": 0,
        "since_date": None,
        "destination_playlist": None,
    }

    def log(message: str = "") -> None:
        if not quiet:
            print(message)

    def report(**payload: Any) -> None:
        if on_progress:
            on_progress(payload)

    if include_artist_releases is None:
        include_artist_releases = config.CHECK_ARTIST_RELEASES
    if include_artist_discovery is None:
        include_artist_discovery = load_artist_discovery_enabled()

    playlists_config = load_playlists_config()
    config.MIJN_DOEL_PLAYLIST_ID = playlists_config.get("destination_playlist", "")
    config.BRON_PLAYLISTS = playlists_config.get("source_playlists", [])
    tracking_playlists = playlists_config.get("tracking_playlists") or []

    if not config.MIJN_DOEL_PLAYLIST_ID:
        message = "No destination playlist configured. Set it in Settings first."
        log(f"{Colors.BRIGHT_YELLOW}⚠️  No destination playlist configured in the database.{Colors.RESET}")
        log(f"{Colors.DIM}   Set a destination playlist via the settings page or populate app_config.{Colors.RESET}")
        if quiet:
            raise RuntimeError(message)
        return result

    discovery_enabled = include_artist_discovery and bool(tracking_playlists)
    if not config.BRON_PLAYLISTS and not include_artist_releases and not discovery_enabled:
        message = (
            "Nothing to sync. Add source playlists, enable followed-artist sync, "
            "or configure tracking playlists for artist discovery."
        )
        log(f"{Colors.BRIGHT_YELLOW}⚠️  {message}{Colors.RESET}")
        if quiet:
            raise RuntimeError(message)
        return result

    result["playlist_count"] = len(config.BRON_PLAYLISTS)
    result["destination_playlist"] = config.MIJN_DOEL_PLAYLIST_ID

    if not quiet:
        backfill_playlist_names(sp)
    else:
        try:
            backfill_playlist_names(sp)
        except Exception:
            pass

    historische_nummers = load_historical_data(config.BRON_PLAYLISTS)
    nieuwe_nummers_uris: list[str] = []
    sync_since_date = resolve_sync_since_date()
    sync_start_saved = load_sync_start_date()
    sync_window_label = (
        f"since {sync_since_date.strftime('%Y-%m-%d')}"
        if sync_start_saved
        else "in the last 7 days"
    )
    result["since_date"] = sync_since_date.strftime("%Y-%m-%d")

    log(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
    log(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🎵  Start Playlist Sync  🎵{Colors.RESET}")
    log(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")

    report(
        phase="starting",
        message=f"Syncing since {result['since_date']}",
        playlist_total=len(config.BRON_PLAYLISTS),
        since_date=result["since_date"],
    )

    if include_artist_releases:
        log(f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}")
        log(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎤  New Releases from Followed Artists  🎤{Colors.RESET}")
        log(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}\n")
        report(phase="artists_start", message="Scanning followed artists…")

        try:
            days_back = resolve_sync_days_back()
            artist_releases = get_all_artist_releases(
                sp,
                days_back,
                on_progress=lambda event: report(**event),
                quiet=quiet,
            )
            result["artist_releases_found"] = len(artist_releases)

            if artist_releases:
                laatst_bekende_artist_releases = historische_nummers.get(ARTIST_RELEASES_KEY, set())
                nieuwe_artist_uris = set(artist_releases.keys()) - laatst_bekende_artist_releases
                result["artist_releases_new"] = len(nieuwe_artist_uris)
                if nieuwe_artist_uris:
                    log(
                        f"{Colors.BRIGHT_GREEN}🎉 {len(nieuwe_artist_uris)} new artist releases to add{Colors.RESET}\n"
                    )
                    nieuwe_nummers_uris.extend(sorted(nieuwe_artist_uris))
                historische_nummers[ARTIST_RELEASES_KEY] = set(artist_releases.keys())
            else:
                log(f"{Colors.DIM}🤷 No new releases found from followed artists.{Colors.RESET}\n")

            report(
                phase="artists_done",
                message=(
                    f"Artist sync — {result['artist_releases_new']} new release"
                    f"{'' if result['artist_releases_new'] == 1 else 's'}"
                ),
                artist_releases_new=result["artist_releases_new"],
                artist_releases_found=result["artist_releases_found"],
            )
        except SpotifyException as e:
            message = f"Error fetching artist releases: {e}"
            log(f"{Colors.BRIGHT_RED}❌ {message}{Colors.RESET}")
            if e.http_status == 403:
                log(
                    f"{Colors.BRIGHT_YELLOW}   No permission to fetch followed artists. "
                    f"Check your scope (user-follow-read).{Colors.RESET}"
                )
            if quiet:
                raise
        except Exception as e:
            message = f"Unexpected error fetching artist releases: {e}"
            log(f"{Colors.BRIGHT_RED}❌ {message}{Colors.RESET}")
            if quiet:
                raise

    if discovery_enabled:
        log(f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}")
        log(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🧭  New Artists From Tracking Taste  🧭{Colors.RESET}")
        log(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}\n")
        report(phase="discovery_start", message="Discovering artists from tracking taste…")

        try:
            days_back = resolve_sync_days_back()
            discovery_releases = get_discovery_artist_releases(
                sp,
                tracking_playlists,
                days_back,
                max_seed_artists=config.ARTIST_DISCOVERY_MAX_SEED_ARTISTS,
                max_candidates=config.ARTIST_DISCOVERY_MAX_CANDIDATES,
                max_tracks_per_playlist=config.ARTIST_DISCOVERY_MAX_TRACKS_PER_PLAYLIST,
                on_progress=lambda event: report(**event),
                quiet=quiet,
            )
            result["discovery_releases_found"] = len(discovery_releases)

            if discovery_releases:
                known_uris = _all_historical_uris(historische_nummers)
                discovery_known = historische_nummers.get(ARTIST_DISCOVERY_KEY, set())
                nieuwe_discovery_uris = (
                    set(discovery_releases.keys()) - known_uris - discovery_known
                )
                result["discovery_releases_new"] = len(nieuwe_discovery_uris)
                if nieuwe_discovery_uris:
                    log(
                        f"{Colors.BRIGHT_GREEN}🎉 {len(nieuwe_discovery_uris)} discovery "
                        f"releases to add{Colors.RESET}\n"
                    )
                    nieuwe_nummers_uris.extend(sorted(nieuwe_discovery_uris))
                historische_nummers[ARTIST_DISCOVERY_KEY] = discovery_known.union(
                    discovery_releases.keys()
                )
            else:
                log(f"{Colors.DIM}🤷 No discovery releases found.{Colors.RESET}\n")

            report(
                phase="discovery_done",
                message=(
                    f"Discovery — {result['discovery_releases_new']} new release"
                    f"{'' if result['discovery_releases_new'] == 1 else 's'}"
                ),
                discovery_releases_new=result["discovery_releases_new"],
                discovery_releases_found=result["discovery_releases_found"],
            )
        except SpotifyException as e:
            message = f"Error during artist discovery: {e}"
            log(f"{Colors.BRIGHT_RED}❌ {message}{Colors.RESET}")
            if quiet:
                raise
        except Exception as e:
            message = f"Unexpected error during artist discovery: {e}"
            log(f"{Colors.BRIGHT_RED}❌ {message}{Colors.RESET}")
            if quiet:
                raise
    elif include_artist_discovery and not tracking_playlists:
        log(
            f"{Colors.DIM}🧭 Artist discovery skipped — no tracking playlists configured."
            f"{Colors.RESET}\n"
        )

    if config.BRON_PLAYLISTS:
        report(
            phase="sources_start",
            message=f"Scanning source playlists {sync_window_label}",
            playlist_total=len(config.BRON_PLAYLISTS),
            since_date=result["since_date"],
        )

    for idx, pl_id in enumerate(config.BRON_PLAYLISTS, 1):
        try:
            log(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╔{'═'*68}╗{Colors.RESET}")
            log(
                f"{Colors.BRIGHT_CYAN}{Colors.BOLD}║{Colors.RESET}  "
                f"{Colors.BRIGHT_WHITE}📋 Playlist {idx}/{len(config.BRON_PLAYLISTS)}{Colors.RESET}  "
                f"{Colors.DIM}ID: {pl_id[:20]}...{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-45)}║{Colors.RESET}"
            )
            log(f"{Colors.BRIGHT_CYAN}{Colors.BOLD}╠{'═'*68}╣{Colors.RESET}")

            playlist_name = "Unknown"
            playlist_image_url = None
            try:
                playlist_info = sp.playlist(pl_id, fields="name,images")
                playlist_name = playlist_info["name"]
                images = playlist_info.get("images") or []
                playlist_image_url = images[0].get("url") if images else None
                log(
                    f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BOLD}{Colors.BRIGHT_GREEN}🎼 {playlist_name}"
                    f"{Colors.RESET}  {Colors.BRIGHT_CYAN}{' '*(68-len(playlist_name)-6)}║{Colors.RESET}"
                )
            except Exception:
                log(
                    f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.DIM}Playlist name unavailable{Colors.RESET}  "
                    f"{Colors.BRIGHT_CYAN}{' '*(68-30)}║{Colors.RESET}"
                )

            report(
                phase="playlist_start",
                message=f"Checking {playlist_name}",
                playlist_index=idx,
                playlist_total=len(config.BRON_PLAYLISTS),
                playlist_name=playlist_name,
                playlist_image_url=playlist_image_url,
            )

            log(f"{Colors.BRIGHT_CYAN}║{Colors.RESET}")
            log(
                f"{Colors.BRIGHT_CYAN}║{Colors.RESET}  {Colors.BRIGHT_YELLOW}⏳{Colors.RESET} "
                f"{Colors.DIM}Checking tracks added {sync_window_label}...{Colors.RESET}  "
                f"{Colors.BRIGHT_CYAN}{' '*(68-50)}║{Colors.RESET}"
            )
            report(
                phase="fetching_tracks",
                message=f"Fetching tracks from {playlist_name}",
                playlist_index=idx,
                playlist_total=len(config.BRON_PLAYLISTS),
                playlist_name=playlist_name,
                playlist_image_url=playlist_image_url,
            )
            if quiet:
                recent_tracks = get_recent_playlist_tracks(
                    sp,
                    pl_id,
                    since_date=sync_since_date,
                    return_track_info=True,
                )
            else:
                with loading_bar("Fetching recent tracks..."):
                    recent_tracks = get_recent_playlist_tracks(
                        sp,
                        pl_id,
                        since_date=sync_since_date,
                        return_track_info=True,
                    )
            recent_uris = set(recent_tracks.keys())
            result["tracks_found"] += len(recent_uris)
            result["playlists_checked"] += 1

            laatst_bekende_uris = historische_nummers.get(pl_id, set())
            nieuwe_uris = recent_uris - laatst_bekende_uris

            if nieuwe_uris:
                historische_nummers[pl_id] = laatst_bekende_uris.union(recent_uris)
            elif pl_id not in historische_nummers:
                historische_nummers[pl_id] = recent_uris

            if nieuwe_uris:
                nieuwe_nummers_uris.extend(list(nieuwe_uris))

            report(
                phase="playlist_done",
                message=f"{playlist_name}: {len(nieuwe_uris)} new",
                playlist_index=idx,
                playlist_total=len(config.BRON_PLAYLISTS),
                playlist_name=playlist_name,
                playlist_image_url=playlist_image_url,
                tracks_found=result["tracks_found"],
                tracks_new=len(nieuwe_nummers_uris),
            )

        except SpotifyException as e:
            log(f"{Colors.BRIGHT_RED}❌ Spotify API error while processing playlist {pl_id}: {e}{Colors.RESET}")
            report(
                phase="playlist_error",
                message=f"Error on playlist {idx}/{len(config.BRON_PLAYLISTS)}",
                playlist_index=idx,
                playlist_total=len(config.BRON_PLAYLISTS),
            )
            continue
        except Exception as e:
            log(f"{Colors.BRIGHT_RED}❌ Error while processing playlist {pl_id}: {e}{Colors.RESET}")
            report(
                phase="playlist_error",
                message=f"Error on playlist {idx}/{len(config.BRON_PLAYLISTS)}",
                playlist_index=idx,
                playlist_total=len(config.BRON_PLAYLISTS),
            )
            continue

    nieuwe_nummers_uris = list(dict.fromkeys(nieuwe_nummers_uris))
    result["tracks_new"] = len(nieuwe_nummers_uris)
    report(
        phase="adding",
        message=(
            f"Adding {len(nieuwe_nummers_uris)} track"
            f"{'' if len(nieuwe_nummers_uris) == 1 else 's'} to destination…"
            if nieuwe_nummers_uris
            else "No new tracks to add to destination"
        ),
        tracks_new=result["tracks_new"],
        tracks_found=result["tracks_found"],
    )

    tracks_added = add_tracks_to_playlist(
        sp,
        nieuwe_nummers_uris,
        config.MIJN_DOEL_PLAYLIST_ID,
        quiet=quiet,
    )
    result["tracks_added"] = tracks_added

    save_historical_data(historische_nummers)
    log(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ Playlist sync completed!{Colors.RESET}\n")
    if not quiet:
        play_action_done()

    report(
        phase="done",
        message="Playlist sync complete",
        tracks_added=tracks_added,
        tracks_new=result["tracks_new"],
        tracks_found=result["tracks_found"],
        playlists_checked=result["playlists_checked"],
        playlist_total=result["playlist_count"],
        since_date=result["since_date"],
        artist_releases_new=result["artist_releases_new"],
        artist_releases_found=result["artist_releases_found"],
        discovery_releases_new=result["discovery_releases_new"],
        discovery_releases_found=result["discovery_releases_found"],
    )
    return result
