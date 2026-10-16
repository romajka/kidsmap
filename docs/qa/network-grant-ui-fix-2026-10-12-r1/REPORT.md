# NETWORK-GRANT-UI: LOCAL scoped acceptance

Закрытие отчёта: 2026-10-13 (Asia/Baku). Execution identity: root, роль kidsmap-orchestrator, определение `.agents/agents/kidsmap-orchestrator/agent.md`. Работа выполнена последовательно; независимый review не заявляется.

## 1. Состояние области

**ORG-QA-02 = ACCESS-QA-03: LOCAL SCOPED ACCEPTED**, одна общая причина. Владелец теперь обновляет список сотрудников, меняет роль, отзывает сетевой доступ и отменяет ожидающее приглашение через кабинет. Полная ACCEPT-02: **NOT RUN**.

Авторизация: [конкретный план](../network-grant-ui-recheck-2026-10-12-r1/IMPLEMENTATION_PLAN.md), подтверждённый ответом пользователя «дальше» на предъявленный план; запись [authorization.json](authorization.json). Исторический PLAN READY и recheck сохранены.

Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, `active_run: NONE`. Входной полный список dirty и хеши: [entry.json](entry.json); текущая сверка: [final-verification.json](final-verification.json). HEAD и active_run не изменялись. Production не проверялся.

Первопричина: существующие серверные операции не имели доступных владельцу controls и согласованного обновления списка. Минимальный diff использует существующие API/ACL/CAS, без изменений services, моделей и схемы.

Изменены только пять application/test файлов:

- `src/catalog/controllers/organization_workspace.py`: current status и роли для отображения; предыдущая логика ORG-QA-01 сохранена побайтно.
- `src/catalog/templates/pages/organization_workspace.html`: owner-only формы роли, отзыва и отмены приглашения, стабильные fragments/status/refresh.
- `static/js/organization_workspace.js`: JSON/CSRF transport, expected_version, подтверждения, обновление двух fragments, focus и честные error/conflict/uncertain состояния; RU/AZ/EN copy.
- `static/css/pages/organization_workspace.css`: перенос controls/длинного имени и видимый фокус.
- `src/catalog/testcases/test_network_grant_ui.py`: 9 новых regression tests поведения и прав.

Reviewable diff: [APPLICATION_DIFF.patch](APPLICATION_DIFF.patch), controller относительно entry, чтобы не приписывать этому scope предыдущий ORG-QA-01.

Runtime во время принятой проверки (сейчас остановлен, см. handoff ниже): `http://127.0.0.1:36677`, PID `1083502`, [server.json](server.json), [runtime-version-final.json](runtime-version-final.json): startup/entry/disk source match. Собственная DB `networkuifix_20261012_r1`, test DB `test_networkuifix_20261012_r1`, PostgreSQL 17.10 в ранее созданном собственном LOCAL контейнере `start-local-2026-10-12-r1-pg`, только loopback `127.0.0.1:52523`. Fictional fixtures, DJANGO_TESTING=1, отдельные cache/media/private-media/email/cookies и browser session `networkuifix-20261012-r1`. Checkout .env и production credentials не загружались. Python 3.12.3, Node 20.20.2, Playwright CLI 0.1.17, msgfmt 0.21.

RU/AZ/EN собраны из текущих PO в `.tmp/network-grant-ui-fix-2026-10-12-r1/locales`, helper build/verify exit 0; единственный LOCALE_PATHS установлен до django.setup. [Locale manifest](locale-manifest.json) содержит source/MO hashes; shared MO/PO не изменены. Fuzzy/untranslated сообщения исходных PO не объявляются исправленными этим scope.

## 2. Сильные стороны и выполненные проверки

[commands.jsonl](commands.jsonl) хранит точные команды, exits и ссылки на результаты. Backend RED: новый файл, 9 tests, 10 failures (включая языковые subtests), 1 error из-за отсутствовавшего presentation metadata; exit 1, [regression-red.txt](regression-red.txt). Это ожидаемый RED до patch, не environment failure. Assertions ради GREEN не менялись.

Один целевой GREEN: **28 tests, 0 failures/errors, exit 0**, 29.048s, [targeted-green.txt](targeted-green.txt). [discovery.json](discovery.json) перечисляет 28 уникальных test IDs: новые 9, invitation transport 5, invitation result 3, ORG-QA-01 7, четыре выбранных GrantTests для ACL/CAS/CSRF/replay/cache. Только test process использовал стандартное имя csrftoken для существующих tests; browser cookie остаётся уникальным.

Browser evidence: [browser-evidence-index.json](browser-evidence-index.json), **217 принятых assertions**:

- 108: RU/AZ/EN ×390/1440, native invite → inbox accept → refresh → role change → stale second-tab conflict → revoke → reload; pending cancel → stale recipient accept. Сохранность editor input, candidate/live/ownership, direct Place grant и выбранного scope.
- 79: layout/keyboard/confirmation и accept-versus-cancel race; RU/AZ/EN ×360/390/768/1024/1280/1440. RU включает явно SIMULATED потерю ответа после committed POST и отказ GET после успешного POST, затем ручное восстановление списка без автоматического повторения mutation.
- 12: явно SIMULATED 403/404 для проверки отображения ошибки на трёх языках; DB не меняется. Это проверка UI, не самостоятельное доказательство server ACL.
- 18: свежая усиленная проверка переноса длинного имени после последней CSS-правки, все языки/ширины.

