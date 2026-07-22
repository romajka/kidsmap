#!/usr/bin/env sh
set -eu

if [ -x "./.venv/bin/python" ]; then
  PYTHON_BIN="./.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  PYTHON_BIN="python3"
fi

case "${DJANGO_DEBUG:-0}" in
  1|true|True|yes|on) ;;
  *)
    if ! "${PYTHON_BIN}" manage.py migrate --check; then
      printf '%s\n' '[startup] PostgreSQL is unavailable or migrations are pending; refusing to start production web.' >&2
      exit 1
    fi
    ;;
esac

if [ "${USE_RUNSERVER:-0}" = "1" ]; then
  exec "${PYTHON_BIN}" manage.py runserver 0.0.0.0:${PORT:-8000}
fi

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers ${GUNICORN_WORKERS:-3} \
  --worker-class ${GUNICORN_WORKER_CLASS:-gthread} \
  --threads ${GUNICORN_THREADS:-4} \
  --timeout ${GUNICORN_TIMEOUT:-120} \
  --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT:-30} \
  --worker-tmp-dir ${GUNICORN_WORKER_TMP_DIR:-/dev/shm} \
  --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
  --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} \
  --log-level ${GUNICORN_LOG_LEVEL:-info} \
  --access-logfile - \
  --error-logfile - \
  --capture-output
