#!/usr/bin/env bash
set -euo pipefail

if [ -x "./.venv/bin/python" ]; then
  PYTHON_BIN="./.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  PYTHON_BIN="python3"
fi

SUITE="${1:-smoke}"
shift || true

run_suite() {
  "${PYTHON_BIN}" manage.py test "$@" "${EXTRA_ARGS[@]}"
}

EXTRA_ARGS=("$@")

case "$SUITE" in
  smoke)
    run_suite \
      src.catalog.testcases.tracking \
      src.catalog.testcases.auth_access
    ;;
  auth)
    run_suite \
      src.catalog.testcases.auth_access \
      src.catalog.testcases.auth_flow
    ;;
  public)
    run_suite src.catalog.testcases.public
    ;;
  admin)
    run_suite src.catalog.testcases.admin
    ;;
  owner)
    run_suite src.catalog.testcases.owner
    ;;
  catalog)
    run_suite src.catalog.testcases.catalog
    ;;
  full)
    run_suite catalog
    ;;
  *)
    echo "Unknown suite: $SUITE" >&2
    echo "Available suites: smoke, auth, public, admin, owner, catalog, full" >&2
    exit 1
    ;;
esac
