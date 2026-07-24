"""Download YouTube audio as AIFF files using yt-dlp and a single ffmpeg pass."""

import os
import re
import shutil
import subprocess
from typing import Callable, Optional

from db_store import delete_new_track, load_new_tracks
from spotify_playlist.action_sound import play_action_done
from spotify_playlist.colors import Colors
from spotify_playlist.spotify_track_energy import format_energy_label
from spotify_playlist.parse_wav_filename import parse_wav_filename
from spotify_playlist.release_year import normalize_release_year, release_year_from_youtube_info
from spotify_playlist.tag_wav_metadata import apply_aiff_metadata, apply_cover_art
from spotify_playlist.youtube_thumbnail import cover_art_from_youtube_info

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _require_yt_dlp():
    try:
        import yt_dlp
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "yt-dlp is not installed. Run: pip install -r requirements.txt"
        ) from exc
    return yt_dlp


def _find_on_path_or_homebrew(name: str) -> str | None:
    for candidate in (name, f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"):
        path = candidate if os.path.isabs(candidate) else shutil.which(candidate)
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def _find_ffmpeg() -> str | None:
    return _find_on_path_or_homebrew("ffmpeg")


def _require_ffmpeg() -> str:
    path = _find_ffmpeg()
    if not path:
        raise FileNotFoundError(
            "ffmpeg is not installed. On macOS: brew install ffmpeg"
        )
    return path


def _build_youtube_ydl_opts(**extra) -> dict:
    """Base yt-dlp options for reliable YouTube extraction."""
    opts: dict = {
        'noplaylist': True,
        'windowsfilenames': True,
        'quiet': False,
        'no_warnings': False,
    }

    ffmpeg = _find_ffmpeg()
    if ffmpeg:
        opts['ffmpeg_location'] = os.path.dirname(ffmpeg)

    node_path = _find_on_path_or_homebrew('node')
    if node_path:
        opts['js_runtimes'] = {'node': {'path': node_path}}
    else:
        deno_path = _find_on_path_or_homebrew('deno')
        if deno_path:
            opts['js_runtimes'] = {'deno': {'path': deno_path}}
        else:
            opts['remote_components'] = ['ejs:github']

    opts.update(extra)
    return opts


def _safe_filename_stem(name: str) -> str:
    cleaned = _INVALID_FILENAME_CHARS.sub('', name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip().strip('.')
    return cleaned or 'unknown'


AUDIO_EXTENSION = '.aiff'


def _tag_audio_from_filename(
    path: str,
    genre: str | None = None,
    year: int | str | None = None,
    label: str | None = None,
) -> None:
    stem = os.path.splitext(os.path.basename(path))[0]
    artists, title = parse_wav_filename(stem)
    apply_aiff_metadata(path, artists, title, genre, year, label)


def _convert_to_aiff(source_path: str, aiff_path: str) -> None:
    """Convert downloaded audio to AIFF in one ffmpeg pass, preserving sample rate."""
    ffmpeg = _require_ffmpeg()
    result = subprocess.run(
        [
            ffmpeg,
            '-y',
            '-i',
            source_path,
            '-c:a',
            'pcm_s16be',
            '-f',
            'aiff',
            aiff_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or '').strip()
        raise RuntimeError(stderr or 'ffmpeg AIFF conversion failed')


def download_youtube_to_aiff(
    url: str,
    output_dir: str,
    *,
    output_name: Optional[str] = None,
    overwrite: bool = False,
    tag_metadata: bool = True,
    genre: str | None = None,
    year: int | str | None = None,
    energy: float | None = None,
) -> Optional[str]:
    """
    Download a single YouTube URL as an AIFF file.

    When output_name is set (e.g. from the new_tracks app), the AIFF is saved as
    ``output_name.aiff`` instead of using the YouTube video title.

    Returns the path to the downloaded AIFF file, or None on failure.
    """
    yt_dlp = _require_yt_dlp()
    _require_ffmpeg()

    os.makedirs(output_dir, exist_ok=True)

    if output_name:
        outtmpl = os.path.join(output_dir, f'{_safe_filename_stem(output_name)}.%(ext)s')
    else:
        outtmpl = os.path.join(
            output_dir,
            '%(artist,channel,uploader)s - %(title)s.%(ext)s',
        )

    ydl_opts = _build_youtube_ydl_opts(
        format='bestaudio/best',
        outtmpl=outtmpl,
        overwrites=overwrite,
    )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            return None

        source_path = ydl.prepare_filename(info)
        audio_path = os.path.splitext(source_path)[0] + AUDIO_EXTENSION

    if not os.path.isfile(source_path):
        print(
            f"{Colors.BRIGHT_RED}❌ Audio file not found after download: "
            f"{source_path}{Colors.RESET}"
        )
        return None

    try:
        _convert_to_aiff(source_path, audio_path)
    except RuntimeError as exc:
        print(f"{Colors.BRIGHT_RED}❌ AIFF conversion failed: {exc}{Colors.RESET}")
        return None
    finally:
        if os.path.isfile(source_path):
            os.remove(source_path)

    if not os.path.isfile(audio_path):
        print(f"{Colors.BRIGHT_RED}❌ AIFF file not found after download: {audio_path}{Colors.RESET}")
        return None

    if tag_metadata:
        release_year = normalize_release_year(year) or release_year_from_youtube_info(info)
        energy_label = format_energy_label(energy) if energy is not None else None

        try:
            _tag_audio_from_filename(audio_path, genre, release_year, energy_label)
            details = []
            if release_year is not None:
                details.append(f'year {release_year}')
            if energy_label is not None:
                details.append(f'energy {energy_label}')
            if details:
                print(
                    f"    {Colors.BRIGHT_GREEN}✅ ID3 metadata added "
                    f"(incl. {', '.join(details)}){Colors.RESET}"
                )
            else:
                print(f"    {Colors.BRIGHT_GREEN}✅ ID3 metadata added{Colors.RESET}")
        except Exception as exc:
            print(
                f"    {Colors.BRIGHT_YELLOW}⚠️  Metadata not applied "
                f"(filename must be 'Artist - Title.aiff'): {exc}{Colors.RESET}"
            )

        try:
            cover_art = cover_art_from_youtube_info(info)
            if cover_art:
                apply_cover_art(audio_path, cover_art)
                print(f"    {Colors.BRIGHT_GREEN}✅ YouTube cover art added{Colors.RESET}")
        except Exception as exc:
            print(
                f"    {Colors.BRIGHT_YELLOW}⚠️  Cover art not applied: {exc}{Colors.RESET}"
            )

    return audio_path


def download_youtube_urls(
    urls: list[str],
    output_dir: str,
    *,
    overwrite: bool = False,
    tag_metadata: bool = True,
) -> tuple[int, int]:
    """Download multiple YouTube URLs. Returns (success_count, error_count)."""
    success_count = 0
    error_count = 0

    for index, url in enumerate(urls, start=1):
        print(f"\n{Colors.BRIGHT_WHITE}[{index}/{len(urls)}]{Colors.RESET} {url}")
        try:
            audio_path = download_youtube_to_aiff(
                url,
                output_dir,
                overwrite=overwrite,
                tag_metadata=tag_metadata,
            )
            if audio_path:
                print(f"    {Colors.BRIGHT_GREEN}✅ Saved: {audio_path}{Colors.RESET}")
                success_count += 1
            else:
                error_count += 1
        except Exception as exc:
            print(f"    {Colors.BRIGHT_RED}❌ Error: {exc}{Colors.RESET}")
            error_count += 1

    if success_count:
        play_action_done()

    return success_count, error_count


def load_tracks_from_app() -> list[dict]:
    """Load new_tracks rows that have a YouTube reference URL."""
    tracks = load_new_tracks()
    with_url = [
        track
        for track in tracks
        if track.get('reference_url')
    ]
    if not with_url:
        raise ValueError(
            "No tracks with YouTube URL found in the app. "
            "Add reference URLs in the new tracks todo first."
        )
    return with_url


def download_youtube_tracks(
    tracks: list[dict],
    output_dir: str,
    *,
    overwrite: bool = False,
    tag_metadata: bool = True,
    on_progress: Callable[[dict], None] | None = None,
) -> tuple[int, int]:
    """Download tracks from the app. Successfully downloaded rows are removed from the database."""
    success_count = 0
    error_count = 0
    last_error: str | None = None

    if on_progress:
        on_progress(
            {
                "phase": "starting",
                "track_total": len(tracks),
                "message": f"Downloading {len(tracks)} track(s)…",
            }
        )

    for index, track in enumerate(tracks, start=1):
        track_name = track.get('track', 'unknown')
        url = track.get('reference_url')
        print(
            f"\n{Colors.BRIGHT_WHITE}[{index}/{len(tracks)}]{Colors.RESET} "
            f"{Colors.BRIGHT_CYAN}{track_name}{Colors.RESET}"
        )
        print(f"    {Colors.DIM}{url}{Colors.RESET}")
        if on_progress:
            on_progress(
                {
                    "phase": "downloading",
                    "track_index": index,
                    "track_total": len(tracks),
                    "track_name": track_name,
                    "success_count": success_count,
                    "error_count": error_count,
                    "message": f"Downloading {track_name} ({index}/{len(tracks)})",
                }
            )
        try:
            audio_path = download_youtube_to_aiff(
                url,
                output_dir,
                output_name=track_name,
                overwrite=overwrite,
                tag_metadata=tag_metadata,
                genre=track.get('genre'),
                year=track.get('release_year'),
                energy=track.get('energy'),
            )
            if audio_path:
                print(f"    {Colors.BRIGHT_GREEN}✅ Saved: {audio_path}{Colors.RESET}")
                track_id = track.get('id')
                if track_id is not None:
                    try:
                        if delete_new_track(track_id):
                            print(
                                f"    {Colors.BRIGHT_GREEN}✅ Removed from database{Colors.RESET}"
                            )
                        else:
                            print(
                                f"    {Colors.BRIGHT_YELLOW}⚠️  Track not found in database "
                                f"(id={track_id}){Colors.RESET}"
                            )
                    except Exception as exc:
                        print(
                            f"    {Colors.BRIGHT_YELLOW}⚠️  Could not remove track from "
                            f"database: {exc}{Colors.RESET}"
                        )
                success_count += 1
            else:
                last_error = f"Could not download {track_name}"
                error_count += 1
        except Exception as exc:
            print(f"    {Colors.BRIGHT_RED}❌ Error: {exc}{Colors.RESET}")
            last_error = str(exc)
            error_count += 1

        if on_progress:
            on_progress(
                {
                    "phase": "downloading",
                    "track_index": index,
                    "track_total": len(tracks),
                    "track_name": track_name,
                    "success_count": success_count,
                    "error_count": error_count,
                    "last_error": last_error,
                    "message": last_error or f"Downloaded {success_count}, failed {error_count}",
                }
            )

    if success_count:
        play_action_done()

    return success_count, error_count


def load_urls_from_file(path: str) -> list[str]:
    """Load YouTube URLs from a text file (one per line, # comments allowed)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

    urls: list[str] = []
    with open(path, encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, start=1):
            cleaned = line.strip()
            if not cleaned or cleaned.startswith('#'):
                continue
            urls.append(cleaned)

    if not urls:
        raise ValueError(f"No URLs found in: {path}")

    return urls


def _read_urls_from_input() -> list[str]:
    print(
        f"\n{Colors.DIM}Paste YouTube URL(s), one per line. "
        f"Press Enter on a blank line to start.{Colors.RESET}\n"
    )
    urls: list[str] = []
    while True:
        try:
            line = input().strip()
        except EOFError:
            break
        if not line:
            break
        urls.append(line)
    return urls


def run_download_youtube_wav(
    default_directory: str = '',
    default_urls_file: str = '',
) -> None:
    """Interactive flow to download YouTube audio as AIFF from the menu."""
    try:
        _require_yt_dlp()
        _require_ffmpeg()
    except (ModuleNotFoundError, FileNotFoundError) as exc:
        print(f"{Colors.BRIGHT_RED}❌ {exc}{Colors.RESET}")
        return

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎵  Download YouTube to AIFF  🎵{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(
        f"\n{Colors.DIM}For personal use only. "
        f"Do not download copyrighted material without permission.{Colors.RESET}"
    )

    if default_directory:
        directory = os.path.abspath(os.path.expanduser(default_directory))
        os.makedirs(directory, exist_ok=True)
        print(
            f"\n{Colors.BRIGHT_CYAN}Output directory:{Colors.RESET} "
            f"{Colors.BRIGHT_WHITE}{directory}{Colors.RESET}"
        )
    else:
        directory = input(
            f"\n{Colors.BRIGHT_CYAN}Output directory ('q' to go back): {Colors.RESET}"
        ).strip()

        if directory.lower() == 'q':
            return

        if not directory:
            print(f"{Colors.BRIGHT_RED}❌ No directory specified.{Colors.RESET}")
            return

        directory = os.path.abspath(os.path.expanduser(directory))
        os.makedirs(directory, exist_ok=True)

    if default_urls_file:
        print(f"{Colors.DIM}Default URL file: {default_urls_file}{Colors.RESET}")

    source = input(
        f"\n{Colors.BRIGHT_CYAN}URL source: [Enter] app database  [1] paste  [2] file: {Colors.RESET}"
    ).strip().lower()

    tracks_from_app: list[dict] = []
    urls: list[str] = []

    if source in ('', 'app', 'database', 'db'):
        try:
            tracks_from_app = load_tracks_from_app()
            print(
                f"\n{Colors.BRIGHT_GREEN}✅ {len(tracks_from_app)} track(s) with YouTube URL "
                f"loaded from the app{Colors.RESET}"
            )
            print(
                f"{Colors.DIM}Successfully downloaded tracks are automatically removed from the "
                f"database.{Colors.RESET}\n"
            )
            for track in tracks_from_app:
                print(f"  • {track['track']}")
                print(f"    {Colors.DIM}{track['reference_url']}{Colors.RESET}")
        except ValueError as exc:
            print(f"{Colors.BRIGHT_RED}❌ {exc}{Colors.RESET}")
            return
        except Exception as exc:
            print(f"{Colors.BRIGHT_RED}❌ Could not load tracks from database: {exc}{Colors.RESET}")
            return
    elif source in ('2', 'f', 'file', 'bestand'):
        urls_path = input(
            f"{Colors.BRIGHT_CYAN}Path to URL file (Enter for default): {Colors.RESET}"
        ).strip()
        if not urls_path:
            urls_path = default_urls_file
        if not urls_path:
            print(f"{Colors.BRIGHT_RED}❌ No URL file specified.{Colors.RESET}")
            return
        urls_path = os.path.expanduser(urls_path)
        try:
            urls = load_urls_from_file(urls_path)
            print(f"{Colors.BRIGHT_GREEN}✅ {len(urls)} URL(s) loaded from {urls_path}{Colors.RESET}")
        except (OSError, ValueError) as exc:
            print(f"{Colors.BRIGHT_RED}❌ {exc}{Colors.RESET}")
            return
    else:
        urls = _read_urls_from_input()

    if not tracks_from_app and not urls:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  No URL(s) specified.{Colors.RESET}")
        return

    overwrite = input(
        f"{Colors.BRIGHT_CYAN}Overwrite existing files? (y/n): {Colors.RESET}"
    ).strip().lower() == 'y'

    tag_metadata = input(
        f"{Colors.BRIGHT_CYAN}Add ID3 metadata from filename? (y/n): {Colors.RESET}"
    ).strip().lower() != 'n'

    print(
        f"\n{Colors.BRIGHT_WHITE}Downloading "
        f"{len(tracks_from_app) or len(urls)} track(s) to:{Colors.RESET}\n"
        f"  {Colors.BRIGHT_CYAN}{directory}{Colors.RESET}\n"
    )

    if tracks_from_app:
        success_count, error_count = download_youtube_tracks(
            tracks_from_app,
            directory,
            overwrite=overwrite,
            tag_metadata=tag_metadata,
        )
    else:
        success_count, error_count = download_youtube_urls(
            urls,
            directory,
            overwrite=overwrite,
            tag_metadata=tag_metadata,
        )

    print(
        f"\n{Colors.BRIGHT_GREEN}Done: {success_count} downloaded, {error_count} failed.{Colors.RESET}"
    )
    if success_count and tracks_from_app:
        print(
            f"{Colors.DIM}Successfully downloaded tracks were removed from your todo app.{Colors.RESET}"
        )
    elif success_count:
        print(
            f"{Colors.DIM}Tip: rename files to 'Artist - Title.aiff' if metadata was not applied.{Colors.RESET}"
        )
