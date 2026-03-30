import os
import csv
import traceback
from datetime import datetime, timedelta

from db_store import load_tracking_start_date, save_tracking_start_date

from spotify_playlist.colors import Colors
from spotify_playlist.deps import SpotifyException
from spotify_playlist.get_playlist_tracks_since_date import get_playlist_tracks_since_date


def export_new_tracks_since_date(sp, playlist_ids, since_date=None, output_file=None):
    """Exporteert nieuwe tracks die sinds een specifieke datum zijn toegevoegd aan playlists.

    Args:
        sp: Spotify client
        playlist_ids: List van playlist ID's om te controleren
        since_date: datetime object - als None, wordt de opgeslagen start datum gebruikt of vandaag - 7 dagen
        output_file: Optionele bestandsnaam voor CSV export
    """
    try:
        # Laad opgeslagen start datum
        saved_start_date = load_tracking_start_date()

        # Bepaal sinds welke datum we moeten kijken
        if since_date is None:
            # Gebruik de opgeslagen start datum, of standaard 7 dagen terug
            if saved_start_date:
                since_date = saved_start_date
            else:
                since_date = datetime.now() - timedelta(days=7)
                print(f"{Colors.BRIGHT_YELLOW}⚠️  Geen start datum gevonden. Gebruik standaard: {since_date.strftime('%Y-%m-%d')}{Colors.RESET}")

        # Vandaag is de einddatum
        today = datetime.now()

        # Waarschuwing als start datum gelijk is aan vandaag (geen bereik)
        if since_date.date() == today.date():
            print(f"{Colors.BRIGHT_YELLOW}⚠️  Start datum is vandaag. Er worden alleen tracks van vandaag gecontroleerd.{Colors.RESET}")
            print(f"{Colors.DIM}   Als je tracks van eerdere dagen wilt zien, stel een eerdere start datum in.{Colors.RESET}\n")

        print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}🔍  Nieuwe Tracks Van {since_date.strftime('%Y-%m-%d')} Tot {today.strftime('%Y-%m-%d')}  🔍{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}{'═'*70}{Colors.RESET}\n")

        all_new_tracks = []
        playlist_info_map = {}

        # Doorloop elke playlist
        for playlist_id in playlist_ids:
            try:
                # Haal playlist naam op
                playlist_info = sp.playlist(playlist_id, fields='name')
                playlist_name = playlist_info['name']
                playlist_info_map[playlist_id] = playlist_name

                print(f"{Colors.BRIGHT_CYAN}📋 Controleer playlist: {Colors.BRIGHT_WHITE}{playlist_name}{Colors.RESET}")
                print(f"{Colors.DIM}   Periode: {since_date.strftime('%Y-%m-%d %H:%M:%S')} tot {today.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

                # Eerst checken of we toegang hebben tot added_at door een test query te doen
                try:
                    test_results = sp.playlist_items(playlist_id, fields='items.added_at,items.track.uri', limit=1)
                    has_added_at_access = False
                    if test_results and 'items' in test_results and len(test_results['items']) > 0:
                        first_item = test_results['items'][0]
                        if 'added_at' in first_item and first_item['added_at'] is not None:
                            has_added_at_access = True

                    if not has_added_at_access:
                        print(f"{Colors.BRIGHT_RED}   ❌ GEEN TOEGANG TOT added_at VELD!{Colors.RESET}")
                        print(f"{Colors.BRIGHT_YELLOW}   ⚠️  De Spotify API geeft geen 'added_at' informatie voor deze playlist.{Colors.RESET}")
                        print(f"{Colors.DIM}   Mogelijke oorzaken:{Colors.RESET}")
                        print(f"{Colors.DIM}   - Je bent niet de eigenaar van deze playlist{Colors.RESET}")
                        print(f"{Colors.DIM}   - Je hebt geen collaborator rechten{Colors.RESET}")
                        print(f"{Colors.DIM}   - De playlist is public maar je hebt geen schrijfrechten{Colors.RESET}")
                        print(f"{Colors.DIM}   Oplossing: Zorg dat je eigenaar of collaborator bent van de playlist.{Colors.RESET}")
                        continue
                except Exception as e:
                    print(f"{Colors.BRIGHT_YELLOW}   ⚠️  Kon toegang tot added_at niet verifiëren: {e}{Colors.RESET}")

                # Gebruik alleen datum (zonder tijd) voor vergelijking
                since_date_only = since_date.date()
                today_date_only = today.date()

                # Haal nieuwe tracks op sinds de start datum (gebruik start van dag voor query)
                since_date_for_query = since_date.replace(hour=0, minute=0, second=0, microsecond=0)
                # Gebruik debug mode om te zien wat er gebeurt
                new_tracks = get_playlist_tracks_since_date(
                    sp, playlist_id, since_date_for_query, return_track_info=True, debug=True
                )

                print(f"{Colors.DIM}   Totaal tracks gevonden na {since_date_only}: {len(new_tracks)}{Colors.RESET}")

                # Filter tracks die tussen start_date en today zijn toegevoegd
                filtered_tracks = {}
                tracks_before_start = 0
                tracks_after_today = 0
                tracks_in_range = 0

                for uri, track_info in new_tracks.items():
                    added_at_str = track_info.get('added_at', '')
                    if added_at_str:
                        try:
                            added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                            if added_at.tzinfo:
                                added_at = added_at.astimezone().replace(tzinfo=None)

                            # Gebruik alleen datum voor vergelijking
                            added_at_date_only = added_at.date()

                            # Debug output voor eerste paar tracks
                            if tracks_in_range < 3:
                                print(
                                    f"{Colors.DIM}      Track: {track_info['name']} - Added: "
                                    f"{added_at.strftime('%Y-%m-%d %H:%M:%S')} (datum: {added_at_date_only}){Colors.RESET}"
                                )

                            # Alleen tracks tussen start_date en today (inclusief beide datums)
                            if since_date_only <= added_at_date_only <= today_date_only:
                                filtered_tracks[uri] = track_info
                                tracks_in_range += 1
                            elif added_at_date_only < since_date_only:
                                tracks_before_start += 1
                            else:
                                tracks_after_today += 1
                        except (ValueError, AttributeError) as e:
                            # Als parsing mislukt, neem de track op (voor veiligheid)
                            print(f"{Colors.BRIGHT_YELLOW}      ⚠️  Kon datum niet parsen voor track {track_info.get('name', 'Unknown')}: {e}{Colors.RESET}")
                            filtered_tracks[uri] = track_info
                    else:
                        # Als geen added_at, neem de track op
                        filtered_tracks[uri] = track_info

                # Debug output
                if tracks_before_start > 0 or tracks_after_today > 0:
                    print(
                        f"{Colors.DIM}   Debug: {tracks_before_start} voor start datum, "
                        f"{tracks_after_today} na vandaag, {tracks_in_range} in bereik{Colors.RESET}"
                    )

                if filtered_tracks:
                    print(f"{Colors.BRIGHT_GREEN}   ✅ {len(filtered_tracks)} nieuwe tracks gevonden in bereik{Colors.RESET}")
                    for uri, track_info in list(filtered_tracks.items())[:5]:  # Toon eerste 5
                        track_display = f"{track_info['artists']} - {track_info['name']}"
                        if len(track_display) > 60:
                            track_display = track_display[:57] + "..."
                        print(f"{Colors.DIM}      • {track_display}{Colors.RESET}")
                    if len(filtered_tracks) > 5:
                        print(f"{Colors.DIM}      ... en {len(filtered_tracks) - 5} meer{Colors.RESET}")

                    for uri, track_info in filtered_tracks.items():
                        all_new_tracks.append({
                            'Track': f"{track_info['artists']} - {track_info['name']}",
                            '': ''  # Blank field
                        })
                else:
                    print(f"{Colors.DIM}   🤷 Geen nieuwe tracks in deze periode{Colors.RESET}")
                    if len(new_tracks) > 0:
                        print(f"{Colors.BRIGHT_YELLOW}   ⚠️  Maar {len(new_tracks)} tracks gevonden buiten het bereik{Colors.RESET}")

            except SpotifyException as e:
                print(f"{Colors.BRIGHT_RED}   ❌ Fout bij ophalen playlist {playlist_id}: {e}{Colors.RESET}")
                if e.http_status == 404:
                    print(f"{Colors.BRIGHT_YELLOW}      Playlist niet gevonden{Colors.RESET}")
                elif e.http_status == 403:
                    print(f"{Colors.BRIGHT_YELLOW}      Geen toegang tot deze playlist{Colors.RESET}")
                continue
            except Exception as e:
                print(f"{Colors.BRIGHT_RED}   ❌ Onverwachte fout: {e}{Colors.RESET}")
                continue

        # Exporteer naar CSV
        if all_new_tracks:
            # Sorteer tracks alfabetisch
            all_new_tracks = sorted(all_new_tracks, key=lambda x: x['Track'].lower())
            # Genereer bestandsnaam als niet opgegeven
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"new_tracks_{since_date.strftime('%Y%m%d')}_to_{today.strftime('%Y%m%d')}_{timestamp}.csv"

            # Zorg dat bestandsnaam eindigt op .csv
            if not output_file.endswith('.csv'):
                output_file = output_file + '.csv'

            # Schrijf naar CSV
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Track', '']  # Track en een lege kolom
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for i, row in enumerate(all_new_tracks):
                    writer.writerow(row)
                    if (i + 1) % 5 == 0:
                        writer.writerow(dict.fromkeys(fieldnames, ''))  # Lege regel na elke 5 rijen

            print(f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}✅ {len(all_new_tracks)} nieuwe tracks geëxporteerd naar: {output_file}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}{'═'*70}{Colors.RESET}")
            print(f"{Colors.DIM}   Bestandslocatie: {os.path.abspath(output_file)}{Colors.RESET}")
        else:
            print(f"\n{Colors.BRIGHT_YELLOW}⚠️  Geen nieuwe tracks gevonden om te exporteren.{Colors.RESET}")

        # Update start datum naar vandaag (voor volgende keer)
        today = datetime.now()
        save_tracking_start_date(today)
        print(f"\n{Colors.BRIGHT_GREEN}✅ Start datum bijgewerkt naar vandaag ({today.strftime('%Y-%m-%d')}){Colors.RESET}")
        print(f"{Colors.DIM}   De volgende keer worden tracks vanaf deze datum gecontroleerd.{Colors.RESET}")

        # Belangrijke informatie over Spotify API beperkingen
        if len(all_new_tracks) == 0:
            print(f"\n{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}ℹ️  BELANGRIJKE INFORMATIE OVER SPOTIFY API{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}")
            print(f"{Colors.BRIGHT_WHITE}De Spotify API geeft alleen 'added_at' informatie voor:{Colors.RESET}")
            print(f"{Colors.DIM}  ✓ Playlists die je zelf bezit{Colors.RESET}")
            print(f"{Colors.DIM}  ✓ Collaborative playlists waar je collaborator bent{Colors.RESET}")
            print(f"\n{Colors.BRIGHT_YELLOW}Voor andere playlists (bijv. public playlists van anderen):{Colors.RESET}")
            print(f"{Colors.DIM}  ✗ Geen 'added_at' informatie beschikbaar{Colors.RESET}")
            print(f"{Colors.DIM}  ✗ Kan niet bepalen wanneer tracks zijn toegevoegd{Colors.RESET}")
            print(f"\n{Colors.BRIGHT_CYAN}Oplossing:{Colors.RESET}")
            print(f"{Colors.DIM}  • Zorg dat je eigenaar of collaborator bent van de playlists{Colors.RESET}")
            print(f"{Colors.DIM}  • Of gebruik een andere methode (bijv. vergelijken met vorige staat){Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}{'═'*70}{Colors.RESET}\n")

    except Exception as e:
        print(f"{Colors.BRIGHT_RED}❌ Onverwachte fout bij exporteren nieuwe tracks: {e}{Colors.RESET}")
        print(f"{Colors.DIM}   Traceback: {traceback.format_exc()}{Colors.RESET}")
