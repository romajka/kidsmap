#!/usr/bin/env sh
set -eu

if [ -x "./.venv/bin/python" ]; then
  PYTHON_BIN="./.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  PYTHON_BIN="python3"
fi

"${PYTHON_BIN}" manage.py migrate --noinput
"${PYTHON_BIN}" manage.py compilemessages --ignore .venv --ignore venv || true

# Production uses ManifestStaticFilesStorage, so stale static manifests turn
# missing asset references into 500s. Refresh staticfiles on every non-debug
# container start unless explicitly disabled.
if [ "${RUN_COLLECTSTATIC_ON_START:-auto}" = "1" ] || \
   { [ "${RUN_COLLECTSTATIC_ON_START:-auto}" = "auto" ] && [ "${DJANGO_DEBUG:-0}" != "1" ]; }; then
  "${PYTHON_BIN}" manage.py collectstatic --clear --noinput
fi
"${PYTHON_BIN}" manage.py check
