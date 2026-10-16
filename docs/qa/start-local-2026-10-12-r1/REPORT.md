# START LOCAL QA — 2026-10-12 r1

Режим START, без application fixes. Один исполнитель /root по канонической kidsmap-orchestrator; независимые специалисты не запускались.

## Checkout и доставка

- Checkout: `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`.
- На входе чистый WORKTREE, active_run NONE. На выходе только собственный untracked каталог `docs/qa/start-local-2026-10-12-r1`; scratch ignored. Tracked diff пустой, исходники/shared MO побайтно сохранены.
- Прочитаны guide (вступление, статус, 13 модулей, этапы и Git-перенос), AGENTS и канонические README/registry/orchestrator/architecture/source-of-truth/audit-contract, isolated-locale-build и тестовые settings. Исторические отчёты module01 recheck, PLACE-QA-08 и module13 сопоставлены в этой переписке; их runtime факты не перенесены.
- Все 167 required inputs, 18 modified inventory paths и 12442 transfer inventory paths присутствуют. Missing: 0. PLACE fixes/helper/regression tests присутствуют в HEAD; функциональная полнота доставки этим не доказана.
- PLACE-QA-01–08 имеют исторические scoped результаты; PLACE-QA-08=CROSS-QA-03. Full module01 NOT RUN. Очередь 76 ID/73 группы, guide 88 блоков — 73 PLAN/13 ACCEPT/2 service.

## Собственный runtime

- URL: http://127.0.0.1:51665; PID 80429; `/home/ramin/kidsmap/docs/qa/start-local-2026-10-12-r1/runtime.py`.
- PostgreSQL 17.10: container `start-local-2026-10-12-r1-pg`, volume `start-local-2026-10-12-r1-pgdata`, host `127.0.0.1:52523`, DB/user `start_20261012_r1`. Только loopback PortBinding проверен Docker inspect.
- 175 migration rows, 2 synthetic users, 1 unpublished synthetic Place. Фикстуры создавались только в новой собственной DB; это setup, не проверенный UI lifecycle.
- DJANGO_TESTING=1, DEBUG=False, LocMem cache/email, собственные media/private-media/staticfiles. Внешние ключи пустые; окружение allowlisted, manage.py/.env не загружались.
- Python socket connect/connect_ex разрешает только свой PostgreSQL; отрицательный egress probe остановлен до соединения. libpq использует явно настроенную единственную QA DB. Это runtime guard, не OS network sandbox. В браузере все origin вне собственного loopback блокируются.
- Пароли/secret key хранятся только в ignored scratch с mode600. Значения в отчёт/evidence не включены.
- Source entry=startup=current: 2792 файлов, SHA digest `d8c972148de8ba3cb3cafb8f0a6aa9872efa4491a4ecc4bf005a2a6bd8629649`. Runtime attestation выполнен на работающем процессе; app source и общие MO сохранены.
- RU/AZ/EN собраны native GNU msgfmt в `/home/ramin/kidsmap/.tmp/start-local-2026-10-12-r1/locales`; manifest verified до django.setup, единственный LOCALE_PATHS `/home/ramin/kidsmap/.tmp/start-local-2026-10-12-r1/locales/locale`. [Manifest](locale-manifest.json).

## Свежие проверки и команды

[Ledger](commands.jsonl), [tools](tools.json), [read-only readback](readback.json), [runtime](runtime-version.json), [preservation](verification.json).

- `.venv/bin/python docs/qa/start-local-2026-10-12-r1/bootstrap.py`: exit1 на собственной seed ошибке после успешной миграции; последующее resume завершено exit0.
- `runtime.py check`: exit0, 0 issues. `runtime.py test catalog.testcases.test_place_qa08_district_localization`: 2 tests PASS, exit0. Это targeted locale check, не полная module01 regression.
- `build_isolated_locales.py build/verify --compiler native`: exit0; 3 текущих каталога. Собственный native probe: build/verify PASS и stale-source rejection с ожидаемым exit1.
- Исходная helper suite `python -m unittest discover -s scripts/tests -p test_build_isolated_locales.py`: exit1, 9 tests, 6 failures/1 skip/2 passes. Шесть failures: hardcoded wsl.exe отсутствует на Linux; два passing negative tests не являются доказательством компиляции. Windows junction NOT RUN. Тест/его assertions не изменены и не выдаются за PASS.
- `.venv/bin/python docs/qa/start-local-2026-10-12-r1/runtime.py readback`: exit0, READ ONLY transaction, statement timeout10s/lock timeout2s, aggregate counts; внешнее соединение отвергнуто.
- `playwright-cli -s=kidsmap-start-20261012-r1 open about:blank --browser chrome`: exit0. Chrome 153.0.8010.36.
- `playwright-cli -s=kidsmap-start-20261012-r1 run-code --filename docs/qa/start-local-2026-10-12-r1/browser-smoke.js`: final exit0, AZ/RU/EN homepage+admin login 4 HTTP200, 0 pageerrors/0 local HTTP>=400. Google Fonts deliberately blocked; font fallback возможен. 4 native viewport PNG, [manifest](screenshots-manifest.json). RU390 PNG визуально просмотрен; full visual acceptance не заявлен.

## Ошибки собственной обвязки и ограничения

- Seed attempt1 повторно создавал EDU, которую уже создаёт taxonomy migration; исправлен собственный fixture setup на get_or_create, без сброса DB/потери данных. Raw failure сохранён в ignored scratch; ledger фиксирует exit1.
- Первый browser probe вызвал unavailable URL global в CLI sandbox. Сохранён [attempt1](browser-smoke-attempt1.txt), собственный QA script исправлен, final result отдельно. CLI exit0 сам по себе не доказывает успех: final JSON/страницы проверены.
- Reused venv: Python3.12.3/Django6.0.2/psycopg3.2.10, остальные версии в tools.json. Redis/mysqlclient отсутствуют; profile использует PostgreSQL+LocMem, поэтому startup прошёл. Полная parity с requirements и полный Django/JS corpus NOT RUN. Node20.20.2 доступен; все Node regression dependencies/test suites не проверены.
- Full module01, lifecycle/save/moderation/publication, роли/ACL, concurrency/recovery, полная states×18 cells matrix, остальные modules, real providers/GPS/OAuth/GA/SMTP/IndexNow, devices/screenreader/production NOT RUN. Приложение не исправлялось; historical PASS не подтверждает эти области.

## Сохранность и handoff

10 final checks PASS, input missing0; foreign running container IDs preserved, active_run NONE unchanged. Стенд оставлен запущенным. Собственная browser session закрывается после smoke; чужие сессии не затрагиваются. Нет commit/push/deploy/production, сбросов или чужих остановок.

Для продолжения: [полный ACCEPT-01 prompt](next-prompt.txt). Это следующий отдельный выбранный scope, сейчас не выполняется. При reuse подтвердить HEAD/source/locale gate заново. Для перезапуска только собственного процесса проверить PID и cmdline из server.json, завершить только его и запустить `.venv/bin/python docs/qa/start-local-2026-10-12-r1/runtime.py serve`; не запускать bootstrap повторно и не reseed существующую DB. Credentials остаются в scratch; не переносить в Git.

Документация Django6.0 для settings initialization/LocMem/email проверена через Context7: https://docs.djangoproject.com/en/6.0/topics/settings/ и https://docs.djangoproject.com/en/6.0/topics/email/ .
