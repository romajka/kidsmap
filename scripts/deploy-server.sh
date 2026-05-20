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
if ! git fetch "$REMOTE" "$BRANCH"; then
  log "git fetch failed."
  log "If GitHub SSH auth is not configured on the server, run:"
  log "  ./scripts/setup-github-ssh.sh"
  log "Then add the printed public key to GitHub and verify with:"
  log "  ssh -T git@github.com"
  exit 1
fi

log "Checking out branch $BRANCH"
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH" >/dev/null
else
  git checkout -b "$BRANCH" "$REMOTE/$BRANCH" >/dev/null
fi

log "Pulling latest changes"
if ! git pull --ff-only "$REMOTE" "$BRANCH"; then
  log "git pull failed. Check branch state and GitHub SSH access."
  exit 1
fi

log "Creating database backup"
./scripts/backup-db.sh

log "Rebuilding and starting containers"
docker compose down
docker compose up -d --build

log "Checking migrations drift"
docker compose exec -T web python manage.py makemigrations --check --dry-run

log "Running Django check"
docker compose exec -T web python manage.py check

log "Restoring featured public clubs"
docker compose exec -T web python manage.py restore_featured_places

smoke() {
  local path="$1"
  local code
  local final_url
  read -r code final_url <<<"$(curl -sS -L -o /dev/null -w '%{http_code} %{url_effective}' "${APP_BASE_URL}${path}")"
  log "Smoke ${path} -> ${code} (${final_url})"
  if [[ "$code" != "200" ]]; then
    log "Unexpected final status ${code} for ${path}"
    exit 1
  fi
}

log "Running smoke checks"
smoke "/"
smoke "/catalog/"
smoke "/admin/"

log "Deploy complete"
