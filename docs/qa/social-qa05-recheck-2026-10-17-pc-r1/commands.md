# SOCIAL05 PLAN — выполненные команды и результаты

C:\kidsmap, 2026-10-17. Это журнал завершённого PLAN run, не инструкция слепо запускать прежние runtime/PID. Scratch .tmp/social05-pc-plan-r1 игнорируется Git. Перед любым повтором нужны ownership/isolation/source/locale gates; полный suite не повторялся.

## Подготовка и изоляция

Выполнены git rev-parse HEAD/HEAD^{tree}/task33-progress, git branch --show-current, git status --porcelain=v1 -uall, git diff --cached --name-only, сравнение1021source/PO и3sharedMO, active_run. Exit0; source1021 совпал с предыдущим SOCIAL04 final. Graph readiness/coverage и targeted SiteReviewsController search/trace проверены, затем source и literal rg fallback. Секреты/env/graph cache не экспортировались.

~~~powershell
python -X utf8 .tmp/social05-pc-plan-r1/bootstrap.py
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/social05-pc-plan-r1/locales --locales ru az en --compiler native
wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social05-pc-plan-r1/start.sh
wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social05-pc-plan-r1/prepare.sh
~~~

Все завершились0. Prepare:2 readiness observations not-ready, затем ready; migrations/fictional seed только в собственном PG, затем собственный HTTP. При setup runtime проверяет source/PO/MO и sole LOCALE_PATHS. Proxy запущен через Start-Process wsl.exe с -WindowStyle Hidden: собственный proxy.py, bind127.0.0.1:33325, PID сохранён в ignored scratch. Чужих stop/restart/kill не было.

Native CLI запускался через browser_driver.py: npx --yes --package node@24 --package @playwright/cli playwright-cli -s=social05-pc-plan-r1, separate Chromium context, собственная config. Open и initial runtime-info запросы завершились0; точные CLI commands/exits сохранены в [browser-commands.jsonl](browser-commands.jsonl). Browser driver и cell source включены в пакет; локальные settings/DB passwords не копируются.

## Native baseline и affected backend

~~~powershell
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social05-pc-plan-r1/matrix.py
wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social05-pc-plan-r1/baseline.sh
~~~

Matrix завершилась0 как сбор evidence, product outcome —36cells,324controlPASS,210layoutPASS/24layoutFAIL в3author768cells.0pageerrors/localHTTP failures/request failures,36PNG. Actual submit/sort/vote не выполнялись.

Baseline.sh выполнял следующую единственную команду, записав [baseline.exit](baseline.exit)=0 и [baseline.log](baseline.log):

~~~sh
docker exec m09s05-plan-r1-app python /mnt/c/kidsmap/.tmp/social05-pc-plan-r1/runtime.py test \
 catalog.testcases.public.TestReviewEnhancements.test_site_reviews_page_can_sort_reviews_by_likes \
 catalog.testcases.public.TestReviewEnhancements.test_site_reviews_page_skips_blank_text_reviews \
 catalog.testcases.public.TestReviewEnhancements.test_site_review_reactions_update_counters
~~~

Три unique existing methods,0F/0E,0.381s. Own test DB сохранена. Existing assertions не изменялись; test warning про staticfiles directory не скрыт. Этот backend PASS не обнаруживает CSS defect.

## Неприменённый diff и SIMULATED probe

~~~powershell
python -X utf8 .tmp/social05-pc-plan-r1/make_candidate.py
git apply --check --ignore-space-change docs/qa/social-qa05-recheck-2026-10-17-pc-r1/proposed.diff
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social05-pc-plan-r1/browser_driver.py probe-run.js
~~~

Make candidate/apply-check0; application file не записывался. Probe CLI0, но строгий JSON gate обнаружил48PASS/1FAIL и завершился1: только RU1024 restore geometry drift0.0327px из-за finite animation. Исходный raw result сохранён в probe-attempt1.json, все первоначальные PNG сохранены.

~~~powershell
wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social05-pc-plan-r1/browser_driver.py probe-stable.js
~~~

Exit0; повторён только RU1024 после ожидания finite animations, strict JSON equality unchanged. Accepted probe.json явно собран из первых6 исходных случаев и этого replay:7cases/49PASS, отдельный stable PNG. Style удалён, DB unchanged. Root-cause SIMULATED preview не считается patch acceptance.

## Публикация и metadata

Первый functions.exec wrapper записи плана отклонён SyntaxError до исполнения; исправлен tilde fences. Первый publish.py завершился1/FileNotFoundError для probe.json, копирование matrix.json успело завершиться; source/guide не изменены. После явной сборки accepted probe повтор publish.py завершился0. Промежуточный read-only Python summary завершился1/KeyError: lang хранится внутри item в matrix.json; исправлен только metadata query. Product checks не повторялись и не переименовывались в PASS.

~~~powershell
python -X utf8 .tmp/social05-pc-plan-r1/publish.py
python -X utf8 .tmp/social05-pc-plan-r1/finalize_docs.py
python -X utf8 docs/qa/social-qa05-recheck-2026-10-17-pc-r1/verify_artifacts.py
~~~

Успешный publisher0 сохранил44PNG/hash/dimensions, source/runtime snapshots,32foreign container IDs/states и исходные неуспешные попытки. Finalize_docs добавляет только новую guide note с проверкой обратного удаления; verifier проверяет source/refs/index/active_run/MO/.cbmignore/old manifests/candidate/native counts/test log/links/PNG и создаёт artifact manifest. Фактический final exit и UTC записываются в verification.json только после успешной проверки. Проверка metadata не является application GREEN.

Application patch/full ACCEPT09/global/06–09/production/commit/push/deploy НЕ выполнялись. Существующие successful suites не повторялись.
