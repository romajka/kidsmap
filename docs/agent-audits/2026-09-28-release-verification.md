# Production release verification — 2026-09-28

User authorized push and deployment of all changes. This report supersedes the earlier read-only/local-only status for this release, while retaining the historical audit evidence.

## Main application release

Deployed commit `db6b1b0f20992686e0845bc51678ebe2772cef23` from `seo-indexability-20260916`; 70 changed files committed and pushed. Production Git checkout matched exactly, clean before/after activation. Running image: `sha256:550a7ae20ea1a719e776f55e114e5061c9348ad6dbd3caed3ffac6bff016c333`, started 2026-09-28 07:55:02 UTC. All 60 changed source/static files in the running image matched committed blobs by SHA256. `.env` absent from the image.

Migration plan contained only 0115/0116. Both applied successfully with statement/lock timeouts. `sync_site_defaults` filled blank footer_whatsapp; existing nonempty settings retained. Static rebuilt; translations compiled in image/release. Post-activation `migrate --check`, `check`, `makemigrations --check --dry-run` all passed. Existing image and static snapshot retained for rollback; private pre-release backups readable, initial archive successfully restored into isolated PostgreSQL as recorded in preflight.

Origin HTTP 200: healthz, home, catalog, contacts, FAQ, RU/EN catalog and contacts, admin login. Catalog HTML in AZ/RU/EN contains the expansion banner, new WhatsApp and new CSS version. External HTTPS 200: home, catalog, contacts, RU/EN catalog and admin login.

In the running production container, synthetic RequestFactory GET and duplicate-email POST returned 200 in AZ/RU/EN. Duplicate POST yielded an email field error in all languages. All diagnostics used explicit READ ONLY transactions and timeouts, synthetic in-memory actor/session/messages/cache; no accounts created or production records printed. Applied migration records confirmed for 0115/0116. Actual creation with two superadmins and all ordinary roles passed isolated PostgreSQL tests, not production writes.

## Supplemental frontend snapshot

During activation, four additional concurrent edits appeared in the worktree: base/back-to-top icon, header dropdown/check icons, catalog sort dropdown and catalog CSS. User's all-changes authorization covers these; staged snapshot captured separately after the first commit. Native sort-select submission remains canonical; custom buttons dispatch its change event. Added aria-controls/id relationship and CSS cache version 20260928_2; removed a trailing whitespace line without reverting concurrent changes.

Rendered Playwright checks used a complete staged-source copy under `/tmp/kidsmap-release-ui-source-20260928`, isolated SQLite/media/email/cache, disabled external integrations and a local server on 127.0.0.1:8767. No production browser account fixtures.

- Open/close sort menu with click; Escape closes and restores focus to catalog-sort-trigger.
- Enter, Tab, Tab, Enter selects price_asc; URL and native select reflect the chosen value.
- English pointer selection preserved q=robot and updated sort=price_asc after results reload; menu closed and selected text updated.
- AZ/RU/EN sort labels checked; at 390px document width equals viewport and sort trigger remains visible. At 1280px observed decorative hero/banner overflow; sort control itself remains inside viewport. This receipt does not claim a complete responsive redesign or full WCAG audit.
- Console initially clean; after rapid cross-page/AJAX interactions Chromium emitted one native "ViewTransition opt-in disabled" diagnostic. Selection and result reload still completed; no application exception stack observed.
- Supplemental Django suite: `catalog.testcases.test_catalog_expansion_banner catalog.testcases.test_site_whatsapp catalog.testcases.public.TestPublicPagesSmoke`: 91 tests, 90 passed, one pre-existing place-detail schema expectation failed, already reproduced on clean HEAD in preflight. Runner `/tmp/kidsmap-release-checks-20260928.py` with clean env, DJANGO_TESTING=1, SQLite :memory:, temporary media/email/cache.
- Staged diff whitespace check passed.

The supplemental snapshot is committed/pushed after this verification and deployed as the next image, with no additional migration. Its final commit/image are reported in the session and retained in the production release receipt directory.

## Remaining baseline scope

217 affected PostgreSQL tests passed. Default 618-test discovery has 19 failures/errors, all reproduced on clean HEAD with compiled catalogs. No weakened assertions. Full default suite is not green; unchanged baseline findings remain separately documented in preflight. Account-deletion retention-policy activation/scheduler remain pending and were not enabled by this code release.

Temporary private DB dump copies and isolated restore/test container were removed. Production recovery archives remain private in `/opt/kidsmap-releases/20260928-all-changes/`.
