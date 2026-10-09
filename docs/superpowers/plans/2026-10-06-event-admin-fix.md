# Event admin correction Implementation Plan

Goal: correct confirmed event admin labels and readiness without changing publication, organizer, venue, dates or permissions.
Architecture: retain existing form validation; extract its unchanged publication checklist for the summary. Validate a disposable form copy for the server readiness verdict. Give Event its own progress adapter instead of feeding incompatible data to Place's adapter. Keep lifecycle and completeness separate.
Spec: user request and docs/qa/content-entry-audit-2026-10-06.md (EVENT-ADM-01/02/03).

Constraints: dirty WORKTREE preserved; isolated PostgreSQL/cache/media, DJANGO_TESTING=1; no commit/push/deploy. Current user request authorizes this scope. Execute sequentially.

- [x] Add regression tests for global RU translations, add/edit summary and actual publication validation.
- [x] Run them before implementation and record failures.
- [x] Correct confirmed global translations, compile catalogs; inspect shared consumers.
- [x] Extract EventAdminForm publication checklist without changing validation; summary uses a publication probe and conditional address requirement.
- [x] Adapt progress only for Event; a live presence estimate must not claim server approval.
- [x] Recheck mobile on current dirty CSS; only change CSS if overflow is reproduced.
- [x] Run targeted admin/domain/date regressions and actual browser creation/edit/draft/error flows.
- [x] RU/AZ/EN ×360/390/768/1440, empty/filled and physical/online; screenshots and bounded report.

Confirmed during acceptance: location_section.html omitted phone/instagram/website/moderation_note. Add rendering regression then restore those existing fields only.

Confirmed in failed-upload acceptance: preview used form.instance.photo (unsaved upload). Render stored form.initial.photo and distinguish stored versus newly selected photo in live checklist.

Failed POST lifecycle now reads persisted Event status, covered by regression and browser POST. All authorized tasks verified; remaining broad checks listed in the QA report.
