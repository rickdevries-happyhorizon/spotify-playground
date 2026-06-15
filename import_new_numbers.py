#!/usr/bin/env python3
"""Import reference data from new.numbers into the new_tracks table."""
from __future__ import annotations

import sys
from pathlib import Path

from db_store import save_new_tracks

DEFAULT_NUMBERS_FILE = Path(__file__).resolve().parent / "new.numbers"


def load_tracks_from_numbers(path: Path) -> list[dict]:
    try:
        from numbers_parser import Document
    except ImportError as e:
        raise ImportError(
            "numbers-parser is required to read .numbers files. "
            "Install with: pip install numbers-parser"
        ) from e

    doc = Document(str(path))
    table = doc.sheets[0].tables[0]
    tracks: list[dict] = []

    for row_idx in range(1, table.num_rows):
        track = table.cell(row_idx, 0).value
        reference_url = table.cell(row_idx, 1).value
        if not track or not str(track).strip():
            continue
        tracks.append(
            {
                "track": str(track).strip(),
                "reference_url": str(reference_url).strip() if reference_url else None,
            }
        )

    return tracks


def main() -> int:
    numbers_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_NUMBERS_FILE
    if not numbers_path.is_file():
        print(f"❌ Bestand niet gevonden: {numbers_path}")
        return 1

    tracks = load_tracks_from_numbers(numbers_path)
    if not tracks:
        print(f"⚠️  Geen tracks gevonden in {numbers_path}")
        return 1

    inserted, _skipped = save_new_tracks(tracks, replace=True)

    print(f"✅ {inserted} tracks geïmporteerd uit {numbers_path.name}")
    print(f"   Bestand: {numbers_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
