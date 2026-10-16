# Module02 / ORG-QA-01 — fresh local recheck

## 1. Решение и scope

2026-10-12: **ORG-QA-01 CONFIRMED OPEN; IMPLEMENTATION PLAN READY**. Приложение не исправлялось. Начат первый scope module02 по `module01-full-2026-10-12-r6/next-prompt.txt`; остальные findings не проверялись и не закрывались. ACCEPT-02 NOT RUN.

## 2. Checkout и сохранность

Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE сохранён в [entry.json](entry.json), active_run NONE. Все2794 source hashes неизменны;693 файлов предыдущих r6/QA14-close evidence сохранены. Все8 прежних QA runtime PID живы и соответствуют своим launcher: [preservation.json](preservation.json). Git/production действия не выполнялись.

## 3. Источники и архитектура

Прочитаны AGENTS и canonical README/registry/orchestrator/architecture/source-of-truth/audit-contract. Проверены текущие controller `_detail_context`, template edit form, native autosave JS, ServerDraft/service CAS и volunteer moderator route. Историческое finding используется как гипотеза, свежий browser/readback — доказательство.

Graph актуального проекта `home-ramin-kidsmap` (исторический `C-kidsmap` на этом ПК отсутствует): index ready, metadata/hash match, generation2026-10-12T12:35:02Z. Частичное template coverage компенсировано чтением фактической формы около528. Graph не доказательство полноты, его cache не экспортировался.

## 4. Свой LOCAL runtime и locales

Собственный `runtime.py`, loopback `http://127.0.0.1:37753`, PID939714, DB`orgqa01_20261012_r1` / test DB`test_orgqa01_20261012_r1`; PostgreSQL17.10 на127.0.0.1:52523 в уже своём `start-local-2026-10-12-r1-pg`. Новая DB клонирована только из своего fictional QA12 профиля. Новая организация создана native UI, ORM переходов не было. Старые DB/процессы не изменены.

DJANGO_TESTING=1; отдельные cache/media/private-media/email/session cookie/browser profile. Checkout .env не загружался, production credentials не использовались. Secrets только ignored `.tmp`, не в отчёте. Browser route блокирует внешние origins; Python socket guard разрешает собственный PG (это не системный firewall).

Fresh RU/AZ/EN native msgfmt build+verify exit0, единственный LOCALE_PATHS до django.setup; общий MO не изменялся. [locale-manifest.json](locale-manifest.json), [runtime-version.json](runtime-version.json): entry/startup/disk совпали, [tools.json](tools.json): Python3.12.3, Node20.20.2, Playwright CLI0.1.17, msgfmt0.21.

## 5. Воспроизведение

Native owner create org3 → working autosave(base1) → submit revision6 → native moderator approve → published content_version2. Свежая форма:sourceVersion2, draftUUID`b04a04b7-3607-4b7e-9a69-6df9165290e1`, draftVersion1; серверный draft.source_version1.

Новое EN edit вызывает POST `/ru/api/drafts/` HTTP409. Same-tab reload показывает новый ввод из sessionStorage. Независимый owner context показывает только ранее одобренное EN: новое не сохранилось на сервере. Повтор наRU390 даёт тот же409 и видимый текст конфликта. [01-create-submit.result.json](01-create-submit.result.json), [02-approve-edit.result.json](02-approve-edit.result.json), [03-mobile-conflict.result.json](03-mobile-conflict.result.json).

Базовые7 browser assertions:4PASS,3FAIL (desktop autosave, independent persistence, mobile autosave). Повторный mobile screenshot run — отдельная попытка того же assertion, не увеличивает число уникальных проверок. Browser CLI exits0 означают исполнение harness, **не PASS поведения**.

Readback обеих стадий только READ ONLY +10s statement/2s lock timeout: [readback-before-approve.json](readback-before-approve.json), [readback-after-conflict.json](readback-after-conflict.json). После409 live и старый draft неизменны: дефект привязки, CAS работает правильно.

## 6. Причина и предлагаемый scope

`_detail_context` выбирает последний actor/target draft без фильтра текущей базы/schema. Несовпадение версии предотвращает overlay fields, но сам stale draft всё равно попадает в template. JS отправляет его UUID вместе с новой sourceVersion; service корректно отказывает.

[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md): актуальный draft либо новый, защита приоритета более свежего candidate, небольшой regression набор; один application controller и один новый test file. Шаблон/API/CAS/ACL менять не требуется. Реализация ожидает одобрения этого конкретного документа.

## 7. Точечная baseline проверка и команды

[commands.jsonl](commands.jsonl) — точные команды/exits/results. Build/verify/check exit0; native drivers exit0 с указанными FAIL. Четыре существующих targeted Django tests exit0,4/4PASS: working draft reload/live unchanged; candidate/live/stale save; foreign organization actor; existing draft stale conflict. [targeted-baseline-tests.txt](targeted-baseline-tests.txt). Новый regression approve→fresh autosave ещё NOT RUN, будет RED перед patch.

## 8. Environment и QA harness ограничения

Pageerror0. External Google fonts намеренно блокированы (`net::ERR_FAILED`) — environment limitation; local409 — подтверждённый application finding. Изолированный `STATIC_ROOT` ещё не собран: Django warning, tests используют текущий source/runserver static, этот warning не причина409. Первый preservation helper ожидал nested hashes, получил flat map и завершилсяexit1; helper исправлен и повторный aggregate readback завершилсяexit0. App source не изменялся.

Начальный mobile PNG обрезал строку статуса; новый retained attempt прокрутил к visible conflict. Оба evidence сохранены, [png-manifest.json](png-manifest.json) перечисляет все PNG с SHA256.

## 9. NOT RUN и handoff

NOT RUN: реализация, новый regression RED/GREEN, AZ/EN и полная матрица ширин/keyboard/true race этого repair, full module02 ACCEPT-02, другие findings, external integrations, production. Module01 прежняя LOCAL acceptance остаётся исторически привязанной к r6; здесь его полный suite не повторялся.

Следующий шаг — одобрение [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) только ORG-QA-01; [next-prompt.txt](next-prompt.txt). После ремонта остальные задачи module02 остаются отдельными PLAN; full ACCEPT-02 после завершения модуля.
