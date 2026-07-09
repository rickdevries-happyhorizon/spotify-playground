"""Strip radio edit/mix suffixes from track display names."""
from __future__ import annotations

import re

_RADIO_SUFFIX_RE = re.compile(
    r'(?:\s*-\s*radio\s+(?:edit|mix)|\s*\(radio\s+(?:edit|mix)\))\s*$',
    re.IGNORECASE,
)


def normalize_track_name(name: str) -> str:
    """Remove trailing 'Radio Edit' or 'Radio Mix' suffixes from a track name."""
    if not name:
        return name

    cleaned = _RADIO_SUFFIX_RE.sub('', name)
    return re.sub(r'\s+', ' ', cleaned).strip()
