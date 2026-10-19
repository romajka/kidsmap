#!/usr/bin/env bash
# Read-only preflight. Never recreate a container to recover its private files.
set -euo pipefail

container="$(docker compose ps --all -q web)" || exit 1
[[ -n "$container" ]] || exit 0
mounts="$(docker inspect --format '{{range .Mounts}}{{println .Destination}}{{end}}' "$container")" || exit 1

for root in /kidsmap-private-media /app/private_media_drafts; do
  covered=0
  while IFS= read -r mount; do
    mount="${mount%/}"
    [[ -n "$mount" ]] || continue
    if [[ "$root" == "$mount" || "$root" == "$mount/"* ]]; then
      covered=1
      break
    fi
  done <<< "$mounts"
  [[ "$covered" -eq 0 ]] || continue
  # Only an empty or absent directory is safe. No filenames/content are logged.
  if ! docker exec "$container" sh -c '
    root="$1"
    [ ! -e "$root" ] && exit 0
    [ -d "$root" ] && [ ! -L "$root" ] || exit 1
    found=$(find "$root" -mindepth 1 -print -quit) || exit 1
    [ -z "$found" ]
  ' sh "$root"; then
    printf '[deploy] Private storage is not protected by a mount. Preserve and verify it using docs/PRIVATE_STORAGE_RELEASE.md before deployment.\n' >&2
    exit 1
  fi
done
