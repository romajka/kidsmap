# OFFER-QA-05 Admin Status Wrap Implementation Plan

**Goal:** Полностью читать длинные статусные подписи внутри вкладки «Состояние» без внутренней горизонтальной прокрутки.
**Architecture:** Ограничить ширину badge его readonly-контейнером и разрешить перенос текста только у трёх статусных полей change-form. Общие бейджи списков и публикационная логика остаются за границей scope.
**Tech Stack:** Existing Django/Jazzmin admin, CSS, native Chromium.
**Spec:** docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-05.md; fresh docs/qa/offer-qa05-recheck-2026-10-14-r1/REPORT.md.

## Authorization and scope
APPROVED IMPLEMENT: user «да одобряю» on2026-10-14. Scope completed with fresh LOCAL acceptance; see docs/qa/offer-qa05-fix-2026-10-14-r1/REPORT.md. Sequential root execution; no delegated work needed. No commit/push/deploy/production. Preserve incoming WORKTREE, active_run and stands.
Only ID OFFER-QA-05, including the same nowrap cause in Program/Activity/OfferingGroup status fields.

Application file allowed: `static/admin/css/kidsmap_admin_components.css` only.
Selectors limited to `.change-form` descendants of `.field-publication_badge`, `.field-ownership_badge`, `.field-verified_badge` carrying `.km-status-badge`. Add bounded `max-width:100%`, `white-space:normal`, safe text wrapping; preserve indicator, colours, typography and semantics. Check anonymous flex text wrapping before finalizing; do not clip text or hide overflow to mask defect. No global nowrap removal for every list badge.

QA files allowed: new `docs/qa/offer-qa05-fix-2026-10-14-r1/` scripts/reports/screenshots/manifests; this plan progress; OFFER05 scoped status links in `docs/qa/continuation-and-repair-prompts-2026-10-11.md` and `docs/qa/module-acceptance-prompts.md`. Historical reports are preserved. Own ignored `.tmp` profile only. No backend/templates/JS/PO/test files, other findings or business contract changes.

## Task 1 — Minimal repair and targeted verification
- [x] Refresh HEAD/branch/dirty/active_run, exact incoming CSS hash and runtime-source match. Validate owned profile/process/locale manifest before reuse; no .env. Own fictional DB/cache/media/private-media/email; external integrations disabled/blocked and disclosed.
- [x] Preserve fresh RED reproduction from recheck: group RU390 badge right325.05 vs pane322, scrollWidth257 vs254, scrollLeft0; root overflow false. Program/Activity long validation badge right390.81 vs322. Screenshots prove visible clipping.
- [x] Add only scoped CSS rule(s) described above. No behavior tests that mirror CSS, no repeat backend suite.
- [x] Native Program/Activity/OfferingGroup State tabs RU/AZ/EN ×360/390/768/1024/1280/1440 (54 cells). Use fresh current-PO isolated locale profile, verify manifest and sole LOCALE_PATHS before django.setup; do not overwrite shared MO.
- [x] Exercise long draft/pending/published status labels using fictional prerequisite variants; tab opening and keyboard focus; measure complete badge inside readonly AND pane bounds, no inner scroll needed. Check control dimensions, indicator and status text unchanged.
- [x] Native save draft → reload, then explicit READ ONLY transaction with statement/lock timeouts verifies candidate/live/status/version semantics of fictional fixture. Never ORM-substitute checked user transition. Scope does not require changing publication state on real data.
- [x] Shared consumer smoke: list badge layout and another entity admin form remain sound at mobile/desktop; console/pageerror/network evidence. External interactions SIMULATED/NOT RUN.
- [x] Save reviewable incoming-WORKTREE diff, exact commands/native exits/cell counts/PNG manifest, source-runtime identity, preservation checks, NOT RUN bounds. Close only OFFER-QA-05 when its acceptance passes.

Full ACCEPT-05/global suite deferred to module end per user preference. OFFER-QA-06–09 excluded, including untranslated status captions. Any additional app file or independent cause requires a separate concrete scope approval.
