#!/usr/bin/env bash
# Local dev server for design work: updates the venv, checks Django, starts
# runserver on 127.0.0.1:8000. Full output goes to .tmp/dev_server.log so it
# can be read when something fails.
cd "$(dirname "$0")/.." || exit 1
mkdir -p .tmp
LOG=.tmp/dev_server.log
: > "$LOG"
export DJANGO_DEBUG=1
{
  echo "== $(date) =="
  echo "python3: $(command -v python3) $(python3 --version 2>&1)"
  if [ ! -x .venv/bin/python ]; then
    echo "-- creating .venv"
    python3 -m venv .venv || exit 1
  fi
  # mysqlclient needs system headers and is only used in production.
  grep -viE '^\s*mysqlclient' requirements.txt > .tmp/requirements-dev.txt
  echo "-- installing requirements"
  .venv/bin/python -m pip install -q --disable-pip-version-check -r .tmp/requirements-dev.txt || echo "!! pip install failed"
  echo "-- django check"
  .venv/bin/python manage.py check || echo "!! django check failed"
  if command -v ss >/dev/null && ss -ltn 2>/dev/null | grep -q ':8000 '; then
    echo "!! port 8000 is already in use:"; ss -ltnp 2>/dev/null | grep ':8000 '
  fi
  echo "-- starting server on http://127.0.0.1:8000"
} 2>&1 | tee -a "$LOG"
.venv/bin/python manage.py runserver 127.0.0.1:8000 2>&1 | tee -a "$LOG"
