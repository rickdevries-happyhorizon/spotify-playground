"""Embed Spotify and audio-analysis metadata into WAV/AIFF files with logging."""

from __future__ import annotations

import csv
import os
import time
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
from spotify_playlist.spotify_track_energy import fetch_track_energies, format_energy_label
from spotify_playlist.colors import Colors
from spotify_playlist.deps import require_spotipy
from spotify_playlist.get_spotify_client import get_spotify_client
from spotify_playlist.parse_wav_filename import parse_wav_filename
from spotify_playlist.spotify_track_match import find_spotify_track, metadata_from_spotify_track
from spotify_playlist.tag_wav_metadata import apply_rekordbox_fields

STATUS_OK = 'ok'
STATUS_ERROR = 'error'

MAIN_LOG_FIELDS = (
    'timestamp',
    'index',
    'total',
    'file_path',
    'status',
    'spotify_track_id',
    'spotify_track_name',
    'applied_year',
    'applied_release_date',
    'applied_album',
    'applied_energy_label',
    'skipped_fields',
    'error',
)

SKIPPED_LOG_FIELDS = (
    'timestamp',
    'index',
    'total',
    'file_path',
    'skipped_fields',
    'spotify_track_id',
    'spotify_track_name',
)


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


def _open_batch_logs(log_stem: str) -> dict[str, Any]:
    os.makedirs(LOG_DIR, exist_ok=True)
    csv_path = os.path.join(LOG_DIR, f'{log_stem}.csv')
    text_path = os.path.join(LOG_DIR, f'{log_stem}.log')
    skipped_path = os.path.join(LOG_DIR, f'{log_stem}_skipped.csv')

    main_exists = os.path.isfile(csv_path)
    main_csv = open(csv_path, 'a', newline='', encoding='utf-8')
    main_text = open(text_path, 'a', encoding='utf-8')
    main_writer = csv.DictWriter(main_csv, fieldnames=MAIN_LOG_FIELDS)

    skipped_exists = os.path.isfile(skipped_path)
    skipped_csv = open(skipped_path, 'a', newline='', encoding='utf-8')
    skipped_writer = csv.DictWriter(skipped_csv, fieldnames=SKIPPED_LOG_FIELDS)

    if not main_exists:
        main_writer.writeheader()
        main_csv.flush()
        main_text.write(f'Spotify metadata batch started at {utc_timestamp()}\n')
        main_text.flush()

    if not skipped_exists:
        skipped_writer.writeheader()
        skipped_csv.flush()

    return {
        'csv_path': csv_path,
        'text_path': text_path,
        'skipped_path': skipped_path,
        'main_csv': main_csv,
        'main_text': main_text,
        'main_writer': main_writer,
        'skipped_csv': skipped_csv,
        'skipped_writer': skipped_writer,
    }


def _close_batch_logs(logs: dict[str, Any]) -> None:
    logs['main_csv'].close()
    logs['main_text'].close()
    logs['skipped_csv'].close()


def _log_main_row(
    logs: dict[str, Any],
    *,
    index: int,
    total: int,
    file_path: str,
    status: str,
    spotify_track: dict[str, Any] | None = None,
    applied: dict[str, Any | None] | None = None,
    skipped_fields: list[str] | None = None,
    error: str = '',
) -> None:
    applied = applied or {}
    skipped_fields = skipped_fields or []
    spotify_track_id = spotify_track.get('id', '') if spotify_track else ''
    spotify_track_name = spotify_track.get('name', '') if spotify_track else ''

    row = {
        'timestamp': utc_timestamp(),
        'index': index,
        'total': total,
        'file_path': file_path,
        'status': status,
        'spotify_track_id': spotify_track_id,
        'spotify_track_name': spotify_track_name,
        'applied_year': applied.get('year') or '',
        'applied_release_date': applied.get('release_date') or '',
        'applied_album': applied.get('album') or '',
        'applied_energy_label': applied.get('energy_label') or '',
        'skipped_fields': ';'.join(skipped_fields),
        'error': error,
    }
    logs['main_writer'].writerow(row)
    logs['main_csv'].flush()

    if status == STATUS_OK:
        logs['main_text'].write(
            f'[{index}/{total}] OK {file_path} '
            f"(applied: {', '.join(k for k, v in applied.items() if v) or 'none'}; "
            f"skipped: {', '.join(skipped_fields) or 'none'})\n"
        )
    else:
        logs['main_text'].write(f'[{index}/{total}] ERROR {file_path}: {error}\n')
    logs['main_text'].flush()


