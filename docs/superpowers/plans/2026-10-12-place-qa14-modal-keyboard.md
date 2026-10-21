# PLACE-QA-14 — unsaved modal keyboard focus — APPROVED 2026-10-12 / IMPLEMENTED PARTIALLY, QA14 OPEN

LOCAL only. No commit/push/deploy/production. Preserve QA09–13, active_run and every existing stand.

## Bug and desired behavior

Native EN390 and RU360–1440: opening the admin unsaved-navigation modal leaves document.activeElement on the underlying breadcrumb. Forward Tab does not reach its actions; Shift+Tab reaches Discard. Copy and actual click/save actions are independent and work. Current scope QA13 only translates strings; it does not authorize the shared modal component.

Confirmed source pitfall: static/admin/js/kidsmap_notifications.js:getFocusableElements accepts every `[href]`, including SVG `<use href=...>` inserted in the modal icon, rather than actual links. Such elements can have visible rects but are not keyboard controls. Verify exact runtime selector sequence before patch; diagnose the initial focus timing separately instead of assuming the SVG selector explains every symptom.

## Exact scope

- static/admin/js/kidsmap_notifications.js: getFocusableElements, unsavedChanges focus timing and handleKeydown only if needed to fix this cause.
- New scripts/test_admin_modal_keyboard.cjs: meaningful regressions for a modal containing SVG use, native controls, forward/reverse wrap, initial and restored focus. Do not change existing assertions.
- Own docs/qa/place-qa14-fix-2026-10-12-r1/ scripts/evidence/report; current module status links.

No save callbacks/ACL/CAS/copy/global styling/PO/schema edits. Existing untrusted text continues through textContent. Do not add artificial focus fixes in QA harness or weaken autofocus/keyboard acceptance.

## Execution

1. Capture native RED and actual focusable sequence using an isolated own profile. Test RED on the current unchanged shared component.
2. Restrict link selector to real links and focus only visible enabled controls; settle the initial modal focus after actual rendering if the native trace proves it necessary. Keep Escape/close and focus restoration intact.
3. Native RU/AZ/EN ×360/390/768/1024/1280/1440: open by real link, verify initial focus inside, forward/reverse Tab, Enter/Space/Escape, Stay/Discard/Save+reload/read-only persistence and conflict/error retention. No injected focus as acceptance proof.
4. Targeted new tests and actual shared modal consumers (confirm/alert/show and unsaved dialog) on representative local routes. Global project corpus deferred until all13 modules per user's chat instruction.
5. One module01 acceptance after all its fixes; retain baseline/environment/NOT RUN boundaries. Do not begin module02 automatically.

## Execution status

User approved this exact plan. SVG/real-control filtering and initial focus scheduling implemented within permitted functions.4 targeted regression tests pass. Backend module425+45 passes; Node module49PASS/1SKIP. Native matrix reveals remaining failure; do not close QA14 or module01. Fresh rapid-reopen trace proves the220ms close() callback focuses the breadcrumb after a newer modal is visible. close() was outside exact function bounds; extension plan 2026-10-12-place-qa14-close-race.md awaits separate approval. Partial/source/timing attempts retained in docs/qa/place-qa14-fix-2026-10-12-r1/REPORT.md.
