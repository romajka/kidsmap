# PLACE-QA-05 — Responsive category popup implementation plan

> **For agentic workers:** Execute only after user approval of this scope. Use `test-driven-development`, `systematic-debugging`, `kidsmap-ui-design`, `frontend-design`, `fixing-accessibility`, `playwright` and `verification-before-completion` as applicable. One sequential executor; no commit/push/deploy. This plan does not authorize PLACE-QA-01–04.

**Goal:** Открытый список категории административного редактора помещается в viewport 360 px, показывает полные названия и сохраняет доступность выбора с клавиатуры.

**Architecture:** На мобильной ширине ограничить popup шириной его поля, разрешить перенос названий и сжатие поискового input. Сохранить существующий custom picker и native select как источник отправляемого значения. Исправить два подтверждённых сбоя закрытия/возврата фокуса внутри того же picker; серверные формы и taxonomy payload не менять.

**Tech Stack:** Existing CSS/vanilla JavaScript, Django 6.0.2, isolated PostgreSQL 17, Playwright CLI with installed Chromium headless shell 153.0.8010.12.

**Spec:** [PLACE-QA-05](../../qa/module01-2026-10-09-r2/findings/PLACE-QA-05.md). [Fresh browser report](../../qa/place-qa05-plan-2026-10-10/REPORT.md).

## Snapshot and global constraints

- PLAN / AWAITING USER APPROVAL. Checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, `active_run: NONE`; application diff empty during planning.
- Preserve incoming QA register edits, module audit directories, prior finding plans/evidence and foreign stands. No production access/credentials, external integrations, commit/push/deploy or broad redesign.
- All runtime work uses `DJANGO_TESTING=1`, a fresh dedicated DB/test DB, LocMem cache/email, separate media/private-media and synthetic records. Browser transport must permit only the owned loopback stand.
- Keep form field names, selected IDs, category/subcategory dependency, server choices, ACL, carryover fields, validation and save lifecycle. Do not replace the widget or hide page overflow to conceal the defect.
- New application copy/localization and unrelated admin UI changes are outside this scope. Existing Russian picker helper strings on AZ/EN are documented context, not silently corrected here.

## Confirmed baseline

The actual admin page was rendered on a fresh isolated stand. RU/AZ/EN × 360/390/768/1024/1280/1440 completed with zero local resource failures and zero page errors in the effective run. At 360, trigger left = 53, width = 254; popup width = 320 and right = 373. Closed document width = 360; opened width = 373. All three languages fail at 360; the other fifteen combinations have no horizontal document overflow.

Long synthetic option names are ellipsized. At 360, Enter opens and focuses search; Tab/Shift+Tab navigate option/search, and Escape from a nonempty result list closes and returns focus. After keyboard selection focus falls to BODY. Escape with no matching items leaves the popup open. These two bounded keyboard defects are explicitly included in the proposed scope because the finding requires keyboard and post-close focus verification.

## Allowed files / ownership

| File | Proposed edit |
|---|---|
| `static/admin/css/pages/kidsmap_place_form.css` | Mobile popup sizing, search flex shrink and full option-label wrapping, scoped to picker selectors |
| `static/admin/js/kidsmap_place_form.js` | Only `initTaxonomyDropdownPickers` / `buildDropdown`: Escape handling and focus return after selection |
| `src/catalog/templates/admin/catalog/place/change_form.html` | Bump only the changed CSS/JS asset versions |
| `docs/qa/place-qa05-fix-2026-10-10/` (new) | Browser regression harness, isolated settings, report, native command ledger and screenshots |
| `.tmp/place-qa05-fix-20261010/` (ignored, new) | Synthetic credentials/state, media/private-media, browser profile and private runtime logs |

The shared category/subcategory builder means both controls need smoke coverage. Read-only dependencies: `section_basics.html`, `place_taxonomy_config.py`, admin form/save handling. No model/schema/backend or public/owner template changes are planned.

## Task 1: Fresh RED and deterministic browser regression

- [ ] Recheck HEAD/WORKTREE/active_run, approved scope, source hashes and foreign stands. Create new evidence; preserve the planning run unchanged.
- [ ] Adapt this audit's `qa05_settings.py`, `runtime.py`, `prepare.py` and `pw.py` into the new fix directory. Use a distinct container/DB/session/media namespace, for example `kidsmap-placeqa05-fix-20261010`, `placeqa05_fix`, loopback DB 55441 and HTTP 8820. Check availability first; record actual endpoints. Use local `postgres:17-alpine --pull=never` and a threaded Django server without autoreload.
- [ ] Use allowlisted process environments, disabled `.env` loading, local-only backend sockets and browser request routing. Reuse the installed test browser; do not alter system Chrome policies. Keep generated login state in ignored scratch and never print it.
- [ ] Reproduce the actual admin category popup before editing source, using the synthetic admin and long RU/AZ/EN category fixture. Capture closed/open geometry and screenshots. Treat missing CSS/JS or page errors as environment failures, not UI PASS.
- [ ] Copy the audited matrix/keyboard sequences into the fix harness. Replace the audit's baseline-only `minWidth === '320px'` readiness check with successful local stylesheet loading and initialized picker checks, so the harness can evaluate changed widths. Assert behavior rather than CSS text:

