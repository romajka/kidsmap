#!/usr/bin/env bash
set -euo pipefail

DEPLOY_HOST="${KIDSMAP_DEPLOY_HOST:-root@157.173.119.227}"

printf 'Deploying origin/main to %s...\n' "$DEPLOY_HOST"
ssh "$DEPLOY_HOST" 'cd /opt/kidsmap && ./scripts/deploy-server.sh main'
