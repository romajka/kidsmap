# PLACE-QA-14 — shared modal focus scope extension — APPROVED — user 2026-10-12

LOCAL only. Parent approved plan: 2026-10-12-place-qa14-modal-keyboard.md. Existing SVG-selector/timing diff, worktree, active_run and all stands preserved. No commit/push/deploy/production.

## Bug / fresh proof

After Escape, close() removes the previous backdrop after220ms and unconditionally restores the shared lastFocusedElement. If the unsaved modal is reopened before that callback finishes, the old callback focuses the underlying breadcrumb instead of keeping focus in the new visible modal.

Fresh actual native EN390 proof: docs/qa/place-qa14-fix-2026-10-12-r1/rapid-reopen-diagnostic.result.json. Delegating focus-call trace shows the primary button focused, then anchor focus from kidsmap_notifications.js:161 in the220ms close callback; new modal remains visible and activeElement is outside. This separate cause explains why partial normal keyboard passes did not close QA14. It is not a CAS/copy/backend issue.

## Exact additional scope

- static/admin/js/kidsmap_notifications.js: close(), show() and a shared initial-focus helper, in addition to the already approved getFocusableElements/unsavedChanges/handleKeydown bounds. Native price-confirm initial focus also fails although forward/reverse Tab now work (shared-consumers.result.json).
- scripts/test_admin_modal_keyboard.cjs: add meaningful overlap regressions using pending close timer + newly opened modal. Preserve existing assertions/callback behavior.
- Own docs/qa/place-qa14-close-fix-2026-10-12-r1/ evidence/report; current module01 links.

## Minimal implementation

Capture the closing modal's return-focus element locally. Remove only that modal's old backdrop. Restore its trigger only if no newer modal is active and the target is still connected/focusable. Never let an old close callback steal focus from a new modal. Give show()/unsavedChanges one consistent, cancellable initial-focus path that waits for actual visible controls; diagnose first-opening failures as well as overlap, do not assume the close timer explains everything. Keep normal Escape/Stay focus return, onClose/onStay callbacks, animation duration, textContent rendering, save callbacks and all business contracts unchanged. No CSS/PO/backend/schema changes.

## Verification

1. Existing actual close-race RED is preserved in close-race-red.cjs/.txt (1FAIL); promote the meaningful regression to the new test module without weakening it. Add a normal shared-show visibility test. New RED with old close callback pending while another modal is open; it must preserve the new primary focus. Normal close returns to the correct original trigger; removed/disabled triggers do not cause errors.
2. GREEN new targeted tests. Native fast Escape/reopen and Stay/reopen on RU/AZ/EN at390/1440; native full ordinary keyboard/modal actions matrix18cells on final source, no injected focus workaround. Check actual shared confirm/show/alert consumers and save/error/CAS retention.
3. Reuse already completed470 module01 backend tests by verified unchanged Python hashes; do not repeat them for this pure shared-JS fix. Repeat affected JS only, then finish pending native full ACCEPT-01 once. Global project corpus remains deferred until all13 modules per user.
4. Own exact commands/exits/counts/runtime/locale/PNG/preservation report. QA14 remains OPEN until its complete acceptance; module02 not started automatically.
