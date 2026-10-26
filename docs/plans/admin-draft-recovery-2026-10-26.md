# Admin draft recovery implementation plan

**Goal:** Fix the three user-reported admin failures while preserving publication, permissions and concurrency guards.
**Authorization:** User explicitly requested these three fixes. LOCAL implementation and isolated QA; commit/push/deploy and live reset are excluded.
**Spec:** User findings and /home/ramin/Documents/ChatGPT/KidsMap/2026-10-26-pricing-review/REPORT.txt.
**Architecture:** Use existing revision, schedule and private public-page renderers. Recovery is explicit and audited; unknown schedule is an empty weekly payload, distinct from explicitly closed days; saved preview selects the same eligible candidate as the editor.
**Tech stack:** Django, PostgreSQL, existing JS schedule editor, Django templates, gettext AZ/RU/EN.

## Constraints

- Preserve approved content, candidate history, author, private media and live status.
- No automatic conflict bypass, no GET writes, no new schedule mode or data migration.
- No heuristic rewrite of old all-closed schedules; users can explicitly clear unknown hours.
- Use isolated DB/cache/media/email and no external credentials.

## Task 1 — Explicit conflict recovery

Owner: conflict worker. Files: volunteer service, one admin working-revision view, shared volunteer form, own regression file.
- [x] Reproduce missing action in a stale admin candidate.
- [x] Write failing endpoint tests: recover to current base, preserve history/author/live, stale POST and permission denials.
- [x] Add atomic version-checked restart with old proposal in audit and explicit POST action.
- [x] Add visible recovery control and explanatory copy, retaining ordinary save conflict rejection.
- [x] Run targeted service/view regressions; hand off to parent.

## Task 2 — Unknown weekly schedule

Owner: schedule worker. Files: schedule service/form/JS/shared template, own Django and Node regressions.
- [x] Write failing tests for empty serialization/import/save/clear and explicit all-closed preservation.
- [x] Keep absent weekly rows as []; retain explicit closed days as real data.
- [x] Render unknown hours as unfilled; avoid frontend auto-creating closed data.
- [x] Preserve readiness failure for unknown hours, omit public hours/open-status claims.
- [x] Run targeted regressions and hand off. Record manual cleanup needed for legacy fabricated closed weeks.

## Task 3 — Saved candidate preview

Owner: parent. Files: services/admin_place_preview.py, private preview template/context, regression file.
- [x] Add failing authenticated route tests for draft/rejected/pending candidates, saved localized text/prices/schedule/gallery, empty values, read-only behavior and permissions.
- [x] Build private preview from active saved candidate; keep approved/absent revision fallback.
- [x] Label saved draft versus submitted/current state correctly; keep noindex/no-store and stale notice.
- [x] Run targeted tests and adjacent ownership/editor preview tests.

## Acceptance

- [x] All three targeted regression groups pass in disposable PostgreSQL, plus affected adjacent suites once.
- [x] Relevant Node tests, Django check and migration-drift check pass.
- [x] Rendered browser checks cover recovery, unknown/closed schedule and saved preview at desktop/mobile with AZ/RU/EN.
- [x] Report exact LOCAL outcome, untested scope and remaining release steps. No production fix claim before a separate release.

Acceptance completed LOCAL:158 Django/PostgreSQL,80 unique Node checks,45 rendered states. No migrations. No commit/push/deploy. Exact commands and limits: docs/reports/admin-draft-recovery-2026-10-26.md.
