# Exact native command ledger

Commands were run from `C:/kidsmap`; browser cwd is the dedicated ignored scratch directory. Synthetic password arguments are redacted.

## Native commands

1. Exit **0** — `git rev-parse HEAD`
2. Exit **0** — `git branch --show-current`
3. Exit **0** — `git status --short`
4. Exit **0** — `git diff --exit-code --stat HEAD -- src static config locale`
5. Exit **0** — `wsl.exe --exec docker ps --format {{.Names}} {{.Ports}}`
6. Exit **0** — `wsl.exe --exec docker image inspect postgres:17-alpine --format {{.Id}}`
7. Exit **0** — `wsl.exe --exec docker run --pull=never --detach --name kidsmap-placeqa01-07-fix-20261010 --publish 127.0.0.1:55460:5432 --env POSTGRES_DB=placekmfix_plan --env POSTGRES_USER=placekmfix_plan --env POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine`
8. Exit **0** — `wsl.exe --exec docker exec kidsmap-placeqa01-07-fix-20261010 pg_isready -U placekmfix_plan -d placekmfix_plan`
9. Exit **1** — `C:\kidsmap\.venv\Scripts\python.exe C:\kidsmap\docs\qa\place-qa01-07-fix-2026-10-10\runtime.py prepare` → `prepare-runtime.txt`
10. Exit **1** — `.venv/Scripts/python.exe -m unittest discover -s scripts/tests -p test_build_isolated_locales.py` → `locale-tool-red.txt`
11. Exit **0** — `wsl.exe --exec docker inspect 1502f40c17e9e2c217482d2228d9fe1799b43b681ca65d1a1a49307250b2aa05 --format {{.Name}}`
12. Exit **0** — `wsl.exe --exec docker stop 1502f40c17e9e2c217482d2228d9fe1799b43b681ca65d1a1a49307250b2aa05`
13. Exit **0** — `git rev-parse HEAD`
14. Exit **0** — `git branch --show-current`
15. Exit **0** — `git status --short`
16. Exit **0** — `git diff --exit-code --stat HEAD -- src static config locale`
17. Exit **0** — `wsl.exe --exec docker ps --format {{.Names}} {{.Ports}}`
18. Exit **0** — `wsl.exe --exec docker image inspect postgres:17-alpine --format {{.Id}}`
19. Exit **0** — `wsl.exe --exec docker run --pull=never --detach --name kidsmap-placeqa01-07-fix-20261010-r2 --publish 127.0.0.1:55445:5432 --env POSTGRES_DB=placekmfix_plan --env POSTGRES_USER=placekmfix_plan --env POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine`
20. Exit **0** — `wsl.exe --exec docker exec kidsmap-placeqa01-07-fix-20261010-r2 pg_isready -U placekmfix_plan -d placekmfix_plan`
21. Exit **0** — `C:\kidsmap\.venv\Scripts\python.exe C:\kidsmap\docs\qa\place-qa01-07-fix-2026-10-10\runtime.py prepare` → `prepare-runtime.txt`
22. Exit **1** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py test catalog.testcases.test_place_rejection_feedback catalog.testcases.test_place_qa03_pricing_rebase catalog.testcases.test_task33_place_nature_localization` → `django-red.txt`
23. Exit **0** — `.venv/Scripts/python.exe -m unittest discover -s scripts/tests -p test_build_isolated_locales.py` → `locale-tool-green.txt`
24. Exit **1** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py test catalog.testcases.test_place_rejection_feedback catalog.testcases.test_place_qa03_pricing_rebase catalog.testcases.test_task33_place_nature_localization` → `django-red-effective.txt`
25. Exit **1** — `node --test scripts/test_owner_place_map_picker.cjs scripts/test_location_resolution.cjs` → `js-red.txt`
26. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py script seed_browser.py` → `seed-browser.txt`
27. Exit **2** — `.venv/Scripts/python.exe scripts/build_isolated_locales.py build --source-root locale --output .tmp/place-qa01-07-fix-20261010/locale-build-01 --locales ru az en --compiler wsl` → `locale-build-project.txt`
28. Exit **0** — `node --test scripts/test_owner_place_map_picker.cjs scripts/test_location_resolution.cjs` → `js-green-first.txt`
29. Exit **0** — `.venv/Scripts/python.exe scripts/build_isolated_locales.py build --source-locale locale --output .tmp/place-qa01-07-fix-20261010/locale-build-01 --locales ru az en --compiler wsl` → `locale-build-project-effective.txt`
30. Exit **1** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py test catalog.testcases.test_place_rejection_feedback catalog.testcases.test_place_qa03_pricing_rebase catalog.testcases.test_task33_place_nature_localization catalog.testcases.test_place_qa04_manual_location` → `django-green-first.txt`
31. Exit **1** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py test catalog.testcases.test_place_qa03_pricing_rebase.MixedProjectionTests.test_explicit_different_projection_is_not_discarded_as_an_echo` → `pricing-intent-red.txt`
32. Exit **0** — `.venv/Scripts/python.exe scripts/build_isolated_locales.py build --output .tmp/place-qa01-07-fix-20261010/locale-build-02 --locales ru az en --compiler wsl` → `locale-build-final.txt`
33. Exit **1** — `.venv/Scripts/python.exe -m unittest scripts.tests.test_build_isolated_locales.IsolatedLocaleBuildTests.test_source_and_output_junctions_are_refused` → `locale-junction-red.txt`
34. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py test catalog.testcases.test_place_rejection_feedback catalog.testcases.test_place_qa03_pricing_rebase catalog.testcases.test_task33_place_nature_localization catalog.testcases.test_place_qa04_manual_location catalog.testcases.test_task33_publication catalog.testcases.test_task33_place_continuous catalog.testcases.place_taxonomy_admin catalog.testcases.test_task33_admin_editors` → `django-green-second.txt`
35. Exit **0** — `.venv/Scripts/python.exe -m unittest scripts.tests.test_build_isolated_locales` → `locale-tool-final.txt`
36. Exit **0** — `node --test scripts/test_owner_place_map_picker.cjs scripts/test_location_resolution.cjs` → `js-final.txt`
37. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/verify_locale_startup.py` → `locale-startup.txt`
38. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py script verify_locale_runtime.py` → `locale-runtime.txt`
39. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py script browser_extra_fixtures.py` → `browser-extra-fixtures.txt`
40. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py test catalog.testcases.test_location_assignment catalog.testcases.test_location_resolution catalog.testcases.test_location_correction catalog.testcases.test_task33_drafts catalog.testcases.test_task33_pricing catalog.testcases.pricing_plans_relational` → `django-geography-pricing-regression.txt`
41. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py script readback.py` → `db-created.txt`
42. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py test catalog.testcases.test_place_qa03_pricing_rebase.ConcurrentMixedProjectionTests catalog.testcases.test_place_json_and_pricing_modes catalog.testcases.test_volunteer_admin` → `django-concurrency-final.txt`
43. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py script verify_pricing_browser.py pending` → `pricing-db-pending.txt`
44. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py script readback.py` → `db-resubmitted.txt`
45. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py script verify_pricing_browser.py approved` → `pricing-db-approved.txt`
46. Exit **1** — `node --test --test-name-pattern=restored scripts/test_location_resolution.cjs` → `partial-coordinate-red.txt`
47. Exit **0** — `node --test scripts/test_owner_place_map_picker.cjs scripts/test_location_resolution.cjs` → `js-final-expanded.txt`
48. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py script readback.py` → `db-concurrency-diagnostic.txt`
49. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/runtime.py script verify_browser_final.py` → `browser-final-db.txt`
50. Exit **2** — `git -c core.autocrlf=false diff --check` → `diff-check.txt`
51. Exit **0** — `.venv/Scripts/python.exe scripts/build_isolated_locales.py verify --manifest .tmp/place-qa01-07-fix-20261010/locale-build-02/manifest.json` → `locale-verify-final.txt`
52. Exit **0** — `git diff --check` → `diff-check-final.txt`
53. Exit **1** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/finalize_evidence.py` → `final-evidence.txt`
54. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/finalize_evidence.py` → `final-evidence-effective.txt`
55. Exit **0** — `.venv/Scripts/python.exe docs/qa/place-qa01-07-fix-2026-10-10/cleanup.py` → `cleanup.txt`

## Browser commands

1. Exit **0** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan open http://127.0.0.1:8840 --config=C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser.config.json`
2. Exit **1** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
3. Exit **1** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan help run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
4. Exit **1** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
5. Exit **0** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
6. Exit **1** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
7. Exit **1** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
8. Exit **0** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
9. Exit **1** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
10. Exit **0** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/admin-state.json`
11. Exit **1** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
12. Exit **0** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
13. Exit **0** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
14. Exit **0** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/owner-state.json`
15. Exit **0** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan goto http://127.0.0.1:8840/ru/account/places/create/`
16. Exit **1** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan goto http://127.0.0.1:8840/ru/account/places/create/?type=permanent&fresh=1`
17. Exit **0** — `C:\Program Files\nodejs\npx.cmd --offline --package @playwright/cli playwright-cli -s=placekmfix-plan eval () => ({fields:[...document.querySelectorAll("[data-permanent-place-form] [name]")].map(x=>({name:x.name,type:x.type,value:x.type==="hidden"?"hidden":x.value})), readiness:JSON.parse(document.getElementById("pc-readiness").textContent)})`
18. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
19. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
20. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan eval () => ({url:location.href, errors:[...document.querySelectorAll(".pw-error,.errorlist,[data-pc-errors]")].map(x=>x.textContent), text:document.querySelector("main").innerText.slice(0,1500)})`
21. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan eval () => ({kind:[...document.querySelector("[data-tariff-key=editor_kind]").options].map(x=>[x.value,x.textContent]),nature:document.querySelector("[name=nature]").value})`
22. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
23. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan eval () => ({url:location.href,errors:document.querySelector("[data-pc-errors]")?.textContent, main:document.querySelector("main").innerText.slice(0,700), tariff:document.querySelector("[name=pricing_plans]")?.value})`
24. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
25. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
26. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/admin-state.json`
27. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
28. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/owner-state.json`
29. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
30. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
31. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
32. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
33. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
34. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
35. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
36. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
37. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
38. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
39. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/admin-state.json`
40. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
41. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
42. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan eval () => ({url:location.href,labels:[...document.querySelectorAll("label[for=id_description_az],label[for=id_description_ru],label[for=id_description_en]")].map(x=>x.textContent),errors:[...document.querySelectorAll(".errorlist,.errornote")].map(x=>x.textContent),buttons:document.querySelectorAll(".km-pf-picker-btn").length})`
43. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
44. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/owner-state.json`
45. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
46. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
47. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-save C:/kidsmap/.tmp/place-qa01-07-fix-20261010/owner-current.json`
48. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
49. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/admin-state.json`
50. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
51. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/owner-current.json`
52. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
53. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/admin-state.json`
54. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
55. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/owner-current.json`
56. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
57. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
58. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/admin-state.json`
59. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
60. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/owner-current.json`
61. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
62. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/admin-state.json`
63. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
64. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/other-state.json`
65. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
66. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
67. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
68. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
69. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/admin-state.json`
70. Exit **1** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
71. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
72. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
73. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan state-load C:/kidsmap/.tmp/place-qa01-07-fix-20261010/owner-current.json`
74. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan run-code <exact inline scenario retained in browser-command-ledger.jsonl>`
75. Exit **0** — `C:\Program Files\nodejs\node.exe C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js -s=placekmfix-plan close`

