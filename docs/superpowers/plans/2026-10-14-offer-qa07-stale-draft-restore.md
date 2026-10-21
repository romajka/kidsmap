# OFFER-QA-07 Stale Draft Restore Implementation Plan

**Goal:** Старый локальный/server draft не должен молча заменять сохранённую карточку или текущего кандидата; прежний ввод должен оставаться доступным для явного восстановления.
**Architecture:** Проверка identity/version перед любым apply; ограниченный выбор восстановления в существующей savebar. Успешный explicit save помечает завершёнными только более ранние рабочие копии того же actor+existing target. Содержимое и media сохраняются, newer/foreign/create drafts не закрываются вслепую. Существующие candidate/live/ACL/CAS проверки остаются серверными.
**Tech Stack:** existing Django services/PostgreSQL, owner JS, existing UI copy dictionaries, targeted Django tests/native browser.
**Spec:** docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-07.md; fresh docs/qa/offer-qa07-recheck-2026-10-14-r1/REPORT.md.

## Authorization / exact scope
Approved by user2026-10-14; implementation and scoped acceptance completed. One ID OFFER-QA-07, no other repairs. Sequential root, no delegation needed. Preserve incoming WORKTREE, active_run and stands. No commit/push/deploy/production, bulk deletion or global cache cleanup. No schema migration/dependency/helper/shared MO changes proposed.

Files allowed:
1. `static/js/owner_place_continuous.js`: validate cached/fetched working-copy identity/schema/source before assigning draft ID/version or applying fields. Compare with GET-built canonical baseline/candidate; when candidate base cannot be proven current or contents diverge after a save boundary, request explicit user choice rather than silently overlaying it. Preserve legitimate current private/local recovery and offline input.
2. `src/catalog/services/server_drafts.py`: bounded lifecycle handling in mark_explicit_save; fields/photo records remain intact. Existing read/write ACL/CAS preserved.
3. `src/catalog/photo_views.py`: capture explicit request cutoff before controller save; pass it on success to lifecycle helper. Reuse existing error mapping/CAS, no unrelated controller changes.
4. `src/catalog/views.py`: wire same cutoff to existing non-AJAX owner create/edit call sites; preserve legacy/shared consumers and None target behavior. No broad view refactor.
5. `src/catalog/services/permanent_place_wizard.py`: only localized recovery warning/action copy keys in existing ui_copy: working_copy_conflict, restore_working_copy, use_current_card, RU/AZ/EN. No new backend business rule or unrelated copy changes.
6. Create `src/catalog/testcases/test_offer_qa07_stale_draft_restore.py`: behavioral lifecycle/API/security regression tests, RED then GREEN; no existing assertion changes.

Evidence/docs allowed: new docs/qa/offer-qa07-fix-2026-10-14-r1/, this plan progress, scoped status links in docs/qa/continuation-and-repair-prompts-2026-10-11.md and docs/qa/module-acceptance-prompts.md; own ignored .tmp profile. Historical evidence retained.

## Task 1 — Restore safely without discarding input
- [x] Refresh snapshot/source/role instructions and exact incoming file hashes. Reproduce native old-A/new-B fixture before patch in owned isolated profile. Never reuse historical PID/port unverified or copy .env.
- [x] Add guards BEFORE local apply(local), server apply(detail), hidden server_draft_id assignment and remembered version assignment. Reject unsupported schema, wrong target/type, stale source version; local legacy metadata not provably current must not silently overwrite canonical fields. Namespace stays actor+target; backend remains final ACL validator.
- [x] Keep canonical B on screen when stale/retired/divergent copy found. Show existing styled, accessible savebar recovery actions with localized copy. Allow explicit choice to keep current card or restore user's preserved working input as a NEW private draft based on current canonical source/candidate CAS. Never reuse old consumed draft ID/version or alter readonly publication controls through restored fields. No live write until normal explicit user action.
- [x] Preserve old cached data under its owned recovery namespace before replacing that cache; retain server fields/photo_name. If preservation fails, do not discard input. Remove the automatic clear-and-redirect path for retired local copies where it would lose unsaved input; don't clear unrelated keys. Current-card choice opens actual canonical candidate view, not another stale restore loop.
- [x] Existing matching-source resume and offline typing remain usable; asynchronous response must not replace input typed since fetch began. Cover same-source candidate-only save boundary with explicit-choice behavior, not only post-approval source-version drift.

