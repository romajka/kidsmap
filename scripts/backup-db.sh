#!/usr/bin/env bash
set -eu

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="$BACKUP_DIR/kidsmap-db-$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

if ! docker compose exec -T db sh -lc 'exec mariadb-dump --single-transaction --routines --triggers -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE"' | gzip -c > "$OUT_FILE"; then
  rm -f "$OUT_FILE"
  exit 1
fi

printf '[backup] database saved to %s\n' "$OUT_FILE"

# Clean up older database backups
KEEP_BACKUPS="${KEEP_BACKUPS:-5}"
log_cleanup() {
  printf '[backup] cleaning up old database backups (keeping last %s)\n' "$KEEP_BACKUPS"
}
log_cleanup
ls -1tr "$BACKUP_DIR"/kidsmap-db-*.sql.gz 2>/dev/null | head -n -"$KEEP_BACKUPS" | xargs -r rm || true

