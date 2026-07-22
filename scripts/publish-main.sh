#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "" ]]; then
  printf 'Usage: %s "Commit message"\n' "$0" >&2
  exit 2
fi

if [[ "$(git branch --show-current)" != "main" ]]; then
  printf 'Refusing to publish: switch to main first.\n' >&2
  exit 1
fi

git diff --check
git add -A

if git diff --cached --quiet; then
  printf 'Nothing to publish.\n'
  exit 0
fi

git commit -m "$1"
git push origin main

printf '\nPublished to GitHub. To deploy: ./scripts/deploy-production.sh\n'
