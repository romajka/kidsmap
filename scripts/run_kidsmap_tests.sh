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
  seo)
    run_suite \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_robots_txt_disallows_private_sections \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_includes_all_languages_and_hreflang_alternates \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_and_robots_use_configured_public_origin \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_xml_is_valid_xml \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_excludes_place_new \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_excludes_draft_places \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_excludes_deleted_places \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_has_no_duplicate_urls \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_lastmod_matches_model_updated_at \
      src.catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_does_not_contain_changefreq_or_priority \
      src.catalog.testcases.test_seo_landing_visibility
    ;;
  full)
    run_suite catalog
    ;;
  *)
    echo "Unknown suite: $SUITE" >&2
    echo "Available suites: smoke, auth, public, admin, owner, catalog, seo, full" >&2
    exit 1
    ;;
esac
