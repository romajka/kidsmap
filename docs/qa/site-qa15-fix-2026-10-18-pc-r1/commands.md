# Exact runners and evidence

Working directory C:\kidsmap; WSL Ubuntu-24.04. Scripts retain structured subprocess argv, exits and safe summaries. Runtime is an isolated test profile with cleared environment before Django setup; raw test/application logs stay in ignored scratch.

```
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/prepare.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/setup_runtime.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/run_backend.py red
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/apply_approved.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/run_backend.py green
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/run_backend.py green-final
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/refine_template.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/run_render_backend.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/run_static_final.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/refine_preview.py red
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/refine_preview.py apply
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/prepare_preview_final.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/run_preview_backend.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/docs/qa/site-qa15-fix-2026-10-18-pc-r1/run_static_preview.py
git diff --check
```

The first green was retained as FAIL because its keepdb had been flushed by RED's TransactionTestCase. Between green and green-final, scratch qa_settings.py/stage.json selected the new owned test DB test_m10s15_fix_r1_green. No app/assertion repair. Preview refinement then added one failing regression before backend change; prepare_preview_final.py selected another fresh test_m10s15_fix_r1_preview DB, final55methodsPASS. See backend JSON for actual docker exec test labels and exits; runtime's runner uses verbosity2, keepdbTrue, interactiveFalse. Static suite enumeration records55 current unique method IDs; earlier54 preserved separately. Source-lineage.json binds stages to hashes/evidence.

Browser: browser_driver.py NAME.js runs npx --yes --package node@24 --package @playwright/cli playwright-cli -s=site15-pc-fix-r1 run-code with that exact saved JS and embedded baseline. See evidence/browser-commands.jsonl and each *-cli.txt for all invocations/results. run_edges.py executes the initial edges. Current suites use browser-preview-file-media.js, browser-preview-final-matrix.js, then run_preview_edges.py (recovery/editors/permissions), sequentially against the same owned fixture DB; browser contexts do not run concurrent suites. The scripts are evidence, not idempotent commands to rerun over this sealed package.

Own extra fixture roles and catalog-fixture check are recorded in extra_seed.py/seed_catalog_fixture.py. All data are fictional and confined to the normal fixture DB. No production snapshot was read. Initial static probe assertions passed but evidence write hit readonly repo Errno30; corrected to own RW scratch then host copied, evidence retained in qa-adjustments.json.
