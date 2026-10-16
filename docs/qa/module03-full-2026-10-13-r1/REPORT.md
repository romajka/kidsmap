# Module03 — specialists and private documents — final LOCAL acceptance

2026-10-13, root sequential execution. **Verdict: LOCAL MODULE03 PASS within the documented acceptance scope. SPEC-QA-01–04 CLOSED LOCAL.** See verification.json and arrows-acceptance.json for authoritative final evidence. No independent specialist execution claimed.

## Snapshot and authorization

Checkout `/home/ramin/kidsmap`, `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` + preserved/approved dirty WORKTREE; active_run NONE throughout. Approved plans: [SPEC-QA-01–03](../../superpowers/plans/2026-10-13-module03-spec-qa01-03.md), [test portability](../../superpowers/plans/2026-10-13-module03-acceptance-test-portability.md), [SPEC-QA-04 glyphs](../../superpowers/plans/2026-10-13-spec-qa04-mobile-arrow-glyphs.md). Module01/module02 prior changes are retained; module04 not started.

Start hashes22268 nonignored files: [snapshot](../module03-plan-2026-10-13-r1/snapshot.json). Final arrow scope preserves enabled boundary buttons: existing JS clamps navigation at the first/last step. The initial new probe incorrectly assumed disabled attributes; final checks exercise native boundary no-op behavior. Relative SVG custom-property URLs resolved against the pages stylesheet, so the approved implementation uses correct explicit relative paths to the same existing local assets; first404/probe results retained.

Source/runtime/HEAD/branch/active_run/preservation: [verification](verification.json). This report certifies the documented LOCAL scope, never production or the global project corpus.

## Changes and causes

| ID | Cause / change | Evidence |
|---|---|---|
| SPEC-QA-01 | Upload accepted extension alone. New bounded worker structurally validates genuine PNG/JPEG/PDF before private storage/DB writes. Original document bytes preserved. Password-protected PDF rejected with explicit error; no password UI exists.5s wall/3s CPU/512MiB worker limits, existing10MiB upload bound. Safe RU/AZ/EN errors preserve metadata. | [RED browser](../module03-spec-fix-2026-10-13-r1/red-browser.result.json), [RED tests](../module03-spec-fix-2026-10-13-r1/red-tests.txt), [GREEN91](../module03-spec-fix-2026-10-13-r1/green-targeted.json), [native uploads/downloads](../module03-spec-fix-2026-10-13-r1/green-browser.result.json), [READ ONLY bytes match](readback.json) |
| SPEC-QA-02 | ModelForm normalized an already-saved FieldFile during conflict handling. Only this specialist form now normalizes new uploads, preserving canonical photo on409 and400; new upload/clear still work. CAS and newer data unchanged. | GREEN regression; six native RU/AZ/EN390/1440 two-tab/reload/photo checks in scoped browser evidence |
| SPEC-QA-03 | Old8px descendant CSS applied to header/nav. Rule now affects only the progress track; text/buttons keep content height. |180 role×language×width×5step cells; keyboard90; cropped mobile detail PNG |
| SPEC-QA-04 | Existing Font Awesome markup had no stylesheet/class wiring; glyphs remained blank after unclipping. Explicitly approved local-SVG masks restore visible arrows, scoped only to .km-step-arrow. | [Fresh finding](findings/SPEC-QA-04.md), [arrow acceptance180PASS](arrows-acceptance.json) |

Download ACL/headers, identity-always-private, independent person consent/reviewer approval, CAS, author/person/business separation and schema are unchanged. PDF parsing is structural validation, not antivirus, execution or full PDF rendering proof. Linux resource enforcement tested; other OS/platforms NOT RUN.

Only17 application/test/config/PO files are in implementation scope (12 pre-existing changes +5 new helpers/regressions), plus own evidence/status/plan documents. [APPLICATION_DIFF.patch](APPLICATION_DIFF.patch) includes this batch against entry source, including new files, without earlier module edits.

## Backend verification