Первые 199 assertions выполнены до последнего CSS-only изменения. Их применимость подтверждена [css-forward-provenance.json](css-forward-provenance.json): Python/HTML/JS не менялись. После CSS повторена только соответствующая матрица 18. Это не единый повторный прогон всех 217 на последнем CSS.

Фактический запрет отозванному участнику на editor проявляется redirect на dashboard с финальным HTTP200; доказательство учитывает URL и состояние, не ошибочно называет его 404. Direct Place доступ сохраняется. Реальные server ACL/guessed nested IDs/CAS подтверждены целевыми tests; ORM использовался для fictional fixture setup и readback, не для проверяемых пользовательских переходов. Readback отмечен READ ONLY с timeout в QA profile.

[PNG manifest](png-manifest.json): 142 файла с hashes, включая RED/промежуточные попытки; 106 уникальных PNG относятся к принятым rows. Screenshot count не равен числу assertions.

## 3. Реальные проблемы и их устранение

Длинное имя в подтверждении визуально обрезалось. Первый слабый gate (18 PASS в `text-overflow.result.json`) проверял недостаточную геометрию и **не принят** как доказательство. Усиленная проверка parent/viewport дала 18 FAIL в `text-overflow.result.attempt1791813102.json`. Добавлен `overflow-wrap: anywhere` к тексту подтверждения; свежий `text-overflow.result.attempt1791813233.json` дал 18 PASS, PNG проверены визуально.

Попытка `text-overflow.result.attempt1791813171.json` попала на перезапуск собственного runtime и получила connection refused; это environment/harness failure, не PASS. Сохранена без подмены. Остановлен только собственный старый PID1047779 после сверки cmdline, данные в `server-before-css.json`; новый PID1083502.

Page errors: 0. Console/network не объявляются пустыми: ожидаемые локальные 409/403, SIMULATED 403/404/ERR_FAILED, заблокированные внешние Google Fonts и unpkg Leaflet 1.9.4. Первоначальная финальная классификация не учитывала blocked Leaflet; allowlist исправлен на точные внешние пути. Внешние SDK не принимались.

## 4. Tech debt

Использован существующий способ RU/AZ/EN copy в SSR/JS. Глобальная унификация переводов вне scope. Список получает authoritative fragments через существующую workspace страницу; отдельный API не вводился.

## 5. Risks и сохранность

Сверка подтверждает: чужие application changes и assertions сохранены; 874 прежних evidence files побайтно неизменны; на момент принятой проверки 11 предыдущих стендов были живы и соответствовали своим runtime paths; текущий статус указан ниже. Проверены exact пять разрешённых source/test файлов, ORG-QA-01 byte preservation, HEAD/branch/active_run, 88 копируемых блоков guide. [Final verification](final-verification.json).

Локальная приёмка не доказывает production. Смена роли использует существующий серверный контракт стандартных permissions; не вводит новую модель прав.

## 6. Dead/legacy candidates

Не исследовались и не удалялись. Исторические recheck/PLAN/RED/промежуточные evidence сохранены.

## 7. Tests gaps / NOT RUN

Полная ACCEPT-02, полный проектный discovery/test corpus, остальные findings, production, реальные внешние интеграции, commit/push/deploy: **NOT RUN**. Recipient decline ACCESS-QA-02, leave/reactivate/ownership-transfer UI вне scope. Targeted discovery не закрывает CROSS-QA-02. Независимый specialist review не выполнялся.

## 8. Recommendations / handoff

Следующий конкретный этап — [PLAN ORG-QA-03](next-prompt.txt): свежий recheck переполнения toolbar выбора мест в админке и конкретный план. Автоматически не начат. ACCEPT-02 выполнить после оставшихся задач модуля, согласно выбранному пользователем порядку. В guide обновлён только текущий статус NETWORK-GRANT-UI.

Финальная команда сверки: `.venv/bin/python docs/qa/network-grant-ui-fix-2026-10-12-r1/verify-evidence.py`; она проверяет сохранённые evidence и live source match, выполняет `git diff --check` и `node --check static/js/organization_workspace.js`, без повторного backend/browser набора.

## 9. P0/P1/P2/P3

P2 ORG-QA-02 / ACCESS-QA-03: одна причина, закрыта только LOCAL scoped acceptance выше. Новых подтверждённых P0/P1 в рамках этой работы не заявлено. Общий PASS module02 не выставлен.

### Финальная сверка handoff 2026-10-13

Повтор `verify-evidence.py` завершился exit 1 на live HTTP: connection refused. Все 12 записанных PID, включая наш, сейчас отсутствуют. Причина завершения процессов не установлена; при этой сверке процессы не останавливались и не запускались. Сохранённый `final-verification.json` отражает предыдущую успешную проверку, а не текущую доступность runtime.

Свежая команда `.venv/bin/python docs/qa/network-grant-ui-fix-2026-10-12-r1/verify-handoff.py` — exit 0, [handoff-verification.json](handoff-verification.json): текущие исходники совпадают с принятым snapshot, 874 предыдущих evidence сохранены, все 142 PNG hashes совпадают, 106 принятых PNG, сохранённые 28 backend и 217 browser результатов подтверждены; diff/syntax checks exit 0. Backend/browser повторно не запускались. LIVE runtime verification сейчас BLOCKED; перед новым browser QA нужен собственный проверенный runtime. Это ограничение доступности среды не подменено новым PASS.
