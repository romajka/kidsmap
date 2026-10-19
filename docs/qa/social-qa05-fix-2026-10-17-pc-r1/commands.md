# SOCIAL05 approved fix — commands/results

C:\kidsmap,2026-10-17. Source/app scope: только static/css/site.css. Scratch .tmp/social05-pc-fix-r1, original plan profile .tmp/social05-pc-plan-r1. Не запускать эти параметры на другом ПК без ownership/source/isolation proof.

1. Прочитаны canonical entry/registry/orchestrator, source-of-truth/audit/architecture и approved plan/skills. Source1021/sharedMO/HEAD/index и original live origins совпали. Docker inspect прочитан без вывода env: own old app/PG running/internal network/repository RO.
2. python -X utf8 .tmp/social05-pc-plan-r1/bootstrap_fix.py первоначально exit1: guard ожидал broad .tmp RW вместо actual own PLAN scratch RW. Локальные settings/секреты не экспортировались. Fresh locale build exit0; exact apply-check0, затем approved apply0:

~~~powershell
git apply --check --ignore-space-change docs/qa/social-qa05-recheck-2026-10-17-pc-r1/proposed.diff
git apply --ignore-space-change docs/qa/social-qa05-recheck-2026-10-17-pc-r1/proposed.diff
~~~

3. Исправлен только QA bootstrap mount assumption; retry0 проверил approved after SHA/остальные1020source и создал новый own app profile. Reconstructed pre-patch entry hashes получены из immutable PLAN evidence. Новый app монтирует repo RO и только свой fix scratch RW.

~~~powershell
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/locales --locales ru az en --compiler native
wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/start.sh
~~~

Exit0. New app m09s05-fix-r1-app; own existing internal network/fictional PG reused. Proxy Start-Process wsl.exe -WindowStyle Hidden, loopback33326; own PID stored ignored. Immediate readiness URL query exit1 RemoteDisconnected, first CLI open exit1 ERR_EMPTY_RESPONSE; no product result from that attempt. Subsequent readiness current CSS/template hashes/testing/soleMO MATCH, initial CLI0. npx prerequisite available.

4. Separate CLI session social05-pc-fix-r1 used npx node@24/@playwright/cli with own config, no user browser. Exact names/exits in browser-commands.jsonl:

~~~powershell
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/matrix.py
wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/baseline.sh
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/extras.py
~~~

All0:36cells324controls234layoutPASS;6boundary54controls54layout/trackPASS. Finite-animation wait added; original outcome assertions unchanged. Backend3unique existing methods,0F/0E,0.355s, keep own testDB, no full-suite repeat. Exact test command:

~~~sh
docker exec m09s05-fix-r1-app python /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/runtime.py test \
 catalog.testcases.public.TestReviewEnhancements.test_site_reviews_page_can_sort_reviews_by_likes \
 catalog.testcases.public.TestReviewEnhancements.test_site_reviews_page_skips_blank_text_reviews \
 catalog.testcases.public.TestReviewEnhancements.test_site_review_reactions_update_counters
~~~

5. Own runtime.py seed0 added only four fictional shared targets/SiteSettings flags; SiteReview baseline unchanged. Own refresh_own_server.py verified exactly one /proc PID matching fix runtime.py serve and terminated only that process, then own serve relaunched for QA reviewer role/aggregate helpers. No container or foreign restart. Immediate metadata readiness query exit1 WinError10053; subsequent native run reached ready HTTP.

~~~powershell
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/run_json.py actions
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/run_json.py submit_transport
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/run_json.py shared
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social05-pc-fix-r1/run_json.py shared_baseline
~~~

Actions0:17rows147PASS; submit_transport0:1row8PASS. Native actions/guards and explicitly SIMULATED intercepted aborts separated in raw JSON/CLI. Shared exit1:36rows243PASS/9Activity-headingFAIL; formatter additionally KeyError id after complete JSON saved. Formatter fixed only for diagnostics. No full shared rerun:9affected original-CSS SIMULATED baseline cases alone executed0/36parityPASS; same9headingfailures reproduced, not marked PASS. Missing speculative literal-search paths had read-only nonzero exits; actual source/graph used, no app files created.

6. urllib actual static CSS200/hash/source proof0; PNG screenshots manually inspected (form RU768/cards RU390/SIMULATED submit error RU390). Export0 copied111nativePNG/manifests and all safe source/evidence. No secrets/local settings or real user records copied.

~~~powershell
python -X utf8 .tmp/social05-pc-fix-r1/export.py
python -X utf8 .tmp/social05-pc-fix-r1/finalize_docs.py
python -X utf8 docs/qa/social-qa05-fix-2026-10-17-pc-r1/verify_artifacts.py
git diff --check -- static/css/site.css docs/qa/continuation-and-repair-prompts-2026-10-11.md
~~~

Final verifier writes actual exit/UTC to verification.json after source/index/refs/MO/active_run/.cbmignore/prior package/34entrycontainers/native counts/9retained failures/111PNG/links checks. Metadata gate is separate from scoped application result. No commit/push/deploy/reset/clean/stash/dirty checkout switch, no SOCIAL06/fullACCEPT09/global.
