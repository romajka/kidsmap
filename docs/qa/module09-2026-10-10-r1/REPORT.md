# Модуль09 — отзывы, избранное и уведомления: FAIL

Дата/run:2026-10-10 / module09-2026-10-10-r1; итог сформирован 2026-10-10T14:27:04.054252+00:00. AUDIT ONLY, один модуль. Lead /root последовательно выполнял canonical kidsmap-orchestrator, django-reviewer, frontend-reviewer/browser-qa и bounded seo-reviewer для query redirect; независимые subagents не запускались. Definitions — `.agents/agents/<role>/agent.md`, registry.active. Приложение/правила/миграции/существующие assertions не менялись. Production/commit/push/deploy NOT RUN.

## 1. Состояние области

Фактический checkout **C:/kidsmap**, branch **task33-progress**, HEAD **8d188b316f800fbedf0b1e376905dfd4924cb1b6**. Входной WORKTREE содержит QA/docs прежних запусков и изменённый module journal; application source не dirty относительно HEAD. `active_run: NONE` сохранён. [Snapshot](snapshot.json), [source/runtime/preservation verification](verification.json), [runtime](runtime-final.json), [isolation](isolation.json), [documents](documents.json): требуемые пользовательские документы присутствуют, missing=[]; старые отчёты использованы только как checklist/дедупликация.

Новый PostgreSQL17.11: `kidsmap-module09-20261010-r1`, loopback55440, DB module09/test_module09; HTTP `http://localhost:8822`, PID32520. Python3.12.15, Django6.0.2, Chromium153.0.8010.12 headless shell1243/session module09-r1. Отдельные LocMem cache/email, media/private-media, session/CSRF cookies; inherited credential prefixes очищены, .env не загружается в TESTING, server socket guard и browser route blocker запрещают внешний transport. Fictional users `example.invalid`, test content/photos only. SMTP/Google/SDK/CDN реальные интеграции не выполнялись.

Runtime запускается из WORKTREE с startup SHA guard для2784 source/static/config/locale/template файлов, без autoreloader. Повторная сверка текущего manifest и listener PID подтверждает соответствие. `/qa/version/` сам по себе возвращает manifest, не независимую аттестацию; доказательство включает startup guard/current hashes/PID. Existing `.mo` использованы как есть; compilemessages не запускался. Source digest `933b55c01caf9ab69bce9d81d23b69e87c262ffcf5d192917e8d9272b0f7ee83`. Production revision/build UNKNOWN.

AS-IS: typed reviews Place/Specialist/Activity/Event имеют head/current/candidate/revisions; SiteReview — отдельные записи/обычный admin change form. Business replies/reports проверяют object-specific actions; business owner Specialist не равен verified person, Event owner без lawful organizer не даёт rights. Favorites — зарегистрированным пользователям, hidden карточки фильтруются. Inbox — список последних100 notices, POST read/accept и recipient-current-email ACL; dedicated unread badge/popup в этом контракте не реализован.

## 2. Сильные стороны

Настоящие UI create/required fields→pending→reload→approve/reject→public→edit→candidate/live→approve выполнены для4typed targets; Specialist дополнительно2tabs409→reject with reason→correct/resubmit→approve. Server state сравнивался read-only в отдельной QA-only `/qa/state/` transaction с10s statement/2s lock timeout. Candidate edits не меняют live/count до решения, после approval count остаётся1 и rating обновляется. Реакции helpful/unhelpful, повтор и reload подтверждены сохранёнными counters для4типов и сайта; stale typed reaction получает409, self/unauthorized response —403. Ответы места/занятия native, verified person/explicit employee grant/valid organizer positive cases native; приватные reports сохранены и не публичны.

SiteReview native create→admin rejected→approved→hidden(pending)→approved с public checks. Входная rating по умолчанию5; пустую оценку через эту UI не заявляем. Нативное редактирование SiteReview автором не поддержано; отсутствие функции не classified defect. Один дополнительный SiteReview pending создан валидной UI отправкой в диагностическом readback; он сохранён, не очищался ORM. Это не ошибочный PASS required-rating.

Favorite native add/double click создаёт1row; filled list/reload/logout/login сохранены, remove подтверждён. Initial saved likes hidden/draft/inactive/archived/deleted карточек не раскрывают контент. Filled favorites дополнительно18cells. Read/read-repeat/reload notices, foreign ID404, native invite→accept→one grant, второйtab/revoked invite403 без лишних grants; nonexistent entity notices не выводят приватные payload/links. Place/org/personal identity verification как продуктовый процесс здесь не повторялась: positive ACL fixture states первоначальны и вымышлены, а проверяемые reply/accept/moderation переходы были через UI/HTTP, не ORM.

