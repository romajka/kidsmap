# PLACE-QA-14 — shared unsaved modal keyboard focus — P2 OPEN

LOCAL `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 + approved QA09–13 dirty changes. Current shared `static/admin/js/kidsmap_notifications.js` unchanged by these fixes.

Native English390 and Russian360/390/768/1024/1280/1440: change valid admin field, click actual breadcrumb. Modal appears with correct translated text, but activeElement stays on the underlying breadcrumb. Three forward Tab presses leave focus outside; Shift+Tab reaches Discard. Repeated settled1200ms visible/document.hasFocus=true trace gives same outcome. Real commands, input and screenshots, not a source-only finding.

Cause verified for forward focus trap: `getFocusableElements` selector `[href]:not([disabled])` includes visible SVG `<use href=...>` in the dialog icon. Runtime exact selector list is `[SVG use, Stay BUTTON, Save BUTTON, Discard BUTTON]`. Its first SVG node is not a keyboard control. Initial focus call trace separately shows primaryButton.focus invoked while final activeElement is the breadcrumb; precise render/click timing requires diagnosis before its fix.

Evidence in ../place-qa12-fix-2026-10-12-r1/: focus-diagnostic.result.json, focus-diagnostic-settled.result.json, focus-call-trace.result.json, focus-event-trace.result.json, focus-selector-diagnostic.result.json; modal-green-ru.result.json contains original actual failing keyboard rows. Native screenshots linked in each raw result and SHA manifest. Diagnostic prototype instrumentation delegates original focus unchanged and only records calls; uninstrumented tests also reproduce. No injected focus accepted as proof of fixed keyboard behavior.

QA13 language/action verification is separate and passes18cells; this shared keyboard issue is not claimed repaired or a newly introduced regression. No canonical overwrite/security leak demonstrated. Applies to keyboard users; other shared modal consumers require scoped fresh checks.

Proposed exact plan: ../../superpowers/plans/2026-10-12-place-qa14-modal-keyboard.md. NOT APPROVED, implementation NOT RUN. Do not expand QA12/13 approval to this file. Module01 remains OPEN; module02 not started.
