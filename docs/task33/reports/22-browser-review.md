# Stage22 independent browser review

**PASS for the scoped stage22 browser acceptance.** Final responsive matrix462/462, lifecycle/keyboard48/48 and translated admin smoke36/36 passed. Six ViewTransition errors during mutation navigation reproduce with unchanged LOCAL HEAD shared motion code on standalone pages; they are a pre-existing enhancement issue, explicitly excluded from any claim of zero overall flow page errors.

## Task, authorization and snapshot

Independent executor `/root/stage21_browser`, canonical `browser-qa`, AUDIT. Parent `/root` authorized stage22 only under the existing user instruction. Owned changes are `docs/task33/qa22/*`, this report and ignored synthetic screenshot copies. This reviewer did not edit application code, commit, push, deploy, use production or start later stages.

LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`; branch `task33-progress`; dirty WORKTREE. HEAD alone does not identify the implementation. Canonical role/registry, relevant READ FIRST knowledge, engineering/audit contracts and Playwright skill were read. Codebase Memory was available/ready, but new affected paths had coverage gaps; controller/template/service/admin conclusions were verified in actual source.

Final source manifest: `/root/task33-evidence/browser22-source-20261003-accepted.json`, SHA256 `25d47950a97710a5a999422b55dda8c03495b75ddbc376e4a8c0b02324fc8a22`. It records2669 allowlisted files as actual Linux bytes; final verification found0 mismatches. `/root/task33-evidence/browser22-final-metadata.json` retains individual source/helper hashes and compiled AZ/RU/EN catalog hashes, without hashing this report. Focused hashes:

| Artifact | SHA256 |
| --- | --- |
| typed_reviews.py | 3a369d3c05b2c907e6fe556f3b5fd35298776451f7aceb3e21f619395e31a1f6 |
| services/review_versions.py | df377059cc2c4fe008149d48aa9911c0f56eb7fab405a6663aa5f4db2d1dfe99 |
| domain_admin/review_versions.py | cd5f043cf42b0d11e2569a97970a14932acb87fdf90fdc77aab0761c70471aa6 |
| typed_reviews.html | 0eb8bd0f85d3bf292ba4ee4335db0cba0561d5202a0d4abdca660f1e93dc68c7 |
| PlaceReview change_form.html | cc2e1a9e1b8b40a460b8c8008ba7787fdb3135b23d112e639ceaaa0a244e33fc |
| kidsmap_admin_form_shell.css | 487fee0548c6c95997d236eebee46e9b7ef73bb87780681430a47271765f5a11 |

The462 matrix predates final new admin-label catalog edits. Its runtime application code matches the accepted source; subsequent source deltas are AZ/EN/RU catalogs and an independent test file. The48 lifecycle replay uses translated AZ/EN catalogs, and36 admin cells verify the final explicit RU fallback correction. This distinction is preserved in separate manifests/evidence.

## Executed checks and isolation

Actual Chromium155 through Playwright CLI0.1.22, Linux Node22.23.3, Python3.12/Django6.0.2. Unchanged QA04 launcher: disposable PostgreSQL17, isolated cache/media/email, `DJANGO_TESTING=1`, no production credentials or integrations. Bridge binds loopback, actor-specific Django clients enforce CSRF, and only synthetic target/action routes plus real static/admin JS catalog are allowed. External scripts/widgets are stubbed; Material Symbols fonts are cached locally. SiteSettings synthetic Specialist/Event features are enabled; Event dates are future. ThreadingHTTPServer avoids speculative-connection deadlock.

Commands are run through WSL Ubuntu-24.04 as root from `/root/task33-browser-tools`; source root adapted from historical `/home/ramin/kidsmap` to Windows `C:/kidsmap` and isolated Linux `/root/kidsmap-task33`:

```text
python3 /mnt/c/kidsmap/docs/task33/qa22/mirror.py /root/task33-evidence/browser22-source-20261003-accepted.json
.venv/bin/python -m django compilemessages --locale az --locale ru --locale en --ignore .venv --ignore scratch
npx playwright-cli -s=qa22 open about:blank --browser chromium
/bin/bash /root/task33-browser-tools/run-browser22-frozen-next.sh matrix-20261003-final matrix
/bin/bash /root/task33-browser-tools/run-browser22-frozen-next.sh flows-20261003-corrected flows
/bin/bash /root/task33-browser-tools/run-browser22-admin-frozen.sh admin-20261003-accepted admin
```

Fresh CLI sessions isolate final phase logs; immutable shell copies prevent editing active launchers. Python AST/bash/JavaScript syntax checks passed.

| Actual run | Acceptance result | Browser/network result | QA04 exit/cleanup |
| --- | --- | --- | --- |
| matrix-20261003-final |462/462 | page/console errors0, failed requests0,4xx/5xx0;588 explicitly tracked external stubs | child0, PASS |
| flows-20261003-corrected |48/48 | failed requests0, unexpected HTTP0;22 deliberate403/409/429;6 classified shared-motion page errors | child0, PASS |
| admin-20261003-accepted |36/36 | page/console errors0, failed requests0,4xx/5xx0 | child0, PASS |

All final run/socket roots were removed by normal nonce-guarded QA04 cleanup. Evidence remains outside Git under `/root/task33-evidence/browser22-*`.

Matrix: AZ/RU/EN ×320/360/390/768/1024/1280/1440.336 public/author/business/staff review cells on Place/Activity/Specialist/Event,42 author/business dashboard cells,84 read-only admin cells. Checked actual HTML language, localized review headings, approved projection, private candidate/report exclusion, public business replies, actor-specific edit/reply/report/moderation controls, CSRF, escaped script-termination text, icons/font readiness and horizontal overflow. Admin uses an explicit locale cookie honored by actual AdminLocaleMiddleware; new language-specific labels receive exact DOM assertions in the final36-cell smoke at320/390/1280.

Lifecycle: English390, all four target kinds. Native form submission preserves old approved text/rating/reaction contribution; business approval and legacy Place approve/reject endpoints return403; stale reviewer/reaction decisions return409; public replies remain visible and private reports remain private; approval promotes the new revision, resets current reaction totals and preserves old reaction rows; a voter can react independently to the new revision. Separate rejection fixture retains approved text and both historical revisions. Keyboard covers review-form Tab, mobile drawer Enter and Escape/focus restoration.

Preserved cooldown policy is explicit: Place immediate stale submission returns429 while its durable gate is active, with no revision write; a nonce-scoped synthetic-only POST control expires only this fixture author's gate, and the same stale numeric ID then returns409/no write. Activity/Event cooldown remains429 with Retry-After. Specialist keeps its legacy no-cooldown policy: a second valid submission succeeds and its latest candidate is reviewed. Production settings were not changed.

60 matrix screenshots and6 final translated-admin screenshots were retained. This reviewer visually inspected publicAZ390/EN1280, authorRU390/AZ1280, businessEN390/RU1280, staffAZ390/EN1280; Place admin390/1280, final translated adminAZ/RU390/EN1280 and business dashboardEN1280. Text, controls, escaping and wrapping are legible; representative views now fit their viewport. Selected synthetic screenshots were copied only to ignored `output/playwright/qa22/final` for view_image inspection.

## Findings, corrections and baseline

B22-01, P1, resolved: first PlaceReview admin page raised `TypeError: 'tuple' object is not callable` because review_workflow_link shadowed gettext `_`. Actual Chromium navigation failed. Parent corrected the application and independent admin render regression; final matrix/admin smoke pass. Initial evidence: `browser22-matrix-20261003-b/launcher/django.log`.

B22-02, P1, resolved: RU/EN review labels remained AZ although the surrounding shell was translated.224 cells and screenshots confirmed an ineffective top-level get_current_language assignment in an extending template. Parent supplied controller language context; final localized matrix passes.

B22-03, P2, resolved: customized PlaceReview read-only history expanded document width to470 at320/360/390. Actual DOM showed a326px grid parent expanding its track to437.641px. Reversible DOM-only readonly wrapping reduced470→390; removing the test style restored470. Parent applied scoped wrapping and replaced obsolete edit/approve/hide/reject guidance/controls with read-only workflow guidance. Final matrix passes all widths. Evidence: `browser22-diagnose-20261003-d/css-diagnosis-cli.txt`.

B22-04, P3, resolved: new admin workflow/history/metrics labels lacked AZ/EN translations; later RU workflow inherited AZ from the default catalog. Parent added catalog entries including explicit RU identities. Final36 exact workflow-anchor/history-label assertions pass in all three languages.

B22-05, P2 PRE-EXISTING, retained: shared motion enhancement can emit empty-stack `InvalidStateError: Transition was aborted because of invalid state. ViewTransition opt-in disabled` during native form navigation. Corrected48 flows record6 errors on Place/Activity/Event pages; all functional assertions pass. `git diff/status` for static/js/motion.js and static/css/motion.css are empty. Controlled real-loopback baseline removes Django, DB and new review code:8 cycles with unchanged motion.css and native POST→302 produce0errors; adding only unchanged LOCAL HEAD motion.js reproduces6 identical errors. These are not a stage22 regression. No application fix was made for this existing enhancement in stage22. Evidence: `/root/task33-evidence/browser22-transition-real-cli.txt` versus `browser22-transition-shared-cli.txt`; both tiny owned servers stopped through `/finish`, exit0. Owner/handoff: frontend-reviewer, separately scoped follow-up for shared view-transition lifecycle/rejection handling.

Harness failures remain distinct: missing admin/jsi18n allowlist produced84 initial resource failures; absence of forwarded Retry-After caused3 false cooldown failures; unread deliberate fetch bodies caused14 aborted requests. Corrected helpers forward the real header, consume bodies and allow the real JS catalog. Assertions were not weakened. The initial failed462 run (229 passing) and initial45/48 flow replay remain preserved; they are not final PASS evidence. A failed mocked-redirect transition probe was also retained; successful attribution uses real HTTP302 baselines instead.

## Limits and named handoff

NOT RUN: production, external widgets/CDNs/integration availability, Safari/Firefox or other Chromium versions, full accessibility audit, exhaustive translation of legacy admin labels, production data normalization/concurrency/deletion or later stages. Database/backend concurrency/migration acceptance belongs to the other actual reviewers and lead report; this browser report does not replace it. The per-actor bridge exercises rendered controls and actual Django requests/state/CSRF; it uses synthetic forced-login clients, not a production login or live WSGI deployment.

Next: `/root` (django-reviewer lead) can accept the stage22 browser portion, refresh final helper/source hashes and combine it with independent backend/database evidence. B22-05 remains a separately scoped frontend follow-up; no claim of all-flow zero page errors or whole-site/production readiness is made.
