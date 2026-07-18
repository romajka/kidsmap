#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE="${REMOTE:-origin}"
BRANCH="${1:-main}"
APP_BASE_URL="${APP_BASE_URL:-http://127.0.0.1:8000}"
PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-https://kidsmap.az}"
ADMIN_BASE_URL="${ADMIN_BASE_URL:-https://admin.kidsmap.az}"
COMPOSE=(docker compose -f docker-compose.yml)

log() {
  printf '[deploy] %s\n' "$*"
}

cd "$ROOT_DIR"

if [[ ! -d .git ]]; then
  log "Git repository not found in $ROOT_DIR"
  exit 1
fi

ensure_web_running_on_failure() {
  local status=$?
  if [[ "$status" -eq 0 ]]; then
    return 0
  fi

  log "Deploy failed with status ${status}; ensuring web service is running"
  "${COMPOSE[@]}" up -d web >/dev/null 2>&1 || true
}

trap ensure_web_running_on_failure EXIT

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
log "Starting database"
"${COMPOSE[@]}" up -d db

log "Building new web image while current app stays online"
"${COMPOSE[@]}" build web

log "Running release tasks"
"${COMPOSE[@]}" run --rm web ./scripts/release-server.sh

log "Starting updated application"
"${COMPOSE[@]}" up -d --no-deps --force-recreate web

log "Checking migrations drift"
"${COMPOSE[@]}" exec -T web python manage.py makemigrations --check --dry-run

log "Running Django check"
"${COMPOSE[@]}" exec -T web python manage.py check

smoke() {
  local path="$1"
  local code
  local final_url
  read -r code final_url <<<"$(curl -sS -L --max-time 20 \
    -H 'X-Forwarded-Proto: https' \
    -o /dev/null \
    -w '%{http_code} %{url_effective}' \
    "${APP_BASE_URL}${path}")"
  log "Smoke ${path} -> ${code} (${final_url})"
  if [[ "$code" != "200" ]]; then
    log "Unexpected final status ${code} for ${path}"
    exit 1
  fi
}

purge_cloudflare_cache() {
  if [[ -z "${CF_API_TOKEN:-}" || -z "${CF_ZONE_ID:-}" ]]; then
    log "Skipping Cloudflare cache purge: CF_API_TOKEN or CF_ZONE_ID is not set"
    return 0
  fi

  if ! command -v curl >/dev/null 2>&1; then
    log "Skipping Cloudflare cache purge: curl is not installed"
    return 0
  fi

  local payload
  payload="$(cat <<JSON
{
  "files": [
    "${PUBLIC_BASE_URL}/",
    "${PUBLIC_BASE_URL}/az/",
    "${PUBLIC_BASE_URL}/en/",
    "${PUBLIC_BASE_URL}/ru/",
    "${PUBLIC_BASE_URL}/static/css/site.css",
    "${PUBLIC_BASE_URL}/static/admin/css/kidsmap_admin.css",
    "${ADMIN_BASE_URL}/admin/",
    "${ADMIN_BASE_URL}/admin/catalog/category/"
  ]
}
JSON
)"

  log "Purging Cloudflare cache for key public and admin URLs"
  curl -fsS -X POST "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/purge_cache" \
    -H "Authorization: Bearer ${CF_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "${payload}" >/dev/null
}

log "Running smoke checks"
smoke "/healthz"
smoke "/"
smoke "/catalog/"
smoke "/admin/"

purge_cloudflare_cache

log "Deploy complete"
