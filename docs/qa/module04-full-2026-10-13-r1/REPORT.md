# Module04 — Events — final LOCAL acceptance

2026-10-13, root sequential execution, lead kidsmap-orchestrator. **LOCAL PASS in the executed module04 scope. EVENT-QA-01–06 CLOSED LOCAL.** No independent specialists claimed. Final verification.json is the source/runtime/preservation gate; this is neither a production nor global-project acceptance.

## 1. Snapshot, scope and authorization

Checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` plus preserved and approved dirty WORKTREE; active_run NONE. Initial [snapshot](../module04-recheck-2026-10-13-r1/entry.json), final [verification](verification.json), [runtime](runtime-version-final.json), [diff](application.diff), [source changes](source-change-manifest.json).

Approved plans and explicit chat receipts:
- [EVENT-QA-02/03 and ACCEPT-04](../../superpowers/plans/2026-10-13-module04-event-photo-localization.md).
- [EVENT-QA-04 publication photo gate](../../superpowers/plans/2026-10-13-event-qa04-published-photo-gate.md).
- [EVENT-QA-05 error message plus separately approved adjacent singular/plural instruction](../../superpowers/plans/2026-10-13-event-qa05-admin-publication-message.md).
- [EVENT-QA-06 explicit Russian fallback entries](../../superpowers/plans/2026-10-13-event-qa06-russian-fallback.md).

Only7 application/source files: shared admin shell JS, Event readiness JS, EventAdminForm in domain_admin/place.py, new test_event_admin_photo_clear.py, RU/AZ/EN PO. Prior Place changes within domain_admin/place.py remain intact. Only EventAdminForm publication-checklist branch changed; no service/model/schema/ACL/CAS/default-language change. Corresponding guide/status links updated; historical reports/index/transfer inputs retained.

## 2. Strong outcomes and repairs

| ID | Result / cause | Fresh evidence |
|---|---|---|
| EVENT-QA-01 | Correct current RU owner/venue labels after own current-PO build; no field/schema patch. Historical stale common MO not reused. | Initial rendered labels,2 existing label/shared-consumer tests, full admin states/language matrix. |
| EVENT-QA-02 | Event loads different shared shell from Place. Three wrong id lookups replaced with real form/name checkbox binding; removal emits native change; Event readiness reads actual checkbox. Draft deletion/reload, replacement and cancellation work. | Native RED5 failed assertions → GREEN8; gallery/public/readback and shared consumers. |
| EVENT-QA-03 | Owner/admin edit caption fuzzy; stepper/next/organizer accessible names absent. Correct AZ/EN strings with actual isolated MO. Original long requirements/recovery translations already present; no workflow/copy rewrite. | Fresh Django-native proof and owner label18 cells; error/conflict/recovery matrices. |
| EVENT-QA-04 | Explicit clear is False, and Python False == 0; numeric-zero exception accidentally treated removal as allowed. Separate photo-False branch rejects published clear. Draft delete remains allowed. | Published browser save/readback exposed empty-photo published baseline; meaningful regression RED → GREEN5; native gate18. |
| EVENT-QA-05 | Publication message fuzzy/wrong previous translation; adjacent plural correction instruction empty. Entire validation warning now translated in AZ/EN. | Whole-alert18 single-error cells plus6 plural cases; actual photo remains unchanged. |
| EVENT-QA-06 | Partial locale repair exposed Django default-AZ fallback in RU:3 absent labels and a singular-only entry used by ngettext. Explicit RU labels/matching plural entry eliminate this repair regression. LANGUAGE_CODE remains az. | [Django-native RED](native-locale-proof-red.json), [final](native-locale-proof.json); final owner18 and full-alert24. |

New04–06 findings were implemented only after specific scope approval. No other module ID closed by this run. EVENT-QA-01 acceptance does not close PUBLIC-QA-03/SITE-QA-07 or the entire shared locale group.

## 3. Functional and rendered browser acceptance

Actual Chromium, own new CLI session/contexts, own fixtures. Checked business transitions use native clicks, keys, file selection and submits; no ORM Event transition substituted for them.

- Organization-owner3-step draft save from every step, reload, required-field submission errors, physical/custom address, online/back retention, Asia/Baku overnight interval, submit→pending→reject reason→correct/resubmit→approve→public and published-owner editing restriction.
- Independently verified specialist organizer, online draft/date/age/file errors, actual submit and moderator approval/public online display. An unlinked/no-organizer user receives guidance.
- Own/public venue selection and organizer separation; hidden/foreign draft choices excluded; unavailable venue during input rejected without Event write.
- Foreign-ID GET/POST/edit/manage/cancel/reschedule denied; organization rights revoked after input and verified-person link reassigned in old session denied. These negative prerequisites were explicit **fictional fixture stimuli**, with restoration and READ ONLY no-Event-write proof; the role/ownership changes themselves were not presented as tested business UI transitions.
- Owner two tabs/CAS and input retention, administrative two-tab CAS with original token preserved, actual saving state and duplicate Enter suppression, explicit restore/discard and successful save/reload after one own POST network abort.
- Primary upload/replacement/cancel selection, draft removal, published removal rejection/photo/status/version unchanged; gallery first upload2, keyboard order roundtrip, delete/readback and public image. Actual final public image URL equals saved admin photo across18 language/width cells.
- Cancel/reschedule reasons, equal interval rejection, overnight move, unchanged ID/old public link, cancellation controls, honest cancelled list/card state. Past owner submission rejected; current backend expiry contracts checked.
- Native select/format keyboard, Tab/Shift+Tab/Enter/Space/Escape, visible focus samples; open admin select geometry; new/draft/pending/published/rejected admin states, long data, owner/public/error/conflict/loading across RU/AZ/EN×360/390/768/1024/1280/1440. Original empty readiness0/0, label, mobile overflow and format-keyboard findings rechecked.

[Effective matrix](matrix-effective.json) / [CSV](matrix.csv) / [counts](counts.json) contain550 PASS evidence rows; counts.json is authoritative. These are observations/assertions, **not550 independent test paths**. Raw outputs live in the linked scoped run. Main geometry144 cells is completed by replacement evidence for12 admin language-route mistakes; affected public image cells use final public image evidence. Native saving is passively observed and captured through original Chromium screencast frames after native Ctrl+Home, not DOM styling or fake screenshots.

[PNG manifest](png-manifest.json) hashes native originals; [overview](visual-overview.jpg) is a derived navigation aid. Source/geometry/assertions do not replace actual rendering. Representative mobile owner, admin warning, conflict, saving, recovery and public originals reviewed; pixel-by-pixel review of every PNG not claimed.

Console: accepted scripts record no application pageerrors. Local403/404 negative permissions and intentionally forbidden manual add routes are retained. All requests outside the owned loopback were blocked; external font/CDN transport failures are expected environment limitations. Own delayed/aborted POSTs explicitly SIMULATED. No actual maps/mail/OAuth/analytics operation accepted.

## 4. Test results, discovery and debt

[Explicit discovery](backend-discovery-final.json): **143 unique method IDs accepted locally**:136 module methods (135 PASS in one batch plus the exact1 fixture-order case PASS on a fresh isolated DB),5 new photo regressions,2 historical Event geography/fallback checks. Full backend native exit remains **1**, not misreported as0: the one TransactionTestCase setup lacked seed category EDU after previous database flush. Original assertion/method ran alone with native exit0. This is test fixture/order debt, not an application regression. Existing test assertions/source were not changed.

[Full command](../module04-recheck-2026-10-13-r1/full-module-backend-ready.command.json), [log](../module04-recheck-2026-10-13-r1/full-module-backend-ready.txt); [exact1 supplement](../module04-recheck-2026-10-13-r1/autocommit-targeted-fresh-db.command.json); [new5 GREEN](../module04-recheck-2026-10-13-r1/photo-regressions-final-green.command.json); [old geography/fallback2](../module04-recheck-2026-10-13-r1/historical-event-geography-fallback.command.json).

The initial publication-False fallback-condition hypothesis was insufficient because False was excluded earlier by ==0; one targeted case remained RED. Final direct photo-False branch fixes that cause. First20-method targeted batch had19 PASS/1 same regression; final5 photo cases GREEN, unrelated passed methods retained by scoped source provenance. No repeated full suite after every patch. No-label wrapper/global corpus not invoked; CROSS-QA-02 global discovery still outside this scope.

Historical checks: EVENT-ADM01–03, EVENT-A11Y/SPEC01, ACE05/06/07/08/09/16/21 and Event portions of CE-GET/NULL/GALLERY-FIRST/GALLERY-KEYS have fresh corresponding UI/test evidence. GENERAL COMMON01 is not globally closed by this module.

## 5. Risks, baseline and harness failures

Raw failures are preserved, never silently presented as passing:
- Own PostgreSQL exited255 and browser/session/process receipts became invalid during an external runtime interruption; cause UNKNOWN. First backend attempt discovered136 but executed none (connection refused). Verified own container/loopback bindings and free ports, started only owned PG, waited for readiness and started own server; no foreign recovery action.
- Unnecessary GET logout405, strict media/public-link locator, outdated multi-day selector, hidden nested summary click, Chrome error-page navigation race, admin language URL assumption, expected publish button on already-published form, nonexistent error CSS class, organizer label incorrectly sought as visible text in locked edit instead of creator radiogroup, mobile-only Next expected on desktop. Corrected own probes/finished only affected gaps; raw outputs retained.
- Manual PlaceReview/ownership-request add endpoints legitimately403 by current admin permission policy. Replaced smoke targets with actual own fictional change views200, no permission-rule patch.
- Plain gettext proof originally missed Django default-language fallback; final proof uses actual Django and actual native UI. The insufficient RU locale repair was explicitly reported/approved/fixed.
- A diagnostic process-argv read accidentally exposed a fictional QA password in tool output; rotated only those six own users before continuing. No production credential used/copied; artifact credential gate reports a boolean, never values.

Some final-named PNG cells were refreshed during own targeted repeats; raw earlier JSON/text failures and independent RED evidence remain, and prior historical run directories were not overwritten. Raw test/debt/fixture/probe failures remain distinguishable from actual fixed application findings. Reviewable diff preserves the existing business publication policy, numeric-zero handling, version checks and candidate/live logic.

## 6. Legacy/dead candidates

None deleted or declared dead. Lower-level Event publication service/legacy compatibility was not changed to duplicate UI checklist policy. Bulk moderation/publication actions are **not certified equivalent to the repaired edit-form photo gate**; dedicated broader administrative workflows belong to module08/global follow-up. Do not infer a universal publication invariant from this scoped form repair.

## 7. Isolation and NOT RUN

Own profile `.tmp/module04-recheck-2026-10-13-r1`, container/volume `module04-recheck-2026-10-13-r1-pg`, DB `module04event_20261013_r1`, explicit loopback. HTTP127.0.0.1:49583; current PID/PG port/version/source in runtime receipt, not old Windows coordinates. Separate cache/media/private-media/LocMem email/cookies; clean environment, DJANGO_TESTING=1, no manage.py dotenv load/production credentials; sockets connect/connect_ex allowed only own PostgreSQL.

[Actual tool versions](tool-versions.json): Python3.12.3/Django6.0.2/Pillow11.3.0/psycopg3.2.10/pypdf6.20.1; Node20.20.2; Docker29.8.0; gettext0.21; Playwright CLI0.1.17; actual PostgreSQL17.10 from process. Existing installed packages reused; no dependency/source upgrade. Borrowed pypdf path belongs to prior own module03 virtualenv, not a production runtime.

Current RU/AZ/EN copied/compiled to own **locales-v6**: [manifest](locale-manifest-final.json), verify before django.setup, sole LOCALE_PATHS. Existing shared MO unchanged. Earlier owned locale outputs retained; v3 compiled before a stopped patch precondition and was never used for final acceptance. Old `.venv/.tmp/MO/browser/container` state is not a Git transfer bundle.

READ ONLY readbacks use statement_timeout10s/lock_timeout2s. Fictional fixtures and separate test DB only. NOT RUN: production/release/deploy/commit/push, global corpus/fullCI, next modules, real external maps/calendar CDN/font delivery/SMTP/OAuth/analytics, other OS/browser engines/physical devices, screen reader/fullWCAG, load/stress, all gallery operations in every matrix cell, all bulk admin actions, background expiry scheduler/real time elapse, genuine notification delivery/participants/refunds. Native date text entry/expiry-submit errors and existing backend expiry tests are accepted; blocked external picker UI is not.

## 8. Preservation and handoff

verification.json compares every pre-existing nonignored file against entry hashes, allowing only approved7 source paths plus the corresponding2 status docs. HEAD/branch/active_run unchanged. Earlier modules01–03, historical QA reports/index/transfer documents and shared MO retained. Own stand remains available; no foreign process/container stop/restart, stand takeover or production access. The external interruption is not falsely described as all old processes remaining alive.

See [commands](COMMANDS.md), [closed findings](FINDINGS.md), [next prompt](next-prompt.txt). Module05 is the next user-selected PLAN; it was not started automatically. Repeat ACCEPT-04 only on request and with own runtime/source/locale checks; keep prior passing checks by provenance and rerun affected gaps.

## 9. Priorities and decision

No OPEN finding remains in the executed module04 repair/acceptance scope. EVENT-QA-01–06 CLOSED LOCAL after actual targeted evidence. Global/shared locale and administrative bulk/production/test-order obligations remain bounded follow-ups; historical PASS does not certify production. This report is not a claim that every possible Event path or all13 modules are accepted.
