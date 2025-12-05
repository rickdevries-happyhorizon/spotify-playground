#!/bin/bash

# Script om de Spotify playlist synchronisatie uit te voeren

# Ga naar de script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Bepaal het pad naar de Python executable in de virtual environment
PYTHON_EXE=""
if [ -f "path/to/venv/bin/python3" ]; then
    PYTHON_EXE="path/to/venv/bin/python3"
elif [ -f "venv/bin/python3" ]; then
    PYTHON_EXE="venv/bin/python3"
else
    echo "❌ Fout: Virtual environment niet gevonden!"
    echo "   Zoek naar: path/to/venv/bin/python3 of venv/bin/python3"
    exit 1
fi

# Controleer of Python script bestaat
if [ ! -f "playlist_sync.py" ]; then
    echo "❌ Fout: playlist_sync.py niet gevonden in $SCRIPT_DIR"
    exit 1
fi

# Controleer of spotipy geïnstalleerd is
if ! "$PYTHON_EXE" -c "import spotipy" 2>/dev/null; then
    echo "❌ Fout: spotipy niet gevonden in virtual environment!"
    echo "   Installeer met: $PYTHON_EXE -m pip install spotipy"
    exit 1
fi

# Voer het Python script uit met de venv Python
"$PYTHON_EXE" playlist_sync.py

