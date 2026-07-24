from datetime import datetime, timedelta

from spotify_playlist.deps import SpotifyException


def _parse_release_date(release_date: str) -> datetime | None:
    if not release_date:
        return None
    try:
        if len(release_date) == 4:
            return datetime(int(release_date), 1, 1)
        if len(release_date) == 7:
            year, month = release_date.split("-")
            return datetime(int(year), int(month), 1)
        return datetime.strptime(release_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def get_artist_new_releases(sp, artist_id, days_back=30):
    """Fetches new releases from an artist within the specified number of days."""
    new_tracks = {}
    try:
        cutoff_date = datetime.now() - timedelta(days=days_back)
        offset = 0

        while True:
            page = sp.artist_albums(
                artist_id,
                album_type="album,single",
                limit=50,
                offset=offset,
            )
            items = page.get("items") or []
            if not items:
                break

            parsed_any = False
            page_all_too_old = True

            for album in items:
                release_dt = _parse_release_date(album.get("release_date", ""))
                if release_dt is None:
                    continue

                parsed_any = True
                if release_dt < cutoff_date:
                    continue

                page_all_too_old = False
                album_tracks = sp.album_tracks(album["id"])
                for track_item in album_tracks.get("items") or []:
                    if track_item and track_item.get("uri"):
                        uri = track_item["uri"]
                        artists = ", ".join(
                            artist["name"] for artist in track_item.get("artists", [])
                        )
                        new_tracks[uri] = {
                            "name": track_item.get("name", "Unknown"),
                            "artists": artists,
                            "album": album.get("name", "Unknown"),
                            "release_date": album.get("release_date", ""),
                        }

            if parsed_any and page_all_too_old:
                break
            if not page.get("next"):
                break
            offset += len(items)

        return new_tracks
    except SpotifyException as e:
        print(f"❌ Spotify API error fetching releases for artist {artist_id}: {e}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected error fetching releases: {e}")
        return {}
