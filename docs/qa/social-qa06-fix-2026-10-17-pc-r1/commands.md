# SOCIAL06 approved implementation — commands/results

C:\kidsmap,2026-10-17. Application scope один template. Bootstrap/source/locale/live/ownership proof выполнен до patch; original PLAN/source1021 unchanged.

~~~powershell
python -X utf8 .tmp/social06-pc-fix-r1/bootstrap.py
git apply --check --ignore-space-change docs/qa/social-qa06-recheck-2026-10-17-pc-r1/proposed.diff
git apply --ignore-space-change docs/qa/social-qa06-recheck-2026-10-17-pc-r1/proposed.diff
python -X utf8 .tmp/social06-pc-fix-r1/prepare_sources.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/locales --locales ru az en --compiler native
wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/start.sh
~~~

All0. New own app/internal network/own fictionalPG reuse verified; repositoryRO/new scratchRW. FreshMO/cleared testing env/setup source gates. Hidden own proxy started with Start-Process wsl.exe -WindowStyle Hidden; npx available. Bounded readiness0transients.

~~~powershell
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/browser_driver.py open http://127.0.0.1:33337/ru/reviews/ --config=.tmp/social06-pc-fix-r1/playwright.json
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/browser_driver.py browser-initial.js
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/matrix.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/run_json.py acceptance-extra
~~~

Open/initial/matrix0:18cells198control144semantic-keyboardPASS. Extended exit1:9cells117PASS/9resetFAIL,0pageerrors. Original JSON/helper/raw CLI/PNG/source/diff retained with initial prefix; assertions unchanged. No application reset/clean or rollback.

~~~powershell
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/browser_driver.py reset-diagnostic.js
~~~

Diagnostic0 proves hidden value/defaultValue both become2 and native reset remains2. Same-file correction captures original defaultRating before choose and uses it in reset callback. Final combined applied.diff/source guard saved; exact initial candidate retained separately.

Own refresh_own_server.py verified one /proc PID with exact fix runtime.py serve path, terminated only it; own serve relaunched with final source/MO gates. One own process reload, no container/foreign restart. Final readiness MATCH.

~~~powershell
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/run_json.py reset-recheck
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/run_json.py actions
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social06-pc-fix-r1/run_json.py shared
~~~

All0:9reset cases27PASS (9replace priorFAIL+18sanity),9native submit/reload/range/CSRF/guest/SIM rows68PASS,45shared cells270bounded controlsPASS. Original18matrix/117nonreset extended passes retained with initial source attribution; not repeated after reset-only correction. Actual POST ratings3/1/5 pending readback, real API0/6→400/CSRF403/guest401, SIMULATED abort before delivery. No backend suite repeat.

Shared source/DOM reviewed; separate read-only fictional auth HTML probe confirmed real Place detail widget (HTTP200), no app changes. Shared limitations:81media404events/9unique own missing gallery assets;36blocked external CDN/maps requests,0unhandled pageerrors. Existing SOCIAL07 observed9times, not asserted repaired.

~~~powershell
python -X utf8 .tmp/social06-pc-fix-r1/export.py
python -X utf8 .tmp/social06-pc-fix-r1/finalize_docs.py
python -X utf8 docs/qa/social-qa06-fix-2026-10-17-pc-r1/verify_artifacts.py
git diff --check -- src/catalog/templates/pages/site_reviews.html docs/qa/continuation-and-repair-prompts-2026-10-11.md
~~~

Export0:107nativePNG and safe evidence. Finalizer adds closure note only; verifier records actual exit/UTC on success after source/initial-to-final reset-only delta/refs/index/MO/active_run/.cbmignore/37entrycontainers/old packages/70PLANfiles/PNG/assertions checks. Raw FormData/CSRF tokens/env/settings/real records not copied. No commit/push/deploy/reset/clean/stash/dirty checkout switch/SOCIAL07/fullACCEPT09/global.
