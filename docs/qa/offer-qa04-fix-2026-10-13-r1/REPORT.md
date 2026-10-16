# OFFER-QA-04 — CLOSED LOCAL, scoped CSS repair

2026-10-13, /root sequential canonical kidsmap-orchestrator; no independent agents claimed. User approved `docs/superpowers/plans/2026-10-13-offer-qa04-schedule-container-layout.md`. Only OFFER-QA-04; full ACCEPT-05 NOT RUN.

## Outcome / snapshot

Owner «Интервал»/«Копировать» fit the actual table width with sidebar at all27tested RU/AZ/EN×360/390/768/900/960/1024/1100/1280/1440 cells. Open copy picker fits viewport at12mobile/desktop cases, actual controls work, keyboard/pointer tests pass. Shared Place admin and actual volunteer consumers preserve existing layout/actions.335accepted unique native assertions PASS,0accepted FAIL,81accepted PNGs. No backend/full/global suites run for this reversible visual CSS change; no source-mirroring tests.

Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, task33-progress, dirty incoming WORKTREE captured in entry.json, active_run NONE. Exactly1application file changed: static/css/components/kidsmap_schedule_editor.css,39appended lines. application.diff compares incoming WORKTREE, preserving previous module/repair changes. No JS/templates/backend/schema/business rules/PO/old assertions changed.

## Cause / implementation

Baseline recheck `../offer-qa04-recheck-2026-10-13-r1/REPORT.md`:17/27geometryFAIL plus3/3exact-table1024FAIL. Sidebar left only621px atRU1024; viewport-selected fixed160/120/200/175px columns and nowrap actions overflowed/clipped copy button at1097.94 beyond table942/viewport1024. Document scrollWidth alone did not reveal clipping.

Owner-only named inline-size container on TABLE (not entire editor), narrow tables use existing stacked reading order with wrapped actions, no smaller fonts/hidden actions/horizontal scroll. Query on table excludes editor-appended mobile popup/overlay; shared admin selectors remain excluded. Native acceptance exposed desktop copy popup's bottom extending beyond viewport after actions became accessible; same approved CSS file now centers owner desktop picker, constrains its height and allows internal scroll. Disable only its generic desktop translate animation so it cannot override centering. Mobile bottom-sheet and admin popup anchoring retain their existing rules. Tokens/text/handlers/contracts unchanged.

## Isolation / current runtime

New own profile offer-qa04-fix-2026-10-13-r1, separate PostgreSQL17.10 container/volume/DB/user with explicit loopback, cache/media/private-media/email and named browser sessions. Own HTTP127.0.0.1:55765; current PID/source/ports in runtime-version-final.json, do not reuse as portable parameters. DJANGO_TESTING=1, no checkout .env load, inherited env cleared; transport permits only own PG connect/connect_ex. LocMem cache/email; browser outside requests BLOCKED/SIMULATED, no real integrations. Credentials only ignored own .tmp files0600, never report/Git.

Fresh RU/AZ/EN build through scripts/build_isolated_locales.py, native GNU msgfmt, own locale directory; locale-manifest.json and final verify exit0, sole LOCALE_PATHS installed before django.setup. Current PO unchanged; shared MO preserved. tools.json records actual tool versions; runtime receipt binds current source/startup/disk. Fictional prerequisites only, regular schedule with2Monday intervals; other days inherited canonical test helper, not an assertion that all weekends initially closed. Later explicit native closed/open/24h tests cover weekend transitions.

## Native evidence / accepted aggregation

- browser.result.json:27/27real-rendered table/button geometry cells PASS,3languages×9widths,2Monday intervals, pageerror/local error lists empty. No injected prototype CSS in acceptance.
- Functional completed RU prefix in functional.result.json + functional-contract.result.json:92unique accepted assertions. Actual third interval19:00–20:00 added, copy toTue/Thu with real confirm dialog, untouchedWed preserved, save/reload; invalid18:00 end rejected422 and input retained; native24h/hours/closed transitions, copy cancel retains input, explicit save/public and actual moderation path. Existing contract preserves schedule's immediate explicit-save policy (below).
- Shared completed Place RU prefix in shared-admin.result.json + shared-admin-resume.result.json:128unique accepted assertions across18cells (Place admin/actual volunteer×RU/AZ/EN×390/1024/1440). Actual third interval/copy popup/cancel/keyboard smoke, owner named container excluded. Shared saves NOT RUN; own owner save/readback separately verified.
- popup-hit-test.result.json:73/73final-source assertions,12cases RU/AZ/EN×390/768/1024/1440, whole popup bounds inside viewport, actual cancel and control/keyboard hit tests. Full control descendants count as valid pointer hits. Pageerrors empty.
- state-transitions-settled.result.json:15/15final-source assertions,3languages at390, explicitly start closed → open →24h → ordinary hours →closed, native visible labels, waits for existing150ms visibility transition. No explicit save in this supplemental state smoke; live unchanged by it.