- Fresh RED18 regression methods,14 failure entries including subtests, exit1. Expected fake-file admission and photo-copy/conflict failures retained.
- Targeted + affected consumers:91 methods PASS, runner21.029s, native exit0 /64.138s total. Labels captured in [command](../module03-spec-fix-2026-10-13-r1/green-targeted.json).
- Full module discovery: [16 explicit labels /154 unique IDs](discovery.json), including non-prefixed `catalog.testcases.specialists`; no no-label wrapper/full-project claim. One full batch:146 PASS/8 failures, exit1, runner67.050s /110.219s total. [Initial raw log](backend-full.txt), [exact command](backend-full.command.json).
- Six failures were environment guards hardcoded to another PC's Unix-socket launcher, before business scenarios executed. The approved additional guard supports the genuine current loopback profile and verifies actual DB/root/media/cache isolation; six test bodies/assertions remain.
- Legacy authorized-upload test supplied literal `pdf` bytes. Replaced both fixtures with genuine fictional PDFs, preserving proposer denial and all assertions. Two-method pre-patch overlay: upload test PASS; legacy owner GET test already FAIL302vs200. [Baseline source proof](baseline-source.json), [raw baseline](baseline-legacy-retry.txt). The feature test now follows and explicitly verifies the actual canonical redirect while retaining final200.
- Only these8 failed methods rerun:8 PASS, exit0, runner102.597s /158.974s total. [Labels](supplement-labels.json), [command](backend-supplement.command.json), [raw log](backend-supplement.txt). The unchanged146 are not rerun. All154 module methods are accepted by original passing results + approved targeted supplement; this is not a second154-test green run.
- [Original116 assertions unchanged](../module03-spec-fix-2026-10-13-r1/assertion-preservation.json); [supplement business assertions retained](supplement-assertion-preservation.json). No model/migration/business changes for test portability.

## Native browser acceptance

Own Chromium profile, credentials exclusively ignored scratch. RU/AZ/EN×360/390/768/1024/1280/1440. Actual browser actions: input/check/select/file chooser, native submit, navigation, reload, moderation, claim/reject/resubmit/review, publication, network invitation/consents/cancel/repeat, document opt-in/withdraw, keyboard and two-tab conflicts. Fictional setup used ORM; checked transitions did not.

- Scoped repair210 PASS:180 five-step author/person states +30 upload/conflict/readback rows. [Result](../module03-spec-fix-2026-10-13-r1/green-browser.result.json).
- Full rendered matrix180 PASS across author, person, independently verified claimant, network owner, admin, guest: [result](matrix.result.json). Original profile1 tests document privacy/CAS; native-created profile3 has distinct proposer/person, two real receiving rows and public profile. Another online proposal tests repeat submission without duplicate profile. [READ ONLY aggregate](readback.json).
- Keyboard90 PASS, Tab/Shift+Tab/Enter/Space/Escape; desktop/mobile direction selection/removal, format and native select focus. [Result](keyboard.result.json).
- Error/conflict/offline states90 PASS from108 initial rows;18 loading checks sampled after navigation and failed the timing heuristic. Raw failures remain [here](state-matrix-runtime.result.json), not silently reclassified as application defects. Fresh native-submit passive observation18 PASS and actual Chromium screencast18 PASS, all languages/widths, while only the own POST was SIMULATED paused. [Observer](loading-observer.result.json), [rendered6](loading-screencast.result.json), [remaining12](loading-screencast-gaps.result.json). Literal navigation-time screenshot API attempts failed/blocked and are retained; screencast originals show the real saving text, no DOM mutation.
- [Native lifecycle](lifecycle.result.json), [completed gaps](lifecycle-submit-gap.result.json), [claim/review lifecycle](claim-lifecycle.result.json), [gap readback](gaps.result.json), [private docs/7-role ACL](documents.result.json), [network cooperation](cooperation.result.json), [repeat send/double-click](duplicate.result.json), [native reviewer revoke](revocation.result.json), [genuine employee ACL control](employee-acl.result.json). The final employee fixture uses real canonical organization view/edit actions; browser positive workspace200 + person/doc404/identity404 proves business access does not grant personal rights. Revoke changes own moderator role through actual admin UI; old session private download200→403 and review404.
- Raw harness gaps preserved: incomplete fictional Place fixture omitted age/description, so canonical place select correctly omitted it; incomplete direction input after context restart correctly blocked submit400; a heading-text expectation incorrectly marked genuine author404 denial FAIL; public page has two matching main elements, causing a strict locator error; missing own invalid.txt stopped final document probes. Only affected gaps rerun with complete fictional fixtures/correct observations; native publish/public data and author denial confirmed. No application patch for these harness issues.
- [Effective matrix](matrix-effective.json) combines accepted rows with source references; counts are assertions/evidence rows, not independent full test paths. Final arrow acceptance180PASS and genuine-employee4PASS are appended; effective667 PASS rows +210 scoped repair rows, not independent test counts. [PNG manifest](png-manifest.json) contains629 originals/hashes/sizes; overviews are navigation aids. [Visual review](visual-review.md).

