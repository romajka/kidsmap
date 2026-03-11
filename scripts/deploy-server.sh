#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${REMOTE:-origin}"
BRANCH="${1:-main}"
APP_BASE_URL="${APP_BASE_URL:-http://127.0.0.1:8000}"

log() {
  printf '[deploy] %s\n' "$*"
}

cd "$ROOT_DIR"

if [[ ! -d .git ]]; then
  log "Git repository not found in $ROOT_DIR"
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet || [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
  STASH_NAME="auto-deploy-$(date +%Y%m%d-%H%M%S)"
  git stash push -u -m "$STASH_NAME" >/dev/null
  log "Saved local server changes to stash: $STASH_NAME"
fi

log "Fetching $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"

log "Checking out branch $BRANCH"
git checkout "$BRANCH" >/dev/null 2>&1 || true

log "Pulling latest changes"
git pull --ff-only "$REMOTE" "$BRANCH"

log "Rebuilding and starting containers"
docker compose down
docker compose up -d --build

log "Running Django check"
docker compose exec -T web python manage.py check

smoke() {
  local path="$1"
  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' "${APP_BASE_URL}${path}")"
  log "Smoke ${path} -> ${code}"
  case "$code" in
    200|301|302) ;;
    *)
      log "Unexpected status ${code} for ${path}"
      exit 1
      ;;
  esac
}

log "Running smoke checks"
smoke "/"
smoke "/ru/catalog/"
smoke "/ru/admin/login/"

log "Deploy complete"
