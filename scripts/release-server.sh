#!/usr/bin/env sh
set -eu

if [ -x "./.venv/bin/python" ]; then
  PYTHON_BIN="./.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  PYTHON_BIN="python3"
fi

# The Python default introduced in0142 is not a persistent SQL default.
# Confirm the externally enforced maintenance boundary before the whole batch.
MIGRATION_PLAN="$("${PYTHON_BIN}" manage.py showmigrations catalog --plan)"
if printf '%s\n' "$MIGRATION_PLAN" | grep -Eq '^\[ \] catalog\.014(2_workflownotification_event_context|4_workflownotification_event_context_db_default)([[:space:]]|$)'; then
  if [ "${KIDSMAP_WRITERS_STOPPED:-0}" != "1" ]; then
    printf '%s\n' 'Release blocked: stop and verify all writers before0142–0144; see docs/PRIVATE_STORAGE_RELEASE.md.' >&2
    exit 1
  fi
fi

"${PYTHON_BIN}" manage.py migrate --noinput
"${PYTHON_BIN}" manage.py sync_site_defaults
# NOTE: seed_catalog_taxonomy is NOT run on deploy.
# It must only be run manually for an empty database:
#   python manage.py seed_catalog_taxonomy --force

# Rebuild project translation binaries from source .po files on every release.
find locale -path '*/LC_MESSAGES/django.mo' -type f -delete 2>/dev/null || true
"${PYTHON_BIN}" manage.py compilemessages --ignore .venv --ignore venv

if [ "${RUN_COLLECTSTATIC_ON_RELEASE:-1}" = "1" ]; then
  "${PYTHON_BIN}" manage.py collectstatic --clear --noinput
fi

"${PYTHON_BIN}" manage.py check
