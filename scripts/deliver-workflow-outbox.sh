#!/usr/bin/env bash
# Send queued service emails (moderation decisions, invitations, etc.).
# Run from cron on the production host, e.g. every 2 minutes:
#   */2 * * * * cd /opt/kidsmap && ./scripts/deliver-workflow-outbox.sh >> /var/log/kidsmap-outbox.log 2>&1
set -euo pipefail

# cron has a minimal PATH; docker compose lives in /usr/local/bin or /usr/bin.
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIMIT="${OUTBOX_LIMIT:-50}"
cd "$ROOT_DIR"

# One run at a time; rows are also locked with SKIP LOCKED inside the command.
exec 9>"${TMPDIR:-/tmp}/kidsmap-outbox.lock"
flock -n 9 || exit 0

printf '[outbox] %s ' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
docker compose exec -T web python manage.py deliver_workflow_outbox --send --limit "$LIMIT"
