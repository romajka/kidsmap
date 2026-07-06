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

if [ "${RUN_COLLECTSTATIC_ON_RELEASE:-1}" = "1" ]; then
  "${PYTHON_BIN}" manage.py collectstatic --clear --noinput
fi

"${PYTHON_BIN}" manage.py check
