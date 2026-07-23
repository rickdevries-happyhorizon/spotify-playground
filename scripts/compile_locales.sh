#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 scripts/generate_locale_pos.py
python3 spotify_playlist/i18n.py

echo "Locales compiled to spotify_playlist/locale/*/LC_MESSAGES/messages.mo"
echo "Client JSON exported to spotify_playlist/static/locale/*.json"
