# Exact commands and exits

Full ledger: ../module04-recheck-2026-10-13-r1/commands.jsonl and every *.command.json / *.txt. CLI exit0 is transport execution, not an assertion PASS; raw JSON and effective matrix decide browser verdicts.

Working directory /home/ramin/kidsmap. Runtime/profile paths are this run's actual receipts, not portable parameters for another machine. Credentials only in ignored scratch, never in commands here.

One full Event batch: 17 explicit module/class labels in backend-discovery.json. Exact argv in full-module-backend-ready.command.json. Native1:135 PASS/1 fixture-order setup error. Initial connection-refused attempt executed0; retained separately.

Exact one-method fresh-DB repeat:
```text
.venv/bin/python docs/qa/module04-recheck-2026-10-13-r1/command.py autocommit-targeted-fresh-db .tmp/module04-recheck-2026-10-13-r1/venv/bin/python docs/qa/module04-recheck-2026-10-13-r1/runtime.py test catalog.testcases.test_content_entry_final.EventAdminAutocommitTests.test_edit_get_readiness_does_not_lock_or_write_outside_transaction
```
Native0/1 PASS. Existing assertions unchanged.

New photo regression tests: native1/5 (4 PASS/1 expected clear failure) before patch; first targeted20 batch native1/19 PASS/1 same failure; final native0/5 PASS. Exact labels and argv in photo-regressions-{red,green,final-green}.command.json. No repeated full module batch after patches.

Two historical Event-only supplement labels: historical-event-geography-fallback.command.json, native0/2 PASS. Final unique method inventory143 includes these; no claim of one native143-method batch.

Owned locale builds: locales-v2/v4/v5/v6 native0, v3 unused build before corrected patch precondition. Final:
```text
.venv/bin/python docs/qa/module04-recheck-2026-10-13-r1/command.py locale-build-v6 .tmp/module04-recheck-2026-10-13-r1/venv/bin/python scripts/build_isolated_locales.py build --output .tmp/module04-recheck-2026-10-13-r1/locales-v6 --locales ru az en --compiler native
```
Build verifies current-source hashes before django.setup via runtime.py. Public actual runtime/source receipt obtained with own start-server.py; restart.py verifies own PID command path before SIGTERM. No foreign process control.

Browser:
```text
.venv/bin/python docs/qa/module04-recheck-2026-10-13-r1/drive.py /home/ramin/kidsmap/docs/qa/module04-full-2026-10-13-r1/<script>.js
```
Script/source/result filenames listed in matrix-effective.json. Driver uses only session module04event-20261013-r1. Own delayed/aborted POST explicitly SIMULATED; browser egress outside own base aborted. Only filenames/summary counts shown; secrets redacted.

READ ONLY fixture/runtime readbacks: runtime.py script readback.py / fixture-stimuli.py readback, native0;10s statement/2s lock timeouts. Explicit fixture stimuli restore all own prerequisite records and record no Event ORM writes; checked negative requests remain native/browser requests.

Final tooling:
```text
.venv/bin/python docs/qa/module04-full-2026-10-13-r1/build-effective.py
.venv/bin/python docs/qa/module04-full-2026-10-13-r1/package-evidence.py
.venv/bin/python docs/qa/module04-full-2026-10-13-r1/verify-final.py
```
Final command exits saved separately in final-commands.json. No commit/push/deploy/production/global wrapper.
