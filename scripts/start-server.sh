#!/usr/bin/env sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${USE_RUNSERVER:-0}" = "1" ]; then
  exec python manage.py runserver 0.0.0.0:${PORT:-8000}
fi

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers ${GUNICORN_WORKERS:-3} \
  --timeout ${GUNICORN_TIMEOUT:-120}

