#!/bin/bash

# Script om de Spotify playlist synchronisatie uit te voeren

# Ga naar de script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Bepaal het pad naar de Python executable in de virtual environment
PYTHON_EXE=""
if [ -f ".venv/bin/python3" ]; then
    PYTHON_EXE=".venv/bin/python3"
elif [ -f "path/to/venv/bin/python3" ]; then
    PYTHON_EXE="path/to/venv/bin/python3"
elif [ -f "venv/bin/python3" ]; then
    PYTHON_EXE="venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    echo "⚠️  Geen virtual environment gevonden. Gebruik menu-optie 10 om packages te installeren."
    PYTHON_EXE="python3"
else
    echo "❌ Fout: python3 niet gevonden!"
    exit 1
fi

# Controleer of Python script bestaat
if [ ! -f "playlist_sync.py" ]; then
    echo "❌ Fout: playlist_sync.py niet gevonden in $SCRIPT_DIR"
    exit 1
fi

# Laad .env als die bestaat (STORAGE_BACKEND, MySQL-instellingen, etc.)
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

STORAGE_BACKEND="${STORAGE_BACKEND:-mysql}"

# Waarschuwing als packages ontbreken (menu-optie 10 kan ze installeren)
if ! "$PYTHON_EXE" -c "import spotipy" 2>/dev/null; then
    echo "⚠️  spotipy niet gevonden. Kies menu-optie 10 om packages te installeren."
fi
if [ "$STORAGE_BACKEND" = "mysql" ] && ! "$PYTHON_EXE" -c "import pymysql" 2>/dev/null; then
    echo "⚠️  pymysql niet gevonden. Kies menu-optie 10, of zet STORAGE_BACKEND=txt in .env"
fi
if ! "$PYTHON_EXE" -c "import mutagen" 2>/dev/null; then
    echo "⚠️  mutagen niet gevonden. Kies menu-optie 10 om packages te installeren."
fi

# Voer het Python script uit met de venv Python
"$PYTHON_EXE" playlist_sync.py

