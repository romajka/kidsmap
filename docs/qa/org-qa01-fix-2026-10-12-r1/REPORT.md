# Module02 / ORG-QA-01 — local scoped repair and acceptance

## 1. Решение и авторизация

2026-10-12: **ORG-QA-01 LOCAL SCOPED ACCEPTED**. После одобрения организации новая форма использует черновик актуальной базы либо создаёт новый; автосохранение восстанавливается в независимой сессии. Старые draft rows и защита CAS/ACL сохранены. Более новый submitted candidate не скрывается старым рабочим draft.

Одобрен только [конкретный план](../org-qa01-recheck-2026-10-12-r1/IMPLEMENTATION_PLAN.md), прямой ответ пользователя «дальше» на предъявленный план/вопрос одобрения; [authorization.json](authorization.json). Другие ORG/NETWORK ID не реализовывались. **Module02 IN PROGRESS; full ACCEPT-02 NOT RUN.**

## 2. Checkout, WORKTREE и сохранность

Checkout `/home/ramin/kidsmap`, HEAD`e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch`task33-progress`, active_run NONE. Входящий dirty/untracked snapshot — [entry.json](entry.json). Исходные изменения Place/UI/tests сохранены; application provenance показывает ровно два изменённых/новых файла в этом run. Существующие assertions не менялись.

739 файлов предыдущих r6/QA14-close/ORG recheck evidence byte-identical. Девять старых QA PID живы с прежними runtime paths; старые stand DB/cache/media/browser sessions не присваивались и не останавливались. [final-verification.json](final-verification.json). После source patch прежние runtime нельзя считать свежей проверкой организации; их исторические отчёты сохранены.

## 3. Причина и минимальный diff

Историческая гипотеза подтверждена свежим [recheck](../org-qa01-recheck-2026-10-12-r1/REPORT.md): content_version2 получает draft.source_version1; autosave409, same-tab sessionStorage маскирует отсутствие серверного сохранения.

`src/catalog/controllers/organization_workspace.py::_detail_context`: добавлены фильтры actor/target/current content_version/current schema до выбора последнего draft. Отсутствует подходящая запись → существующий template выводит draft_id empty/version0, неизменённый API создаёт актуальный draft. Overlay старого working copy запрещён, если active candidate новее него (`updated_at > saved_at`); актуальный более новый working copy показывается как прежде. `current=1` продолжает запрещать overlay.

Новый `src/catalog/testcases/test_org_qa01_autosave_base.py` содержит7 поведенческих regression tests. [APPLICATION_DIFF.patch](APPLICATION_DIFF.patch). Template/JS/API/service CAS/publication/ACL/PO/schema/migrations не изменены. Review выполнен последовательно ведущим агентом; независимая делегация не заявляется.

## 4. Собственный runtime и локализация

Loopback URL`http://127.0.0.1:43009`, PID980403, DB`orgqa01fix_20261012_r1`, test DB`test_orgqa01fix_20261012_r1`. PostgreSQL17.10 в своём `start-local-2026-10-12-r1-pg`, explicit127.0.0.1:52523. Новая DB клонирована только из своей fictional QA12 DB; шесть организаций для acceptance созданы native UI. Старые базы не редактировались.

DJANGO_TESTING=1, собственные cache location/media/private-media/email/browser session/HTTP profile; .env не загружался, production credentials не использовались. Ignored `.tmp/<run>/credentials.json` mode600, только собственные вымышленные QA credentials. Browser блокирует external origins; Python socket guard разрешает собственный PG, это не OS firewall.

Fresh native msgfmt RU/AZ/EN build+verify exit0; единственный LOCALE_PATHS до django.setup; общий MO не перезаписывался. [locale-manifest.json](locale-manifest.json). Python3.12.3 / Node20.20.2 / Playwright CLI0.1.17 / GNU msgfmt0.21 — существующий runtime предыдущего recheck; новых установок не было.

[runtime-version-final.json](runtime-version-final.json): PID, TESTING и entry/startup/disk source match. Каждая native case дополнительно сверяет реальный imported controller path/hash по READ ONLY helper. Воспроизводимый запуск/reuse собственного профиля:

```text
.venv/bin/python docs/qa/org-qa01-fix-2026-10-12-r1/start-server.py
```

Этот helper не останавливает другие процессы. Если source changed после acceptance, старый процесс нельзя объявлять актуальным.

## 5. RED → GREEN, целевые tests и discovery

Все точные команды/exits сохранены в [commands.jsonl](commands.jsonl).

1. До patch новый regression набор:7 tests,4FAIL/3PASS, exit1. Четыре отказа показывают409 после approve, игнорирование подходящего draft из-за более позднего obsolete, binding несовместимой schema, перекрытие нового submitted candidate старым draft. Три отрицательных CAS/ACL проверки уже PASS. [regression-red.txt](regression-red.txt).
2. После patch явный targeted набор обнаружил44 tests. Все7 новых regression и31 существующая проверка прошли;6 существующих CSRF test cases дали8 failures с учётом трёх языковых subtests — environment profile failure. Они вручную ставят literal cookie`csrftoken`, тогда как own QA profile применяет уникальное CSRF cookie name. [targeted-green.txt](targeted-green.txt) сохранён как **первый неуспешный запуск**, не переписан в PASS.
3. Только own test-process settings используют стандартный cookie name; browser-process по-прежнему имеет уникальный. Assertions и application CSRF не менялись. Повтор только этих6 tests:6PASS, exit0. [csrf-profile-corrected-tests.txt](csrf-profile-corrected-tests.txt).