Console: no pageerrors in accepted scoped/main/state/keyboard/native role-revoke scripts. Expected local400/409/403/404 negative responses are listed in raw results; font transport outside the owned loopback was blocked and console network errors from that transport are explicitly environment limitations. The actual arrow glyph defect was source-backed, not attributed to blocked transport. No real maps/OAuth/mail/analytics interaction.

## Isolation and runtime

[Tools](tool-versions.json): Python3.12.3, Django6.0.2, Pillow11.3.0, pypdf6.20.1, psycopg3.2.10, Node20.20.2, Docker29.8.0, GNU msgfmt0.21, Playwright CLI0.1.17. Actual PostgreSQL version in readback/runtime receipt. Own virtualenv borrows existing installed packages read-only through a.pth; pypdf installed only into own virtualenv. Original .venv untouched.

Own PostgreSQL container `module03-spec-fix-2026-10-13-r1-pg`, unique volume/role/DB, explicit127.0.0.1 port from newly allocated config; own runtime URL127.0.0.1:50263. Current PID/source hash and actual loopback PostgreSQL port in [runtime receipt](runtime-version-final.json), not historical Windows parameters. Startup environment cleared; no checkout dotenv, production/remote DB or external network. Unique cache/media/private-media/email/cookies. READ ONLY readback with10s statement/2s lock timeouts.

RU/AZ/EN current PO compiled to own `.tmp/module03-spec-fix-2026-10-13-r1/locales-v2`, [final manifest](../module03-spec-fix-2026-10-13-r1/locale-manifest-v2.json) verify before django.setup, sole LOCALE_PATHS. The first post-PO attempt correctly stopped at stale catalogue gate before tests; rebuilt only this profile. Old shared MO and all previous PO entries preserved. Initial stand setup's historical example admin-password field failed after migration; corrected only own launcher/fixtures and retained sanitized log.

## Preservation, limits and handoff

Final hash verification preserves all pre-existing files outside explicitly approved source/status paths; HEAD/branch/active_run unchanged. Seven current Linux server receipts remain alive, older inactive/Windows receipts remain historical; no old process/container restart/stop or stand takeover. Own stand remains available. Historical QA findings/reports/index counts are unchanged.

NOT RUN: production, commit/push/deploy, global project corpus/fullCI, other modules, real SMTP/maps/OAuth/analytics/external fonts, real devices, other browsers/OS, screen reader, antivirus/PDF rendering, load/concurrent upload stress and deployment/recovery. Browser offline/delayed response explicitly SIMULATED. The pre-patch corrupt fictional document is retained in this own DB as RED evidence; no migration/remediation of existing files is claimed.

Next: module04 PLAN selected from guide only after user instruction. A repeat ACCEPT-03 can use [next-prompt.txt](next-prompt.txt); do not restart unrelated modules or rerun unchanged full suites automatically.
