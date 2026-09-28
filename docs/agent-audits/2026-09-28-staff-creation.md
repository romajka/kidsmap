# Staff creation: local fix and verification

Snapshot: LOCAL HEAD `ef949ea99a7635076e4477a29d42b0a5d63796d4`; pre-existing dirty WORKTREE preserved. PRODUCTION checkout has the same HEAD and was clean when inspected. Running Django 6.0.2; hashes of staff admin source and add template matched local source before this fix.

Authorization: user requested the staff creation fix. Production strictly read-only; no migration, deployment, restart, configuration change, user creation, commit or push. Roles performed inline, without delegated independent review.

## Confirmed defect

`StaffAccessUserCreationForm` accepts an existing User email. Migration 0101 protects `auth_user` with the database-only `kidsmap_user_email_ci_unique` index on `LOWER(TRIM(email))`, excluding empty emails. ModelForm validation does not know this database-only index. Saving a duplicate raises unhandled IntegrityError at `StaffAccessUserAdmin.save_model()`.

The new regression test failed before the change with `UNIQUE constraint failed: index 'kidsmap_user_email_ci_unique'` for two creators and three case/whitespace variants. In production, a read-only form validation using an existing email internally returned valid=True and no field errors. Only booleans/field names were output; email/account values were never copied into artifacts.

Retained container logs contain seven POST 500s on this route on September 23–24, 2026; the ten GETs returned 200. The original exception traceback was not present in retained output, so the duplicate-email defect cannot be asserted as the cause of every historical 500. Synthetic production GET rendering in AZ/RU/EN returned 200 under explicit read-only transactions and 15s statement/2s lock timeouts, with an in-memory synthetic user/session/messages/cache. First diagnostic attempt lacked LANGUAGE_CODE, a RequestFactory setup issue corrected on the next run.

Production tables for UserProfile, StaffRoleAudit and SuperadminPromotionRequest exist; catalog migrations reach 0114 and the normalized email unique index exists. Inspection used explicit READ ONLY transactions with timeouts and rollback. No production POST was executed.

## Change

`src/catalog/domain_admin/user.py:StaffAccessUserCreationForm.clean_email` now trims email and checks all User accounts using the index's normalization. A duplicate returns an email field ValidationError: «Пользователь с таким email уже существует.» Empty email remains optional, as before. No schema change or privilege changes.

`src/catalog/testcases/test_staff_creation.py` verifies the real admin route: two superadmins, moderator/content_manager/volunteer creation, password hashing, exactly one profile, proxy User linkage, expected groups/permissions and role audit; AZ/RU/EN GET rendering; missing/duplicate username, malformed/duplicate email, missing/weak/mismatched password, missing/invalid/forged superadmin role; limited staff with add/change model permissions still receive 403.

## Verification

All test commands used a clean environment, DJANGO_TESTING=1 and DJANGO_DEBUG=1. SQLite database was in memory, cache LocMem, email test backend, external integration credentials absent. PostgreSQL 17 used a newly created disposable local container on 127.0.0.1:55441 with tmpfs data, isolated from existing local databases and production. The PostgreSQL runner `/tmp/kidsmap-staff-test-runner.py` used temporary media, LocMem email and disabled integration keys. Its connection password is a dummy fixture for the disposable trust-auth database.

Labels for expanded suite: `catalog.testcases.test_staff_creation catalog.testcases.admin.UserAdminUXTests catalog.testcases.test_staff_role_workflow catalog.testcases.test_staff_profile`.

| Command | Result |
| --- | --- |
| `env -i PATH=/usr/bin:/bin HOME=/home/ramin DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=sqlite:///:memory: .venv/bin/python manage.py test catalog.testcases.test_staff_creation.StaffCreationRegressionTests.test_existing_email_is_a_validation_error_for_both_creators --noinput -v 1` before fix | Exit 1: 6 duplicate-email IntegrityErrors, establishing RED |
| Same isolated SQLite command, expanded labels above | Exit 0: 41 tests, 40 passed, one PostgreSQL-only concurrency test skipped |
| `env -i PATH=/usr/bin:/bin HOME=/home/ramin DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=postgresql://postgres:stafftest@127.0.0.1:55441/postgres .venv/bin/python /tmp/kidsmap-staff-test-runner.py` with expanded labels above | Exit 1: 41 tests, 37 passed, 4 errors in pre-existing superadmin promotion confirmation flow |
| Same PostgreSQL command with `catalog.testcases.test_staff_creation` only | Exit 0: all 5 tests passed |
| Same PostgreSQL runner with KIDSMAP_STAFF_SOURCE=/tmp/kidsmap-staff-baseline-20260928/src and KIDSMAP_STAFF_TEST_DB=test_staff_baseline; label `catalog.testcases.test_staff_role_workflow.StaffRoleWorkflowTests.test_superadmin_promotion_requires_a_different_active_superadmin` | Exit 1: same promotion exception on clean HEAD source exported by `git archive HEAD src static locale` |
| `env -i PATH=/usr/bin:/bin HOME=/home/ramin DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=sqlite:///:memory: .venv/bin/python manage.py check` | Exit 0, no issues |
| `.venv/bin/python -m compileall -q src/catalog/domain_admin/user.py src/catalog/testcases/test_staff_creation.py` | Exit 0 |
| `git diff --check -- src/catalog/domain_admin/user.py` | Exit 0 |

An initial PostgreSQL runner attempt without a URL password stopped at configuration validation before testing; corrected to the dummy test password. Global `git diff --check` also reported an unrelated trailing blank line in pre-existing `static/css/pages/catalog_places.css`; it was not changed.

## Separate baseline finding

`src/catalog/services/staff_role_workflow.py:resolve_superadmin_promotion` applies `select_for_update()` to a queryset with nullable outer joins. PostgreSQL raises `NotSupportedError: FOR UPDATE cannot be applied to the nullable side of an outer join`. Three confirmation tests and one concurrency test fail for this reason. Confirmed on clean HEAD, so this is independent of the new email validation. Ordinary staff creation and role assignment pass. Recommendation: a separate scoped backend fix should restrict locked tables and rerun confirmation/concurrency tests. No assertion changes or unrelated fixes made here.

## Limits and handoff

- Fix is LOCAL ONLY. Existing production behavior remains until an explicitly approved release. Need release-reviewer for a patch containing only this admin validation and its tests, excluding the extensive pre-existing dirty worktree.
- No rendered-browser QA or real production account creation; HTML rendering and creation acceptance were tested against isolated fixtures.
- Concurrent writers inserting the same email between validation and save can still race the database index; that race was not changed or tested in this bounded fix.
- Exact submitted payloads for historical 500s are unknown. If a GET still fails for a real account, a fresh safe traceback is needed; neither retained access logs nor current read-only synthetic GET reproduced it.
