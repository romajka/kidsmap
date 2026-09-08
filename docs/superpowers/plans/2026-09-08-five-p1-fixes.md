# Five P1 fixes Implementation Plan

Goal: fix SEC-01, SEC-02, BE-01, OPS-01, DB-01 sequentially with regression evidence.
Architecture: preserve existing service/form/command boundaries; reject consumed verification challenges, share HTML-safe JSON serialization, preserve scalar-only cards, fail backup pipelines before retention, skip relationally migrated places. No schema changes or production commands.
Tech stack: existing Python/Django, Bash, unittest.
Spec: docs/agent-audits/MASTER_AUDIT.md and linked domain reports. User explicitly authorized all five fixes, one at a time. Execute inline; no commit/push/deploy, preserve prior work.

## Task 1 — SEC-01
- [x] Add discovered test module test_email_verification_consumption.py: consumed/Google-verified records cannot authorize a new session; first valid registration still succeeds through existing auth_flow tests.
- [x] Run failing tests using isolated /tmp/kidsmap-audit-20260908-qa/run.py.
- [x] Modify services/email_verification.py: reject is_verified before returning any authenticated user; retain normal first verification.
- [x] Run new tests and existing auth/Google suites; inspect failures before proceeding.

## Task 2 — SEC-02
- [x] Add test_json_ld_serialization.py checking JSON value round-trip and HTML script-boundary containment for actual SEO serializers.
- [x] Run failing regression.
- [x] Add shared serializer in services/seo.py: JSON then escape &, <, > as JSON Unicode escapes; replace schema JSON dumps there.
- [x] Verify new regression and existing SEO/schema tests; no UI redesign.

## Task 3 — BE-01
- [x] Add test_admin_legacy_price_preservation.py: ordinary scalar-only published save preserves all five price columns; new tariff replaces projections; deleting real tariffs still works.
- [x] Run failing preservation regression.
- [x] Modify domain_admin/place.py to avoid scheduling empty relational replacement for untouched scalar-only tariff cards, matching existing owner behavior; explicit relational edits retain replacement semantics.
- [x] Run regression and existing pricing/readiness/JSON suites.

## Task 4 — OPS-01
- [x] Add scripts/tests/test_backup_db.py using copied script, exported Docker function stub, disposable backups only; dump failure must fail, remove incomplete output and retain old backups; success must produce valid gzip.
- [x] Run red regression.
- [x] Enable pipefail in scripts/backup-db.sh; verify retention remains intentional on successful dump.
- [x] Run unittest and bash -n; never run against real Docker or backups.

## Task 5 — DB-01
- [x] Add test_pricing_migration_preservation.py: modern primary+addon+localized data unchanged by apply and dry-run; scalar-only legacy conversion works and rerun preserves edited tariffs.
- [x] Run failing regression.
- [x] Modify migrate_pricing_plans command to skip existing relational plans, recheck under Place row lock inside apply transaction before conversion; retain mixed-state data for manual review rather than overwrite.
- [x] Run new and existing relational/legacy suites, check migration drift and final diff.

## Closure
Record exact red/green results and current limitations. This fixes local code, not already-lost data, deployed production or untested concurrent writers. Other P2 findings remain outside these five fixes.

Completed evidence: docs/agent-audits/2026-09-08-project/P1_FIXES.md.