## Task 2 — Complete older copies on explicit save, narrowly
- [x] Capture cutoff at successful explicit request START, not after controller save, in AJAX and existing non-AJAX callers. Do nothing on422/403/409/failure.
- [x] In helper, recheck fresh actor/access, lock target before sorted drafts, retire only same actor/type/existing target older-or-equal saved_at cutoff and eligible base source. Retain fields/media, no row deletion. Concurrent newer drafts remain active. Consume provided matching copy only if it is inside safe boundary; do not retire a concurrently updated newer copy.
- [x] Missing draft_id for existing-place save still prevents earlier same-target drafts from silently resuming; invalid/mismatched ID never authorizes foreign or different-target changes. For target_id=None creation, preserve existing matched-copy-only behavior: unrelated new-place drafts have no distinct target ID and must not all be closed.
- [x] Reuse materialized_place resume-exclusion marker only with existing semantics; demonstrate readback/history and idempotent successful save. Future resume/write of consumed old ID must remain conflict-protected. No uncontrolled retirement across actors/targets or timestamp race.

## Task 3 — Targeted regression and native acceptance
- [x] RED/GREEN new behavior tests: older same-target retirement, missing ID path, other actor/target/create unaffected, newer concurrent copy survives, field/photo preservation, unauthorized/stale write rejection, failed explicit save doesn't retire history, idempotence. Use isolated PostgreSQL transaction tests for cutoff/lock behavior if needed.
- [x] Run only affected existing named guards from test_task33_drafts.py and test_task33_place_continuous.py (matching-draft consumption, private create/resume/read permission/revocation/version CAS) and targeted AJAX/non-AJAX call-site checks. Record discovered method IDs, counts/exits. No broad/full wrapper or assertion weakening.
- [x] Native independent contexts A/B/C: A autosave old tree, B actual draft/save/submit/approval, C normal /edit/ and fresh=1; logout/login and reload. Current canonical B activity/IDs/prices remain intact. User explicitly recovering A creates private input only; no silent price/tree overwrite, no loss of recovery data. Verify current private resume, local/server version conflicts, revoked access, delayed response while typing, same-source candidate-only change and post-approval drift.
- [x] UI warning/choice states RU/AZ/EN ×360/390/768/1024/1280/1440; native keyboard/focus, error/conflict, control visibility and no overflow; console/network and PNG manifest. Browser transitions cannot be ORM substitutes; ORM only fictional prerequisites and READ ONLY final readback with timeouts.
- [x] Compile current RU/AZ/EN to own isolated directory via helper; validate manifest and sole LOCALE_PATHS before django.setup. Never overwrite common MO. Bind runtime to current source. Egress disabled/blocked, synthetic actors/data only, own DB/cache/media/private-media/LocMem email.
- [x] Reviewable incoming-WORKTREE diff, exact commands/exits/counts, native screenshots, lifecycle reason and preservation evidence; close only07 after actual scoped acceptance. Full ACCEPT05/global/external/production NOT RUN. If additional source/schema/independent cause proves necessary, stop dependent change and propose concrete extension.

Next finding08 is outside scope and not automatically started. Full module acceptance once its selected repairs complete, per user preference.

## Completion2026-10-14

OFFER-QA-07 CLOSED LOCAL. [REPORT](../../qa/offer-qa07-fix-2026-10-14-r1/REPORT.md):27unique targeted test methods;103 native assertions with3 explicitly SIMULATED;47PNG. Exact6source/test files only; other incoming source hashes preserved. Full ACCEPT05/global/external/production NOT RUN. Next PLAN08 not started.
