# OFFER-QA-03 — CLOSED LOCAL, scoped repair

2026-10-13. Executor /root, sequential canonical kidsmap-orchestrator; no independent agents claimed. User explicitly approved `docs/superpowers/plans/2026-10-13-offer-qa03-structured-error-focus.md`. Only OFFER-QA-03; full ACCEPT-05 NOT RUN.

## Snapshot / isolation

`/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch task33-progress, incoming dirty WORKTREE captured in entry.json, active_run NONE. Four existing application files and one new regression module. application.diff compares incoming WORKTREE to this repair, avoiding previous module/finding changes. entry-final.json binds source loaded by own process; final verification records allowed changes, retained input hashes and runtime receipt.

New own QA profile `offer-qa03-fix-2026-10-13-r1`: separate PostgreSQL17.10 container/volume/DB/user, explicit loopback; own cache/media/private-media/email/browser sessions. HTTP127.0.0.1:47411 PID457642, own DB offerqa03fix_20261013_r1; fresh actual PG port in runtime-version-final.json. .env not loaded, inherited env cleared, DJANGO_TESTING=1; backend socket connect/connect_ex permits only own PostgreSQL. Browser outside requests BLOCKED (not real integrations). Credentials only ignored .tmp/profile with0600 files, never evidence/Git. Fictional fixtures only.

Fresh RU/AZ/EN compiled from current PO via scripts/build_isolated_locales.py into own profile, native GNU msgfmt; locale-manifest.json/source hashes and final verify exit0. Sole LOCALE_PATHS installed before django.setup. Shared old MO unchanged. No PO changes or new messages in this repair; other tariff enum captions still partly Russian in AZ/EN (existing scoped02 limitation, OFFER-QA-06 fresh recheck), not claimed localized by this repair.

## Root cause / changes

Historical finding confirmed again in `../offer-qa03-recheck-2026-10-13-r1/REPORT.md`: price0 in second plan/group/activity gets422 and preserves value, but error button focuses first activity program_id. Backend flattened field validation into translated text without tree address, frontend tried to parse paths from that text.

1. services/pricing_plans.py: attach independent field_path in ValidationError.params, prefix activity/group/plan indices, preserve existing canonical validation/message/order, numeric conversion field and age bound targets. Safe block targets for structure/foreign IDs. Defaults remain compatible; prior OFFER01 archival/OFFER02 choices retained.
2. photo_views.py: add parallel error_targets aligned with existing errors, retaining conflict metadata.
3. permanent_place_photos.js: preserve targets through XHR/save error branches.
4. owner_place_continuous.js: validated numeric segment/address whitelist, no translated error parsing; one summary link per message, correct details/focus, visible billing fallback, clear only summary-owned previous ARIA state.
5. new test_offer_qa03_error_targets.py: meaningful service/form/HTTP boundary tests, actual second tree node, localization-independent paths, price/range/billing/age/number format, foreign IDs, rejected write boundaries and successful candidate-only save.

forms.py proved to preserve params without modification; no business rules, models/schema/migrations/publication/ACL/CAS/constraints/CSS changed. No extra finding repaired or closed.

## Backend evidence

`backend-red.txt`: initial9methods,17failure reports includes one new fixture mistake: direct plan price0 omitted price_kind=exact and canonical compatibility correctly inferred free. Corrected fixture before application patch, no existing assertion changed. `backend-red-corrected-fixture.txt`:9methods,16expected missing-path failure reports,2existing-behavior checks PASS. Prior native focus6expected FAIL preserved in recheck evidence.

Approved patch followed by `backend-green.txt`:14/14methods PASS,9new +5existing service/form guards,0failures/errors, exit0. Tests use own isolated PostgreSQL; --keepdb is only own unique test DB. Same assertions kept through RED/GREEN, no no-label/global wrapper. Canonical valid HTTP save stayed candidate-only; error422 did not change live or create candidate. Node checks for both changed JS files exit0; final locale verification exit0. Exact argv/exits/counts in *.command.json and commands.jsonl. No unchanged full suites repeated.

## Native browser acceptance

`native-matrix-final.json`:314unique PASS assertions across RU/AZ/EN×360/390/768/1024/1280/1440. Every cell uses2activities/4groups/8plans and error in1/1/1, native save422, close/click error, correct exact price focus, appropriate ancestors open/first branch closed, invalid/description ARIA references, uncovered focus, retained0, geometry, real successful save/reload. At390 each language additionally verifies range max, plan age, group age, recurring count and installment cycles, hidden advanced details and repeated-summary cleanup. Keyboard Tab/ShiftTab around price included.

`billing-keyboard.result.json`:15/15 PASS, native recurring-count422, retained0, count focus, Tab skips hidden cycles and ShiftTab returns; viewport PNGs in3languages.

`admin-browser.result.json`:16/16 PASS, actual admin language menu transitions RU/AZ/EN, native nested price0 rejection and retained value, corrected25 saved/reloaded. No substitute ORM user action; ORM only fictional fixture prerequisites and explicit readback.

`moderation.result.json`:16/16 PASS. Native owner submits corrected30 in3languages, real staff approval, public Activity shows30 only after approval, owner reload sees30. Prior live20 retained before moderation.

Total361 accepted unique assertion IDs (314+15+16+16),0accepted FAIL/harness exceptions.96accepted native viewport PNGs, plus3retained diagnostic PNGs; png-manifest.json records paths/bytes/SHA256. Visually inspected RU360 price focus, EN390 recurring count and AZ390 group age. Main console/pageerrors empty; local >=400 responses only expected save422, outside map/media requests blocked. This proves scoped browser behavior, not all module consumers.

## Harness / baseline corrections, preserved raw evidence

First native capture attempted response.json after successful navigation and lost response body; browser.result.json / diagnostic.result.json preserve the harness failure. Corrected recording via interception of the actual button-generated local POST: route.fetch forwards unchanged request to own backend, stores actual response body before route.fulfill. No simulated validation/success response, no API substitute for checked user transitions. Positive one-cell diagnostic accepted13assertions (not added to final count).

Initial corrected bulk reached complete ru360 then stopped at ru390 because a group age selector also matched its nested plans (strict selector harness failure). Raw browser.result.attempt1791897302.json retained. Scoped to the group's first actual field and resumed remaining17cells in browser-resume.result.json, without app changes or repeating completed ru360. Final matrix aggregates completed11ru360 assertions plus303resume assertions; unfinished-prefix rows excluded. Diagnostic screenshots separately retained before final run.

First own readback assumed every revision carried nested_pricing and got KeyError for unchanged-price candidates. Canonical candidate payload is a delta. Corrected evidence script reads effective live20 only when no tree change exists and requires explicit candidate tree for all corrected30 cases; raw failed command retained, no application or existing test assertion changed. All live20 and revision_version1 verified before moderation, so rejected saves did not increment revisions. A first evidence aggregation assumed13cell assertions (two were global checks); corrected to actual completed ru360 IDs; no browser assertions altered.

OFFER-QA-09 partial candidate readiness baseline remains OPEN, not repaired. These harness corrections do not erase independent application findings or confer full module PASS.

## Readback / preservation / limits

READ ONLY transactions, statement_timeout10s/lock_timeout2s, own fictional rows only. readonly-candidate-readback-corrected exit0:18valid candidates, all live20/IDs stable, revision_version1. readonly-approved-readback exit0:3native approvals now live30/revision3;15others live20/revision1;3admin candidates25 with live20. No ORM used to perform checked save/moderation transitions.

verification.json: entry/HEAD/branch/active_run preserved, exact5application files, previous reports/source/tests preserved, current runtime source match, locale verify, PNG hashes. Own new stand retained; other containers/volumes/profiles/processes not stopped/restarted or reconfigured. All approved repairs remain local dirty diff, no commit/push/deploy/production.

NOT RUN: full ACCEPT-05, global suite/full discovery, other OFFER findings, production, real maps/external APIs/email delivery, physical devices/screen reader, exhaustive unrelated shared consumers. Backend old assertions unchanged. LOCAL scoped closure applies only OFFER-QA-03 on recorded WORKTREE/runtime. Next PLAN OFFER-QA-04 after user selection; no automatic next implementation.
