#!/usr/bin/env bash
# Backup the spotify_playground MySQL database.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$ROOT/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT="$BACKUP_DIR/spotify_playground_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

# Load .env if present (MYSQL_* vars).
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

HOST="${MYSQL_HOST:-127.0.0.1}"
PORT="${MYSQL_PORT:-3306}"
USER="${MYSQL_USER:-root}"
PASSWORD="${MYSQL_PASSWORD:-}"
DATABASE="${MYSQL_DATABASE:-spotify_playground}"

MYSQL_ARGS=(-h "$HOST" -P "$PORT" -u "$USER")
if [[ -n "$PASSWORD" ]]; then
  MYSQL_ARGS+=(-p"$PASSWORD")
fi

echo "Backing up database '$DATABASE' to $OUTPUT ..."
mysqldump "${MYSQL_ARGS[@]}" "$DATABASE" > "$OUTPUT"
echo "Done. Backup size: $(du -h "$OUTPUT" | cut -f1)"
