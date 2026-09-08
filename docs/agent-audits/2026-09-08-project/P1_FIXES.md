# Исправления пяти P1 — 2026-09-08

User authorization: «исправь эти проблемы по одному». APPROVED IMPLEMENT, sequential SEC-01 → SEC-02 → BE-01 → OPS-01 → DB-01. LOCAL HEAD remains d75b34f4db5d4ba484cf8392ff3ae0c9939031e2 plus these WORKTREE fixes. No commit/push/deploy, production connection or real backup/migration execution. Previous audit remains a historical baseline, not the current status of these five source paths.

## Changes

| Finding | Final behavior | Regression |
|---|---|---|
| SEC-01 | Consumed verification records return failure without a user; provider-created verified records cannot authorize registration-code login; first verification still works | test_email_verification_consumption.py, 3 tests |
| SEC-02 | Every schema serializer in services/seo.py uses one JSON serializer escaping `<`, `>`, `&` as JSON Unicode escapes. Names/URLs/FAQ data round-trip unchanged and remain inside script raw text | test_json_ld_serialization.py, 3 tests |
| BE-01 | Admin empty tariff payload on an existing card with no relational rows no longer schedules destructive projection sync; actual tariff additions/removals retain existing behavior | test_admin_legacy_price_preservation.py, 3 tests |
| OPS-01 | pipefail propagates dump failure through gzip; failure removes partial output and exits before success message/retention | scripts/tests/test_backup_db.py, 3 tests |
| DB-01 | Command skips all existing relational tariffs, including inactive rows and mixed states with stale JSON. Apply reloads/locks Place before eligibility/input reads; first legacy conversion remains supported | test_pricing_migration_preservation.py, 5 tests |

These changes prevent the identified triggers; they do not reconstruct previously lost data. Skipped mixed legacy/modern pricing requires a separately reviewed reconciliation, not automatic merging. Other audit findings, including malformed schedule BE-03 and QA discovery QA-01, are outside these five fixes.

## Red → green evidence

Each regression was added and run before its corresponding implementation:

- SEC-01: 3 tests failed on original code; subsequent auth/new/Google selection: **65 tests, OK**.
- SEC-02: 3 tests failed on original serialization; new/SEO visibility/relational selection: **23 tests, OK**.
- BE-01: 1 of3 tests failed, showing all five scalar fields erased; new/pricing/readiness/JSON selection: **120 tests, OK**.
- OPS-01: dump-failure case failed, compression failure/success controls passed; after fix **3 tests, OK**.
- DB-01: 4 of5 tests failed, including loss of addon/metadata/inactive rows and incorrect skip reporting; new/relational/legacy selection: **42 tests, OK**.
- Final combined new Django regressions: **14 tests, OK**; final backup unittest: **3 tests, OK**. These are17 new tests. Intermediate selections overlap; their counts are not unique test coverage.

All Django commands use `.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py`: DJANGO_TESTING=1, cleared inherited credentials, disposable in-memory SQLite test DB, LocMem cache/email, scratch media/static, external socket connections disabled. Local scratch static directory created to remove missing-directory warning. Backup tests execute a copied script with an exported Docker function stub and synthetic temporary archives; no Docker daemon involved.

Exact commands (repository root):

```sh
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py test catalog.testcases.test_email_verification_consumption catalog.testcases.auth_flow catalog.testcases.test_google_auth --noinput --verbosity 0
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py test catalog.testcases.test_json_ld_serialization catalog.testcases.test_seo_landing_visibility catalog.testcases.pricing_plans_relational --noinput --verbosity 0
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py test catalog.testcases.test_admin_legacy_price_preservation catalog.testcases.pricing_plans catalog.testcases.pricing_plans_relational catalog.testcases.place_readiness catalog.testcases.test_place_json_and_pricing_modes catalog.testcases.test_json_roundtrip_audit --noinput --verbosity 0
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py test catalog.testcases.test_pricing_migration_preservation catalog.testcases.pricing_plans_relational catalog.testcases.legacy_migrations --noinput --verbosity 0
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py test catalog.testcases.test_email_verification_consumption catalog.testcases.test_json_ld_serialization catalog.testcases.test_admin_legacy_price_preservation catalog.testcases.test_pricing_migration_preservation --noinput --verbosity 0
python3 -m unittest discover -s scripts/tests -p test_backup_db.py -v
bash -n scripts/backup-db.sh
.venv/bin/python /tmp/kidsmap-audit-20260908-qa/run.py makemigrations --check --dry-run
git diff --check
```

Every final command exited0; migration drift check: No changes detected. Red commands used each new Django module individually, or the same backup unittest command, before the fix; exited1 with failures above.

## Review / boundaries

Root implemented in sequence and reviewed final source diff. Existing worker /root/audit_backend performed a separate bounded read-only review of BE-01/DB-01 and their new tests; no introduced correctness issue found, no tests/DB run by that reviewer. Codebase Memory discovery/coverage followed by actual source checks; new test files metadata_match/no_recorded_issue, best-effort only.

Final hash comparison against the2686-file audit baseline finds exactly five changed tracked implementation files: scripts/backup-db.sh, domain_admin/place.py, services/email_verification.py, services/seo.py, management/commands/migrate_pricing_plans.py. Previous tracked agent-team work preserved. Added four Django test modules, one backup test module, plan and this report; audit master receives a status notice.

NOT RUN: PostgreSQL locks/concurrent writers, full default suite/CI, real Google OAuth, browser JS execution of JSON-LD, real backup restoration/deploy/production migrations. New JSON tests check real serialized payloads with HTMLParser and JSON decoding. Sequential challenge reuse is covered; existing concurrent OTP consumption risk remains outside this bounded fix. The Place lock coordinates migration instances; no claim that all unrelated pricing writers obey the same lock. Backup tests cover control flow, not database restore validity. Production remains unchanged until a separately authorized release.
