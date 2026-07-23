#!/bin/bash

# Run Spotify playlist synchronization

# Change to the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Resolve Python executable in the virtual environment
PYTHON_EXE=""
if [ -f ".venv/bin/python3" ]; then
    PYTHON_EXE=".venv/bin/python3"
elif [ -f "path/to/venv/bin/python3" ]; then
    PYTHON_EXE="path/to/venv/bin/python3"
elif [ -f "venv/bin/python3" ]; then
    PYTHON_EXE="venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    echo "⚠️  No virtual environment found. Install packages with: pip install -r requirements.txt"
    PYTHON_EXE="python3"
else
    echo "❌ Error: python3 not found!"
    exit 1
fi

# Check that the Python script exists
if [ ! -f "playlist_sync.py" ]; then
    echo "❌ Error: playlist_sync.py not found in $SCRIPT_DIR"
    exit 1
fi

# Load .env if present (MySQL settings, etc.)
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# Warn if packages are missing
if ! "$PYTHON_EXE" -c "import spotipy" 2>/dev/null; then
    echo "⚠️  spotipy not found. Install packages with: pip install -r requirements.txt"
fi
if ! "$PYTHON_EXE" -c "import pymysql" 2>/dev/null; then
    echo "⚠️  pymysql not found. Install packages with: pip install -r requirements.txt"
fi
if ! "$PYTHON_EXE" -c "import mutagen" 2>/dev/null; then
    echo "⚠️  mutagen not found. Install packages with: pip install -r requirements.txt"
fi

# Run the Python script with the venv Python
"$PYTHON_EXE" playlist_sync.py
