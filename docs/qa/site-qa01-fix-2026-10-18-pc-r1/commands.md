# Commands and actual results

Host working directory `C:\kidsmap`; commands below run in WSL Ubuntu-24.04 unless stated otherwise. Each script is owned by this fresh package. Runtime setup clears inherited environment, validates source hashes and fresh locales before django.setup. Browser scripts use fresh fictional role contexts and block external hosts. Full raw local logs remain under `.tmp/site01-pc-fix-r1`; exported backend summaries contain method results/counts/exits and raw-log SHA256.

1. `python3 /mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1/prepare.py` → exit0;1027 sources,24 prior packages verified, fresh own app/normalDB/testDB selection, internal QA PostgreSQL safety verified. `git apply --check` embedded before any application edit: exit0.
2. `python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py build --source-locale /mnt/c/kidsmap/locale --output /mnt/c/kidsmap/.tmp/site01-pc-fix-r1/locales --compiler native` → exit0;3 current catalogues.
3. `docker exec m10s01-fix-r1-app python /mnt/c/kidsmap/.tmp/site01-pc-fix-r1/runtime.py migrate` executed inside shell wrapper redirecting to own migrate.log. Migration output completed; wrapper returned1 because PowerShell expanded its shell status variable before Bash received it. No direct subprocess migration exit was retained. Fresh seed and later explicit no-pending-migrations proof establish schema availability; no migration rerun.
4. `docker exec m10s01-fix-r1-app python /mnt/c/kidsmap/.tmp/site01-pc-fix-r1/seed.py` → exit0;9 fictional staff, fresh normalDB only. Adapted new scratch seed source derived from old plan without executing old script path.
5. `docker exec m10s01-fix-r1-app python /mnt/c/kidsmap/.tmp/site01-pc-fix-r1/seed_extra.py` → exit0;4 extra fictional roles, own logo/gallery.
6. `python3 /mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1/run_backend.py red` → exit1 EXPECTED;28methods/31failure observations/0errors. Exact docker test labels in `evidence/red-backend.json`.
7. `python3 /mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1/start_browser_runtime.py red` → exit0;own loopback33480 server/proxy ready.
8. `python3 /mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1/browser_driver.py open http://127.0.0.1:33480/ --config=/mnt/c/kidsmap/.tmp/site01-pc-fix-r1/playwright.json` → exit0;fresh Chromium session `site01-pc-fix-r1`. `npx` was verified available before use. CLI prefix/version selection and all browser exits are in `evidence/browser-commands.jsonl`.
9. Same browser driver with `browser-red.js` → exit0 script /2expected failing security assertions. Two fresh native PNG.
10. `python3 /mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1/apply_approved.py` → exit0;exact approved4file patch initially applied,3 existing candidate hashes and initial candidate test hash verified. No staged changes.
11. Same `run_backend.py green` → exit1;28methods/1failure/0errors. Candidate test incorrectly assumed `/az/admin` directly403; actual existing301 canonical redirect. Raw log and exported summary retained.
12. Same `start_browser_runtime.py green` → exit0;only own serving process replaced after command-line identity check, own proxy retained.
13. `python3 /mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1/verify_route_refinement.py` → exit0 orchestration;its one refined method test against exact original backend source-overlay returned1 EXPECTED (200!=403). Current routing untouched. Details in `evidence/route-refinement.json`.
14. Same `run_backend.py green-final` → exit0;28/28methods,0failures/0errors,5.006s. Exact labels and command in `evidence/green-final-backend.json`.
15. Browser driver `browser-matrix.js` → exit0;90cells/630checksPASS.
16. `docker exec m10s01-fix-r1-app python /mnt/c/kidsmap/.tmp/site01-pc-fix-r1/static_runtime.py` → exit0;Python/template/28method IDs/safety/no pending migrations. Own script copied from this package.
17. `npx --yes --package node@24 node --check /mnt/c/kidsmap/static/admin/js/kidsmap_site_media.js` → exit0;repeated inside finalizer for final source proof. `git diff --check` → exit0.
18. Browser driver `browser-actions.js` → exit0;27operation rows/105checksPASS.
19. Browser driver `browser-supplement.js` → exit0;10rows/20checksPASS.
20. `python3 /mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1/finalize.py` → exit0;current1028source hashes,24prior packages/sharedMO/.cbmignore/refs/empty index bytes/foreign container identities and states/activeNONE, all acceptance datasets and PNG signatures/hashes verified; guide/MASTER append-only.

Finalizer attempt1 exited1 after its redundant slow WSL Git diff subprocess was intentionally terminated (SIGTERM), with exact command-line identity verified. It had not reached document writes. Final attempt uses `/mnt/c/Program Files/Git/cmd/git.exe -C C:/kidsmap diff --check`; native check passed earlier and is revalidated for final snapshot. This is an execution-environment issue, not an application failure.

Exact original/updated test diffs and source hashes are retained. The first GREEN error is classified as test-contract error, not an application fix. The migration wrapper incident is an environment/command issue. Historical QA results, browser rows and screenshots were not overwritten.
