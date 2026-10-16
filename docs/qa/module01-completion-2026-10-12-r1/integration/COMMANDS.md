# Exact integration commands

CWD /home/ramin/kidsmap. Credentials stay in ignored START scratch and are not printed or copied. Runtime copied structurally from previous owned profile, with new output/DB/cache/media names, environment sanitization and fresh locale manifest.

```bash
docker ps --filter name=start-local-2026-10-12-r1-pg --format '{{.Names}} {{.Ports}}'
.venv/bin/python scripts/build_isolated_locales.py build --output .tmp/module01-completion-2026-10-12-r1/integration/locales --locales ru az en --compiler native
.venv/bin/python .tmp/module01-completion-2026-10-12-r1/integration/run.py discovery
.venv/bin/python .tmp/module01-completion-2026-10-12-r1/integration/run.py target
.venv/bin/python .tmp/module01-completion-2026-10-12-r1/integration/run.py affected
```

Build/discovery exit0, explicit2097IDs/wrapper1957/no-label618. Initial target attempt3fail (two invalid geography fixture expectations) and diagnostics3fail are ignored logs, not acceptedRED. Corrected fresh fictional fixture validRED5tests4P1F exit1, run4.481s; minimalbackend patch thenGREEN5P0F0E0skip exit0. Existing assertions never changed for green. New age assertion strengthened to age_to field; final affected/full run verifies final new test source.

Runtime flags DJANGO_TESTING=1 and allowlisted environment; DATABASE_URL/REDIS/productioncredentials cannot be inherited. Own test database names are integration-only. Every script checks own locale manifest and soleLOCALE_PATHS before django.setup. Native msgfmt used, no fake WSL.

Full command after root final-source signal (parallel4 real workers, dedicated separate testDB test_completion01_integration_full_20261012_r1+4clones):

```bash
.venv/bin/python .tmp/module01-completion-2026-10-12-r1/integration/run.py full
.venv/bin/python .tmp/module01-completion-2026-10-12-r1/integration/source-snapshot.py full-source-before
.venv/bin/python scripts/build_isolated_locales.py verify --manifest .tmp/module01-completion-2026-10-12-r1/integration/locales/manifest.json
KIDSMAP_JSDOM="$PWD/.tmp/module01-full-2026-10-12-r1/integration/node/node_modules/jsdom" NODE_PATH="$PWD/.tmp/module01-full-2026-10-12-r1/integration/node/node_modules" node --require ./.tmp/module01-completion-2026-10-12-r1/integration/resolve-jsdom.cjs --test $(rg --files scripts | rg '^scripts/test_.*\.cjs$' | rg -v 'test_(localized_place_urls|review_cooldown|review_submission)') static/js/tests/*.test.js scripts/tests/*.test.cjs
```

Own dependency loader resolves historical hardcoded jsdom path to earlier own installed26.1.0 (read-only reuse; prior runtime untouched). First Node attempt used newempty dependency path (ENV failure, preservednode-corpus.txt); corrected only own resolver, finalNode117tests116PASS/0FAIL/1SKIP exit0 (node-corpus-final.txt). Final skip is actual-HTML legacy wizard probe: no fresh integration/photo-form.html yet. Three Playwright launchers are real browsers, not unit corpus; root owns rendered-browser checks.

Final outcomes: affected324/324PASS,0fail/error/skip,exit0,597.533s actualtests; full2097attempts2054PASS/18FAIL/25ERROR/0skip,exit43,705.377s actualtests,total764.2428s. Exact43failedIDs and finalexception lines equal cleanHEAD r1 baseline;0new failures. No need to repeat unchanged43baseline failure cases: prior r1 sequential reproduction retained and currentexact ID/exception match recorded.42historical guard blocks/1stale specialist assertion remain outside scope.

```bash
.venv/bin/python .tmp/module01-completion-2026-10-12-r1/integration/source-snapshot.py full-source-after
```

Exit0,source2827 paths hash4804e1f50213581113826fe780bcfdbcebc7f4d21cf1bf0347defac5b99d1fc2 matchesbefore; only5approved app paths differHEAD. Final readback uses explicit ownpostgres connection, `SET TRANSACTION READ ONLY`,statement_timeout10s/lock_timeout2s and aggregate `SELECT count(*) FROM pg_database WHERE datname LIKE 'test_completion01_integration_%'`; count0. Foreign DBs/records not read.
