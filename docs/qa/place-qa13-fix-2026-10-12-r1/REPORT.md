# PLACE-QA-13 — copy cause FIXED LOCAL, 2026-10-12 r1

Codex primary, sequential; user approved `docs/superpowers/plans/2026-10-12-place-qa13-unsaved-modal-localization.md` with QA12. Shared owned QA12 runtime/profile; [source/isolation/preservation](../place-qa12-fix-2026-10-12-r1/REPORT.md). Checkout `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, dirty approved fixes, active_run NONE.

## Cause / patch

Existing admin unsaved-navigation callback passed five Russian literals in every language. Fresh native EN390 and AZ390 RED both failed active-language check; raw JSON/PNG in QA12 `modal-red.result.json`.

Only five approved `t(ru,az,en)` ui_copy keys added in `src/catalog/services/permanent_place_wizard.py`. Existing `static/admin/js/kidsmap_place_form.js` uses them for title/body/Stay/Save+leave/Discard and existing localized labelSaving for saving toast. Callbacks, form transport, business contracts and language selection unchanged. QA12-specific CAS guard is separately authorized. No new PO/shared MO, templates/global modal/style/backend save/schema changes for QA13.

## Verification

[Qualified copy/action observations](qualified-copy-actions.json): all18 RU/AZ/EN×360/390/768/1024/1280/1440,72PASS: exact five strings, viewport/wrapping geometry, real Stay input retention, actual Discard navigation/no persistence, actual Save+leave POST and later GET/reload readback. No HTTP-status-only acceptance. Final POST response can be200; acceptance requires the deliberately saved value on the following actual form. Earlier own302-only oracle retained and superseded by real persistence proof.

Native three-language simulated network failure and genuine CAS keep original input and stay on page; QA12 report links9PASS. Eight new backend negative/retention tests,65 affected existing passes, Node11PASS/1SKIP listed there; no blanket global-suite claim. Fresh RU/AZ/EN compiler manifest verified before django.setup; no shared catalogue writes. Screenshots and exact native commands in QA12 manifest/commands; EN390 modal and file-error screen manually inspected, not all PNGs.

## Independent OPEN / boundaries

Initial full modal acceptance exposed separate PLACE-QA-14: initial focus on underlying breadcrumb; forward Tab cannot reach actions, Shift+Tab reaches Discard. Language strings and click actions pass; keyboard acceptance is **FAIL**, not silently removed or relabeled PASS. Native raw focus/keydown/call/selector traces retained, no injected focus workaround accepted. This copy defect is fixed, but complete plan/module UI acceptance is blocked by that independent shared-component cause. Proposed QA14 changes are unapproved.

Generic older admin error/toast copy can still mix languages; only approved unsaved-dialog copy is closed here. Global locale/cross-module tasks remain separate. Physical devices/other browsers/screenreader/provider/production/global corpus NOT RUN. User requested targeted checks per fix; full module after its remaining findings, global after all13. Existing worktree/active_run/stands preserved. No commit/push/deploy/production.
