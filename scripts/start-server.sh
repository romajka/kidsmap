#!/usr/bin/env sh
set -eu

if [ -x "./.venv/bin/python" ]; then
  PYTHON_BIN="./.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  PYTHON_BIN="python3"
fi

if [ "${USE_RUNSERVER:-0}" = "1" ]; then
  exec "${PYTHON_BIN}" manage.py runserver 0.0.0.0:${PORT:-8000}
fi

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers ${GUNICORN_WORKERS:-3} \
  --timeout ${GUNICORN_TIMEOUT:-120} \
  --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT:-30} \
  --worker-tmp-dir ${GUNICORN_WORKER_TMP_DIR:-/dev/shm} \
  --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
  --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
  --access-logfile - \
  --error-logfile - \
  --capture-output
