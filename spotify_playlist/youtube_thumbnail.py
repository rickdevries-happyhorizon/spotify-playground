"""Fetch YouTube thumbnails and prepare square cover art."""

from __future__ import annotations

import io
import urllib.error
import urllib.request
from typing import Any


def thumbnail_url_from_info(info: dict[str, Any]) -> str | None:
    """Return the best available thumbnail URL from a yt-dlp info dict."""
    thumbnail = info.get('thumbnail')
    if thumbnail:
        return thumbnail

    thumbnails = info.get('thumbnails') or []
    if thumbnails:
        best = max(thumbnails, key=lambda item: (item.get('height') or 0, item.get('width') or 0))
        url = best.get('url') or best.get('thumbnail')
        if url:
            return url

    video_id = info.get('id')
    if not video_id:
        return None

    return f'https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg'


def fetch_thumbnail_bytes(url: str) -> bytes | None:
    """Download thumbnail bytes, trying fallback YouTube sizes when needed."""
    urls = [url]
    if '/maxresdefault.' in url:
        urls.append(url.replace('/maxresdefault.', '/hqdefault.'))
        urls.append(url.replace('/maxresdefault.', '/mqdefault.'))

    for candidate in urls:
        try:
            request = urllib.request.Request(
                candidate,
                headers={'User-Agent': 'Mozilla/5.0'},
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                data = response.read()
        except (OSError, urllib.error.HTTPError, urllib.error.URLError):
            continue

        if len(data) > 1000:
            return data

    return None


def square_center_crop(image_bytes: bytes, size: int = 600) -> bytes:
    """Crop an image to a centered square and resize it."""
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Pillow is niet geïnstalleerd. Voer uit: pip install -r requirements.txt"
        ) from exc

    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    cropped = image.crop((left, top, left + side, top + side))
    if size and (cropped.width != size or cropped.height != size):
        cropped = cropped.resize((size, size), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    cropped.save(output, format='JPEG', quality=90, optimize=True)
    return output.getvalue()


def cover_art_from_youtube_info(info: dict[str, Any], *, size: int = 600) -> bytes | None:
    """Fetch and square-crop a YouTube thumbnail for use as cover art."""
    url = thumbnail_url_from_info(info)
    if not url:
        return None

    image_bytes = fetch_thumbnail_bytes(url)
    if not image_bytes:
        return None

    return square_center_crop(image_bytes, size=size)
