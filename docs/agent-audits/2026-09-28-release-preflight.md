# Approved release preflight — 2026-09-28

User explicitly authorized committing/pushing all changes and applying them on server 157.173.119.227. Earlier read-only boundary is superseded for this release. Work performed inline, without delegated independent audits. Initial local/remote/production HEAD: `ef949ea99a7635076e4477a29d42b0a5d63796d4`, branch `seo-indexability-20260916`. Production checkout clean before release. No merge to main requested or performed.

## Scope

All existing tracked/untracked source, tests, styles and documentation changes; moderation SLA queue/lifecycle, volunteer editor and duplicate/deletion guards, catalog/contact UI and new WhatsApp defaults, account-deletion PostgreSQL locking fix, staff creation email validation. Also removed nullable related joins from the locked superadmin promotion request query; target locking remains explicit and existing confirmation/concurrency tests pass. Added cache versions `20260928_1` for changed CSS/JS consumers. Removed a trailing blank line from the modified catalog stylesheet.

No secrets, database/media artifacts or temporary files staged. Credential-pattern scan produced zero matching paths; forbidden artifact-path scan produced zero. Retention-policy operational activation remains pending; release does not invent policy settings or delete real accounts.

## Verification

New disposable PostgreSQL 17 container `kidsmap-release-tests-20260928`, loopback 55442, tmpfs data. All tests: clean environment, DJANGO_TESTING=1, isolated LocMem cache/email, temporary media, disabled external integrations. Fast password hasher used only in the test runner. Runner: `/tmp/kidsmap-release-checks-20260928.py`; logs outside repository.

Command prefix:

```sh
env -i PATH=/usr/bin:/bin HOME=/home/ramin DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=postgresql://postgres:releasetest@127.0.0.1:55442/postgres .venv/bin/python /tmp/kidsmap-release-checks-20260928.py
```

- Default discovery: **618 tests, 599 passed, 15 failures + 4 errors**, 245.662s. This default discovery omits standalone test modules, so it was supplemented explicitly.
- Affected suite: **217 tests, all passed, no skips**, 67.425s; KIDSMAP_RELEASE_TEST_DB=test_kidsmap_release_affected. Labels: `catalog.testcases.test_volunteer_admin`, `test_moderation_sla`, `test_account_deletion`, `test_volunteer_dashboard`, `test_review_confirmation`, `test_place_review_cooldown`, `place_readiness`, `test_staff_creation`, `test_staff_role_workflow`, `test_staff_profile`, `test_site_whatsapp`, `test_catalog_expansion_banner`, `specialists` (all under catalog.testcases).
- Clean HEAD baseline: exported `git archive HEAD src static locale` to `/tmp/kidsmap-staff-baseline-20260928`, compiled translations, reran all 19 failing labels with KIDSMAP_RELEASE_SOURCE pointing to that source and KIDSMAP_RELEASE_TEST_DB=test_kidsmap_release_baseline. **Same 15 failures + 4 errors**, 7.879s. Failure-name set exactly matches; no new failure names. An initial baseline without compiled catalogs reproduced 18; compiling catalogs also reproduced the tariff-copy language assertion.
- Check-only runner: `KIDSMAP_RELEASE_CHECK_ONLY=1` with the prefix above: `check` no issues; `makemigrations --check --dry-run` no changes.
- `node --check static/admin/js/volunteer_place_form.js`: exit 0.
- `.venv/bin/python -m compileall -q src/catalog`: exit 0.
- `git diff --cached --check`: exit 0.

Baseline failure groups: geographic assignment/publication guards and outdated district/map fixtures, filter counts/subcategories, admin pagination, tariff validation language and a place-detail schema expectation. Assertions were not weakened. Entire default suite is not green; release acceptance is based on identical baseline failure set plus passing affected suite. Rendered-browser evidence for the volunteer/SLA/owner changes is in the earlier remediation verification report; no new rendered-browser claim is made by backend tests.

## Recovery preparation

Production services healthy/running; 66GB available before release. Preserved previous image ID `sha256:7569d21e4ae272c26fa7a89900732bd011573a32f3833715d350e09549c0f0bb` as `kidsmap-web:rollback-20260928-ef949ea9`.

Private production-only recovery files: `/opt/kidsmap-releases/20260928-all-changes/`; rollback compose override, previous revision/image, database custom archive, compressed static snapshot. Archive sizes at preparation: database 1,140,804 bytes; static 61,239,212 bytes. Database archive readable (716 TOC listing lines), static archive readable. No retention-cleanup script invoked.

Database backup successfully restored into the disposable local PostgreSQL database `kidsmap_release_restore_check` with pg_restore --exit-on-error --no-owner --no-privileges. Verified only aggregates: 65 public tables, 148 migrations, 340 Places. No production records printed or added to repository. Initial stdin-based transport attempts yielded an empty stream; retried by SCP and docker cp, then file-based restore succeeded. Temporary private copies are removed after verification.

New migrations 0115/0116 add nullable lifecycle columns and the needs_changes status choice; no data backfill, deletion or renaming. Previous application image remains compatible with additive columns for rollback. Migration plan is verified again against production before execution.

Status at this receipt: preflight complete, release authorized, activation not yet performed. Final deployed revision, image and health are reported after activation.