native-final.json deduplicates completed IDs:27+92+128+73+15=335PASS. PNG manifest separates81accepted screenshots,1permission-fixture diagnostic,18interrupted captures; only final popup/state subset rerun after popup-only refinement. Prior row/admin/backend prefixes remained byte-identical and unaffected; no unchanged whole matrix/backend repetition after refinement. Source stage is explicit: initial row/native lifecycle/shared matrix used row CSS before popup refinement; final popup/state use final CSS, with prefix preservation proven. Visually inspected EN1024layout and final RU1024popup. Exact argv/exits/raw outcomes in commands.jsonl/*.command.json/COMMANDS.md. Browser CLI0 alone is never PASS.

## Canonical business contract clarification

The approved plan's candidate-only schedule expectation was wrong. Current docs/task33/prompts/08.md:51 explicitly permits price amounts/schedule immediately after explicit save of published Place; prompts/09.md:50 keeps autosave private. publication.py:_immediate implements it. schedule-boundary-diagnostic.json READ ONLY showed live3intervals plus draft nature-only candidate; no backend regression. functional-final.result.json retains the false-positive pending-public assertion. Correct only that new expectation, do not change business rules or existing assertions. New native explicit-save/public proof passes; actual submit/approval/public metadata path still tested. No extra finding invented/closed.

Final READ ONLY readback, statement_timeout10s/lock_timeout2s, own fictional rows only: functional3places have expected Mon/Tue/Thu3intervals, Wed unchanged, Sat closed, approved revision_version3; geometry/admin6prerequisites remain original2Monday intervals with no revision. Rejected422 saves did not increment revision; native explicit saves update schedule per canonical policy. Place IDs stable; schedule rows are canonically recreated by sync_place_schedule, not claimed stable row PKs. ORM used only prerequisites/readback, never checked UI transitions.

## Environment and harness failures retained

External lifecycle interruption: own old runtime525077/browsers disappeared; owned PostgreSQL container Exited255. Cause UNKNOWN. Interrupted native commands have no final result and are not accepted;18PNG retained separately. Resumed ONLY own exact container/volume, started own runtime, verified source, READ ONLY saw zero revisions before recovery runs. No foreign stand restarted/stopped/reconfigured, their availability after interruption is NOT RUN. Own runtimes later restarted only after verifying exact /proc script identity to bind popup CSS source.

Functional scripts initially targeted hidden styled checkbox inputs; visible label click is the actual UI transition. Restored private edit state required setting desired checked state through native labels rather than assuming starting state. These harness failures/prefixes retained, no forced clicks or app changes. Late supplemental state test initially observed controls during existing visibility animation; waitFor visible completed and same assertions passed.

Shared volunteer initial403 was correct ACL: superuser deliberately cannot use volunteer workspace. Created fictional actual staff volunteer with canonical KidsMap Volunteers group and its own unowned fixture, preserving permission rules. Wrong-role diagnostic/FAIL retained outside accepted aggregation. Popup initial uncovered assertion expected BUTTON itself although real hit was a child span; own harness corrected to self-or-descendant (not overlay), same pointer behavior requirement; raw FAIL retained. Initial schedule assertion corrected only against canonical source/spec, never altered app tests to obtain green.

## Preservation / limits / handoff

verification.json validates preserved incoming files except exactly1approved application CSS plus bounded plan/status/docs, unchanged HEAD/branch/active_run, current runtime source and locale hashes, no extra source files, native/readback result counts/PNG SHA/bytes. Full source inspected scoped diff; existing backend/tests/PO/foreign WORKTREE bytes retained. No commit/push/deploy/production, no foreign process/container/profile controls or active_run assignment.

NOT RUN: full ACCEPT-05/global suite/full discovery, production, external maps/email/APIs, physical devices/screen reader/other browser engines, unrelated historical findings. Only scoped OFFER-QA-04 CLOSED LOCAL; OFFER01–03 retain prior scoped closures, OFFER05–08 require fresh recheck, OFFER09 remains OPEN baseline. Next PLAN OFFER-QA-05 only after user selection, no automatic implementation.
