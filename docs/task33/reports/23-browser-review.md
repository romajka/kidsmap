# Stage23 independent browser review

Role: `/root/stage23_browser`, canonical `browser-qa` (AUDIT); 2026-10-03. Assigned output is this report. Stage23 LOCAL ACCEPTANCE was authorized by the parent task. No application, production, commit, push or deployment changes were made. LOCAL branch `task33-progress`, HEAD `015d031d8eb17114bd860159dde805b38df3c13c`, with a dirty WORKTREE containing stage21–22 changes; HEAD by itself is not the tested implementation. Production was not contacted.

## Evidence and scope

The fresh Linux mirror was made from the current Windows worktree using `docs/task33/qa22/mirror.py`, not a Git checkout. `/root/task33-evidence/browser23-source-20261003-initial.json` hashes 2669 allowlisted source files; manifest SHA256 `1156ac5941976bf50039c7b2b9b13bedd77a6bda79f7da18846d47a11d25a1c4`. A post-run comparison found **0 Windows source mismatches** against that manifest. The AZ/RU/EN message catalogs compiled successfully. Codebase Memory `C-kidsmap` was ready but reported `coverage_unavailable`/`metadata_changed` for the stage22 browser bridge and current review source; actual bridge, test payloads, routes and templates were inspected directly. Static `motion.js`/`motion.css` are unchanged from LOCAL HEAD (`git diff --exit-code` passed).

Actual Chromium through Playwright CLI 0.1.22 rendered a synthetic local fixture on the unchanged QA04 launcher: disposable PostgreSQL17 in a `network=none`/tmpfs Docker container, Unix socket, `DJANGO_TESTING=1`, isolated cache/media/email, and no production credentials or external integrations. The bridge binds `127.0.0.1`; third-party scripts/widgets were stubbed and Material Symbols font served locally. All four launcher runs exited 0, reported `cleanup=PASS`, and removed their temp DB/socket roots. Raw evidence and screenshots are under `/root/task33-evidence/browser22-stage23-*` and `/root/task33-evidence/browser21-stage23-*`; four selected synthetic screenshots were visually reviewed from ignored `output/playwright/qa23/`.

| Fresh rendered check | Result |
| --- | --- |
| Review matrix: AZ/RU/EN × 320/360/390/768/1024/1280/1440, public/author/business/staff, Place/Activity/Specialist/Event, owner review dashboard and read-only admin | **462/462 PASS**; page/console errors 0, failed requests 0, HTTP4xx/5xx 0. 588 external requests explicitly stubbed. |
| Public URL matrix: AZ/RU/EN × same seven widths, fallback/translated/closed Place, Organization, Activity | **105/105 PASS**; canonical/hreflang, approved entity JSON-LD, translation fallback, AZN/geography, hostile text inert, synthetic image loaded, icons, no overflow; page/console errors 0, failed requests 0, HTTP4xx/5xx 0. |
| Legacy Place `/place/<pk>/` | **3/3** same-language redirects reached stable URL with HTTP200. |
| Final public keyboard smoke | **15/15 HTTP200**; desktop language dropdown Enter/Tab selected RU and navigated with `html[lang=ru]`; mobile drawer Enter and RU link did likewise. |
| Review lifecycle | **48/48 PASS**: candidate preserves approved projection, business moderation denied, reply visible/report private, staff approval/rejection, stale revision/reaction denial, new-revision reaction, keyboard/drawer focus. 22 expected 403/409/429 responses; failed requests and unexpected HTTP errors 0. |

The lifecycle run recorded **10** page errors, all the identical `InvalidStateError: Transition was aborted because of invalid state. ViewTransition opt-in disabled`. Stage22 independently reproduced this message with unchanged shared `static/js/motion.js` during native form navigation on a minimal loopback server. This stage did not repeat that attribution experiment, so exact causality of these 10 events is **UNKNOWN**; the signature is consistent with the prior finding and the shared file has no worktree diff. Functional lifecycle assertions passed, but this is not a claim of zero browser errors. Owner: frontend-reviewer for a separately scoped shared-motion investigation. The public matrix's immediate dropdown probe observed focus before its CSS transition; the separate final keyboard smoke waited for visibility and passed. These results are reported separately, without weakening assertions.

Visual inspection of public RU390 review, business EN1280 review, admin390 Place review, and Organization EN320 showed legible wrapped content, correct controls/fallback notice, and no apparent clipping or active hostile script. DOM checks supplied the full width matrix; four screenshots alone do not establish every visual state.

## Exact commands and limits

```text
python3 /mnt/c/kidsmap/docs/task33/qa22/mirror.py /root/task33-evidence/browser23-source-20261003-initial.json
cd /root/kidsmap-task33 && .venv/bin/python -m django compilemessages --locale az --locale ru --locale en --ignore .venv --ignore scratch
cd /root/task33-browser-tools && PATH=/root/task33-browser-tools/node_modules/.bin:$PATH npx playwright-cli -s=qa22 open about:blank --browser chromium
/bin/bash /mnt/c/kidsmap/docs/task33/qa22/run-browser.sh stage23-matrix-20261003 matrix
cd /root/task33-browser-tools && PATH=/root/task33-browser-tools/node_modules/.bin:$PATH npx playwright-cli -s=qa21 open about:blank --browser chromium
/bin/bash /mnt/c/kidsmap/docs/task33/qa21/run-browser.sh stage23-public-20261003 matrix
/bin/bash /mnt/c/kidsmap/docs/task33/qa21/run-browser.sh stage23-public-keyboard-20261003 final-smoke
/bin/bash /mnt/c/kidsmap/docs/task33/qa22/run-browser.sh stage23-flows-20261003 flows
/usr/bin/python3 /mnt/c/kidsmap/scratch/task33-stage23/browser-summary.py
git diff --exit-code -- static/js/motion.js static/css/motion.css
```

The QA04 browser bridge uses synthetic `force_login` actors and fixed allowlisted routes, not a production sign-in or deployed WSGI stack. The manager (`selected`/`all_network`), volunteer and full owner place workflows have **no separate rendered fixture in this audit**: NOT RUN here, for the lead's isolated Django integration evidence to assess. The current browser runs also do not test production data, real external providers, Safari/Firefox, exhaustive accessibility, real media storage or the release recovery/restore path. No browser evidence is offered for those. The parent must reconcile this bounded PASS with its full-suite failures before R1 acceptance; a passing browser slice cannot make the whole package ready.

Handoff: `/root` integration-reviewer lead should incorporate this bounded browser evidence, preserve the 10 shared-motion errors and manager/volunteer browser gaps, and decide stage23 status using migration, security and full-suite results.
