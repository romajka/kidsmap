# PLACE-QA-03 — fresh PostgreSQL diagnosis and implementation scope

Date: 2026-10-10, Asia/Baku. Mode: AUDIT / PLAN. Executor `/root`, sequential canonical kidsmap-orchestrator / django-reviewer responsibility. No independent specialist execution claimed. Application changes await user scope approval.

## Snapshot and isolation

Actual checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, journal `active_run: NONE`. PRODUCTION not accessed; current state UNKNOWN.

Preserved incoming modified `docs/qa/module-acceptance-prompts.md`, untracked module01-r1/r2, module02-r1, module03-r1, module04-r1 QA directories and PLACE-QA-01/02 plans/evidence. No foreign stand was changed/stopped. Source hashes and hashed input files match before/after tests; application diff from HEAD is empty.

Created a dedicated owned PostgreSQL container `kidsmap-placeqa03-plan-20261010`, loopback 55437, image `postgres:17-alpine` with `--pull=never`; DB `placeqa03_plan`, test DB `test_placeqa03_plan`. Existing plain `postgres:17` image was absent; inspected the available image tag only, never container environment/secrets. Test runner created and destroyed only its isolated test DB. Shared source runs with allowlisted environment and `DJANGO_TESTING=1`; `.env` is not loaded, cache/email are LocMem, media/private-media are separate ignored directories, external socket transport is blocked. [Isolation](isolation.json), [snapshot/source hashes](snapshot.json).

## Fresh results

Executed real service operations and the actual moderator GET through Django test client against PostgreSQL, without application monkeypatches:

| Test | Result |
|---|---|
| Mixed draft rebases scalar projections | FAIL: base `price_from=15.00`, live `18.00` |
| Mixed save/resubmit reviewer has no conflict and offers approve | FAIL: HTTP 200, conflict true, approve button absent |
| Mixed save/resubmit service approval | ERROR: business `Publication source conflict` |
| Price-only immediate update and approval | PASS; scalar price and tariff ID preserved |
| Actual overlapping source mutation | PASS; conflict detected and mutation preserved |
| Stale content version | PASS; second write rejected |

**6 tests: 3 PASS, 2 FAIL, 1 ERROR, 0 skipped; native test exit 1.** The recorder exited 0 because it successfully saved failing evidence; it does not represent a green application suite. The ERROR is the reproduced publication rejection, not a migration/environment error.

```powershell
.venv/Scripts/python.exe docs/qa/place-qa03-plan-2026-10-10/record_baseline.py
```

[Exact native commands and exits](command-ledger.jsonl), [raw test result](baseline-tests.txt), [test code](audit_projection_tests.py), [sanitized synthetic diagnostic](diagnostic.jsonl). The second-writer control uses an intentional ORM mutation; real two-actor UI and concurrent connections are not claimed.

## Cause refined by runtime evidence

The failure requires attention to two stages:

1. Full mixed snapshot save applies the amount-only tariff immediately. `_apply` refreshes correctly and `sync_legacy_price_fields` writes live 18.00. Candidate base retains 15.00 in `price_from/price_to`, but `changed_fields` initially contains only address/name, so `revision_base_matches` still returns true.
2. A fresh snapshot/re-submit echoes live scalar values 18.00. The stale 15.00 base makes them appear as candidate edits, and `revision_base_matches` / publication review then detect a mismatch. Reviewer hides the approve action; service review refuses too.

No concurrent writer was present in the mixed-edit cases. Existing plain-price and genuine-conflict controls passed. This supports the specific local P1 finding; it does not establish that all revisions or production are blocked.

Primary source: `src/catalog/services/publication.py:305` (`_immediate`), `:320` (`propose`), `:383` (review source guard); `pricing_plans.py:603` (`sync_legacy_price_fields`); `volunteer_places.py:61` (`revision_base_matches`); `domain_admin/volunteer.py:166` (actual reviewer).

A safe repair must both rebase the changed pricing projections and avoid turning an old scalar echo into a queued rollback. Resetting all base fields, weakening CAS or changing immediate eligibility is outside the proposed repair.

## Discovery limits

Codebase Memory matched checkout/branch/HEAD. Focused symbol search returned eight source matches (`has_more=false`); inbound traces identified pricing sync callers and review guard consumers. Coverage metadata reported `metadata_changed` / `coverage_unavailable`, so relevant source and dynamic signal/template wiring were read directly. Graph caches were not exported and graph completeness is not claimed.

A guessed test path `test_volunteer_places.py` was absent; the existing publication and volunteer-admin files were inspected instead. A probe for local image `postgres:17` reported absent image; no pull was attempted. These discovery failures are separate from application test failures.

## Proposed scope and boundaries

[Concrete plan](../../superpowers/plans/2026-10-10-place-qa03-pricing-rebase.md): one application file (`publication.py`) plus a new regression suite and isolated QA evidence. Atomic rebase uses observed before/after projection changes from the same immediate write. Existing authorization/version/source/dependency/readiness gates remain in place. No frontend/model/migration/production edits or retrospective revision rewriting.

NOT RUN: rendered browser baseline/save/reload/approval and screenshots, actual two-user UI flow, concurrent-connection lock test, complete regression families/full suite, production, real external integrations, commit/push/deploy. PostgreSQL tests and server-rendered HTML are not rendered-browser evidence.

[Final verification](plan-verification.json): HEAD/active_run unchanged, application diff empty, hashed inputs preserved and document links valid. Only the container created by this audit was stopped, using its recorded immutable ID; it was not removed. Foreign stands were untouched. Final verifier command `.venv/Scripts/python.exe docs/qa/place-qa03-plan-2026-10-10/verify_plan.py` exited 0.

Finding remains **OPEN / P1**. Await user approval of the linked bounded implementation scope. PLACE-QA-01/02 are not implicitly approved.
