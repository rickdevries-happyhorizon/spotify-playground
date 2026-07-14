"""Download YouTube audio as AIFF files using yt-dlp and ffmpeg."""

import os
import re
import shutil
import subprocess
from typing import Optional

from db_store import delete_new_track, load_new_tracks
from spotify_playlist.action_sound import play_action_done
from spotify_playlist.colors import Colors
from spotify_playlist.parse_wav_filename import parse_wav_filename
from spotify_playlist.tag_wav_metadata import apply_aiff_metadata

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _require_yt_dlp():
    try:
        import yt_dlp
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "yt-dlp is niet geïnstalleerd. Voer uit: pip install -r requirements.txt"
        ) from exc
    return yt_dlp


def _require_ffmpeg() -> None:
    if not shutil.which('ffmpeg'):
        raise FileNotFoundError(
            "ffmpeg is niet geïnstalleerd. Op macOS: brew install ffmpeg"
        )


def _build_youtube_ydl_opts(**extra) -> dict:
    """Base yt-dlp options for reliable YouTube extraction."""
    opts: dict = {
        'noplaylist': True,
        'windowsfilenames': True,
        'quiet': False,
        'no_warnings': False,
    }

    node_path = shutil.which('node')
    if node_path:
        opts['js_runtimes'] = {'node': {'path': node_path}}
    elif shutil.which('deno'):
        opts['js_runtimes'] = {'deno': {'path': shutil.which('deno')}}
    else:
        opts['remote_components'] = ['ejs:github']

    opts.update(extra)
    return opts


