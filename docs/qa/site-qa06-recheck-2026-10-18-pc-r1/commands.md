# Recheck commands and evidence ownership

Host C:/kidsmap, PowerShell; execution inside WSL Ubuntu-24.04/Docker. No application implementation command was run.

```
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/prepare.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/setup_runtime.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/run_red.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/prepare_red_final.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/run_red.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/extend_static_raster_test.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/run_red.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/start_browser.py red
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/repair_helper.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/start_browser.py red
wsl -d Ubuntu-24.04 -- docker exec m10s06-plan-r1-app python /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/seed_media.py
wsl -d Ubuntu-24.04 -- docker exec m10s06-plan-r1-app python /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/seed_partner.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/browser_driver.py open http://127.0.0.1:33510 --config=playwright.json
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/browser_driver.py browser-red.js
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/browser_driver.py browser-generic-error.js
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/build_candidate.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa06-recheck-2026-10-18-pc-r1/run_static.py
git diff --check
```

This list names the actual invocations; overlapping independent test/normal-DB browser setup ran concurrently. Backend JSON retains exact docker exec argv/labels/exits and raw-log hashes. All test commands run through the saved scratch runtime: environment.clear, DJANGO_TESTING1, own settings before django.setup, source1029/current locale verification, custom runner verbosity2/keepdbTrue/interactiveFalse. Three successive RED runs used separate testDBs; raw logs remain ignored scratch. Renaming of earlier candidate/results is explicit in prepare_red_final.py/extend_static_raster_test.py.

Browser driver invokes `npx --yes --package node@24 --package @playwright/cli playwright-cli -s=site06-pc-plan-r1 run-code` with the saved JS. Browser command ledger/results in evidence/browser-commands.jsonl and *-cli.txt; Chromium binary/config in ignored own profile. External requests aborted; fixture login simulated; real upload/form events and backend row/file readbacks. Browser corrupt inputs are PNG only, never active SVG payloads.

Static command list/exits in evidence/static-commands.json; initial CRLF patch failure in static-initial-commands.json. Candidate PO compilation uses own candidate-locales and does not select it for the live RED app or touch shared MO. No candidate Python module imported/executed.

These are retained one-time launchers/evidence, not commands to rerun over this sealed package. Implementation after approval requires a new unique fix package/runtime and fresh current-source locales/RED as specified in IMPLEMENTATION_PLAN.md.
