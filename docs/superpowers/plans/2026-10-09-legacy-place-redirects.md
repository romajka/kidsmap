# Legacy Place Redirects Implementation Plan

**Goal:** Restore old `/<id>-<slug>/` place links with permanent redirects to the current public URL in the requested language.

**Architecture:** Add a narrowly matched root route and reuse `place_detail_legacy`. The existing published/active/not-deleted lookup is shared with the public detail view. Ignore the obsolete slug; identify the place only by its numeric ID.

**Tech Stack:** Existing Django URL routing and isolated PostgreSQL tests.

**Spec:** User-approved scope in this chat, 2026-10-09: local 301 redirects, AZ/RU/EN, no loops, hidden/deleted places retain 404. No production deployment.

## Constraints

- Preserve dirty work; LOCAL HEAD `2da9d33a`, branch `task33-progress`, active_run NONE at preflight.
- No migrations, metadata/canonical policy changes, production writes, commit or push.
- Test with DJANGO_TESTING=1, disposable PostgreSQL/cache/media and disabled external services.

## Task: Old root URLs

Files: modify `src/catalog/urls.py` and `src/catalog/views.py`; create `src/catalog/testcases/test_legacy_root_place_redirects.py`.

- [x] Add regression tests for GET/HEAD, AZ/RU/EN, localized URL flag on/off, missing/draft/inactive/deleted places, and one-hop termination at a 200 detail page.
- [x] Run `python3 docs/task33/qa04/run.py --output /tmp/kidsmap-seo-legacy-red-20261009 --label catalog.testcases.test_legacy_root_place_redirects`; verify the public legacy URL test fails with 404 instead of 301.
- [x] Register `re_path(r"^(?P<pk>[0-9]+)-(?P<slug>[^/]+)/$", place_detail_legacy, name="place_detail_root_legacy")` at the end of the catalog routes; accept optional `slug=None` in the existing view. Use its unchanged public lookup and permanent redirect.
- [x] Repeat the isolated run with new regressions, `test_localized_place_seo`, and `test_seo_indexability`; inspect exact counts and environment checks.
- [x] Compare changed files against saved pre-edit copies; record results and limitations. Do not deploy or request indexing before deployment.
