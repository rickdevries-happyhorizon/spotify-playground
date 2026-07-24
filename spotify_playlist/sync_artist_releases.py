from typing import Any, Callable

import spotify_playlist.config as config
from db_store import (
    load_historical_data,
    load_playlists_config,
    resolve_sync_days_back,
    save_historical_data,
)

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.add_tracks_to_playlist import add_tracks_to_playlist
from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_all_artist_releases import get_all_artist_releases

ProgressCallback = Callable[[dict[str, Any]], None]


def sync_artist_releases(
    sp,
    on_progress: ProgressCallback | None = None,
    quiet: bool = False,
) -> dict[str, Any]:
    """Checks followed artists for new releases and adds them to the destination playlist."""
    result: dict[str, Any] = {
        "artists_checked": 0,
        "releases_found": 0,
        "releases_new": 0,
        "releases_added": 0,
        "skipped": False,
        "skip_reason": None,
    }

    def log(message: str = "") -> None:
        if not quiet:
            print(message)

    def report(**payload: Any) -> None:
        if on_progress:
            on_progress(payload)

    playlists_config = load_playlists_config()
    config.MIJN_DOEL_PLAYLIST_ID = playlists_config.get("destination_playlist", "")
    config.BRON_PLAYLISTS = playlists_config.get("source_playlists", [])

    if not config.MIJN_DOEL_PLAYLIST_ID:
        message = "No destination playlist configured. Skipping followed artists."
        log(f"{Colors.BRIGHT_YELLOW}⚠️  No destination playlist configured in the database.{Colors.RESET}")
        log(f"{Colors.DIM}   Set a destination playlist via the settings page or populate app_config.{Colors.RESET}")
        result["skipped"] = True
        result["skip_reason"] = message
        report(phase="artists_done", message=message)
        return result

    historische_nummers = load_historical_data(config.BRON_PLAYLISTS)
    nieuwe_nummers_uris = []

    log(f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}")
    log(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎤  New Releases from Followed Artists  🎤{Colors.RESET}")
    log(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}{'═'*70}{Colors.RESET}\n")

    report(phase="artists_start", message="Scanning followed artists…")

    try:
        days_back = resolve_sync_days_back()
        artist_releases = get_all_artist_releases(
            sp,
            days_back,
            on_progress=on_progress,
            quiet=quiet,
        )
        result["releases_found"] = len(artist_releases)

        if artist_releases:
            artist_releases_key = "__artist_releases__"
            laatst_bekende_artist_releases = historische_nummers.get(artist_releases_key, set())
            nieuwe_artist_uris = set(artist_releases.keys()) - laatst_bekende_artist_releases
            result["releases_new"] = len(nieuwe_artist_uris)

            if nieuwe_artist_uris:
                log(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╔{'═'*68}╗{Colors.RESET}")
                log(
                    f"{Colors.BOLD}{Colors.BRIGHT_GREEN}║{Colors.RESET}  "
                    f"{Colors.BOLD}{Colors.BRIGHT_WHITE}🎉 {len(nieuwe_artist_uris)} new releases found!"
                    f"{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-30)}║{Colors.RESET}"
                )
                log(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╠{'═'*68}╣{Colors.RESET}")
                log(
                    f"{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BRIGHT_MAGENTA}🆕 New releases:"
                    f"{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-18)}║{Colors.RESET}"
                )
                for uri in sorted(
                    nieuwe_artist_uris,
                    key=lambda u: artist_releases.get(u, {}).get("name", ""),
                ):
                    release_info = artist_releases.get(uri, {})
                    if release_info:
                        release_display = (
                            f"{release_info['name']} - {release_info['artists']} "
                            f"({release_info.get('album', 'Unknown')}) - {release_info.get('release_date', '')}"
                        )
                        if len(release_display) > 60:
                            release_display = release_display[:57] + "..."
                        log(
                            f"{Colors.BRIGHT_GREEN}║{Colors.RESET}      "
                            f"{Colors.BRIGHT_GREEN}•{Colors.RESET} {Colors.BRIGHT_WHITE}{release_display}"
                            f"{Colors.RESET}  {Colors.BRIGHT_GREEN}{' '*(68-len(release_display)-8)}║{Colors.RESET}"
                        )
                log(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}╚{'═'*68}╝{Colors.RESET}\n")

                nieuwe_nummers_uris.extend(list(nieuwe_artist_uris))
                historische_nummers[artist_releases_key] = set(artist_releases.keys())
            else:
                log(f"{Colors.DIM}🤷 No new releases from followed artists found.{Colors.RESET}\n")
        else:
            log(f"{Colors.DIM}🤷 No new releases found from followed artists.{Colors.RESET}\n")
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
        result["skipped"] = True
        result["skip_reason"] = message
        return result
    except Exception as e:
        message = f"Unexpected error fetching artist releases: {e}"
        log(f"{Colors.BRIGHT_RED}❌ {message}{Colors.RESET}")
        if quiet:
            raise
        result["skipped"] = True
        result["skip_reason"] = message
        return result

    if nieuwe_nummers_uris:
        report(
            phase="artists_adding",
            message=f"Adding {len(nieuwe_nummers_uris)} artist releases to destination…",
            releases_new=len(nieuwe_nummers_uris),
        )
        add_tracks_to_playlist(
            sp,
            nieuwe_nummers_uris,
            config.MIJN_DOEL_PLAYLIST_ID,
            quiet=quiet,
        )
        result["releases_added"] = len(nieuwe_nummers_uris)
    else:
        report(phase="artists_adding", message="No new artist releases to add")

    save_historical_data(historische_nummers)
    log(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ Artist releases sync completed!{Colors.RESET}\n")
    if not quiet:
        play_action_done()

    report(
        phase="artists_done",
        message=(
            f"Artist sync complete — {result['releases_new']} new release"
            f"{'' if result['releases_new'] == 1 else 's'}"
        ),
        **{k: result[k] for k in ("releases_found", "releases_new", "releases_added")},
    )
    return result