```javascript
const bounds = await popup.boundingBox();
const geometry = await page.evaluate(() => ({
  viewport: innerWidth,
  scrollWidth: document.documentElement.scrollWidth
}));
assert.ok(bounds.x >= -1);
assert.ok(bounds.x + bounds.width <= geometry.viewport + 1);
assert.ok(geometry.scrollWidth <= geometry.viewport + 1);
```

`popup` is the open `.km-pf-picker-dropdown` inside the category wrapper; `page` is the actual authenticated admin page. Import `assert` from `node:assert/strict` in a browser-runner wrapper, or collect these measurements through CLI and assert them in Python as in the audit. Native CLI exit 0 alone is not a behavioral PASS.

- [ ] Preserve RED failures for 360 overflow, clipped long labels, post-Enter focus and Escape with an empty result. Also cover Escape after Tab moves focus onto an option, so the fix is not tied solely to the search input.

## Task 2: Bounded layout and keyboard changes

- [ ] Add the mobile override next to the picker styles, retaining desktop dimensions. Starting implementation:

```css
@media (max-width: 575.98px) {
  .km-pf .km-pf-picker-dropdown {
    min-width: 0;
    max-width: 100%;
    box-sizing: border-box;
  }
}
.km-pf .km-pf-picker-search input {
  min-width: 0;
  flex: 1 1 0;
}
.km-pf .km-pf-picker-item__name {
  white-space: normal;
  overflow-wrap: anywhere;
  overflow: visible;
  text-overflow: clip;
}
```

The existing popup `width:100%`, `left:0` and positioned wrapper already provide the anchor. At 360 this proposes a 254 px popup ending at 307, within the viewport. Validate this prediction in the rendered form; do not claim it as measured before implementation. Keep the existing vertical list scroll, option count and icons. Do not use body overflow hiding, a clipped fixed-height label or a JS label truncation workaround.

- [ ] Move Escape handling to the picker container before any empty-item early return. It must close when focus is in search or an option, including no-results state. Set `aria-expanded=false` and return focus to the existing trigger. One handler, no duplicate dispatch or global document trap.
- [ ] After `selectValue()` updates the native select, dispatches the existing change and closes the popup, explicitly focus the trigger. Keep outside-click closure from stealing focus from the clicked control. Focus-control shape:

```javascript
container.addEventListener('keydown', function (event) {
  if (event.key !== 'Escape' || dropdown.hidden) return;
  event.preventDefault();
  event.stopPropagation();
  closeDropdown();
  button.focus();
});
```

Remove the now-duplicated search-only Escape branch; its ArrowUp/ArrowDown/Enter behavior remains. Add `button.focus()` to the successful selection path only. Preserve pointer selection, item click semantics and category → subcategory updates.

- [ ] Bump the CSS and JS versions in the active admin Place template, suggested `20261010_place_qa05`. No template layout or form markup changes.

## Task 3: GREEN browser, persistence and targeted regression

- [ ] Run RU/AZ/EN × 360/390/768/1024/1280/1440 with the list open. Require loaded local assets, correct locale, zero horizontal document overflow, popup left/right inside viewport and complete option names accessible through wrapping/vertical scroll. Capture all eighteen states and compare desktop to baseline.
- [ ] Test the same sequences on the subcategory control, long words/long names, scrolling inside the list, search with one/no matches, and resizing while open. Verify the search input and count text do not protrude or cover labels. Do not introduce a fixed height that cuts off multi-line options.
- [ ] At 360 in each language: keyboard Enter opens/focuses search; Tab/Shift+Tab work; ArrowDown/Enter selects; Escape from search/option/empty-result closes; selection/Escape return focus to the trigger; outside click keeps its intended focus. Use actual `document.activeElement` and `aria-expanded` readback.
- [ ] Add a valid translated synthetic subcategory under the long synthetic category during fixture setup. On a valid synthetic draft, choose category/subcategory through the real control, save through admin, reload and verify selected native values, displayed labels and DB values agree. Preserve sentinel title/address and unrelated fields. Reopen the popup after reload. Save validation errors must remain visible and be reported, not bypassed by direct DB updates.
- [ ] Run existing `catalog.testcases.place_taxonomy_admin` and `catalog.testcases.test_task33_admin_editors` on the dedicated test DB via the allowlisted isolated runner. This is targeted coverage for shared form wiring; do not add CSS-string assertions or unrelated unit tests for this change.
- [ ] Retain blocked external-font/CDN requests separately from local static errors. Report actual browser version, DPR/viewport, console/page errors and local resource outcomes. Existing locale helper-string limitations are not a reason to rewrite other screens.

## Task 4: Review and handoff

- [ ] Save exact commands/exit codes, baseline and post-change geometry, keyboard results, screenshots, saved/reloaded DB readback, HEAD/worktree and source hashes. Explicitly list NOT RUN checks with reasons.
- [ ] Review only the approved file diff. Preserve incoming changes. Close only the owned browser session/server/container, identified from creation records; no blanket cleanup or foreign stand restarts.
- [ ] Mark PLACE-QA-05 fixed only when layout, full labels, keyboard, save/reload and targeted regressions meet these acceptance criteria. Report any unrelated finding separately instead of widening implementation silently.
