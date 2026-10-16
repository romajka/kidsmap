# PLACE-QA-12 — FIXED LOCAL, 2026-10-12 r1

Lead: Codex primary, sequential execution; approved concrete plan `docs/superpowers/plans/2026-10-12-place-qa12-admin-cas-retention.md`. User explicitly approved QA12+QA13 together. No new application scope was inferred.

## Snapshot / isolation

Checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`; dirty prior QA09/10/11 edits preserved; active_run NONE unchanged. Fresh own fictional PostgreSQL DB `qa12_20261012_r1`, loopback HTTP46873, existing owned PostgreSQL loopback52523, unique cache/media/private-media/session/CSRF and LocMem email. Own prior fictional QA DB/media only cloned; no production data/credentials or checkout .env loaded. Secrets remain ignored mode600 scratch. [Final process/source](runtime-final.json), [HTTP static match](runtime-static-match.json), [versions](versions.json), [native RU/AZ/EN manifest](locale-manifest.json), [preservation](preservation.json).

Helper verifies fresh compiled locales before django.setup; sole LOCALE_PATHS. Shared MO unchanged. External Python socket connects restricted to own PG; browser external origins aborted. Explicit libpq settings, not a claim of an OS network sandbox. External fonts blocked; real maps/SDK/geocoder/OAuth/SMTP/production NOT RUN.

## Cause and exact changes

Actual stale admin candidate save raised typed `candidate_version_conflict` after validation. Transaction rolled back, then old changeform_view redirected to GET and discarded posted input. Protection of newer A/live worked already.

Only `PlaceAdmin.get_form/changeform_view/render_change_form` changed in domain_admin/place.py: after actual typed CAS rollback, normal admin renderer rebuilds the submitted bound POST with a request-local non-field error. It is invalid, so no save_model/save_related replay occurs. Other ValidationErrors keep existing handling; normal permission checks execute again. No singleton monkeypatch, token refresh, forced merge or POST→GET substitution.

Place change_form template adds translated conflict banner and same-object authorized GET link in a separate noopener tab. Controller keeps error/dirty state, disables stale save/publish and blocks native submit/save-and-exit retries; AJAX conflict keeps original document/input and imports only the escaped same-origin banner. Scalar/nested input remains editable. Files cannot survive server document replacement: existing reselect note is shown, no staging/storage subsystem added. Existing ACL/CAS/candidate/live/readiness/pricing contracts unchanged.

## Evidence / exact checks

[Test command index](test-command-index.json), [browser commands](commands.jsonl), [CAS18 cells /54 observations](cas-qualified.json), [PNG SHA manifest](screenshots-manifest.json).

- New initial6 meaningful regression tests: RED3PASS/3FAIL exit1 (`tests-red.txt`), GREEN6PASS exit0 (`tests-green.txt`). Real A/B GET tokens and POSTs protect newer candidate/live, retain scalar/description/JSON/stale token, no second write, ordinary validation/other save error/foreign+inactive ACL/fresh correction.
- Supplemental actual second-connection commit after valid form.clean:1PASS exit0 (`race-green-final.txt`). Exactly one attempted stale save; committed A retained; bound B returned. Supplemental nonempty nested input + selected-file warning:1PASS exit0 (`nested-file-green.txt`). Final exact new regression module discovery/run:8/8PASS,0failures/errors/skips, exit0 (`tests-final-module.txt`); helper imported by module alias to avoid imported TestCase rediscovery. Earlier targeted logs retained.
- Affected existing suites:65PASS,0FAIL; run66 had1ERROR in our new race fixture calling setUp twice. Only own fixture corrected and repeated separately; existing65 not rerun merely for a green total. Another own race snapshot attempt used pre-DB integers versus reloaded Decimal serialization; fixture reloaded before unchanged equality assertions, retained failure log. No application regression or assertion weakening attributed to these harness errors.
- Native all18 RU/AZ/EN×360/390/768/1024/1280/1440: rejected B retains name/description/exact token, save disabled/error status, A comparison GET/noopener, deliberate current-view correction/save/reload with original B unchanged:54PASS. Initial combined run completed RU then interrupted by our own process restart; those RU records retained, missing AZ/EN executed separately. No unfinished cells counted.
- Additional native three languages390: simulated aborted save-and-leave, genuine AJAX CAS, selected-file server redisplay/reselect warning:9PASS in `errors-files.result.attempt1791800746.json`. Raw initial own syntax-error attempt retained. No unexpected page errors or local HTTP failures; intentionally aborted transport clearly SIMULATED.
- Related JS12 executed:11PASS/0FAIL/1SKIP exit0; absent legacy actual-HTML fixture explicitly skipped, not fabricated. [Commands/results](node-targeted.json), [TAP](node-targeted.txt). JS syntax and scoped diff whitespace checks exit0.
- Readback is READ ONLY with10s statement/2s lock timeout; fictional fields only. [Readback](readback.json). Runtime loaded retention + new EN copy, entry=startup=disk, four served assets SHA=disk.

## Limits / handoff

Shared unsaved-modal keyboard issue independently confirmed as PLACE-QA-14; not part of QA12 repair. QA12 input-retention acceptance passes. Full module01 remains OPEN; all application-wide2097 tests were not repeated per user's newer testing cadence. Prior full-suite baseline remains dated evidence, not current green. Full module acceptance after all module findings; global corpus after all13 modules.

HEAD/branch/active_run/prior report bytes/shared MO/old five stands/foreign containers preserved. Only4 existing source files +1 new test changed since preflight, all approved. Actual own credential literal scan0matches in new reports; not a universal secret audit. No commit/push/deploy/production. Next: separately approved QA14 plan, then ACCEPT-01; do not automatically start module02.
