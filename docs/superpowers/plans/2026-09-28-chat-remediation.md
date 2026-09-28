# Chat changes remediation Implementation Plan

**Goal:** Исправить F01–F09 из `docs/agent-audits/2026-09-28-chat-changes-review.md` и проверить результат на изолированном стенде.
**Architecture:** Сохранить рабочую ревизию как источник unpublished данных. Общие predicates для удаления и duplicate projection; SLA обслуживает единый lifecycle и read-only очередь.
**Tech Stack:** Existing Django, PostgreSQL, templates, plain JS/CSS.
**Authorization:** Пользователь «исправь», ранее утверждённые duplicate/SLA планы. Inline execution, без deploy/commit/push.

**Execution evidence (2026-09-28):** see `docs/agent-audits/2026-09-28-chat-remediation-verification.md`. Targeted PostgreSQL suite: 169/169. Expanded suite: 7 pre-existing failures reproduced on clean HEAD, recorded separately. Additional reproduced fixes: PostgreSQL nullable-join locking in account deletion and editor initialization dirty-state warning. Production activation remains outside this local implementation.

## Global Constraints

- Production strictly read-only; application changes only local.
- Preserve FAQ/contacts and other unrelated worktree edits.
- Tests: DJANGO_TESTING=1, isolated SQLite/PostgreSQL, LocMem cache/email, temporary media, external services disabled.
- SLA durations require explicit confirmation; no publication guarantee.

## Task 1: Deletion and duplicate/media regressions

Files: `test_volunteer_admin.py`, `services/place_duplicates.py`, `services/volunteer_places.py`, `services/volunteer_dashboard.py`, `domain_admin/volunteer.py`, `volunteer_middleware.py`, `volunteer_forms.py`.

- [ ] Add HTTP tests: renamed revision duplicate rejected; branch with another address accepted only with explicit checkbox; duplicate with upload creates zero files; pending/live/foreign/owned deletion denied; missing CSRF denied.
- [ ] Run failing tests with isolated runner.
- [ ] Read active payloads via candidate_from_payload, check all name matches, serialize creation using creator lock, perform duplicate gate before storage writes.
- [ ] Centralize deletion predicate, lock Place/revision in one transaction, preserve CSRF/admin wrapper, whitelist only the guarded route. Remove debug identifier output and CSRF exemption from this in-scope handler.
- [ ] Run targeted suite again.

## Task 2: UI regression fixes

Files: volunteer templates/CSS, locale catalogs and tests.

- [ ] Browser reproduction: 375px badge clipping; file inputs labels.length=0; Russian verification in AZ/EN; missing branch checkbox.
- [ ] Mobile banner stacks vertically, matching markup selectors, label/description/error bindings for photos, visible explicit branch confirmation.
- [ ] Add translated copy using the project's existing RU/AZ/EN copy function; test actual rendered localized pages.
- [ ] Repeat browser metrics/screenshots at 375/768/1024/1440px, languages, console, duplicate and deletion flow.

## Task 3: SLA integration

Files: SLA service/tests, moderation lifecycle models/services/admin, new queue view/template, owner/review messages and migration.

- [ ] Add tests for missing timestamps, queue ordering/filters/ACL, submit/resubmit/pause/decision dates, public copy.
- [ ] Run red tests, then connect lifecycle to submission and moderation paths. No timer reset for ordinary pending edits.
- [ ] Add read-only unified queue for Place/revision/PlaceReview/SiteReview/SpecialistReview; query permission guards per type; sort oldest first; filter status/type/submission date/SLA state; internal alerts/counts.
- [ ] Render truthful localized review-time copy and Needs changes reason; missing historic timestamp uses deterministic created_at fallback, displayed as estimated.
- [ ] Verify drift/migrations and regressions, then browser queue/owner/review flows. Record not-tested operational scope.