Настоящие4public cards дополнительно RU/AZ/EN×390/1440: displayed current text и links к typed workflow подтверждены (24 PASS). User controls Tab/ShiftTab/Enter/Space/Escape, focus-visible, account dropdown Escape, empty/filled/pending/long text/409/loading/network error states проверены по [матрице](matrix.csv). Script/Special HTML осталось текстом, `window.QA09_XSS` не исполнен. Native site pagination page1→2 PASS; global place review pagination — FAIL.

## 3. Реальные проблемы

**9 OPEN SOCIAL-QA:8 P2,1 P3** — [отдельные findings и9 repair-промптов](FINDINGS.md). Основные: потеря выбранного rating после reload; невидимая причина отказа; сырой409 без редактора; неподключённые стили inbox; site768 overflow; недоступное selected state звёзд; Activity object вместо имени; пустая403 после revoked invite;301 сбрасывает законные page/sort.

Shared `MOD-QA-03` admin1024 overflow свежо повторён в3cells этого run; причина уже имеет отдельный ремонтный prompt08, новый duplicate SOCIAL ID не создан. Возможность decline inbox invitation из ACCESS-QA-02 не объявляется новой находкой этого scope; native decline здесь NOT RUN.

## 4. Tech debt

Typed review SSR форма и legacy site/place widgets имеют разные feedback/transport contracts. Unread list/notification presentation не используют подключённый account component CSS. Query allowlist и реальные route consumers расходятся. Это verified bounded source map, без предложения удаления legacy. [Graph summary](graph-summary.json): root/HEAD ready при входе, coverage unavailable/metadata_changed; critical edges verified against source. Поздняя graph search для canonical redirect вернула Transport closed; bounded middleware/public_urls чтение и native301 были fallback, MCP не переустанавливался.

## 5. Risks и классификация

App failures — PRE-EXISTING BASELINE на неизменённом entry source. REGRESSION от изменений этого audit отсутствует в проверенном source manifest; исторический release comparison NOT RUN. P0/P1 не подтверждены.403/409 защищают права и БД, но UI feedback недостаточен; Back восстанавливал конфликтный текст в отдельной проверке, постоянную потерю данных не утверждаем.

ENVIRONMENT FAILURE:10 Django crash methods требуют `guard.socket_path()`, Unix PostgreSQL socket и TASK33_QA_ROOT; Windows/TCP stand не удовлетворяет этому preflight. `ModuleNotFoundError: guard` не app crash, тела10 методов NOT RUN. Не подменяли guard permissive shim и не меняли assertions. External fonts/SDK blocked — SIMULATED/offline integration boundary; local UI CSS/geometry findings подтверждены отдельно.

SIMULATED: browser delayed POST/route.abort для site review и favorite. Все18site cells сохраняют input и честное loading disabled state, не добавляют row; fake external delivery не считается SMTP PASS. Fresh unchanged tests simulate outbox failure/transactional dedupe. [Command ledger](command-ledger.jsonl), [tests log](tests.log), [test command](tests-command.json).

## 6. Dead/legacy candidates

Ничего не удалялось и dead-code findings не делались. Legacy typed admin approve/hide routes intentionally403; VersionedReviewAdminMixin направляет к typed moderation и оставляет fields read-only. SiteReview стандартная форма отличается от этих путей. Legacy published Event без lawful organizer позволяет public review, но не даёт бизнес-ответ; отдельный valid-organizer initial case + native owner reply PASS. Это разные проверенные contracts, не inferred permissions.

## 7. Проверки и пробелы

Неизменённый targeted Django набор: **77 methods:67 PASS,0 assertion FAIL,10 ENVIRONMENT ERROR в setUp**, exit1,29.960s. PostgreSQL concurrency и lifecycle tests среди67 прошли; полный suite NOT RUN. Exact target argv/exit/duration — [tests-command.json](tests-command.json). Перечень10 body NOT RUN — [tests.log](tests.log), отсутствующие environment prerequisites перечислены выше.

Browser observations **3314 PASS / 207 FAIL / 1 NOT RUN**, всего3522; отдельно13 scope NOT RUN. **1515 свежих native PNG** сSHA/dimensions в [manifest](screenshots-manifest.json). Counts — отдельные assertions, не количество независимых сценариев/дефектов. Primary rendered matrix:2991PASS/87FAIL/0NOTRUN; role/language/width/source/url/state разобраны по rows. [Results](results-summary.json), [matrix JSON](matrix.json), [scope gaps](coverage-gaps.json).

