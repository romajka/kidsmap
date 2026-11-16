#!/usr/bin/env bash
set -euo pipefail
DEPLOY_HOST="${KIDSMAP_DEPLOY_HOST:-root@157.173.119.227}"
REVISION="${1:-}"
if [[ ! "$REVISION" =~ ^[0-9a-f]{40}$ ]]; then
  printf '%s\n' 'Usage: ./scripts/deploy-production.sh <tested-40-character-commit-SHA>' >&2
  exit 2
fi
# SHA is validated before interpolation; the host remains a single SSH argument.
ssh "$DEPLOY_HOST" "set -eu; cd /opt/kidsmap; git fetch origin main; runner=\$(mktemp /tmp/kidsmap-deploy-XXXXXXXX.py); trap 'rm -f \"\$runner\"' EXIT; git show '$REVISION:scripts/deploy_server.py' > \"\$runner\"; python3 \"\$runner\" --root /opt/kidsmap '$REVISION'"
