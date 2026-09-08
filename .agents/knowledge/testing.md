# Testing knowledge — KidsMap

> Актуализация 2026-09-08: [current snapshot](current-snapshot.md) уточняет LOCAL HEAD, volunteer workspace, MCP и native agents. Текст ниже — датированный срез 2026-09-06; production факты и untracked/dirty пометки не описывают сегодняшнее состояние. Перед использованием перепроверить source.

AS-IS discovery: 2026-09-06, local `main` at `df6fef3` plus a large pre-existing working diff. Production is a separate clean checkout at `86a0b8c` on `readiness-legacy-migration`; local results do not certify it. See [architecture](architecture.md), [source of truth](source-of-truth.md), and [deployment](deployment.md).

## Test surfaces

| Surface | Actual source / invocation |
| --- | --- |
| Domain Django tests | `src/catalog/testcases/`; `src/catalog/tests.py:1` imports non-prefixed domain suites, alongside discoverable `test_*.py` modules |
| Suite wrapper | `scripts/run_kidsmap_tests.sh:22`: smoke, auth, public, admin, owner, catalog, seo, full |
| Authentication | `auth_access.py`, `auth_flow.py`, `test_password_reset.py`, `test_google_auth.py`; the wrapper's auth suite currently omits the two standalone modules |
| Business invariants | `pricing_plans.py`, `pricing_plans_relational.py`, `place_card_validation.py`, `permanent_place_wizard.py`, `test_place_json_and_pricing_modes.py`, `test_json_roundtrip_audit.py` |
| Media/contact flows | `image_uploads.py`, `photo_workflow.py`, `phone_reveal.py` |
| SEO/analytics | `test_seo_audit_system.py`, `test_seo_landing_visibility.py`, `test_indexnow.py`, `test_ai_referral_tracking.py`, `tracking.py` |
| JavaScript logic | `node static/js/tests/ai_referral_tracking.test.js` |
| DOM interaction | `node --test scripts/test_phone_reveal.cjs scripts/test_photo_editor.cjs`; both require jsdom from ignored `.tmp/phone-dom/node_modules` |
| Rendered browser checks | `scripts/test_mobile_navigation.sh`, `scripts/test_footer_overflow.sh`; require an installed external Playwright CLI wrapper and a running test app |

No repository package manifest/lock or Playwright test configuration was found in discovery. DOM tests substitute browser APIs and are not rendered browser QA. Existing browser scripts cover narrow scenarios, not the entire product.

## Safe execution boundary

Audit mode permits source reading and isolated test execution; it does not permit production writes. Never run tests against production credentials, production media, or a shared production Redis. Django tests create/write/drop a test database, so they are not production read-only checks. Do not run deploy, release, backup retention, seed/import, migrate, or cleanup commands as verification during this audit.

Set `DJANGO_TESTING=1` **before** Django loads settings. `src/config/test_runner.py:28` calls `cache.clear()` per test; only `src/config/settings.py:390`'s testing branch guarantees LocMem. The suite wrapper does not set this flag. Explicitly select a disposable local PostgreSQL database/role for PostgreSQL-sensitive tests; verify the selected engine/host/database without printing credentials. Use temporary media storage for any uploads. SQLite results do not establish PostgreSQL constraints, concurrency, lock or migration behavior.

After isolation is established, examples:

```powershell
$env:DJANGO_TESTING = '1'
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe manage.py test catalog.testcases.auth_access catalog.testcases.auth_flow catalog.testcases.test_google_auth catalog.testcases.test_password_reset --noinput
```

Choose targeted domains by changed behavior; record exact labels, environment, snapshot, exit code, counts and skipped checks. Broaden once when integration risk justifies it. A test that passes by mocking Google HTTP verifies the application's callback handling, not a real Google Cloud client or live sign-in. A GET smoke check can trigger application tracking, so production browsing needs the audit's explicitly bounded read-only interpretation.

## CI and evidence

`.github/workflows/deploy.yml:12` provisions PostgreSQL 17 and Redis 7.4 on Ubuntu, uses Python 3.12, installs pinned requirements, applies migrations, checks drift/system checks, then runs `manage.py test --parallel auto` (:69). It does not run the Node or browser suites. Its deploy job runs only after quality succeeds on push to main. This describes configuration; no current GitHub run was inspected during discovery.

Historical evidence must remain dated and separate from fresh audit results:

- `docs/FULL_READINESS_SYNC_REPORT.md:226` records discovery of 807 tests and a later 271-test rerun: 250 passed, 20 failed, one errored; all 21 failures/errors reproduced on its pristine donor. The exact list follows at :230. This is not the current baseline.
- `docs/superpowers/plans/2026-09-06-phone-reveal.md:14` records 61 Django and three DOM tests passed, browser unavailable, and a map count failure reproduced at HEAD (five queries versus four expected). `src/catalog/testcases/catalog.py:159` contains that expectation.
- Historical auth-copy failures may have been addressed in the local working diff. Never automatically relabel a newly observed failure as inherited; reproduce on the relevant clean baseline or mark attribution UNKNOWN.

Fresh commands and their results belong in `docs/agent-audits/qa.md` / `browser.md`; a missing browser, database or credential is NOT VERIFIED, not PASS. Initial discovery for this document ran no tests and changed no application data.
