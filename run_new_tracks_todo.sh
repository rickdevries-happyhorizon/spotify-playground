#!/bin/bash

# Start the new tracks to-do web UI (Flask)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_EXE=""
if [ -f ".venv/bin/python3" ]; then
    PYTHON_EXE=".venv/bin/python3"
elif [ -f "venv/bin/python3" ]; then
    PYTHON_EXE="venv/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    echo "⚠️  No virtual environment found. Install packages with: pip install -r requirements.txt"
    PYTHON_EXE="python3"
else
    echo "❌ Error: python3 not found!"
    exit 1
fi

if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

exec "$PYTHON_EXE" run_new_tracks_todo.py
