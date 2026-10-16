# Commands and native exits

Cwd `/home/ramin/kidsmap`. Runtime: `.tmp/offer-qa01-fix-2026-10-13-r1/venv/bin/python docs/qa/offer-qa01-fix-2026-10-13-r1/runtime.py`. No manage.py/.env. Exact native commands/exits in `*.command.json` and commands.jsonl. Setup/locale/prepare/check0.

RED1/1 expected failure: `../offer-qa01-recheck-2026-10-13-r1/approved-repair-regression-red.command.json`.

Targeted38 native0:
```text
.venv/bin/python docs/qa/offer-qa01-fix-2026-10-13-r1/command.py targeted-green .tmp/offer-qa01-fix-2026-10-13-r1/venv/bin/python docs/qa/offer-qa01-fix-2026-10-13-r1/runtime.py test catalog.testcases.test_offer_qa01_group_removal catalog.testcases.test_task33_pricing.GroupPricingTests catalog.testcases.test_task33_completion_taxonomy catalog.testcases.test_task33_program_workspace
```
New10 final native0; discovery38unique; exact receipts new-tests-final.command.json, discovery.command.json. No unchanged shared suites rerun.

Browser driver uses only `playwright-cli -s=offerqa01fix-20261013-r1 run-code` with credentials substituted inside ignored/runtime memory and tool output sanitized; commands.jsonl contains script filenames/result receipts, not credentials. CLI exit0 alone is not browser acceptance: effective JSON rows and raw failures remain authoritative.

`readonly-readback` and `extra-readback-final` native0: READ ONLY,10s statement/2s lock timeout. Locale-final-verify0. Native pre-patch baseline partial-prepatch-baseline-corrected0/1 behavioral characterization, not repair test. Earlier diagnostic1 retained.

Final artifact/preservation verifier:
```text
.venv/bin/python docs/qa/offer-qa01-fix-2026-10-13-r1/verify-final.py
```
Exact final native exit in final-verification.command.json. No commit/push/deploy/production/full wrapper.
