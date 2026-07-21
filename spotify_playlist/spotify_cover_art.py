"""Embed Spotify album art into WAV/AIFF files with resumable logging."""

from __future__ import annotations

import csv
import os
import time
import urllib.request
from datetime import datetime
from typing import Any, TextIO

from tqdm import tqdm

from spotify_playlist.action_sound import play_action_done
from spotify_playlist.audio_batch import (
    DEFAULT_MUSIC_DIR,
    LOG_DIR,
    discover_audio_files,
    spotify_call_with_retry,
    utc_timestamp,
)
from spotify_playlist.colors import Colors
from spotify_playlist.deps import require_spotipy
from spotify_playlist.get_spotify_client import get_spotify_client
from spotify_playlist.parse_wav_filename import parse_wav_filename
from spotify_playlist.spotify_track_match import artist_names_from_track, find_spotify_track
from spotify_playlist.tag_wav_metadata import apply_cover_art, remove_cover_art

CSV_FIELDS = (
    'timestamp',
    'index',
    'total',
    'file_path',
    'status',
    'spotify_track_id',
    'spotify_track_name',
    'spotify_artist_names',
    'error',
)

STATUS_OK = 'ok'
STATUS_ERROR = 'error'


def _album_art_url(track: dict[str, Any]) -> str | None:
    images = track.get('album', {}).get('images') or []
    if not images:
        return None
    return images[0].get('url')


def fetch_image_bytes(url: str, *, timeout: float = 30.0) -> bytes:
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'spotify-playground/1.0'},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _load_completed_paths(log_csv_path: str) -> set[str]:
    if not os.path.isfile(log_csv_path):
        return set()

    completed: set[str] = set()
    with open(log_csv_path, newline='', encoding='utf-8') as fileobj:
        reader = csv.DictReader(fileobj)
        for row in reader:
            if row.get('status') == STATUS_OK and row.get('file_path'):
                completed.add(row['file_path'])
    return completed


def _open_log_files(log_stem: str) -> tuple[str, str, TextIO, TextIO, csv.DictWriter]:
    os.makedirs(LOG_DIR, exist_ok=True)
    csv_path = os.path.join(LOG_DIR, f'{log_stem}.csv')
    text_path = os.path.join(LOG_DIR, f'{log_stem}.log')

    csv_exists = os.path.isfile(csv_path)
    csv_file = open(csv_path, 'a', newline='', encoding='utf-8')
    text_file = open(text_path, 'a', encoding='utf-8')
    writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
    if not csv_exists:
        writer.writeheader()
        csv_file.flush()
        text_file.write(f'Spotify cover art batch started at {utc_timestamp()}\n')
        text_file.flush()

    return csv_path, text_path, csv_file, text_file, writer


def _log_row(
    writer: csv.DictWriter,
    csv_file: TextIO,
    text_file: TextIO,
    *,
    index: int,
    total: int,
    file_path: str,
    status: str,
    spotify_track: dict[str, Any] | None = None,
    error: str = '',
) -> None:
    spotify_track_id = spotify_track.get('id', '') if spotify_track else ''
    spotify_track_name = spotify_track.get('name', '') if spotify_track else ''
    spotify_artist_names = ', '.join(artist_names_from_track(spotify_track)) if spotify_track else ''

    row = {
        'timestamp': utc_timestamp(),
        'index': index,
        'total': total,
        'file_path': file_path,
        'status': status,
        'spotify_track_id': spotify_track_id,
        'spotify_track_name': spotify_track_name,
        'spotify_artist_names': spotify_artist_names,
        'error': error,
    }
    writer.writerow(row)
    csv_file.flush()

    if status == STATUS_OK:
        text_file.write(
            f'[{index}/{total}] OK {file_path} -> {spotify_track_name} ({spotify_track_id})\n'
        )
    else:
        text_file.write(f'[{index}/{total}] ERROR {file_path}: {error}\n')
    text_file.flush()


