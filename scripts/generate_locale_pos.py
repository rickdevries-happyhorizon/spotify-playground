#!/usr/bin/env python3
"""Generate locale .po files from messages.pot with translations."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POT = ROOT / "spotify_playlist" / "locale" / "messages.pot"

NL: dict[str, str] = {
    "Release Finder": "Release Finder",
    "Choose a tool to get started.": "Kies een tool om te beginnen.",
    "Loading…": "Laden…",
    "Settings": "Instellingen",
    "What would you like to do?": "Wat wil je doen?",
    "Control panel": "Controlepaneel",
    "Tune the look, sync playlists, and set how new tracks are imported.": "Pas het uiterlijk aan, stel afspeellijsten in en bepaal hoe nieuwe tracks worden geïmporteerd.",
    "Theme": "Thema",
    "Pick the vibe for the whole app.": "Kies de sfeer voor de hele app.",
    "Light": "Licht",
    "Clean black & white": "Strak zwart-wit",
    "Dark": "Donker",
    "Flat dark mode": "Platte donkere modus",
    "RetroUI": "RetroUI",
    "Neo-brutalism": "Neo-brutalisme",
    "Windows XP": "Windows XP",
    "Classic Luna desktop": "Klassiek Luna-bureaublad",
    "Language": "Taal",
    "Choose the language for labels and messages.": "Kies de taal voor labels en berichten.",
    "English": "Engels",
    "Dutch": "Nederlands",
    "Brabants": "Brabants",
    "Playlists": "Afspeellijsten",
    "Configure destination, sources, and tracking playlists.": "Stel bestemming, bronnen en tracking-afspeellijsten in.",
    "Destination playlist": "Bestemmingsafspeellijst",
    "Where synced tracks land.": "Waar gesynchroniseerde tracks terechtkomen.",
    "Source playlists": "Bronafspeellijsten",
    "Playlists to pull tracks from during sync.": "Afspeellijsten waar tracks vandaan komen tijdens sync.",
    "Tracking playlists": "Tracking-afspeellijsten",
    "Playlists scanned when importing new tracks.": "Afspeellijsten die worden gescand bij het importeren van nieuwe tracks.",
    "0 playlists": "0 afspeellijsten",
    "+ Add source playlist": "+ Bronafspeellijst toevoegen",
    "+ Add tracking playlist": "+ Tracking-afspeellijst toevoegen",
    "Dates": "Datums",
    "Control how far back sync and new-track import look.": "Bepaal hoe ver sync en nieuwe-track import terugkijken.",
    "Sync start date": "Sync-startdatum",
    "Artist releases and source playlist sync look back from this date.": "Artiestreleases en bron-sync kijken vanaf deze datum terug.",
    "Start date": "Startdatum",
    "(empty = last 7 days)": "(leeg = laatste 7 dagen)",
    "New tracks start date": "Startdatum nieuwe tracks",
    "Only import tracks into new_tracks after this date.": "Importeer tracks pas na deze datum in new_tracks.",
    "Ready to save": "Klaar om op te slaan",
    "Save settings": "Instellingen opslaan",
    "Genres": "Genres",
    "Choose a list": "Kies een lijst",
    "Track lists": "Tracklijsten",
    "Has reference URL": "Heeft referentie-URL",
    "Needs reference URL": "Referentie-URL nodig",
    "Add track": "Track toevoegen",
    "Artist - Track name": "Artiest - Tracknaam",
    "Reference URL (optional)": "Referentie-URL (optioneel)",
    "Just a moment": "Even geduld",
    "Skip to main content": "Ga naar hoofdinhoud",
    "Track name": "Tracknaam",
    "Reference URL": "Referentie-URL",
    "Playlist URL": "Afspeellijst-URL",
    "Copy track title": "Tracktitel kopiëren",
    "Add": "Toevoegen",
    "By genre": "Per genre",
    "Genre": "Genre",
    "Total": "Totaal",
    "Has URL": "Heeft URL",
    "Needs URL": "URL nodig",
    "Complete": "Compleet",
    "Spotify import": "Spotify-import",
    "Fetching new tracks": "Nieuwe tracks ophalen",
    "Connecting to Spotify…": "Verbinden met Spotify…",
    "Starting…": "Starten…",
    "Current playlist": "Huidige afspeellijst",
    "Prepare": "Voorbereiden",
    "Scan playlists": "Afspeellijsten scannen",
    "Fetch energy": "Energy ophalen",
    "Save tracks": "Tracks opslaan",
    "View to-do list": "Naar to-do lijst",
    "Fetch again": "Opnieuw ophalen",
    "Back to home": "Terug naar home",
    "Open settings": "Instellingen openen",
    "Try again": "Opnieuw proberen",
    "Track to-do list": "Track to-do lijst",
    "Manage reference URLs for new tracks by genre.": "Beheer referentie-URL's voor nieuwe tracks per genre.",
    "Fetch new tracks": "Nieuwe tracks ophalen",
    "Import new tracks from your Spotify playlists into the to-do list.": "Importeer nieuwe tracks uit je Spotify-afspeellijsten naar de to-do lijst.",
    "Scan tracking playlists for new additions and add them to your download to-do list.": "Scan tracking-afspeellijsten op nieuwe toevoegingen en zet ze op je download to-do lijst.",
    "Scanning tracking playlists for new tracks to download.": "Tracking-afspeellijsten scannen op nieuwe tracks om te downloaden.",
    "Sync playlists": "Afspeellijsten synchroniseren",
    "Pull new tracks from source playlists into your destination playlist.": "Haal nieuwe tracks uit bron-afspeellijsten en zet ze in je doel-afspeellijst.",
    "Pull new tracks from followed artists and source playlists into your destination playlist.": "Haal nieuwe tracks uit gevolgde artiesten en bron-afspeellijsten en zet ze in je doel-afspeellijst.",
    "Scanning followed artists and source playlists since your sync start date.": "Gevolgde artiesten en bron-afspeellijsten scannen sinds je sync-startdatum.",
    "Scan artists": "Artiesten scannen",
    "Current artist": "Huidige artiest",
    "From artists": "Van artiesten",
    "Playlist sync": "Afspeellijst-sync",
    "Syncing playlists": "Afspeellijsten synchroniseren",
    "Scan sources": "Bronnen scannen",
    "Add to destination": "Naar doel toevoegen",
    "Sync again": "Opnieuw synchroniseren",
    "Sync complete": "Sync voltooid",
    "Sync failed": "Sync mislukt",
    "Sync started…": "Sync gestart…",
    "Could not start sync": "Kon sync niet starten",
    "Sync screen is unavailable. Restart the web server.": "Sync-scherm niet beschikbaar. Herstart de webserver.",
    "Sync playlists — {app_name}": "Afspeellijsten synchroniseren — {app_name}",
    "Moving new tracks from source playlists into your destination playlist.": "Nieuwe tracks van bron-afspeellijsten naar je doel-afspeellijst verplaatsen.",
    "1 track added to your destination playlist.": "1 track toegevoegd aan je doel-afspeellijst.",
    "{count} tracks added to your destination playlist.": "{count} tracks toegevoegd aan je doel-afspeellijst.",
    "New tracks were already in your destination playlist.": "Nieuwe tracks stonden al in je doel-afspeellijst.",
    "No new source tracks found since {since_date}.": "Geen nieuwe brontracks gevonden sinds {since_date}.",
    "No new source tracks found.": "Geen nieuwe brontracks gevonden.",
    "Something went wrong while syncing playlists.": "Er ging iets mis bij het synchroniseren van afspeellijsten.",
    "Added": "Toegevoegd",
    "New found": "Nieuw gevonden",
    "Sources": "Bronnen",
    "Statistics": "Statistieken",
    "Overview of tracks, completion, and activity.": "Overzicht van tracks, voortgang en activiteit.",
    "Track to-do": "Track to-do",
    "Choose a genre to manage reference URLs for its tracks.": "Kies een genre om referentie-URL's voor tracks te beheren.",
    "Overview of your new tracks and reference URL progress.": "Overzicht van je nieuwe tracks en referentie-URL voortgang.",
    "Working…": "Bezig…",
    "Import complete": "Import voltooid",
    "Done": "Klaar",
    "Import failed": "Import mislukt",
    "Something went wrong while fetching tracks.": "Er ging iets mis bij het ophalen van tracks.",
    "Your to-do list is up to date.": "Je to-do lijst is up-to-date.",
    "Fetch screen is unavailable. Restart the web server.": "Fetch-scherm niet beschikbaar. Herstart de webserver.",
    "Import started…": "Import gestart…",
    "Importing the latest additions from your Spotify playlists.": "De nieuwste toevoegingen uit je Spotify-afspeellijsten importeren.",
    "Customize your sync workflow and visual style.": "Pas je sync-workflow en visuele stijl aan.",
    "Unsaved changes": "Niet-opgeslagen wijzigingen",
    "Saving…": "Opslaan…",
    "All changes saved": "Alle wijzigingen opgeslagen",
    "Settings saved": "Instellingen opgeslagen",
    "Choose whether to view tracks with or without a reference URL.": "Kies of je tracks met of zonder referentie-URL wilt zien.",
    "tracks with a reference URL": "tracks met een referentie-URL",
    "tracks still missing a reference URL": "tracks zonder referentie-URL",
    "Showing {filter_label}.": "Toont {filter_label}.",
    "Loading settings…": "Instellingen laden…",
    "Could not load settings": "Kon instellingen niet laden",
    "Failed to load settings: {message}": "Instellingen laden mislukt: {message}",
    "Could not save settings": "Kon instellingen niet opslaan",
    "Loading track counts…": "Trackaantallen laden…",
    "Could not load tracks": "Kon tracks niet laden",
    "No tracks found for {genre}.": "Geen tracks gevonden voor {genre}.",
    "Failed to load tracks: {message}": "Tracks laden mislukt: {message}",
    "No genres found.": "Geen genres gevonden.",
    "Loading genres…": "Genres laden…",
    "Could not load genres": "Kon genres niet laden",
    "No tracks found in new_tracks table.": "Geen tracks gevonden in new_tracks-tabel.",
    "Failed to load genres: {message}": "Genres laden mislukt: {message}",
    "1 track": "1 track",
    "{count} tracks": "{count} tracks",
    "Loading statistics…": "Statistieken laden…",
    "Failed to load statistics: {message}": "Statistieken laden mislukt: {message}",
    "Total tracks": "Totaal tracks",
    "Completion": "Voortgang",
    "Title copy clicks": "Titel-kopie kliks",
    "Average energy": "Gemiddelde energy",
    "No tracks found.": "Geen tracks gevonden.",
    "Uncategorized": "Ongecategoriseerd",
    "Home": "Home",
    "Fetch tracks": "Tracks ophalen",
    "Remove playlist": "Afspeellijst verwijderen",
    "1 playlist": "1 afspeellijst",
    "{count} playlists": "{count} afspeellijsten",
    "Could not record click": "Kon klik niet registreren",
    "Could not save click count": "Kon klikteller niet opslaan",
    "Nothing to copy": "Niets om te kopiëren",
    "{label} copied": "{label} gekopieerd",
    "Could not copy {label}": "Kon {label} niet kopiëren",
    "Title": "Titel",
    "Click to copy title": "Klik om titel te kopiëren",
    "Save": "Opslaan",
    "Remove": "Verwijderen",
    "Energy: {value}": "Energy: {value}",
    "Save failed": "Opslaan mislukt",
    "Saved — moved to Has URL list": "Opgeslagen — verplaatst naar Heeft URL-lijst",
    "Cleared — moved to Needs URL list": "Gewist — verplaatst naar URL nodig-lijst",
    "Remove \"{track}\" from the list?": "\"{track}\" uit de lijst verwijderen?",
    "Remove failed": "Verwijderen mislukt",
    "Track removed": "Track verwijderd",
    "No tracks with a URL yet.": "Nog geen tracks met een URL.",
    "All tracks have a reference URL.": "Alle tracks hebben een referentie-URL.",
    "Loading tracks from database…": "Tracks laden uit database…",
    "1 new track added to your to-do list.": "1 nieuwe track toegevoegd aan je to-do lijst.",
    "{count} new tracks added to your to-do list.": "{count} nieuwe tracks toegevoegd aan je to-do lijst.",
    "Found 1 track, but {skipped} already existed in your list.": "1 track gevonden, maar {skipped} stond al in je lijst.",
    "Found {found} tracks, but {skipped} already existed in your list.": "{found} tracks gevonden, maar {skipped} stond al in je lijst.",
    "Scanned your playlist — no new tracks between {since_date} and {until_date}.": "Je afspeellijst gescand — geen nieuwe tracks tussen {since_date} en {until_date}.",
    "Scanned your playlists — no new tracks between {since_date} and {until_date}.": "Je afspeellijsten gescand — geen nieuwe tracks tussen {since_date} en {until_date}.",
    "Scanned 1 playlist — no new tracks between {since_date} and {until_date}.": "1 afspeellijst gescand — geen nieuwe tracks tussen {since_date} en {until_date}.",
    "Scanned {count} playlists — no new tracks between {since_date} and {until_date}.": "{count} afspeellijsten gescand — geen nieuwe tracks tussen {since_date} en {until_date}.",
    "Track to-do — {app_name}": "Track to-do — {app_name}",
    "Statistics — {app_name}": "Statistieken — {app_name}",
    "Fetch tracks — {app_name}": "Tracks ophalen — {app_name}",
    "Settings — {app_name}": "Instellingen — {app_name}",
    "{genre} — Track to-do — {app_name}": "{genre} — Track to-do — {app_name}",
}

BRAB: dict[str, str] = {
    **NL,
    "Choose a tool to get started.": "Kies 'n tool om te beginne.",
    "Loading…": "Bezig met laden…",
    "Settings": "Instellinge",
    "What would you like to do?": "Wat wilste doen?",
    "Control panel": "Controlepaneel",
    "Tune the look, sync playlists, and set how new tracks are imported.": "Pas 't uiterlijk aan, zet playlists klaar en bepaol hoe nieuwe tracks binnenkome.",
    "Theme": "Thema",
    "Pick the vibe for the whole app.": "Kies de sfeer veur de hele app.",
    "Light": "Licht",
    "Clean black & white": "Strak zwart-wit",
    "Dark": "Donker",
    "Flat dark mode": "Platte donkere modus",
    "RetroUI": "RetroUI",
    "Neo-brutalism": "Neo-brutalisme",
    "Windows XP": "Windows XP",
    "Classic Luna desktop": "Klassiek Luna-bureaublad",
    "Language": "Taal",
    "Choose the language for labels and messages.": "Kies de taal veur labels en berichte.",
    "English": "Engels",
    "Dutch": "Nederlands",
    "Brabants": "Brabants",
    "Playlists": "Playlists",
    "Configure destination, sources, and tracking playlists.": "Zet bestemming, bronne en tracking-playlists klaar.",
    "Destination playlist": "Bestemmingsplaylist",
    "Where synced tracks land.": "Waar gesynchroniseerde tracks terechtkome.",
    "Source playlists": "Bronplaylists",
    "Playlists to pull tracks from during sync.": "Playlists waar tracks vandoan kome tijdens sync.",
    "Tracking playlists": "Tracking-playlists",
    "Playlists scanned when importing new tracks.": "Playlists die gescand worre bij 't importeren van nieuwe tracks.",
    "0 playlists": "0 playlists",
    "+ Add source playlist": "+ Bronplaylist toevoege",
    "+ Add tracking playlist": "+ Tracking-playlist toevoege",
    "Dates": "Datums",
    "Control how far back sync and new-track import look.": "Bepaal hoe ver sync en nieuwe-track import terugkijke.",
    "Sync start date": "Sync-startdatum",
    "Artist releases and source playlist sync look back from this date.": "Artiestreleases en bron-sync kieke vanaf deze datum terug.",
    "Start date": "Startdatum",
    "(empty = last 7 days)": "(leeg = laatste 7 dage)",
    "New tracks start date": "Startdatum nieuwe tracks",
    "Only import tracks into new_tracks after this date.": "Importeer tracks pas na deze datum in new_tracks.",
    "Ready to save": "Klaar om op te slaon",
    "Save settings": "Instellinge opslaon",
    "Genres": "Genres",
    "Choose a list": "Kies 'n lijst",
    "Track lists": "Tracklijste",
    "Has reference URL": "Heeft referentie-URL",
    "Needs reference URL": "Referentie-URL nodig",
    "Add track": "Track toevoege",
    "Artist - Track name": "Artiest - Tracknaam",
    "Reference URL (optional)": "Referentie-URL (optioneel)",
    "Just a moment": "Even wachte",
    "Skip to main content": "Ga nor de hoofdinhoud",
    "Track name": "Tracknaam",
    "Reference URL": "Referentie-URL",
    "Playlist URL": "Playlist-URL",
    "Copy track title": "Tracktitel kopieeren",
    "Add": "Toevoege",
    "By genre": "Per genre",
    "Genre": "Genre",
    "Total": "Totaal",
    "Has URL": "Heeft URL",
    "Needs URL": "URL nodig",
    "Complete": "Compleet",
    "Spotify import": "Spotify-import",
    "Fetching new tracks": "Nieuwe tracks ophalen",
    "Connecting to Spotify…": "Verbinden met Spotify…",
    "Starting…": "Starten…",
    "Current playlist": "Huidige playlist",
    "Prepare": "Voorbereiden",
    "Scan playlists": "Playlists scannen",
    "Fetch energy": "Energy ophalen",
    "Save tracks": "Tracks opslaon",
    "View to-do list": "Naor to-do lijst",
    "Fetch again": "Opniej ophalen",
    "Back to home": "Terug naor home",
    "Open settings": "Instellinge opene",
    "Try again": "Opniej proberen",
    "Track to-do list": "Track to-do lijst",
    "Manage reference URLs for new tracks by genre.": "Beheer referentie-URL's veur nieuwe tracks per genre.",
    "Fetch new tracks": "Nieuwe tracks ophalen",
    "Import new tracks from your Spotify playlists into the to-do list.": "Importeer nieuwe tracks uut je Spotify-playlists naor de to-do lijst.",
    "Scan tracking playlists for new additions and add them to your download to-do list.": "Scan tracking-playlists op nieuwe toevoegingen en zet ze op je download to-do lijst.",
    "Scanning tracking playlists for new tracks to download.": "Tracking-playlists scannen op nieuwe tracks om te downloaden.",
    "Sync playlists": "Playlists synchroniseren",
    "Pull new tracks from source playlists into your destination playlist.": "Haol nieuwe tracks uut bron-playlists en zet ze in je doel-playlist.",
    "Pull new tracks from followed artists and source playlists into your destination playlist.": "Haol nieuwe tracks uut gevolgde artiesten en bron-playlists en zet ze in je doel-playlist.",
    "Scanning followed artists and source playlists since your sync start date.": "Gevolgde artiesten en bron-playlists scannen sinds je sync-startdatum.",
    "Scan artists": "Artiesten scannen",
    "Current artist": "Huidige artiest",
    "From artists": "Van artiesten",
    "Playlist sync": "Playlist-sync",
    "Syncing playlists": "Playlists synchroniseren",
    "Scan sources": "Bronnen scannen",
    "Add to destination": "Naor doel toevoegen",
    "Sync again": "Opniej synchroniseren",
    "Sync complete": "Sync klaar",
    "Sync failed": "Sync mislukt",
    "Sync started…": "Sync gestart…",
    "Could not start sync": "Kon sync niet starten",
    "Sync screen is unavailable. Restart the web server.": "Sync-scherm niet beschikbaar. Herstart de webserver.",
    "Sync playlists — {app_name}": "Playlists synchroniseren — {app_name}",
    "Moving new tracks from source playlists into your destination playlist.": "Nieuwe tracks van bron-playlists naor je doel-playlist verplaatsen.",
    "1 track added to your destination playlist.": "1 track toegevoegd aan je doel-playlist.",
    "{count} tracks added to your destination playlist.": "{count} tracks toegevoegd aan je doel-playlist.",
    "New tracks were already in your destination playlist.": "Nieuwe tracks stonden al in je doel-playlist.",
    "No new source tracks found since {since_date}.": "Geen nieuwe brontracks gevonden sinds {since_date}.",
    "No new source tracks found.": "Geen nieuwe brontracks gevonden.",
    "Something went wrong while syncing playlists.": "Der ging iets mis bij 't synchroniseren van playlists.",
    "Added": "Toegevoegd",
    "New found": "Nieuw gevonden",
    "Sources": "Bronnen",
    "Statistics": "Statistieke",
    "Overview of tracks, completion, and activity.": "Overzicht van tracks, voortgang en activiteit.",
    "Track to-do": "Track to-do",
    "Choose a genre to manage reference URLs for its tracks.": "Kies 'n genre om referentie-URL's veur tracks te beheren.",
    "Overview of your new tracks and reference URL progress.": "Overzicht van je nieuwe tracks en referentie-URL voortgang.",
    "Working…": "Bezig…",
    "Import complete": "Import klaar",
    "Done": "Klaar",
    "Import failed": "Import mislukt",
    "Something went wrong while fetching tracks.": "Der ging iets mis bij 't ophalen van tracks.",
    "Your to-do list is up to date.": "Je to-do lijst is up-to-date.",
    "Fetch screen is unavailable. Restart the web server.": "Fetch-scherm niet beschikbaar. Herstart de webserver.",
    "Import started…": "Import gestart…",
    "Importing the latest additions from your Spotify playlists.": "De nieuwste toevoegingen uut je Spotify-playlists importeren.",
    "Customize your sync workflow and visual style.": "Pas je sync-workflow en visuele stijl aan.",
    "Unsaved changes": "Niet-opgeslagen wijziginge",
    "Saving…": "Bezig met opslaon…",
    "All changes saved": "Alle wijziginge opgeslaon",
    "Settings saved": "Instellinge opgeslaon",
    "Choose whether to view tracks with or without a reference URL.": "Kies ofste tracks met of zonder referentie-URL wilt zien.",
    "tracks with a reference URL": "tracks met 'n referentie-URL",
    "tracks still missing a reference URL": "tracks zonder referentie-URL",
    "Showing {filter_label}.": "Toont {filter_label}.",
    "Loading settings…": "Instellinge laden…",
    "Could not load settings": "Kon instellinge niet laden",
    "Failed to load settings: {message}": "Instellinge laden mislukt: {message}",
    "Could not save settings": "Kon instellinge niet opslaon",
    "Loading track counts…": "Trackaantalle laden…",
    "Could not load tracks": "Kon tracks niet laden",
    "No tracks found for {genre}.": "Geen tracks gevonden veur {genre}.",
    "Failed to load tracks: {message}": "Tracks laden mislukt: {message}",
    "No genres found.": "Geen genres gevonden.",
    "Loading genres…": "Genres laden…",
    "Could not load genres": "Kon genres niet laden",
    "No tracks found in new_tracks table.": "Geen tracks gevonden in new_tracks-tabel.",
    "Failed to load genres: {message}": "Genres laden mislukt: {message}",
    "1 track": "1 track",
    "{count} tracks": "{count} tracks",
    "Loading statistics…": "Statistieke laden…",
    "Failed to load statistics: {message}": "Statistieke laden mislukt: {message}",
    "Total tracks": "Totaal tracks",
    "Completion": "Voortgang",
    "Title copy clicks": "Titel-kopie kliks",
    "Average energy": "Gemiddelde energy",
    "No tracks found.": "Geen tracks gevonden.",
    "Uncategorized": "Ongecategoriseerd",
    "Home": "Home",
    "Fetch tracks": "Tracks ophalen",
    "Remove playlist": "Playlist verwijderen",
    "1 playlist": "1 playlist",
    "{count} playlists": "{count} playlists",
    "Could not record click": "Kon klik niet registreren",
    "Could not save click count": "Kon klikteller niet opslaon",
    "Nothing to copy": "Niks om te kopieeren",
    "{label} copied": "{label} gekopieerd",
    "Could not copy {label}": "Kon {label} niet kopieeren",
    "Title": "Titel",
    "Click to copy title": "Klik om titel te kopieeren",
    "Save": "Opslaon",
    "Remove": "Verwijderen",
    "Energy: {value}": "Energy: {value}",
    "Save failed": "Opslaon mislukt",
    "Saved — moved to Has URL list": "Opgeslaon — verplaats naor Heeft URL-lijst",
    "Cleared — moved to Needs URL list": "Gewist — verplaats naor URL nodig-lijst",
    "Remove \"{track}\" from the list?": "\"{track}\" uut de lijst verwijderen?",
    "Remove failed": "Verwijderen mislukt",
    "Track removed": "Track verwijderd",
    "No tracks with a URL yet.": "Nog geen tracks met 'n URL.",
    "All tracks have a reference URL.": "Alle tracks hebben 'n referentie-URL.",
    "Loading tracks from database…": "Tracks laden uut database…",
    "1 new track added to your to-do list.": "1 nieuwe track toegevoeg aan je to-do lijst.",
    "{count} new tracks added to your to-do list.": "{count} nieuwe tracks toegevoeg aan je to-do lijst.",
    "Found 1 track, but {skipped} already existed in your list.": "1 track gevonden, mer {skipped} stond al in je lijst.",
    "Found {found} tracks, but {skipped} already existed in your list.": "{found} tracks gevonden, mer {skipped} stond al in je lijst.",
    "Scanned your playlist — no new tracks between {since_date} and {until_date}.": "Je playlist gescand — geen nieuwe tracks tussen {since_date} en {until_date}.",
    "Scanned your playlists — no new tracks between {since_date} and {until_date}.": "Je playlists gescand — geen nieuwe tracks tussen {since_date} en {until_date}.",
    "Scanned 1 playlist — no new tracks between {since_date} and {until_date}.": "1 playlist gescand — geen nieuwe tracks tussen {since_date} en {until_date}.",
    "Scanned {count} playlists — no new tracks between {since_date} and {until_date}.": "{count} playlists gescand — geen nieuwe tracks tussen {since_date} en {until_date}.",
    "Settings — {app_name}": "Instellinge — {app_name}",
    "Statistics — {app_name}": "Statistieke — {app_name}",
}


def _escape_po(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _write_po(locale: str, translations: dict[str, str]) -> None:
    pot_lines = POT.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    in_header = False

    language_headers = {
        "en": ('"Language: en\\n"', '"Language-Team: English\\n"'),
        "nl": ('"Language: nl\\n"', '"Language-Team: Dutch\\n"'),
        "brab": ('"Language: brab\\n"', '"Language-Team: Brabants\\n"'),
    }

    for line in pot_lines:
        if line == 'msgid ""':
            in_header = True
            out.append(line)
            continue
        if in_header and line.startswith("msgstr "):
            out.append('msgstr ""')
            in_header = False
            continue
        if line.startswith("msgid ") and line != 'msgid ""':
            msgid = _parse_po_string(line[6:].strip())
            out.append(line)
            translation = translations.get(msgid, msgid)
            out.append(f'msgstr "{_escape_po(translation)}"')
            continue
        if line.startswith("msgstr "):
            continue
        if line == '"Language: \\n"':
            out.append(language_headers[locale][0])
            continue
        if line == '"Language-Team: LANGUAGE <LL@li.org>\\n"':
            out.append(language_headers[locale][1])
            continue
        out.append(line)

    target = ROOT / "spotify_playlist" / "locale" / locale / "LC_MESSAGES" / "messages.po"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(out) + "\n", encoding="utf-8")


def _parse_po_string(value: str) -> str:
    value = value.strip()
    if value == '' or value[0] != '"':
        return value
    raw = value[1:-1]
    out: list[str] = []
    i = 0
    while i < len(raw):
        char = raw[i]
        if char != '\\':
            out.append(char)
            i += 1
            continue
        i += 1
        if i >= len(raw):
            break
        escaped = raw[i]
        if escaped == 'n':
            out.append('\n')
        elif escaped == 't':
            out.append('\t')
        elif escaped == '"':
            out.append('"')
        elif escaped == '\\':
            out.append('\\')
        else:
            out.append(escaped)
        i += 1
    return ''.join(out)


def main() -> None:
    english = set()
    for line in POT.read_text(encoding="utf-8").splitlines():
        if line.startswith('msgid "') and line != 'msgid ""':
            english.add(_parse_po_string(line[6:].strip()))
    en_map = {msgid: msgid for msgid in english}
    _write_po("en", en_map)
    _write_po("nl", NL)
    _write_po("brab", BRAB)


if __name__ == "__main__":
    main()
