# OFFER-QA-11 Admin Select2 Serialization Implementation Plan

**Goal:** Choosing a tariff/group option in the actual admin Select2 must update the submitted nested tree and survive save/reload.
**Architecture:** Keep the existing canonical owner/admin offering fields and server validators. Bridge actual Select2 selection/clear events into the same native change path already used by plain owner controls, so serialization and taxonomy/program/billing callbacks receive the real selection. No copied business rules or new data format.
**Tech Stack:** Existing JavaScript, jQuery/Select2 and native Chromium; current isolated Django/PostgreSQL profile.
**Spec:** `docs/qa/offer-qa10-fix-2026-10-14-r1/select2-diagnostic.result.json` and `admin-accept.result.json`.

## Exact scope / authorization

APPROVED2026-10-14 by user «закрой полностью5ый что надо сделай». Completed locally; docs/qa/offer-qa11-fix-2026-10-14-r1/REPORT.md and final verification. The previously approved OFFER10 plan permits only nine PO msgids and explicitly excludes JS. Only the specified JS file was changed,6lines. No commit/push/deploy/production. Preserve incoming/concurrent source, active_run and foreign stands; use own fictional DB/cache/media/private-media/email and strict fresh locale manifest.

Only application file: `static/js/owner_place_offerings.js`, shared field creation/event binding. QA regression scripts/evidence only in a new `docs/qa/offer-qa11-fix-<unique-run>/`, plan progress and scoped module05 status/supplement. No backend/models/schema/ACL/CAS/pricing/readiness/PO/template/CSS/library changes.

## Reproduction / cause

Actual native admin Select2 `product_type` changed membership→tour. Visible/DOM value is tour, but hidden `nested_pricing.activities[0].groups[0].pricing_plans[0].product_type` stays membership. Real admin save/reload also returns membership. Pageerrors0. Labels now translate correctly; this is a separate P2 data-entry bug, not a failed translation. Source: shared `field` listens with addEventListener('change'); Select2 sends jQuery selection/change events. No equivalent native event reaches the existing tree update path.

## Tasks

- [x] Refresh checkout/source/dirty/active_run and own runtime. Recheck current source and preserve RED: actual Select2 selection→DOM/tree equality, native save/reload equality. Do not weaken expected values or replace the tested user transition with ORM/selectOption on a hidden Select2 input.
- [x] In shared field creation, for actual enhanced selects attach a guarded existing-jQuery handler for public `select2:select`/`select2:clear` events, forwarding to the existing native change event path. Ensure plain owner native change remains unchanged, no recursive custom-event loop, no duplicate save/network requests. Program/category/billing-specific native listeners must receive the forwarded change too; updating only the JSON property would leave dependent controls stale.
- [x] Keep/select a canonical value for clear according to existing control/options/server rules. No invented defaults or model enum changes.
- [x] GREEN meaningful native regression with unchanged RED assertions: product type, price kind, group lesson format, recurring interval and billing visibility; category/subcategory/program shared callbacks where applicable. Choose through real visible Select2. Verify DOM+serialized tree agreement, actual save/reload, approve/readback/public price and preserved candidate/live behavior. Restore owned fictional baseline20 through native transitions.
- [x] Targeted owner plain-control smoke and RU/AZ/EN×six widths for affected Select2 keyboard/focus/dropdown/clipping. Existing accepted caption assertions may be reused only with unchanged PO/source receipts; no full334backend rerun for this JS-only bridge. Node syntax plus affected native checks, preserve initial failures and SIMULATED/NOT RUN limits.
- [x] Fresh exact commands/exits/counts/PNG/source/locales, reviewable one-file diff; close11 only on actual acceptance. Resolve runtime/input drift through own new locale directory and source binding, never bypass verify or stop foreign processes. Add full ACCEPT05 supplement only if no remaining confirmed issue; preserve original FAIL reports. Then offer module06 PLAN, do not start06 automatically.

Final2026-10-14: OFFER11 CLOSED LOCAL; module05 ACCEPT LOCAL PASS, docs/qa/module05-full-2026-10-14-r2/REPORT.md.505native accepted checks/36cells/45PNG, fresh15READONLY and84locale checks;334corpus reused,6projection methods repeated for proven foreign helper extraction. Final runtime/source/sole fresh locales MATCH. Old failures kept, no module06 started.