19 diagnostic/superseded records явно отделены в [exclusions](excluded-observations.json). Own initial harness failures: bootstrap OLD-path replacement; seed invalid `permissions` kwarg; auth wrong locator; duplicate main; unsupported SiteReview guessed URL; Select2 hidden tab; premature async state read; wrong catalog path; required-rating assumption(default5). Raw attempts/CLI exits сохранены. К выводам приложения не приравнены. Pagination wait timeouts оказались настоящим301 и затем доказаны отдельной18cell matrix. Никакие application assertions не менялись.

NOT RUN: real SMTP/Google/SDK/production, full suite, real screenreader/touch/Safari/Firefox; every mutation×all roles×18cells; all100+notifications/entity types/expiry; dynamic favorite hide/delete transitions; all4remaining widths of embedded public card sections; native typed hide и author site edit отсутствуют в AS-IS. Не называем отсутствующую функцию дефектом без requirement. Для полного списка применимости см. scope gaps и per-cell NOT RUN, не итоговый blanket PASS.

## 8. Recommendations и команды

Исправлять отдельно согласованными scope: сначала rating/rejection/conflict (01–03), inbox CSS/stale feedback(04/08), затем responsive/semantics(05/06), query contract(09, зависимость module11), name presentation(07).9 копируемых prompts находятся в repair-prompts; текущий audit их не применяет.10 environment crash cases запускать в пригодном изолированном Linux/socket runner; [самостоятельный QA environment prompt](repair-prompts/ENV-QA09-crash-runner.txt) не разрешает менять product assertions.

Создание стенда (выполнено): `wsl.exe -- docker run -d --name kidsmap-module09-20261010-r1 -p 127.0.0.1:55440:5432 -e POSTGRES_DB=module09 -e POSTGRES_USER=module09 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine`; exit0. `pg_isready -U module09 -d module09` exit0 до миграций. Только собственные disposable resources.

Launcher: `.venv/Scripts/python.exe docs/qa/module09-2026-10-10-r1/run.py snapshot|migrate|serve` — отдельные фактические invocations, snapshot0/migrate0; serve long-running own process PID32520. Initial fixtures `seed.py` exit0 после сохранённого bootstrap retry; `extra-fixtures.py` и `event-positive-fixture.py` exit0, новые initial cases, не обход проверяемых переходов. All175 migration recorder rows applied own DB. Python scripts tests-run/drive/supplement commands and native CLI exits — ledger/tests-command; последние valid CLI script runs exit0, это не означает все scenario rows PASS. QA helper syntax/secret/link/preservation и `git diff --check` — свежий [verification](verification.json).

Browser opened командой `"C:/Program Files/nodejs/node.exe" "C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js" -s=module09-r1 open http://localhost:8822/qa/version/ --config=C:/kidsmap/.tmp/module09-20261010-r1/playwright.json`; exit0. Каждая проверка запускается `.venv/Scripts/python.exe docs/qa/module09-2026-10-10-r1/drive.py <script.js>`, exact names/results/exits в command ledger; password substituted only in memory, `.effective.js` содержит placeholder. Trace/storageState/password snapshots не сохранялись.

Чужие8HTTP/10Docker stands и8090 входных документов/QA/инструкций проверены по scoped preservation manifest (journal — единственное разрешённое исключение). Чужой active_run/task33 ledger hash неизменён, другие modules/report files не переписаны; итоговый verification конкретизирует PASS/FAIL. Это ограниченный manifest, не утверждение о всех файлах ПК. Stand09 оставлен для review; его DB/sessions не использовать как свежий PASS следующего модуля. Изменена только row09 относительно journal-entry, прежние dirty rows01–08 сохранены.

Следующий модуль **10 «Настройки, разделы и общие страницы»**,13 после остальных. [Готовый текст следующего чата](next-chat.txt); [канонический журнал](../module-acceptance-prompts.md).

## 9. P0/P1/P2/P3

P0/P1 —0 подтверждённых. P2 —8 SOCIAL findings; P3 —1 naming finding. Shared MOD-QA-03 не duplicate. Environment prerequisite10tests не продуктовый дефект, отдельный NOT RUN. Verdict **FAIL**, bounded audit завершён с явно сохранёнными ограничениями; «всё работает» вне перечисленных PASS не заявляется.