Итого **44 уникальных целевых tests подтверждены PASS в двух запусках:38 +6**, не единым чистым full run. Состав:7 новых; organization workspace; shared server drafts; organization editor errors;2 конкретных publication contracts. [targeted-discovery.json](targeted-discovery.json) содержит все44 уникальных ID. No-label tests и full wrapper не запускались; full project discovery/CROSS-QA-02 не заявляются.

Проверены: approve→fresh autosave201→update200→new Client restore, unchanged live/old draft/candidate; current draft среди более новых incompatible/foreign rows; schema exclusion; newer pending candidate приоритет; true same-version409/submitted_fields/winner retention; obsolete UUID409; outsider403/404. Existing warnings synthetic storage unavailable / malformed image upload — ожидаемые отрицательные тесты, не реальные внешние обращения.

## 6. Native browser acceptance

**96 уникальных assertions PASS,0FAIL, шесть RU/AZ/EN×390/1440 owner/editor cases**, все CLI drivers exit0 и semantic results PASS. [browser-evidence-index.json](browser-evidence-index.json). Административный review выполняется настоящим RU admin UI в каждой case; независимая admin AZ/EN localization matrix не заявляется. Публичное отображение изменяемого EN имени проверено native EN public page для каждой case; это не full public localization audit.

На новых fictional данных каждого case:

- Native organization create→autosave→submit, live остаётся исходным до review.
- Native admin approve, content_version2, stale draft не привязан к форме; fresh autosave201 с локализованным Saved message.
- Reload и независимый owner browser context восстанавливают серверный ввод, без same-tab-only доказательства.
- Native Tab EN field→phone, элемент в viewport и имеет видимые размеры, отдельная фиксация geometry/focus.
- Два независимых редактора на одинаковой версии: первый200, второй409, losing input сохранён; same-tab recovery и independent winning server value проверены раздельно.
- Public live/candidate остаются прежними до native resubmit→admin approve; public reload показывает новый EN, content_version3.

Изменения/одобрение не выполнялись ORM. Fixture proof helper только READ ONLY transaction,10s statement/2s lock timeouts; hashes/path/current versions/fictional fields записаны в case result. [png-manifest.json](png-manifest.json):42 native PNG с SHA256; визуально просмотрены RU mobile saved, AZ desktop saved, EN mobile conflict.

## 7. Console/network, environment и harness

Pageerror0. В каждой case ровно один ожидаемый local409 при реальной конкуренции; других localHTTP≥400 не обнаружено. Google font requests намеренно блокированы (`net::ERR_FAILED`); они объясняют console environment errors и не скрываются как zero-console. Внешние SDK/integrations NOT RUN.

Первый own server launch использовал `.resolve()` на symlink `.venv/bin/python` и попал в системный Python без Django: launch exit1, браузер получил connection refused. Launcher исправлен только внутри собственного QA run: сохраняет путь virtualenv executable. Текущий PID/source match подтверждён. Другие процессы не перезапускались.

RED имел warning отсутствующего собственного STATIC_ROOT; затем создан пустой own каталог. Browser использует source static через локальный runserver, collectstatic не заявляется. Эти environment/harness ошибки не исправлялись изменением приложения или существующих tests.

## 8. Завершающие проверки и ограничения

[verify-evidence.py](verify-evidence.py), exit0: source scope ровно controller/new test; предыдущие evidence сохранены; старые9 процессов живы; current runtime match; native96PASS/42PNG; guide88 copy blocks; active_run NONE; HEAD/branch прежние; `git diff --check` exit0.

NOT RUN: полная ACCEPT-02, widths360/768/1024/1280 и независимая admin locale matrix; остальные module02 findings; общий project/module01 повтор; production; commit/push/deploy; external integrations. Исторический PASS/module01 r6 не превращён в свежий global/production PASS. Данное закрытие относится только к проверенному ORG-QA-01 scope.

## 9. Handoff

Текущая строка guide обновлена со ссылкой на этот отчёт; старый recheck/план/исходные module02/module13 findings сохранены. Следующий отдельный scope — **PLAN NETWORK-GRANT-UI (ORG-QA-02 = ACCESS-QA-03)**: список сотрудников сети и штатный отзыв доступа. [next-prompt.txt](next-prompt.txt) содержит конкретный следующий PLAN, application patch только после его согласования. Здесь он не запускался.

После завершения остальных scopes модуля — ACCEPT-02 из guide. Повторный ACCEPT-01 не нужен для этой backend-only organization правки; нет оснований повторять полный неизменённый corpus на каждом repair.
