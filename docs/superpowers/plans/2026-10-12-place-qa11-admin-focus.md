# PLACE-QA-11 admin focus Implementation Plan

> APPROVED IMPLEMENT: пользователь явно одобрил PLACE-QA-11 в ответе на запрос расширения 2026-10-12. Execute in this conversation only after explicit expansion approval. No commit/push/deploy/production. Existing approved PLACE-QA09/10 changes and QA stands are preserved.

**Goal:** keep native keyboard focus visible above the admin Place Save panel and repeat blocked module01 acceptance checks.

**Architecture:** existing admin form controller measures actual bottom panel occupancy and corrects scroll only when the visible focused control is occluded. Scoped CSS uses measured scroll margins. No backend, template, copy, ACL, CAS, readiness, pricing or publication changes.

**Tech stack:** current vanilla JS/CSS, native browser, own isolated QA.

**Spec:** `docs/qa/module01-full-2026-10-12-r2/PLACE-QA-11.md`; approved module01 completion plan and ACCEPT-01 guide define remaining QA.

## Exact boundaries

- ID: PLACE-QA-11 only. Not a reopening of PLACE-QA01–08 or expansion into other modules.
- Modify only `static/admin/js/kidsmap_place_form.js` and `static/admin/css/pages/kidsmap_place_form.css`.
- Own new QA scripts/evidence/report under `docs/qa/place-qa11-fix-2026-10-12-r1/`; repeat ACCEPT-01 under a new unique run. Update only module01 current journal/guide summary with links.
- Preserve existing worktree, active_run NONE, old artifacts/stands, shared MO and current owner repair. Fresh own runtime source snapshot/locale profile; DJANGO_TESTING=1 and unique DB/cache/media/email with fictional data and blocked/SIMULATED external calls. No .env/credentials in artifacts. Readback READ ONLY/timeouts.

## Task 1 — reproduce then repair actual occlusion

- [ ] Preserve fresh RED: native nameAZ click → Tab → Tab at390×950, snapshot focused selector/category text, bounds, actual occluder and PNG. Recheck all18cells and all currently visible form controls. Use visible label/focus representation for styled hidden inputs and1px tolerance for geometry; normal category button is independently confirmed.
- [ ] Add a form-scoped focusin handler in the existing controller, queued once through requestAnimationFrame after native focus scrolling. If focus is outside the form or inside the bottom panel, leave it alone. Resolve visually hidden control to its real visible focus label. Read visible sticky panel rect and apply minimal immediate delta only when control extends below panelTop−8px. Do not change activeElement, cancel Tab, scroll on ordinary input, or force hidden controls.

Core calculation:

```js
var safeBottom = Math.min(window.innerHeight - 8, stickyRect.top - 8);
var delta = targetRect.bottom > safeBottom ? targetRect.bottom - safeBottom : 0;
if (delta > 1) window.scrollBy({top: delta, behavior: 'instant'});
```

Only count a viewport-intersecting visible sticky panel horizontally overlapping the target. For oversized controls show the leading focus area without an oscillating loop. Existing top section navigation remains intact; measure its actual overlap when top correction is needed. Fixed dropdown/modal targets must use their own existing placement rather than repeatedly scrolling the document.

- [ ] Expose measured bottom occupancy to a scoped CSS variable; add form-control/summary/button/link scroll-margin-bottom with a fallback. Refresh measurement on viewport resize/panel wrapping. ResizeObserver callbacks must not cause typing jumps or scroll feedback loops.
- [ ] No JS-derived readiness or enum changes; existing save/modal/dropdown callbacks remain identical.

## Task 2 — acceptance and preservation

- [ ] GREEN native complete Tab/ShiftTab cycles, Enter/Space/Escape, category popup/search/no-results/outside-click/focus return, pricing modal, file controls and error-summary jumps, RU/AZ/EN×360/390/768/1024/1280/1440; expanded/collapsed sections, long text, short viewport and reduced motion. Verify focus bounds and actual hit-test/visible representation; manually inspect focused PNGs.
- [ ] Native draft save/reload, invalid submission/retained input and published/candidate preservation. Ensure typing does not move the visible focused field, Save panel controls stay usable and no unexpected console/network failures occur.
- [ ] Run affected existing admin/dropdown/JS consumers unchanged, node syntax and diff checks. No tests that merely mirror CSS; native browser proves this reversible visual change. If any backend regression appears, investigate and stop scope expansion.
- [ ] New report: source/runtime/locale snapshots, exact commands/exits/counts, RED/GREEN PNG hashes, limits and preservation. Only close QA11 with actual proof.
- [ ] Resume the remaining module01 ACCEPT checks on final source and publish explicit PASS/FAIL/NOT RUN. Other confirmed findings stay OPEN and get separate plans. Module02 starts only after user selection and actual local module01 acceptance.

Approval phrase: «Одобряю PLACE-QA-11 по docs/superpowers/plans/2026-10-12-place-qa11-admin-focus.md и повторную локальную ACCEPT-01; без commit/push/deploy/production».
