# Stage 26 — independent rendered browser review

Execution identity `/root/stage26_browser`; canonical role `.agents/agents/browser-qa/agent.md`; 2026-10-03. Bounded AUDIT inside the parent stage26 APPROVED IMPLEMENT authorization. Application fixes belong to `/root`; this executor changes only assigned `qa26/application_*` helpers and this evidence. Stage27/calendar UI, production, commit/push/deploy remain NOT_RUN.

## Snapshot and evidence boundary

LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`, branch `task33-progress`, dirty WORKTREE, entry265 files preserved by parent. HEAD is not the version of executed dirty application. Each run freezes its own allowlisted mirror `/root/km26-browser-frozen`, records per-file SHA256 and copies the executed manifest to ignored raw evidence. Mirror contains source/static/locale/config/scripts/QA04/QA26 only; no production env, media, DB or Git data. Generated `.mo` files are identified separately from source comparison.

Codebase Memory `C-kidsmap` callable, root correct/ready. Index generation `2026-10-03T16:54:58Z`, current Event paths had `coverage_unavailable/metadata_changed` and owner Event template `parse_partial/metadata_changed`; graph hints were verified against actual `event_domain`, owner controller/forms, Event admin and templates. No graph completeness/dead-code assertions.

Real cached Chromium through Playwright CLI; actual Django Client bridge with `enforce_csrf_checks=True`, actual templates, model/services, multipart and HTTP responses. Dedicated loopback8786, CLI sessionapplication26; separate mirror from root and security execution. QA04 disposable PostgreSQL17 Unix socket, Docker networknone/tmpfs, LocMem cache/email/tempmedia, `DJANGO_TESTING=1`, clean allowlisted environment, external credential booleans false/network/libpq guards. All fixture accounts/venues/events/reviews are synthetic. Browser external requests are stubbed; cached Material Symbols font is served locally. This is not deployed-server, real CDN, integration or production evidence.

## Causal checks and findings

Command `wsl -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa26/application_sync.sh` PASS; `.../application_run-browser.sh causal3-20261003` exit1 due acceptance failures, with launcher PASS and cleanup PASS. Safe aggregate [26-browser-causal.json](26-browser-causal.json); raw `/root/task33-evidence/browser26-causal3-20261003` remains outside Git.

Initial actual matrix168 contexts AZ/RU/EN × 320/360/390/768/1024/1280/1440 × ownercreate/edit, physical/past/cancelled/rescheduled/online detail and Event landing.126 clean/42 failed owner contexts;347/348 checks PASS. All detail/state/date/organizer/snapshot/typed-review JSON-LD checks, real online draft save without geography, edit/stale/CSRF and venueowner denial PASS. Console2 native ViewTransition InvalidStateError at owner POST redirects;0 static/request failures and no overflow.

Findings handed to `/root`:

- B26-01, P2: online selected form still displayed required address* and mandatory physical-map instructions. Actual selected-state assertion failed. Root owns truthful online UI.
- B26-02, P2: visible map-search input lacked accessible label; owner42 contexts. Root owns shared input label.
- B26-03, P2: new organizer labels/help retained Russian in AZ/EN (28 owner contexts). Root owns translations. Personal screenshot review also found RU date placeholders saying choose-metro, time placeholders choose-gender, price/phone saying60minutes, AZ description/district copy. Prior-source attribution UNKNOWN; recorded as current affected-form copy rather than claimed stage26 regression.
- B26-04, P2: native ViewTransition aborted on actual online-create/edit POST→dashboard. Same browser error family previously observed in25; source attribution initially UNKNOWN; root owns scoped form navigation correction.

Initial causal1/2 failed before browser due fixture movement setup, not application acceptance: unresolved point and string-vs-float mismatch in authorized location override. Corrected fixture uses actual numeric coordinate `set_location_override` + `Place.save`; strict Event snapshot assertions retained. No browser PASS counts from those attempts. Launcher cleanup recorded for each.

Personally inspected causal create390/online390 screenshots copied to ignored `scratch/stage26-browser-inspect`: readable mobile hierarchy, public online has Person organizer, Baku23:30–01:30 and no physical geography; owner issues above reproduced visually. UI source/skills are not substitutes for these rendered checks.

## Further causal checks

Actual original-JS UTC clock case [26-browser-clock-causal.json](26-browser-clock-causal.json): UTC2035-02-03T20:30Z = BakuFeb04 00:30; selectedBakuFeb04 00:00–01:00 gave empty validationMessage/valid date despite start30min past. No POST under mocked clock. Dedicated collector exit0; generic matrix exporter initially raised missing-total KeyError, which was a harness shape mismatch, not a browser/domain result. Corrected separate collector routing for later runs.

First final pass [26-browser-first-final.json](26-browser-first-final.json), command `wsl -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa26/application_run-browser.sh final-20261003`, exit1:210 contexts/168 clean;439/442 checks. Owner/public168 contexts now all clean, true UTC future-save persists Baku instants, mocked UTC Baku past rejected/future valid, actual Event admin save/publication and resulting public detail PASS. Three native owner POST redirect errors persisted, requiring source owner form late navigation override as well as destination dashboard. Archive assertion failed and admin42 contexts exposed additional boundaries.

Dedicated actual diagnostics [26-browser-diagnostics.json](26-browser-diagnostics.json) established:

- B26-05, P2, bounded admin320/360: scrollWidth389, mobile action grid width356.89/right388.89 and sidebar width312/right344 at320. Other widths no overflow. Actual age_from/age_to inputs have neither labels nor ARIA. Root owns widget accessible names; public executor owns `body.model-event` scoped CSS, leaving other model layouts unchanged.
- B26-06, P2: full HTTP archive query lost date in301 from `CleanPublicQueryMiddleware` because `services/public_urls.py:PUBLIC_QUERY_PARAMS['events_landing']` omitted new period/query keys. Reader/controller unit behavior alone did not reveal this. Root owns Event-only allowlist and full Client negative/positive checks. Final browser uses Baku-derived date, `maxRedirects:0` and preserved full query URL, with strict captured district/past membership assertions.
- Initial admin Rounded-font failure was a harness false positive: registered Rounded faces were unused; actual icons used loaded FontAwesome5Free/Brands/FontAwesome. Final icon assertion checks the computed first font family/weight of actually rendered font icons. Font or application files were not changed to hide this result.

Diagnostics raw `/root/task33-evidence/browser26-diagnostics-20261003` and clock raw `/root/task33-evidence/browser26-utc-causal-20261003`, launcher/cleanup PASS. Their first generic matrix export missing-total errors are separately reported harness mismatches. Actual observations preserved; original failures were not relabelled PASS.

## Final acceptance

Full `final2-20261003` run [safe result](26-browser-full-final2.json), exit1:210 contexts/198 clean,440/443 checks. Owner/public168 contexts, actual UTC draft save/Baku near-midnight validation, archive200 with unchanged query, typed review/JSON-LD/snapshot/publication boundaries PASS; zero console/request/static errors. Remaining12 failures were Event admin320/360 overflow and three focus-following Tab cases. Accessible age labels and source owner-form navigation correction were verified.

Bounded `admin-final-20261003` [safe result](26-browser-admin-causal.json), exit1:42 contexts/30 clean,85/88 checks;84 focus/Tab PASS. Overflow remained389px. This run's three publication checks failed and its format-only save assertion was insufficient to establish an actual save. It is preserved as failed evidence. The new save assertion additionally requires updated version, exact entered generic name, persisted photo and no form errors; no prior owner-edit name assumption.

Actual runtime CSS diagnostics disproved stale-cache/shared-source hypotheses: finder, BASE_DIR, Event model and event_domain paths all resolve inside the independent mirror; actual received CSS SHA matched the frozen file, and CSSOM applied the late minmax tracks. Shell/main corrected to256px at320, while child `.km-place-form-sections` retained an implicit356.891px track. DOM-only forced parent widths did not remove scroll; no application edits by this executor.

Bounded `admin-final2-20261003` [safe result](26-browser-admin-second-causal.json), exit1:42 contexts/30 clean,87/88 checks. Received CSS `aceb1f613721fa842fbe72c440b4dd73be11569f8315aaf5217c1e9e09756af7`, runtime paths independently verified. Strengthened actual save, actual publication and public detail PASS. Document overflow improved389→372 but still failed all12 narrow admin contexts. Actual rightmost `English` language-tab button right371.89 exceeded parent222px; hero progress min250/right327 remained beside hero grid0px250. Those runtime facts, rather than source guesses, justified the next scoped fix. The initial publish-enabled check was false while subsequent same-button click and resulting publication succeeded; the final harness consistently waits for networkidle before observing readiness and records count/disabled state without weakening the condition.

[Runtime causal summary](26-browser-runtime-causal.json) preserves actual CSS/path/track observations and cleanup. Specialized diagnostic commands `runtime-css2/3/4-20261003` used `application_runtime_css.js`; first unsupported dynamic node:crypto import stopped `runtime-css-20261003` before observations. SHA now computed offline from actual response bytes. Early custom exporter missing-total/missing-collector errors were harness-only; raw results/cleanup remain valid. Specialized collector routing subsequently corrected. Diagnostic4 exit0, launcher/cleanup PASS.

PASS latest [administrative result](26-browser-admin-final.json), command `wsl -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa26/application_run-browser.sh admin-final3-20261003 /root/km26-browser-frozen/docs/task33/qa26/application_admin_followup.js`, exit0:42/42 contexts and88/88 checks, including84 focus/Tab and four strengthened actual save/publication checks. Zero overflow, console errors, request failures and static failures. Publish button count1/disabledfalse observed after networkidle. Actual received CSS SHA equals frozen/source `2f4ca4d28f7a2f57b398d5d51b45874a5966dd1510f200bd638a4f091f135c5d`; runtime finder/model/domain/base paths remain inside the independent mirror. Launcher/cleanup PASS.

[Final composite result](26-browser-results.json):210 distinct current contexts/210 PASS,443/443 checks. This combines unaffected168 public/owner contexts from full final2 with latest42 administrative contexts; it is not a single latest210 run. Four latest strengthened admin business checks replace the older four, alongside84 corrected admin focus checks. Comparing2741 application source files across runs found exactly one delta: shared admin CSS. Strict removal of the known `body.model-event` track/minimum/hero/tab additions reconstructs the prior CSS SHA exactly, establishing no non-Event application delta. Backend/owner/public source is byte-identical across these runs; other models do not match the new selectors.

Verification commands, both exit0:

- `wsl -u root --exec python3 /mnt/c/kidsmap/docs/task33/qa26/application_source_check.py /root/task33-evidence/browser26-admin-final3-20261003`:2774 source files checked, zero mismatches, zero new application files; generatedAZ/EN/RU `.mo` listed separately.
- `wsl -u root --exec python3 /mnt/c/kidsmap/docs/task33/qa26/application_results.py /mnt/c/kidsmap/docs/task33/reports/26-browser-results.json`:strict context/check/source/delta/runtime CSS/isolation cleanup assertions PASS.

Final executed manifest SHA `54c4c3c6fed1f0fa7471a76db630e2945dce512863436ac376a20161eb0be9c2`. Own harness AST/msgfmt/bash preflight and `git diff --check -- docs/task33/qa26 docs/task33/reports/26-browser*` PASS. No application files changed by browser executor. Original failed runs remain failed; final PASS refers only to the explicitly bounded composite above.

Personal rendered review includes final RU owner390/admin390/rescheduled390 and UTC EN form. New organizer/format labels, online geometry behavior and visible Baku occurrence periods are correct. Existing EN title illustrative placeholder remains Russian; attribution before26 UNKNOWN, reported as inherited-copy limitation rather than expansion into other stages.

Personally viewed latest actual admin320 fullPNG (320×7355) and its clearly-labelled derived top900px crop in ignored `scratch/stage26-browser-inspect`. Hero/progress are one column with readable copy, tabs wrap and organizer/format controls remain usable. Raw screenshots are outside Git; the derived crop is a read-only inspection aid, not a separate viewport test. Parent independently reviewed administrative snapshots.

## Not run and handoff

Full application suite, real OAuth/maps/CDN/fonts integrations, deployed nginx/TLS, production records/media/transfer, physical devices, native OS localization/full screen-reader audit, stage27 calendar UI, production mutations/deployment: NOT_RUN. Backend tests/migration/concurrency evidence remains the parent and dedicated security executor's attribution, not this browser execution.

Named handoff: `/root` (django-reviewer lead), browser acceptance PASS for bounded stage26 composite. Use final source/result evidence above to update stage26 report/journal; retain inherited-copy and NOT_RUN limitations. Stage27 and production remain outside authorization.
