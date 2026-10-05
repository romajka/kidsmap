# Stage23 owner/admin closure

2026-10-03; executor `/root/stage23_owner_admin`, canonical django-reviewer, bounded LOCAL ACCEPTANCE implementation authorized by the direct request to finish stage23 and root's source ownership assignment. LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`, branch `task33-progress`; dirty WORKTREE, not a release commit. Entry preservation is root's snapshot. No production, commit, push or deployment actions.

## Result

Assigned original full-suite evidence contains **98 problem entries / 87 unique test IDs**. Every ID is mapped to a verified source/decision category in `23-owner-admin-classification.json`; duplicates represent subtests. No tests were skipped/deleted and obsolete assertions were not rewritten wholesale to produce a green full suite. Current equivalents and the corrected fixtures passed **161/161, 0 failures, 0 errors, 0 skips** on isolated PostgreSQL17.11.

One real current R1 defect was found and fixed: **R1-MEDIA-01**, gallery upload with a valid signed publication token and a storage error escaped as an OSError instead of returning an editable field error. `publication_forms.gallery_from_form` now handles OSError/RuntimeError consistently with the existing main-image path. The transaction retains approved content and creates no candidate/gallery row after the failed upload. New `test_task33_r1_owner_safety.py` validates that failure, pending main-photo approval, pending gallery ordering with foreign-ID rejection and token/outsider denial.

The parent still owns final whole-suite reconciliation, rendered browser evidence and stage23 acceptance. This report does not declare those checks complete.

## Contract reconciliation

Source/decision-backed intentional differences: D01 removes the fixed ten-place cap; D03 suspends the prior team on ownership transfer; D04 uses signed candidate/version checks and preserves approved content; D05 replaces the old seven-step owner wizard with the continuous editor; D06 makes media/map points optional and permits website/WhatsApp contacts (ten mandatory readiness items); D07 reserves review moderation for KidsMap and uses approved/pending review versions. Restoring the old expectations would violate the accepted product contract.

Three Russian image-error assertions now explicitly select RU, preserving their exact validation-message checks. `TestCreatedByIsAuditOnly` now grants the fixture reviewer the required `change_placeownershiprequest` permission; all creator/ownership/audit assertions remain. Its old membership-survival test was replaced with an explicit D03/D07 suspension test: the row survives, is inactive, and grants no old view/edit/team/moderation rights. Volunteer restart now asserts the empty patch, current base snapshot and actual reloaded editor value. Duplicate-create concurrency explicitly seeds its EDU taxonomy because TransactionTestCase flushes migration-seeded data; the original one-success/one-refusal and one-record assertions remain.

The classification separately flags same-ID stage04 baseline failures. In particular, the pagination fixture filters by a city alias while its stored district is resolved, and the AZ-name test supplies a nonempty AZ description while requiring a description error. These old cases are not a claim that the whole legacy UI suite is green. Old direct admin action/messages and geo fixtures remain visible with bounded current-protocol checks or explicit historical limitations.

## Verification

Own allowlist source mirror `/root/km23-own`, existing dependency venv symlink `/root/kidsmap-task33/.venv`, unchanged QA04 launcher. No env/database/media copied. Disposable network-none PostgreSQL container with tmpfs, isolated cache/media/test email; DJANGO_TESTING=1 and clean child environment. External-credential presence false, network/libpq guards true.

Exact final command from C:\kidsmap:

```powershell
& 'C:/Program Files/WSL/wsl.exe' -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/scratch/task33-stage23/run-owner-admin-qa.sh all stage23-own-final-20261003 --label catalog.testcases.owner.TestCreatedByIsAuditOnly --label catalog.testcases.image_uploads.TestOwnerImageNormalization --label catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_concurrent_admin_edit_requires_explicit_restart --label catalog.testcases.test_volunteer_admin.VolunteerConcurrencyTests --label catalog.testcases.test_task33_r1_owner_safety --label catalog.testcases.test_task33_publication --label catalog.testcases.test_task33_place_continuous --label catalog.testcases.test_task33_admin_editors --label catalog.testcases.test_task33_ownership --label catalog.testcases.test_task33_permissions
```

Exit0; 161 tests PASS; Django check/makemigrations PASS; migrations164 applied/0 pending; canonical discovery1610 unique IDs/0 duplicates at that source snapshot; cleanup PASS, run/socket roots removed. Raw synthetic evidence outside Git `/root/task33-evidence/stage23-own-final-20261003`. `23-owner-admin-source-manifest.json` records five scoped source hashes of the executed mirror; all matched current files when captured. Parent's final full-source manifest supersedes later source revisions.

Meaningful RED: same wrapper `all stage23-own-fixture-red-20261003`, with labels `TestCreatedByIsAuditOnly`, `TestOwnerImageNormalization`, the volunteer restart case, the volunteer concurrent-create case and `test_task33_r1_owner_safety`. 20 tests: 2 failures/1 error. The error was the confirmed uncaught gallery OSError. One failure was the legacy business-moderation assertion; the new foreign-order negative already refused the request but used the wrong expected error field (the established form reports it under `gallery_images`). These causes were investigated and corrected explicitly. Intermediate adjacent run `stage23-own-media-green-20261003`:161 tests/1 failure in the old surviving-team view assertion; D03 suspension source and decision verified before replacement. Final161/161 closes these current checks.

Initial own-mirror discovery `stage23-own-fixture-20261003` failed on another worker's intermediate helper import (`publication.version_token` instead of `publication_forms.version_token`), before test execution. A diagnostic-only own-mirror commands.py error expansion located it; repo QA04 remained unchanged and the wrapper restored the exact QA04 source before acceptance. Environment cleanup passed. This is not application failure evidence.

`git diff --check` for the four changed tracked scope files PASS. Codebase Memory was callable: project C-kidsmap ready, relevant symbol hints used; partial templates/excluded assets and a later transport-closed coverage call mean graph completeness is UNKNOWN. Critical findings verified against source, not graph absence.

## Changed / not run / handoff

Changed: publication_forms.py gallery error handling only (public worker separately owns its location adapter insertion); image_uploads.py RU fixture selection; owner.py explicit reviewer grant and team-suspension contract; test_volunteer_admin.py restart/taxonomy fixtures and failure diagnostics; new test_task33_r1_owner_safety.py; assigned classification/report/source manifest. Prior user edits retained.

NOT RUN by this executor: final full suite, rendered browser matrix, restore/cohort rehearsal, real external integrations, production and stage24. Parent runs the required final full suite on the aggregate source. No current R1 blocker remains in the tested owner/admin/media boundary. Historical old-contract failures remain explicit technical debt, not silent successes.

Named handoff: **integration-reviewer / root** — consume scoped161 PASS, inspect the one-function gallery fix, reconcile final full-suite IDs with the complete98-entry classification, and include independent schema/security/publication review plus browser/recovery evidence before declaring stage23 DONE or readiness for stage24.
