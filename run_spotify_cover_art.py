#!/usr/bin/env python3
"""One-time batch: embed Spotify album art into WAV/AIFF files."""

from __future__ import annotations

import argparse
import sys

from spotify_playlist.spotify_cover_art import DEFAULT_MUSIC_DIR, run_spotify_cover_art_batch


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Embed Spotify album art into WAV/AIFF files with resumable logging.',
    )
    parser.add_argument(
        '--directory',
        default=DEFAULT_MUSIC_DIR,
        help=f'Root directory with audio files (default: {DEFAULT_MUSIC_DIR})',
    )
    parser.add_argument(
        '--resume-log',
        default='',
        help='Basename of an existing log in logs/ to resume (without extension)',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Process only the first N files (for testing)',
    )
    args = parser.parse_args()

    try:
        success_count, error_count = run_spotify_cover_art_batch(
            args.directory,
            resume_log=args.resume_log,
            limit=args.limit,
        )
    except KeyboardInterrupt:
        print('\nInterrupted. Use --resume-log to continue.')
        return 130
    except Exception as exc:
        print(f'Error: {exc}')
        return 1

    return 0 if error_count == 0 or success_count > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
