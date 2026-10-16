# Fresh integration commands (LOCAL AUDIT ONLY)

Working directory `/home/ramin/kidsmap`. No application edits/assertion edits. Runtime `run.py` strips environment before Django loads, imports canonical config.settings without manage.py/.env, requires DJANGO_TESTING=1, blocks sockets except dedicated START PostgreSQL loopback port, verifies own fresh manifest before django.setup. Test DB separate from browser/UI base DB; unique cache/media/private-media/LocMem email.

```bash
.venv/bin/python scripts/build_isolated_locales.py build --output .tmp/module01-full-2026-10-12-r1/integration/locales --locales ru az en --compiler native
.venv/bin/python scripts/build_isolated_locales.py verify --manifest .tmp/module01-full-2026-10-12-r1/integration/locales/manifest.json
.venv/bin/python .tmp/module01-full-2026-10-12-r1/integration/provenance.py
.venv/bin/python .tmp/module01-full-2026-10-12-r1/integration/run.py discovery
.venv/bin/python .tmp/module01-full-2026-10-12-r1/integration/run.py full
.venv/bin/python .tmp/module01-full-2026-10-12-r1/integration/run.py repair
.venv/bin/python -m unittest scripts.tests.test_build_isolated_locales
.venv/bin/python .tmp/module01-full-2026-10-12-r1/integration/native-probe.py
npm install --prefix .tmp/module01-full-2026-10-12-r1/integration/node jsdom@26.1.0 --no-audit --no-fund
.venv/bin/pip install --target .tmp/module01-full-2026-10-12-r1/integration/python-deps tblib==3.2.2 redis==5.2.1
KIDSMAP_JSDOM="$PWD/.tmp/module01-full-2026-10-12-r1/integration/node/node_modules/jsdom" NODE_PATH="$PWD/.tmp/module01-full-2026-10-12-r1/integration/node/node_modules" node --require ./.tmp/module01-full-2026-10-12-r1/integration/resolve-jsdom.cjs --test $(rg --files scripts | rg '^scripts/test_.*\.cjs$' | rg -v 'test_(localized_place_urls|review_cooldown|review_submission)') static/js/tests/*.test.js scripts/tests/*.test.cjs
```

Build/verify/provenance/discovery/native probe/dependency installs exited 0. Original helper exit1 (6 genuine missing-wsl.exe environment failures, 2 PASS, 1 skip). Node final unit corpus exit0 (116 PASS, 1 skip). All three excluded scripts invoke real Playwright/browser sessions with historical fixture config and are NOT part of unit corpus; not run by integration role.

Initial Node attempts include missing-jsdom/playwright environment failures in `node-full.txt` and `node-full-final.txt`, preserved. Final `node-corpus.txt` fixes only runtime dependency resolution, never test source/assertions. Transparent require hook resolves the literal missing `.tmp/phone-dom/node_modules/jsdom` to own pinned install; NODE_PATH serves normal jsdom imports including child Node processes. KIDSMAP_JSDOM supplies existing configurable location/map suites. No browser shim used.

Initial full Django serial run was intentionally interrupted with SIGINT to preserve normal Django TestCase reordering and use four workers. It ran 56 tests and misleadingly returned exit0 after interruption; retained ignored `full-interrupted.log` is NOT full PASS evidence. Final runner deduplicates IDs across explicit catalog modules plus no-label discovery, preserves Django reorder_tests order, wraps KidsMapParallelTestSuite with four real workers/databases, records actual testsRun/errors/failures/skips/stopped. Dependencies tblib/redis installed only in own scratch; reused venv untouched.

After root saved own authenticated actual owner HTML to ignored integration/photo-form.html, exact-path fs adapter added only for historical `.tmp/photo-form.html` fixture lookup. Actual HTML is never a repository artifact.

```bash
KIDSMAP_JSDOM="$PWD/.tmp/module01-full-2026-10-12-r1/integration/node/node_modules/jsdom" NODE_PATH="$PWD/.tmp/module01-full-2026-10-12-r1/integration/node/node_modules" node --require ./.tmp/module01-full-2026-10-12-r1/integration/resolve-jsdom.cjs --test scripts/test_photo_editor.cjs
```

Exit1, 8 tests:7PASS/1FAIL/0skip. Test line122 injects old wizard.js despite actual continuous template loading owner_place_continuous.js; preserved original assertion failure at old wizard.js:578. This is harness/source consumer mismatch, not native-browser application failure.

Final full Django command exit43; actual2092 testsRun (707.535s test execution), 18FAIL/25ERROR/0skip, stopped=False. Final failed-ID sequential reproduction:

```bash
.venv/bin/python .tmp/module01-full-2026-10-12-r1/integration/run.py repro
```

Exit43,43 testsRun (22.219s),18FAIL/25ERROR/0skip.42 genuine old QA04 setup/guard barriers;1 existing legacy specialist status200 assertion versus current redirect302. Full/repro raw verbose logs stay ignored (synthetic fixture diagnostics); repository full-result/repro-result JSON and summary contain IDs/isolation/source traces and exact counts. All own test databases/clones destroyed by test runner; START/browser DBs and processes preserved. The archived driver requires repository root CWD and existing verified own scratch config; it is not a transferable stand.
