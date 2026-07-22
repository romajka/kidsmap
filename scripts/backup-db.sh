#!/usr/bin/env bash
set -eu

# Ensure standard paths are loaded (critical for cron jobs executing docker compose)
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="$BACKUP_DIR/kidsmap-db-$TIMESTAMP.sql.gz"

cd "$ROOT_DIR"

mkdir -p "$BACKUP_DIR"

DUMP_COMMAND='exec pg_dump --format=plain --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
DB_SERVICE="postgres"

if ! docker compose exec -T "$DB_SERVICE" sh -lc "$DUMP_COMMAND" | gzip -c > "$OUT_FILE"; then
  rm -f "$OUT_FILE"
  exit 1
fi

printf '[backup] database saved to %s\n' "$OUT_FILE"

# Clean up older database backups
KEEP_BACKUPS="${KEEP_BACKUPS:-5}"
log_cleanup() {
  printf '[backup] cleaning up old database backups (older than 15 days, or keeping last %s)\n' "$KEEP_BACKUPS"
}
log_cleanup

# 1. Delete backups older than 15 days
find "$BACKUP_DIR" -name "kidsmap-db-*.sql.gz" -type f -mtime +15 -delete 2>/dev/null || true

# 2. Keep maximum of KEEP_BACKUPS (default 5)
ls -1tr "$BACKUP_DIR"/kidsmap-db-*.sql.gz 2>/dev/null | head -n -"$KEEP_BACKUPS" | xargs -r rm || true