def process_file(sp, path: str) -> tuple[dict[str, Any] | None, str | None]:
    """
    Clear existing cover art, fetch Spotify art, and embed it.

    Returns (spotify_track, error_message). error_message is set on failure.
    """
    stem = os.path.splitext(os.path.basename(path))[0]
    artists, _title = parse_wav_filename(stem)

    remove_cover_art(path)

    track = spotify_call_with_retry(lambda: find_spotify_track(sp, artists, stem))
    if track is None:
        return None, 'Geen passende Spotify track gevonden'

    art_url = _album_art_url(track)
    if not art_url:
        return track, 'Spotify track heeft geen album artwork'

    image_bytes = spotify_call_with_retry(lambda: fetch_image_bytes(art_url))
    if not image_bytes:
        return track, 'Album artwork download leverde lege data op'

    mime = 'image/jpeg'
    if art_url.lower().endswith('.png'):
        mime = 'image/png'

    apply_cover_art(path, image_bytes, mime=mime)
    return track, None


def run_spotify_cover_art_batch(
    directory: str = DEFAULT_MUSIC_DIR,
    *,
    resume_log: str = '',
    limit: int | None = None,
) -> tuple[int, int]:
    """
    Embed Spotify cover art for all WAV/AIFF files under directory.

    Returns (success_count, error_count).
    """
    require_spotipy()

    if not os.path.isdir(directory):
        raise NotADirectoryError(f'Map niet gevonden: {directory}')

    audio_files = discover_audio_files(directory)
    if limit is not None:
        audio_files = audio_files[:limit]

    if not audio_files:
        print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen WAV/AIFF bestanden gevonden in: {directory}{Colors.RESET}")
        return 0, 0

    log_stem = os.path.splitext(os.path.basename(resume_log))[0] if resume_log else (
        f'spotify_cover_art_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    )
    csv_path, text_path, csv_file, text_file, writer = _open_log_files(log_stem)

    completed_paths: set[str] = set()
    if resume_log:
        completed_paths = _load_completed_paths(csv_path)
        if completed_paths:
            before = len(audio_files)
            audio_files = [path for path in audio_files if path not in completed_paths]
            skipped = before - len(audio_files)
            print(
                f"{Colors.DIM}Hervatten vanaf log: {skipped} bestanden al OK, "
                f"{len(audio_files)} resterend{Colors.RESET}"
            )

    total = len(audio_files) + len(completed_paths)
    sp = get_spotify_client()

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🖼️  Spotify Cover Art Batch{Colors.RESET}")
    print(f"{Colors.DIM}Map: {directory}{Colors.RESET}")
    print(f"{Colors.DIM}Log CSV: {csv_path}{Colors.RESET}")
    print(f"{Colors.DIM}Log tekst: {text_path}{Colors.RESET}")
    print(f"{Colors.BRIGHT_WHITE}Te verwerken: {len(audio_files)} bestand(en){Colors.RESET}\n")

    success_count = 0
    error_count = 0

    try:
        for offset, path in enumerate(tqdm(audio_files, desc='Cover art', unit='track'), start=1):
            index = len(completed_paths) + offset
            try:
                track, error = process_file(sp, path)
                if error:
                    error_count += 1
                    _log_row(
                        writer,
                        csv_file,
                        text_file,
                        index=index,
                        total=total,
                        file_path=path,
                        status=STATUS_ERROR,
                        spotify_track=track,
                        error=error,
                    )
                else:
                    success_count += 1
                    _log_row(
                        writer,
                        csv_file,
                        text_file,
                        index=index,
                        total=total,
                        file_path=path,
                        status=STATUS_OK,
                        spotify_track=track,
                    )
            except Exception as exc:
                error_count += 1
                try:
                    remove_cover_art(path)
                except Exception:
                    pass
                _log_row(
                    writer,
                    csv_file,
                    text_file,
                    index=index,
                    total=total,
                    file_path=path,
                    status=STATUS_ERROR,
                    error=str(exc),
                )

            time.sleep(0.05)
    finally:
        text_file.write(
            f'\nBatch finished at {utc_timestamp()}: '
            f'{success_count} ok, {error_count} errors\n'
        )
        text_file.flush()
        csv_file.close()
        text_file.close()

    print(
        f"\n{Colors.BRIGHT_GREEN}Klaar: {success_count} met cover art, "
        f"{error_count} zonder cover art (fout){Colors.RESET}"
    )
    print(f"{Colors.DIM}Log: {csv_path}{Colors.RESET}")

    if success_count:
        play_action_done()

    return success_count, error_count


def _list_recent_log_stems() -> list[str]:
    if not os.path.isdir(LOG_DIR):
        return []
    stems = [
        name[:-4]
        for name in os.listdir(LOG_DIR)
        if name.startswith('spotify_cover_art_') and name.endswith('.csv')
    ]
    return sorted(stems, reverse=True)


def run_spotify_cover_art(default_directory: str = '') -> None:
    """Interactive flow to embed Spotify cover art from the menu."""
    try:
        require_spotipy()
        from spotify_playlist.tag_wav_metadata import _require_mutagen

        _require_mutagen()
    except ModuleNotFoundError as exc:
        print(f"{Colors.BRIGHT_RED}❌ {exc}{Colors.RESET}")
        return

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🖼️  Spotify Cover Art Toevoegen  🖼️{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}\n")
    print(
        f"{Colors.DIM}Zoekt cover art op Spotify op basis van bestandsnamen "
        f"(Artiest - Titel). Bestaande cover art wordt overschreven. "
        f"Bij fouten blijft het bestand zonder cover art.{Colors.RESET}\n"
    )

    if default_directory:
        print(f"{Colors.DIM}Standaard map: {default_directory}{Colors.RESET}")

    directory = input(
        f"{Colors.BRIGHT_CYAN}Map met WAV/AIFF bestanden (Enter voor standaard, 'q' om terug): {Colors.RESET}"
    ).strip()

    if directory.lower() == 'q':
        return

    if not directory:
        directory = default_directory

    if not directory:
        print(f"{Colors.BRIGHT_RED}❌ Geen map opgegeven.{Colors.RESET}")
        return

    directory = os.path.expanduser(directory)

    if not os.path.isdir(directory):
        print(f"{Colors.BRIGHT_RED}❌ Map niet gevonden: {directory}{Colors.RESET}")
        return

    try:
        file_count = len(discover_audio_files(directory))
    except Exception as exc:
        print(f"{Colors.BRIGHT_RED}❌ Fout: {exc}{Colors.RESET}")
        return

    if file_count == 0:
        print(
            f"{Colors.BRIGHT_YELLOW}⚠️  Geen WAV/AIFF bestanden gevonden in: {directory}{Colors.RESET}"
        )
        return

    print(f"\n{Colors.BRIGHT_WHITE}Gevonden: {file_count} WAV/AIFF bestand(en){Colors.RESET}")
    print(f"{Colors.DIM}Logs worden opgeslagen in: {LOG_DIR}{Colors.RESET}")

    resume_log = ''
    recent_logs = _list_recent_log_stems()
    if recent_logs:
        resume_choice = input(
            f"\n{Colors.BRIGHT_CYAN}Hervatten vanaf eerdere log? (j/n): {Colors.RESET}"
        ).strip().lower()
        if resume_choice == 'j':
            print(f"\n{Colors.BRIGHT_WHITE}Recente logs:{Colors.RESET}")
            for index, stem in enumerate(recent_logs[:5], start=1):
                print(f"  {index}. {stem}")
            log_choice = input(
                f"{Colors.BRIGHT_CYAN}Kies nummer (Enter voor nieuwste, 'q' om nieuw te starten): {Colors.RESET}"
            ).strip()
            if log_choice.lower() == 'q' or not log_choice:
                resume_log = recent_logs[0] if log_choice != 'q' and not log_choice else ''
            else:
                try:
                    resume_log = recent_logs[int(log_choice) - 1]
                except (ValueError, IndexError):
                    print(f"{Colors.BRIGHT_RED}❌ Ongeldige keuze.{Colors.RESET}")
                    return

    confirm = input(
        f"\n{Colors.BRIGHT_CYAN}Cover art ophalen en toepassen op {file_count} bestand(en)? (j/n): {Colors.RESET}"
    ).strip().lower()

    if confirm != 'j':
        print(f"{Colors.DIM}Geannuleerd.{Colors.RESET}")
        return

    try:
        run_spotify_cover_art_batch(directory, resume_log=resume_log)
    except KeyboardInterrupt:
        print(f"\n{Colors.BRIGHT_YELLOW}Afgebroken. Gebruik optie 11 om te hervatten via de log.{Colors.RESET}")
    except Exception as exc:
        print(f"{Colors.BRIGHT_RED}❌ Fout: {exc}{Colors.RESET}")
