# Stage 22: independent database review

Status: PASS for bounded migration/database review; DB22-06 reproduced and fixed. Overall stage acceptance belongs to the parent and other reviewers.

Reviewer: `/root/stage22_database_review`, canonical `database-reviewer`; definition `.agents/agents/database-reviewer/agent.md`. Mode: bounded read-only AUDIT. Authorization: user approved only stage 22; parent assigned this report and ignored scratch scope. No application edits, production access, commit or push.

Snapshot: branch `task33-progress`, LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`; dirty WORKTREE contains preserved stage 21 work and evolving stage 22 work. HEAD does not identify dirty application source. PRODUCTION: UNKNOWN, not contacted.

## Evidence and graph limits

Codebase Memory is callable in this specialist runtime: project `C-kidsmap`, root `C:/kidsmap`, status ready, 18,041 nodes and 61,340 edges. Coverage generation `2026-10-03T08:27:26Z`, full mode. Exact review/specialist/account-deletion source paths report `coverage_unavailable` and `metadata_changed`; migration directory reports `not_tracked`. Graph search confirms review symbols but is only navigation evidence; conclusions below were checked against source. The change detector compares against main, not index freshness, so its broad diff is not freshness proof.

## Design safeguards handed to django-reviewer

1. Preserve every PlaceReview/SpecialistReview PK. Backfill one baseline revision for each source, including author, text, rating, moderation decision and original timestamps. Select each known-account/target head by approved source first, then effective `moderated_at or created_at`, then PK. Leave null-account sources separate; do not group by author or session.
2. Mark siblings archived before installing conditional known-account/current-head uniqueness. An archived sibling remains archived after its user FK becomes NULL during account deletion. Preserve archive linkage and original reaction ownership.
3. Add nullable revision FKs to legacy reactions, backfill every original reaction to its source baseline, verify zero unmatched reactions, then require the FK and replace review-level uniqueness with revision-level user/session uniqueness. Do not sum sibling reaction totals.
4. Validate reaction.review and revision.review agree. A conventional PostgreSQL CHECK cannot compare data in another table; service/model validation and negative cross-review tests are required if no compound FK/trigger is introduced. Direct QuerySet/bulk operations remain a boundary to document.
5. Migration backfill must use historical `apps.get_model`, database alias from schema_editor and bulk/update paths. Live PlaceReview save and post-save both recalculate ratings; migration must not invoke those signals or fabricate approval times.
6. Transactionally serialize submit/approve/reject and optimistic revision checks. Lock acquisition order must remain identical across submission, moderation, reaction and account deletion. Test concurrent first submission, edits and competing approvals on PostgreSQL rather than SQLite.
7. Pending/rejected candidates cannot replace approved head projection or contribution. Public filters, Specialist.refresh_rating_stats and rating calibration population must exclude archived sources. Existing junk/rating eligibility semantics must remain consistent.
8. Approved account-deletion policy is anonymize published reviews, delete other reviews, retain anonymized moderation history. Extend processing to typed revisions/new targets/reactions without enabling the policy in production. A published head with pending candidate requires separate revision disposition; erase all retained author/session identifiers and deleted-actor labels. SiteReview is a separate retained compatibility domain.

## Source-verified implementation hazards

- `src/catalog/models/review.py:PlaceReview.save` unconditionally sets `is_anonymous=False`; `refresh_reaction_stats` calls save, so anonymization can be undone by a later counter refresh. The new implementation must preserve the deleted-author state.
- `src/catalog/models/specialist.py:SpecialistReview.Meta` has unconditional `(specialist,user)` uniqueness; remove/replace only after preserving sources and assigning current heads.
- `src/catalog/services/account_deletion.py:_finalize_locked` currently selects whole rows by status and handles only Place/Site/Specialist reviews. Head/revision separation requires revision-aware retention and Activity/Event coverage.
- `src/catalog/services/rating_ranking.py:build_place_rating_calibration_proposal` derives its population through public_review_queryset. Its source cutoff uses head.created_at; editing an old head must not cause a later approved revision to appear in an earlier historical cutoff without an explicit technical contract.

These are preparation findings against pre-stage-22 source, not conclusions that upcoming implementation contains defects.

## Foundation implementation review (interim)

Reviewed new `models/review_versions.py`, `services/review_versions.py`, `services/review_retention.py`, migration `0128_task33_review_versions.py` and related compatibility/reaction/ranking paths while the parent continues edits. Positive evidence: migration uses historical models and schema alias, baseline preserves `source_is_approved`, stable source IDs/reactions, unknown identities and effective ordering; data operation precedes conditional uniqueness; irreversible normalization prevents unsafe downgrade deletion. Approved projection and candidate are separated in submit/moderate service. Existing counter refresh now uses QuerySet.update and no longer resets anonymization.

Interim requests to implementation owner (not final findings):

- **DB22-01:** compatibility `reactions.create_or_update_review` still writes heads directly and groups anonymous sources by session. Authenticated normal use case currently bypasses this writer through create_pending_place_review; the remaining anonymous/callable boundary must reject or version writes so approved projection and unknown identity are preserved.
- **DB22-02:** PlaceReviewReaction revision FK remains nullable in 0128, permitting bulk/direct NULL rows to bypass revision uniqueness. Require the FK after backfill; ordinary save can bind an explicit current revision. Its current implicit fallback selects earliest baseline, which is incorrect after an approved edit when intent is reacting to visible text.
- **DB22-03:** rerunning frozen backfill after later revisions currently resets a pointer to baseline. Migration idempotency must be qualified to initial normalization or reruns must skip already-versioned rows and preserve publication.
- Baseline uniqueness per review and missing-pointer behavior need an explicit invariant. ensure_baseline returns an existing revision before repairing pointers; direct revision deletion/QuerySet updates are not automatically safe recovery mechanisms.
- Ranking cutoff now checks current revision.created_at, preventing obvious inclusion of future edits. It excludes an edited contribution at an earlier cutoff instead of reconstructing the then-visible previous revision; document the intended historical-cutoff semantics and test them.

Parent-reported baseline 61/61 and core 3/3 are attributed evidence only. This reviewer has not executed them and has not issued acceptance.

Follow-up source review: DB22-01 authenticated compatibility writer now routes typed submission and anonymous writes are denied; DB22-02 revision FK is required in migration0130 and implicit ordinary reaction saves use current revision; DB22-03 frozen backfill updates pointers only when creating baseline; baseline uniqueness is added in0130. Final runtime confirmation pending.

**DB22-05, P2, source correction verified:** voter account deletion used reaction QuerySet.delete, bypassing model delete overrides. Parent now collects affected review IDs before both early Place deletion and typed deletion, then refreshes current-revision counters. Independent integration reviewer added an all-four-types voter-deletion test; runtime confirmation belongs to that review.

Under the parent's explicit tests-only assignment, this reviewer added `src/catalog/testcases/test_task33_review_migration.py`. It creates only a random owned PostgreSQL schema in guarded `test_qa_stage04`, migrates fresh historical0127 then forward0130, compares synthetic source/reaction values exactly, checks head election/aggregate comparison/constraints and repeats normalization after a later approval plus archived-author anonymization. It restores search_path and removes only its owned schema. Python syntax compilation and final isolated runtime passed. Application code remains unmodified by this reviewer.

## Executed PostgreSQL fixture: DB22-06

**P1 LOCAL WORKTREE release blocker, high confidence:** migration0128 combines source/reaction backfill and subsequent unique-index DDL in an atomic migration. With historical review rows present, deferred FK trigger events remain pending. PostgreSQL rejects the first conditional head unique-index creation with `OperationalError: cannot CREATE INDEX "catalog_placereview" because it has pending trigger events`. Reproduced by the independent fresh-schema MigrationExecutor test at `executor.migrate(after_target)`, before post-migration assertions. Empty fixture databases do not establish populated migration safety.

Exact command:

```powershell
& 'C:/Program Files/WSL/wsl.exe' -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/scratch/task33-stage22/run-linux-qa.sh all db-migration-independent-20261003-a --label catalog.testcases.test_task33_review_migration
```

Exit1; 1 test, 0 assertion failures, 1 error, 0 skips. This is a newly reproduced implementation defect, not a pre-existing baseline failure despite the launcher's generic `BASELINE_FAILURE` label. Raw evidence outside Git: `/root/task33-evidence/db-migration-independent-20261003-a/{django.log,suite-results.json,run.json}`. QA isolation: PostgreSQL17.11/Django6.0.2/Python3.12.3/psycopg3.2.10; network/libpq guards enabled; external credentials absent. Django check and migration consistency PASS; base fixture has164 applied migrations/0 unapplied; discovery1592 unique tests/0 duplicates. Cleanup PASS, run/socket roots removed; owned schema removed by test finally.

Handoff to `django-reviewer`: drain deferred constraint events before subsequent DDL, or split safe normalization/constraints transactions without losing backfill ordering and uniqueness safety. Then rerun the unchanged seeded fixture. Do not weaken assertions or claim populated migration acceptance from empty-database checks.

## Final bounded database verification

Parent added `drain_deferred_foreign_keys` after frozen backfill and before AddConstraint in0128. PostgreSQL executes `SET CONSTRAINTS ALL IMMEDIATE` inside the existing atomic migration. The unchanged independent populated fixture then passed:

```powershell
& 'C:/Program Files/WSL/wsl.exe' -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/scratch/task33-stage22/run-linux-qa.sh all db-migration-independent-20261003-b --label catalog.testcases.test_task33_review_migration
```

Exit0; 1/1 test, 0 failures/errors/skips. All assertions executed: eight Place source rows and eight original reaction rows retain exact IDs, text, author/source decisions and timestamps; one Specialist source/baseline retained; latest-approved effective-time election beats newer pending/rejected siblings; no-approved account uses latest source; two equal-name/equal-session unknowns stay distinct. Fixture rating comparison: old four approved source contributions average3.5; current three independent contributions average11/3. Historical scalar rows themselves remain unchanged. New current-head duplicates, NULL revision reactions and duplicate baselines fail at database constraints. A second frozen normalization after a later approved revision plus anonymized archive retains current pointer, archive identity, eight baseline revisions and eight reactions.

Launcher checks/makemigrations PASS;164 migrations applied/0 unapplied;1594 unique discovery tests/0 duplicates. PostgreSQL17.11, Django6.0.2, Python3.12.3 and psycopg3.2.10; network/libpq guards enabled, external credentials absent. Cleanup PASS; run/socket roots removed. Raw evidence outside Git: `/root/task33-evidence/db-migration-independent-20261003-b/`.

Windows source hashes equal the tested Linux mirror hashes after completion:

| Artifact | SHA256 |
| --- | --- |
| migration0128 | `124cd7f8cdfef5621def7c1dbd5def1634537b5dce5cd863048788942cecfe1d` |
| migration0130 | `f767bb6f1fda87dc09d8b956f7582a9dc4d6eb65b7755446d91a9057235b175b` |
| independent migration testcase | `d9602bf5abd62e7d76bb519df70b40d6a11700b81fecd03d2eb163cfb91e0577` |

No outstanding reproduced database finding remains in this bounded snapshot. Irreversible migration rollback is intentional: do not downgrade through typed writes or delete new history to restore old constraints. Production legacy distributions/performance remain UNKNOWN and production activation is not authorized.

## Verification boundary

Executed: canonical role/shared-contract reads; branch and HEAD commands; bounded rg/source review; Codebase Memory project/status/search/coverage checks; Python syntax compilation; two isolated PostgreSQL migration fixture runs (first reproduced defect, second PASS); source/mirror hash equality; owned-path diff check exit0.

NOT RUN by this reviewer: full application suite, rendered browser, account-deletion runtime and competing submit/moderation concurrency (assigned to independent integration/parent); backward migration after typed writes (intentionally unsupported); production inspection, real-data conversion or performance benchmark. Production data volume, real legacy distributions and deployed schema remain UNKNOWN.

Named handoff: `django-reviewer` retains this evidence and includes the independent migration testcase in final combined stage22 verification. `integration-reviewer` completes voter-retention and PostgreSQL concurrency coverage; `browser-qa` validates affected UI. This report approves only the reviewed local database/migration boundary, not the whole stage/site/production.