def _safe_filename_stem(name: str) -> str:
    cleaned = _INVALID_FILENAME_CHARS.sub('', name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip().strip('.')
    return cleaned or 'unknown'


AUDIO_EXTENSION = '.aiff'


def _tag_audio_from_filename(path: str) -> None:
    stem = os.path.splitext(os.path.basename(path))[0]
    artists, title = parse_wav_filename(stem)
    apply_aiff_metadata(path, artists, title)


def _convert_wav_to_aiff(wav_path: str, aiff_path: str) -> None:
    """Convert a WAV file to AIFF using ffmpeg."""
    _require_ffmpeg()
    result = subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-i',
            wav_path,
            '-ar',
            '44100',
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
        raise RuntimeError(stderr or 'ffmpeg AIFF-conversie mislukt')


def download_youtube_to_aiff(
    url: str,
    output_dir: str,
    *,
    output_name: Optional[str] = None,
    overwrite: bool = False,
    tag_metadata: bool = True,
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
        postprocessors=[{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        postprocessor_args={
            'ffmpeg': ['-ar', '44100'],
        },
    )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            return None

        path = ydl.prepare_filename(info)
        wav_path = os.path.splitext(path)[0] + '.wav'
        audio_path = os.path.splitext(path)[0] + AUDIO_EXTENSION

    if not os.path.isfile(wav_path):
        print(f"{Colors.BRIGHT_RED}❌ WAV bestand niet gevonden na download: {wav_path}{Colors.RESET}")
        return None

    try:
        _convert_wav_to_aiff(wav_path, audio_path)
    except RuntimeError as exc:
        print(f"{Colors.BRIGHT_RED}❌ AIFF-conversie mislukt: {exc}{Colors.RESET}")
        return None
    finally:
        if os.path.isfile(wav_path):
            os.remove(wav_path)

    if not os.path.isfile(audio_path):
        print(f"{Colors.BRIGHT_RED}❌ AIFF bestand niet gevonden na download: {audio_path}{Colors.RESET}")
        return None

    if tag_metadata:
        try:
            _tag_audio_from_filename(audio_path)
            print(f"    {Colors.BRIGHT_GREEN}✅ ID3 metadata toegevoegd{Colors.RESET}")
        except Exception as exc:
            print(
                f"    {Colors.BRIGHT_YELLOW}⚠️  Metadata niet toegepast "
                f"(bestandsnaam moet 'Artiest - Titel.aiff' zijn): {exc}{Colors.RESET}"
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
                print(f"    {Colors.BRIGHT_GREEN}✅ Opgeslagen: {audio_path}{Colors.RESET}")
                success_count += 1
            else:
                error_count += 1
        except Exception as exc:
            print(f"    {Colors.BRIGHT_RED}❌ Fout: {exc}{Colors.RESET}")
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
            "Geen tracks met YouTube URL gevonden in de app. "
            "Voeg eerst reference URL's toe in de new tracks todo."
        )
    return with_url


def download_youtube_tracks(
    tracks: list[dict],
    output_dir: str,
    *,
    overwrite: bool = False,
    tag_metadata: bool = True,
) -> tuple[int, int]:
    """Download tracks from the app. Successfully downloaded rows are removed from the database."""
    success_count = 0
    error_count = 0

    for index, track in enumerate(tracks, start=1):
        track_name = track.get('track', 'unknown')
        url = track.get('reference_url')
        print(
            f"\n{Colors.BRIGHT_WHITE}[{index}/{len(tracks)}]{Colors.RESET} "
            f"{Colors.BRIGHT_CYAN}{track_name}{Colors.RESET}"
        )
        print(f"    {Colors.DIM}{url}{Colors.RESET}")
        try:
            audio_path = download_youtube_to_aiff(
                url,
                output_dir,
                output_name=track_name,
                overwrite=overwrite,
                tag_metadata=tag_metadata,
            )
            if audio_path:
                print(f"    {Colors.BRIGHT_GREEN}✅ Opgeslagen: {audio_path}{Colors.RESET}")
                track_id = track.get('id')
                if track_id is not None:
                    try:
                        if delete_new_track(track_id):
                            print(
                                f"    {Colors.BRIGHT_GREEN}✅ Verwijderd uit database{Colors.RESET}"
                            )
                        else:
                            print(
                                f"    {Colors.BRIGHT_YELLOW}⚠️  Track niet gevonden in database "
                                f"(id={track_id}){Colors.RESET}"
                            )
                    except Exception as exc:
                        print(
                            f"    {Colors.BRIGHT_YELLOW}⚠️  Kon track niet verwijderen uit "
                            f"database: {exc}{Colors.RESET}"
                        )
                success_count += 1
            else:
                error_count += 1
        except Exception as exc:
            print(f"    {Colors.BRIGHT_RED}❌ Fout: {exc}{Colors.RESET}")
            error_count += 1

    if success_count:
        play_action_done()

    return success_count, error_count


def load_urls_from_file(path: str) -> list[str]:
    """Load YouTube URLs from a text file (one per line, # comments allowed)."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Bestand niet gevonden: {path}")

    urls: list[str] = []
    with open(path, encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, start=1):
            cleaned = line.strip()
            if not cleaned or cleaned.startswith('#'):
                continue
            urls.append(cleaned)

    if not urls:
        raise ValueError(f"Geen URL's gevonden in: {path}")

    return urls


def _read_urls_from_input() -> list[str]:
    print(
        f"\n{Colors.DIM}Plak YouTube URL(s), één per regel. "
        f"Druk Enter op een lege regel om te starten.{Colors.RESET}\n"
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
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎵  YouTube naar AIFF Downloaden  🎵{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(
        f"\n{Colors.DIM}Alleen voor persoonlijk gebruik. "
        f"Download geen auteursrechtelijk beschermd materiaal zonder toestemming.{Colors.RESET}"
    )

    if default_directory:
        directory = os.path.abspath(os.path.expanduser(default_directory))
        os.makedirs(directory, exist_ok=True)
        print(
            f"\n{Colors.BRIGHT_CYAN}Opslagmap:{Colors.RESET} "
            f"{Colors.BRIGHT_WHITE}{directory}{Colors.RESET}"
        )
    else:
        directory = input(
            f"\n{Colors.BRIGHT_CYAN}Opslagmap ('q' om terug): {Colors.RESET}"
        ).strip()

        if directory.lower() == 'q':
            return

        if not directory:
            print(f"{Colors.BRIGHT_RED}❌ Geen map opgegeven.{Colors.RESET}")
            return

        directory = os.path.abspath(os.path.expanduser(directory))
        os.makedirs(directory, exist_ok=True)

    if default_urls_file:
        print(f"{Colors.DIM}Standaard URL-bestand: {default_urls_file}{Colors.RESET}")

    source = input(
        f"\n{Colors.BRIGHT_CYAN}URL-bron: [Enter] app-database  [1] plakken  [2] bestand: {Colors.RESET}"
    ).strip().lower()

    tracks_from_app: list[dict] = []
    urls: list[str] = []

    if source in ('', 'app', 'database', 'db'):
        try:
            tracks_from_app = load_tracks_from_app()
            print(
                f"\n{Colors.BRIGHT_GREEN}✅ {len(tracks_from_app)} track(s) met YouTube URL "
                f"geladen uit de app{Colors.RESET}"
            )
            print(
                f"{Colors.DIM}Succesvol gedownloade tracks worden automatisch uit de "
                f"database verwijderd.{Colors.RESET}\n"
            )
            for track in tracks_from_app:
                print(f"  • {track['track']}")
                print(f"    {Colors.DIM}{track['reference_url']}{Colors.RESET}")
        except ValueError as exc:
            print(f"{Colors.BRIGHT_RED}❌ {exc}{Colors.RESET}")
            return
        except Exception as exc:
            print(f"{Colors.BRIGHT_RED}❌ Kon tracks niet laden uit database: {exc}{Colors.RESET}")
            return
    elif source in ('2', 'f', 'file', 'bestand'):
        urls_path = input(
            f"{Colors.BRIGHT_CYAN}Pad naar URL-bestand (Enter voor standaard): {Colors.RESET}"
        ).strip()
        if not urls_path:
            urls_path = default_urls_file
        if not urls_path:
            print(f"{Colors.BRIGHT_RED}❌ Geen URL-bestand opgegeven.{Colors.RESET}")
            return
        urls_path = os.path.expanduser(urls_path)
        try:
            urls = load_urls_from_file(urls_path)
            print(f"{Colors.BRIGHT_GREEN}✅ {len(urls)} URL(s) geladen uit {urls_path}{Colors.RESET}")
        except (OSError, ValueError) as exc:
            print(f"{Colors.BRIGHT_RED}❌ {exc}{Colors.RESET}")
            return
    else:
        urls = _read_urls_from_input()

    if not tracks_from_app and not urls:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen URL(s) opgegeven.{Colors.RESET}")
        return

    overwrite = input(
        f"{Colors.BRIGHT_CYAN}Bestaande bestanden overschrijven? (j/n): {Colors.RESET}"
    ).strip().lower() == 'j'

    tag_metadata = input(
        f"{Colors.BRIGHT_CYAN}ID3 metadata toevoegen vanuit bestandsnaam? (j/n): {Colors.RESET}"
    ).strip().lower() != 'n'

    print(
        f"\n{Colors.BRIGHT_WHITE}Downloaden van "
        f"{len(tracks_from_app) or len(urls)} track(s) naar:{Colors.RESET}\n"
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
        f"\n{Colors.BRIGHT_GREEN}Klaar: {success_count} gedownload, {error_count} mislukt.{Colors.RESET}"
    )
    if success_count and tracks_from_app:
        print(
            f"{Colors.DIM}Succesvol gedownloade tracks zijn uit je todo-app verwijderd.{Colors.RESET}"
        )
    elif success_count:
        print(
            f"{Colors.DIM}Tip: gebruik menu-optie 8 om metadata later aan te passen, "
            f"of hernoem bestanden naar 'Artiest - Titel.aiff'.{Colors.RESET}"
        )
