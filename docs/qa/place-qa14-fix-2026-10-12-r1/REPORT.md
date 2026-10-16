# PLACE-QA-14 — PARTIAL IMPLEMENT / OPEN, 2026-10-12 r1

Lead Codex primary, sequential; user approved exact `docs/superpowers/plans/2026-10-12-place-qa14-modal-keyboard.md`. No delegated or production execution.

## Snapshot / isolation

Checkout `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, prior dirty QA09–13 work preserved, active_run NONE. New owned fictional profile http://127.0.0.1:49735, DBqa14_20261012_r1, verified owned PostgreSQL loopback52523, unique cache/media/private-media/LocMem email/cookies. Fresh native RU/AZ/EN compiled manifest verified before setup; one LOCALE_PATHS, shared MO untouched. No checkout .env or production credentials. Browser external origins and Python non-PG socket egress blocked; libpq explicit, not an OS sandbox.

## Exact permitted changes

Only existing `static/admin/js/kidsmap_notifications.js` getFocusableElements/unsavedChanges changed. Link selector now matches real anchors instead of SVG use[href]; disabled, hidden and negative-tabindex elements excluded. Initial focus scheduling checks the current modal identity and visible primary control after its visibility class changes. New `scripts/test_admin_modal_keyboard.cjs` tests real component behavior in jsdom; native evidence remains distinct. No CSS/copy/save callback/backend/schema/ACL/CAS changes. Prior application diffs preserved.

## Tests and native outcome

- Qualified pre-patch unit RED1PASS/3FAIL exit1; GREEN4/4 exit0, final4/4 exit0 [command](tests-final-command.json), [TAP](tests-final.txt). Initial own callback assertion expected one Stay callback, but unchanged baseline invokes onClose+onStay; corrected the new oracle before patch and preserved that baseline. Existing assertions unchanged. Timer/frame fixture settles deferred render jobs; jsdom does not establish native focus.
- Final module01 backend corpus425/425PASS,0failures/errors/skips, exit0: [exact labels/results](module-tests-result.json), [log](module-tests-final.txt). Additional45/45PASS exit0: real candidate/ServerDraft races, ACL/media/geography/taxonomy/branch and existing scoped repair regressions [results](extra-tests-result.json), [log](extra-tests.txt). Exactly470 accepted module-domain tests across two invocations, not the global2097 corpus. Python source unchanged throughout.
- Own initial corpus used stock DiscoverRunner; language leaked between tests, and missing traceback-pickle support aborted parallel transport. Fixed only QA launcher to use canonical KidsMapTestRunner and existing owned dependency path; retained `module-tests.txt`. No app/assertion patch for that harness failure. Four inactive owned failed-attempt TEST clones removed with exact allowlist and zero-active-connection check; runtime DBs untouched [cleanup](testdb-cleanup.json).
- Related module JS50 executed:49PASS/0FAIL/1SKIP exit0 [command](node-module.json), [TAP](node-module.txt); absent legacy actual-HTML fixture is explicit SKIP. Later change limited to initial focus scheduling; final affected4 tests repeated and pass. No global JS/project corpus repeated.
- Native first opening/Tab-wrap/Escape/Stay/Discard/actual Save+leave produced partial PASS cells, but complete18-cell acceptance **did not pass**. Raw keyboard-final/fresh/remaining/diagnostic attempts retained. Early own attempts pressed keys before asynchronous autofocus, reused an unchanged name, or navigated before the newly owned server was ready; corrected only QA waits/unique fictional text/ready gate. Even then genuine focus failures remained. No injected focus accepted as proof.
- Native network-abort/genuine AJAX CAS/file-reselection checks:9/9PASS,0page errors and0unexpected local HTTP failures (`errors-files.result.json`); aborted connection is explicitly SIMULATED.
- Shared native price confirm: forward/reverse Tab pass, initial focus fails; publication Show probe chose a missing published-card trigger, so its continuation NOT RUN (own fixture/selector, not app failure). `shared-consumers.result.json` retained.

## Confirmed remaining cause / extension needed

Native EN390 rapid Escape→reopen: new visible modal loses focus to underlying anchor. Delegating call trace shows primary button focus then anchor focus from unchanged close() line161, its220ms callback [native](rapid-reopen-diagnostic.result.json), PNG linked there. Actual remaining regression RED1FAIL exit1 [test](close-race-red.cjs), [TAP](close-race-red.txt), [command](close-race-command.json). This confirms an independent close lifecycle cause, not an SVG-only timing assumption. Ordinary initial focus in shared Show/Confirm also requires a consistent visible-render lifecycle; not all failures are assigned to the timer.

Original exact plan excludes close()/show() changes. They remain untouched. Concrete extension: `docs/superpowers/plans/2026-10-12-place-qa14-close-race.md` — pending approval. QA14 and module01 remain OPEN; no new ID/duplicate alias or blanket PASS. Backend470 tests need not repeat for the next JS-only scope if hashes remain equal.

## Preservation / NOT RUN

Own native PNG manifest/runtime/static/source/preservation files accompany this report. Existing stands, foreign containers, active_run, prior report hashes and shared MO preserved. Own browser closed; new QA14 stand left running. Global corpus, full remaining module browser matrix, physical devices/other engines/screenreader/real fonts/maps/GPS/providers/production/CI NOT RUN. Known failed focus gate prevents full acceptance; do not claim module01 complete or begin module02. No commit/push/deploy/production. Next approve the concrete bounded close/show extension, then finish actual ACCEPT-01 once.