def _log_skipped_row(
    logs: dict[str, Any],
    *,
    index: int,
    total: int,
    file_path: str,
    skipped_fields: list[str],
    spotify_track: dict[str, Any] | None = None,
) -> None:
    if not skipped_fields:
        return

    row = {
        'timestamp': utc_timestamp(),
        'index': index,
        'total': total,
        'file_path': file_path,
        'skipped_fields': ';'.join(skipped_fields),
        'spotify_track_id': spotify_track.get('id', '') if spotify_track else '',
        'spotify_track_name': spotify_track.get('name', '') if spotify_track else '',
    }
    logs['skipped_writer'].writerow(row)
    logs['skipped_csv'].flush()


def process_metadata_file(sp, path: str) -> dict[str, Any]:
    """
    Collect and apply metadata for one audio file.

    Returns a result dict with keys: spotify_track, applied, skipped_fields, error.
    """
    stem = os.path.splitext(os.path.basename(path))[0]
    artists, _title = parse_wav_filename(stem)

    skipped_fields: list[str] = []
    spotify_track: dict[str, Any] | None = None
    spotify_data = {'album': None, 'release_date': None, 'year': None}

    try:
        spotify_track = spotify_call_with_retry(
            lambda: find_spotify_track(sp, artists, stem)
        )
    except Exception:
        skipped_fields.extend(['year', 'release_date', 'album', 'spotify_track'])
    else:
        if spotify_track is None:
            skipped_fields.extend(['year', 'release_date', 'album', 'spotify_track'])
        else:
            spotify_data = metadata_from_spotify_track(spotify_track)
            if spotify_data['year'] is None:
                skipped_fields.append('year')
            if spotify_data['release_date'] is None:
                skipped_fields.append('release_date')
            if spotify_data['album'] is None:
                skipped_fields.append('album')

    energy_label: str | None = None
    if spotify_track and spotify_track.get('uri'):
        try:
            energies = fetch_track_energies(sp, [spotify_track['uri']])
            energy = energies.get(spotify_track['uri'])
            if energy is not None:
                energy_label = format_energy_label(energy)
            else:
                skipped_fields.append('energy')
        except Exception:
            skipped_fields.append('energy')
    else:
        skipped_fields.append('energy')

    apply_kwargs: dict[str, Any] = {}
    applied: dict[str, Any | None] = {}

    if spotify_data['album'] is not None:
        apply_kwargs['album'] = spotify_data['album']
        applied['album'] = spotify_data['album']
    if spotify_data['release_date'] is not None:
        apply_kwargs['release_date'] = spotify_data['release_date']
        applied['release_date'] = spotify_data['release_date']
    if spotify_data['year'] is not None:
        apply_kwargs['year'] = spotify_data['year']
        applied['year'] = spotify_data['year']
    if energy_label is not None:
        apply_kwargs['label'] = energy_label
        applied['energy_label'] = energy_label

    if not apply_kwargs:
        return {
            'spotify_track': spotify_track,
            'applied': applied,
            'skipped_fields': sorted(set(skipped_fields)),
            'error': 'No metadata found to apply',
        }

    apply_rekordbox_fields(path, **apply_kwargs)
    return {
        'spotify_track': spotify_track,
        'applied': applied,
        'skipped_fields': sorted(set(skipped_fields)),
        'error': '',
    }


def run_spotify_metadata_batch(
    directory: str = DEFAULT_MUSIC_DIR,
    *,
    resume_log: str = '',
    limit: int | None = None,
) -> tuple[int, int]:
    """Apply Spotify and energy metadata to all WAV/AIFF files under directory."""
    require_spotipy()

    if not os.path.isdir(directory):
        raise NotADirectoryError(f'Directory not found: {directory}')

    audio_files = discover_audio_files(directory)
    if limit is not None:
        audio_files = audio_files[:limit]

    if not audio_files:
        print(
            f"{Colors.BRIGHT_YELLOW}⚠️  No WAV/AIFF files found in: {directory}{Colors.RESET}"
        )
        return 0, 0

    log_stem = os.path.splitext(os.path.basename(resume_log))[0] if resume_log else (
        f'spotify_metadata_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    )
    logs = _open_batch_logs(log_stem)

    completed_paths: set[str] = set()
    if resume_log:
        completed_paths = _load_completed_paths(logs['csv_path'])
        if completed_paths:
            before = len(audio_files)
            audio_files = [path for path in audio_files if path not in completed_paths]
            skipped = before - len(audio_files)
            print(
                f"{Colors.DIM}Resuming from log: {skipped} files already OK, "
                f"{len(audio_files)} remaining{Colors.RESET}"
            )

    total = len(audio_files) + len(completed_paths)
    sp = get_spotify_client()

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🏷️  Spotify Metadata Batch{Colors.RESET}")
    print(f"{Colors.DIM}Map: {directory}{Colors.RESET}")
    print(f"{Colors.DIM}Log CSV: {logs['csv_path']}{Colors.RESET}")
    print(f"{Colors.DIM}Skipped CSV: {logs['skipped_path']}{Colors.RESET}")
    print(f"{Colors.DIM}Log text: {logs['text_path']}{Colors.RESET}")
    print(f"{Colors.BRIGHT_WHITE}To process: {len(audio_files)} file(s){Colors.RESET}\n")

    success_count = 0
    error_count = 0

    try:
        for offset, path in enumerate(tqdm(audio_files, desc='Metadata', unit='track'), start=1):
            index = len(completed_paths) + offset
            try:
                result = process_metadata_file(sp, path)
                if result['error']:
                    error_count += 1
                    _log_main_row(
                        logs,
                        index=index,
                        total=total,
                        file_path=path,
                        status=STATUS_ERROR,
                        spotify_track=result['spotify_track'],
                        applied=result['applied'],
                        skipped_fields=result['skipped_fields'],
                        error=result['error'],
                    )
                else:
                    success_count += 1
                    _log_main_row(
                        logs,
                        index=index,
                        total=total,
                        file_path=path,
                        status=STATUS_OK,
                        spotify_track=result['spotify_track'],
                        applied=result['applied'],
                        skipped_fields=result['skipped_fields'],
                    )

                _log_skipped_row(
                    logs,
                    index=index,
                    total=total,
                    file_path=path,
                    skipped_fields=result['skipped_fields'],
                    spotify_track=result['spotify_track'],
                )
            except Exception as exc:
                error_count += 1
                _log_main_row(
                    logs,
                    index=index,
                    total=total,
                    file_path=path,
                    status=STATUS_ERROR,
                    error=str(exc),
                )

            time.sleep(0.05)
    finally:
        logs['main_text'].write(
            f'\nBatch finished at {utc_timestamp()}: '
            f'{success_count} ok, {error_count} errors\n'
        )
        logs['main_text'].flush()
        _close_batch_logs(logs)

    print(
        f"\n{Colors.BRIGHT_GREEN}Done: {success_count} updated, "
        f"{error_count} failed{Colors.RESET}"
    )
    print(f"{Colors.DIM}Log: {logs['csv_path']}{Colors.RESET}")
    print(f"{Colors.DIM}Skipped log: {logs['skipped_path']}{Colors.RESET}")

    if success_count:
        play_action_done()

    return success_count, error_count


def _list_recent_log_stems() -> list[str]:
    if not os.path.isdir(LOG_DIR):
        return []
    stems = [
        name[:-4]
        for name in os.listdir(LOG_DIR)
        if name.startswith('spotify_metadata_') and name.endswith('.csv')
    ]
    return sorted(stems, reverse=True)


def run_spotify_metadata(default_directory: str = '') -> None:
    """Interactive flow to apply Spotify metadata from the menu."""
    try:
        require_spotipy()
        from spotify_playlist.tag_wav_metadata import _require_mutagen

        _require_mutagen()
    except ModuleNotFoundError as exc:
        print(f"{Colors.BRIGHT_RED}❌ {exc}{Colors.RESET}")
        return

    print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🏷️  Add Spotify Metadata  🏷️{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═' * 70}{Colors.RESET}\n")
    print(
        f"{Colors.DIM}Looks up on Spotify: year, release date, album, and energy. "
        f"Missing fields are skipped and logged.{Colors.RESET}\n"
    )

    if default_directory:
        print(f"{Colors.DIM}Default directory: {default_directory}{Colors.RESET}")

    directory = input(
        f"{Colors.BRIGHT_CYAN}Directory with WAV/AIFF files (Enter for default, 'q' to go back): {Colors.RESET}"
    ).strip()

    if directory.lower() == 'q':
        return

    if not directory:
        directory = default_directory

    if not directory:
        print(f"{Colors.BRIGHT_RED}❌ No directory specified.{Colors.RESET}")
        return

    directory = os.path.expanduser(directory)

    if not os.path.isdir(directory):
        print(f"{Colors.BRIGHT_RED}❌ Directory not found: {directory}{Colors.RESET}")
        return

    try:
        file_count = len(discover_audio_files(directory))
    except Exception as exc:
        print(f"{Colors.BRIGHT_RED}❌ Error: {exc}{Colors.RESET}")
        return

    if file_count == 0:
        print(
            f"{Colors.BRIGHT_YELLOW}⚠️  No WAV/AIFF files found in: {directory}{Colors.RESET}"
        )
        return

    print(f"\n{Colors.BRIGHT_WHITE}Found: {file_count} WAV/AIFF file(s){Colors.RESET}")
    print(f"{Colors.DIM}Logs are saved in: {LOG_DIR}{Colors.RESET}")

    resume_log = ''
    recent_logs = _list_recent_log_stems()
    if recent_logs:
        resume_choice = input(
            f"\n{Colors.BRIGHT_CYAN}Resume from a previous log? (y/n): {Colors.RESET}"
        ).strip().lower()
        if resume_choice == 'y':
            print(f"\n{Colors.BRIGHT_WHITE}Recent logs:{Colors.RESET}")
            for index, stem in enumerate(recent_logs[:5], start=1):
                print(f"  {index}. {stem}")
            log_choice = input(
                f"{Colors.BRIGHT_CYAN}Choose number (Enter for newest, 'q' to start fresh): {Colors.RESET}"
            ).strip()
            if log_choice.lower() == 'q' or not log_choice:
                resume_log = recent_logs[0] if log_choice != 'q' and not log_choice else ''
            else:
                try:
                    resume_log = recent_logs[int(log_choice) - 1]
                except (ValueError, IndexError):
                    print(f"{Colors.BRIGHT_RED}❌ Invalid choice.{Colors.RESET}")
                    return

    confirm = input(
        f"\n{Colors.BRIGHT_CYAN}Fetch and apply metadata to {file_count} file(s)? (y/n): {Colors.RESET}"
    ).strip().lower()

    if confirm != 'y':
        print(f"{Colors.DIM}Cancelled.{Colors.RESET}")
        return

    try:
        run_spotify_metadata_batch(directory, resume_log=resume_log)
    except KeyboardInterrupt:
        print(
            f"\n{Colors.BRIGHT_YELLOW}Interrupted. Use run_spotify_metadata.py --resume-log to continue via the log.{Colors.RESET}"
        )
    except Exception as exc:
        print(f"{Colors.BRIGHT_RED}❌ Error: {exc}{Colors.RESET}")

    print(
        f"\n{Colors.DIM}Tip: in Rekordbox right-click the tracks → Reload Tag to load the metadata.{Colors.RESET}"
    )
