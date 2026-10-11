# Модуль07 — аккаунты, команда, права и приватность

**Аудит завершён; приёмка FAIL: пять подтверждённых P2 и явно перечисленные NOT RUN.** Приложение не исправлялось. Это свежая LOCAL проверка одного модуля; production состояние UNKNOWN.

Дата:2026-10-10, Asia/Baku. Execution identity: один `/root`, последовательно выполняющий обязанности kidsmap-orchestrator/security/backend/frontend/browser; независимые специалисты не запускались. Каноническое определение: `.agents/agents/kidsmap-orchestrator/agent.md`; active registry прочитан. Исторические отчёты использованы только как checklist. Skills: writing-plans, playwright, kidsmap-ui-design, frontend-design, fixing-accessibility, systematic-debugging, verification-before-completion; приложение/правила/assertions не изменялись.

## 1. Состояние области

Фактический checkout **C:\kidsmap**, branch **task33-progress**, HEAD **8d188b316f800fbedf0b1e376905dfd4924cb1b6**. `active_run: NONE` в `docs/task33/implementation-status.md`. WORKTREE уже был dirty: QA-журнал, отчёты01–06 и чужие QA/repair plans. Entry snapshot снят после создания собственного QA-каталога, поэтому также содержит его untracked строку. Application diff отсутствовал. [Snapshot с полным status и2784 source hashes](snapshot.json), [entry preservation6342 файлов](preservation-entry.json), [entry стенды](stands-entry.json). Другие модули/repair scope не выполнялись.

Canonical journal впервые показывал07 NOT RUN после DONE01–06. Выбран07;13 оставлен последним. Из запрошенных обязательных документов ничего не отсутствует: [documents.json](documents.json). Найденный файл всех13 промптов: [module-acceptance-prompts.md](../module-acceptance-prompts.md). Начатые ранее01 проверки не подменяют текущие07 доказательства.

Source research сначала использовал codebase-memory-mcp, project C-kidsmap: ready,115468 nodes/215044 edges,74 partial parses,59 unindexed directories. Точная дата индекса UNKNOWN; graph — hints, не полный/свежий source контракт. Узкие auth/team/ACL/retention edges сверены с текущими source. Ошибочные graph edge совпадения не использованы как доказательства. Graph caches в artifacts не копировались.

Создан **новый** PostgreSQL17-alpine контейнер `kidsmap-module07-20261010-r1`, ID `6ad9a640797f65376743f9532f301bfdcc5ad7117495a8ef0516e9752da6f76c`, loopback55438, собственные `module07`/`test_module07` DB и новый volume.175 существующих migrations применены только там. HTTP **127.0.0.1:8820**, PID **27660**, Python3.12.15/Django6.0.2, runserver без autoreloader. Реальный Chromium153.0.8010.12, собственная Playwright session `module07-r1` (начальный browser PID42512). Собственный ignored `.tmp/module07-20261010-r1`: media/private-media/unit media/email/credentials; LocMem cache и уникальные cookies. [Isolation](isolation.json), [launcher](run.py), [QA settings](qa_settings.py).

`DJANGO_TESTING=1`; launcher удаляет унаследованные credential variables, testing не загружает checkout .env, socket guard блокирует non-loopback; browser abort всех внешних запросов. OAuth/maps/analytics/IndexNow disabled, MD5 hasher только для тестов. Локальный write gate TASK33_R1_WRITE_MODE=all позволяет exercising implemented development transitions; это не утверждение о production gates. Почта перехватывается собственным backend в ignored scratch и используется только в памяти браузерных сценариев. Пароли, коды и подписанные links не сохранены в evidence. PDF bytes вымышленные placeholders; проверялся ACL/consent/download, не PDF viewer или достоверность документа.

Для удаления default policy первоначально inactive (`isolation.json`). Стенд использует существующий `TEST_POLICY` из unchanged deletion tests, ADRP-TEST-01,30 days. Это **SIMULATED retention configuration**; политика/правила приложения не исправлены. Удаление/отмена через actual UI. Финальная обработка двух UI-confirmed собственных fixtures вызвана через canonical `finalize_account_deletion(..., now=scheduled_for+1s)`: **SIMULATED future clock**, без прямого ORM перехода. До дедлайна тот же processor реально вернул skipped без изменений. Natural30-day waiting/backup expiry NOT RUN.

Source identity: digest **933b55c01caf9ab69bce9d81d23b69e87c262ffcf5d192917e8d9272b0f7ee83**. Соответствие runtime WORKTREE проверяется сочетанием startup SHA guard, финального сравнения2784 файлов/новых source paths, PID/command line собственного listener, импортов из C:\kidsmap/src и реального browser UI. `/qa/version/` — echo manifest и отдельно не доказывает loaded code. Использованы существующие `.mo` из WORKTREE, их bytes входят в snapshot; catalog compilation/подмена не выполнялась. [Финальная верификация](verification.json), [её команда/exit](verification-command.json).

Fixtures:18 исходных actors всех требуемых типов +6 зарегистрированных через UI;8 мест (owner/outsider/author/два volunteer/два deletion/branch),1 published organization, seeded employee place and selected-branch grants,2 specialists (proposal author отдельно от verified person),6 private-storage documents с approved/private/consented/unconsented/pending/foreign/identity cases и synthetic legacy media. Initial setup ORM допустим; проверяемые переходы регистрации, consent, команд, удаления выполнены UI или явно названным implemented HTTP/service path. [Fixtures](fixtures.json), [setup](seed.py), [финальный allowlisted synthetic state](state-final.json).

### Выполненные сценарии

В таблице PASS означает только указанную часть/роль/ширину. Полная machine-readable матрица: [matrix.csv](matrix.csv), [matrix.json](matrix.json). HTTP width=N/A не выдаётся за rendered UI. Полный native путь не автоматически переносится на другие widths.

| Сценарий | Роли / языки / ширины | Результат / evidence |
| --- | --- | --- |
| Register → mismatch → native register → wrong code → cooldown → verify/login → profile/avatar save/reload → logout → consumed code denied → reset/new password → reset replay denied → normalized login/safe next → duplicate email |6 новых users, RU/AZ/EN390/1440 |PASS после восстановления mobile QA harness; [auth-flow](auth-flow.result.txt), [mobile completion](auth-resume.result.txt). Другие4 widths: полный transition path NOT RUN; rendered forms covered18. |
| Expired registration challenge, trim/lowercase email, internal/external next, CSRF register/logout, GET logout405, session/remember, unknown-email reset без account enumeration |anonymous/owner, RU/AZ/EN390 и real HTTP |24 PASS: [auth-negative](auth-negative.result.txt). Истечение challenge — SIMULATED initial expired fixture. Natural reset-token expiry NOT RUN. |
| Profile avatar upload/save/reload/remove; native password mismatch/change и сохранение текущей сессии |registered/canceled-own users, RU/AZ/EN390/1440 для initial save;390 для remove/change |PASS: auth-flow + [cancel-recovery](cancel-recovery.result.txt). Изменение profile email и verification lifecycle нового адреса отдельно не выполнялись. |
| Google disabled local error, safe local page |anonymous, RU/AZ/EN ×6 widths |PASS rendered18 + unchanged adapter tests; actual external OAuth NOT RUN. |
| Place invite uppercase email → duplicate/no new row → native inbox accept → editor form → observer role deny → editor restore → native removal |owner/invitee, RU390 |PASS: [team-flow](team-flow.result.txt). Missing recipient native reject: ACCESS-QA-02; real place reject POST200/REJECTED, owner native cancel и canceled replay denial PASS: [team-resume](team-resume.result.txt). |
| Organization native invite selected branch → native accept; role/remove API200, stale version409/no changes |network EN1440, invitee RU390, HTTP widths N/A |PASS executed transitions. Native role/remove/cancel controls отсутствуют: ACCESS-QA-03, NOT RUN операции UI. Org reject/cancel endpoints отдельно NOT RUN. |
| Доступ из открытой формы после place/org revoke; foreign transfer; owner transfer and return; old/new owner edit; stale ownership version |owner/network/employee/outsider, RU390 и HTTP |13 PASS: [access-transitions](access-transitions.result.txt). Native stale save POST save-photos403, name retained, place versions/state unchanged. Transfer через implemented JSON, native transfer screen NOT RUN. |
| CSRF JSON, GET mutation405, nested grant ID другой target, owner-only action grant400, suspended active:true400, admin не получает business team owner rights |owner/network/admin,3 languages, real HTTP |36 PASS, allowlisted domain state before/after identical: [api-contracts](api-contracts.result.txt). |
| Role×place edit×entity, document download×6 fixtures, raw media/private prefix/legacy path и cache headers, forbidden team mutations/no domain effects |anonymous/author/person/owner/network/employee/outsider/volunteer/moderator/reviewer/staff/admin,3 languages |Fresh HTTP ACL matrix PASS после source-backed correction: [acl](acl.result.txt), [admin/volunteer rerun](acl-boundaries.result.txt). Admin canonical editor real200: [final-browser-proof](final-browser-proof.result.txt). Business editor302 denial — intended boundary. |
| Person toggles consent private/public → reload → anonymous download404/200, public HTML only certificate3; no private storage path or identity/private metadata |person/anonymous, RU/AZ/EN390 |9 PASS: [privacy-flow](privacy-flow.result.txt). Identity never public; approved pub flag alone без current-person consent не открывает файл. |
| Request deletion → wrong code/phrase → native confirm → inactive/SCHEDULED → second session invalidation → unsigned status404 → cancel/new code → replay400 → reset/login recovery |9 own fixtures total incl verified person; registered RU/AZ/EN390/1440 +seed RU390/EN1440/person RU390 |Functional PASS: [deletion-flow](deletion-flow.result.txt), [person-deletion](person-deletion.result.txt), [cancel-recovery](cancel-recovery.result.txt). Rendered AZ/EN errors FAIL ACCESS-QA-05; SIMULATED TEST_POLICY. |
| Canonical finalization/deadline/idempotency, ownership unlink/person identity/consent revoke; post-deletion public download deny and retained review access |delete_final/person, future clock; anonymous/author/reviewer/admin3 languages and public UI18 |6 processor invariant PASS: [finalize-owned](finalize-owned.result.json).165 post-deletion observations PASS: [final-browser-proof](final-browser-proof.result.txt). Details of retained emails/docs require policy review below. |
| Base empty/filled/login error/invalid reset/long profile/reset modal/Google error geometry/images/focus; team lists, org/private certificates/conflict; keyboard Space/Enter/Tab/Shift+Tab/Escape |RU/AZ/EN ×360/390/768/1024/1280/1440 |Real Chromium screenshots; FAIL modal focus36, team clipping3, org controls18. [matrix](matrix.result.txt), [supplement](supplement-matrix.result.txt), [modal](modal-proof.result.txt). |
| AJAX network abort / delayed409 / repeat during loading |reset anonymous +org owner,18 combinations |SIMULATED transports, actual client handlers. Reset input preserved/button reenabled18; settled org conflict input preserved18 and one request despite repeat18: [org-conflict-proof](org-conflict-proof.result.txt). |

### Commands, counts и exit codes

Все команды запускались из C:\kidsmap. Credentials выдавались только in-memory из ignored scratch; они отсутствуют в saved executed code.

```powershell
wsl.exe -- docker run -d --name kidsmap-module07-20261010-r1 --publish 127.0.0.1:55438:5432 -e POSTGRES_DB=module07 -e POSTGRES_USER=module07 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/prepare.py
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/run.py serve
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/tests-run.py
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/drive.py auth-flow.js
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/drive.py auth-resume.js
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/finalize-owned.py
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/aggregate.py
.venv/Scripts/python.exe docs/qa/module07-2026-10-10-r1/verify.py
```

Docker/migrate/setup final exit0; seed initial attempt1 была собственной ошибкой поля fixture Specialist и исправлена только в QA harness, без проверяемого перехода ORM. `prepare.py`/seed/serve уже выполнены, **не перезапускать** их на использованном run: они не предназначены для replay истории. Server остаётся активным для просмотра.

Browser открыт командой Node executable `C:/Program Files/nodejs/node.exe`, CLI `C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js`, args `-s=module07-r1 open http://localhost:8820/ru/auth/login/ --config=.tmp/module07-20261010-r1/playwright.json`. `drive.py <script>.js` выполняет real Playwright run-code, хранит sanitized result и native exit, не trace/storage tokens. Exact per-script commands/durations/exits всех19 выбранных browser runs и discovery/retries: [command-ledger.jsonl](command-ledger.jsonl). Browser run-code exit0 **не означает** PASS всех assertions: статусы находятся внутри результатов.

13 unchanged targeted Django suites:282 methods, **281 PASS,1 native preflight FAIL,0 ERROR**, exit1,115.160s. Список suites/точная subprocess команда: [tests-command.json](tests-command.json), [fresh output](tests.log). Единственный fail — `SpecialistTransferReconciliationTests.test_duplicate_names_legacy_business_link_and_private_online_offices_survive`: guard `test_task33_specialist_db_review.py:18` требует `TASK33_QA_ROOT` с Unix prefix `/tmp/kidsmap-task33-qa04-`. На Windows собственного disposable stand этот preflight не выполнен; тело reconciliation NOT RUN. Это **environment/portability failure до application assertions**, не доказанный application regression. Путь не spoofed, guards/assertions не ослаблялись. Отдельной полной JS logic suite аккаунтов в найденных текущих файлах нет; собственные QA JS проверены синтаксически, browser проверки не заменены jsdom.

Selected observations: **2404 PASS /66 FAIL /1 NOT RUN**,2471 строк; это наблюдения, не2471 независимый end-to-end тест.66 FAIL относятся к пяти findings. Отдельно90 явных scope NOT RUN rows; [results-summary.json](results-summary.json), [coverage-gaps.json](coverage-gaps.json).204 собственных superseded/harness observations исключены из решения с сохранением raw outputs: [excluded-observations.json](excluded-observations.json). Native **695 PNG**, включая diagnostic attempts,12 DERIVED contact sheets; [SHA256/dimensions manifest](screenshots-manifest.json). Повторные captures одного state имени относятся к последнему fresh attempt; raw прежних QA ожиданий не используются как финальные assertions.

Visual review: просмотрены contact sheets login/register/settings/reset modal/deletion и originals PC/mobile/error/team/organization/denied save. Полные PNG сохранены; contact sheets не заменяют исходные изображения. Basic layout большинства auth/account states помещается; body overflow check сам по себе недостаточен (ACCESS-QA-04). External fonts blocked: base diagnostics126 `net::ERR_FAILED` именно fonts.googleapis.com, SIMULATED transport/fallback font. Supplement pageerrors0; локальных requestfailed0. Console error при deliberate AJAX abort/HTTP409 — ожидаемое воспроизведение; browser error counters и URLs находятся в raw diagnostics. Никакого стороннего OAuth/SMTP/SDK обращения для интеграционной проверки не было.

## 2. Сильные стороны

Нормализация email и consumed verification/reset token не создают новую сессию повторно. CSRF и POST-only доказаны HTTP отказами; unknown reset не раскрывает наличие пользователя. Native profile/avatar сохранение переживает reload. Открытая employee вкладка после revoke не сохраняет изменения и сохраняет ввод. Business permissions учитывают текущие grant/owner versions: platform admin не получает owner-only team права автоматически. Author proposal и verified person разделены: автор не читает private docs, reviewer имеет отдельное право. Download attachment имеет private/no-store и nosniff; raw private/legacy media404. Native consent/reload и account/person unlink закрывают публичное скачивание. Эти выводы ограничены fixtures и выполненными строками матрицы.

## 3. Реальные проблемы

Все доказательства, роль/URL/шаги/ожидание/факт/source/область/зависимости/priority и самостоятельные промпты находятся в [FINDINGS.md](FINDINGS.md).

| ID | Приоритет | Подтверждённый эффект |
| --- | --- | --- |
| ACCESS-QA-01 | P2 | Tab выходит из reset modal, Escape не возвращает opener;18 combinations. |
| ACCESS-QA-02 | P2 | Inbox не даёт native отказ от приглашения места/сети. Place HTTP reject работает. |
| ACCESS-QA-03 | P2 | Network cabinet не даёт role/remove/cancel controls; API role/remove/conflict работает. |
| ACCESS-QA-04 | P2 | Invitation cards идут до x380.1875 при360px, email обрезан на всех3 languages. |
| ACCESS-QA-05 | P2 | Native deletion code/phrase errors на AZ/EN русские; runtime locale/fuzzy причина. |

Подтверждённой current leak/ACL bypass не найдено в выполненных запросах. Это не общий security PASS проекта. Регрессия относительно отдельного прежнего snapshot не устанавливалась; все пять — fresh observed failures текущего HEAD/WORKTREE. Application baseline test failures не подтверждены; единственная native test failure относится к Windows preflight.

## 4. Tech debt

UI team presentation неполна относительно implemented server contracts. Place legacy native controls не передают пользователю explicit version/conflict experience так же полно, как JSON API; concurrency UX всех вариантов native role forms NOT RUN. Unix-only disposable-root guard затрудняет перенос audits на Windows, но не является разрешением менять assertions ради green.

После SIMULATED финализации person: user/profile/verification/current-person и consent links удалены/отвязаны; place invitation удалена, **organization invitation1, notification emails2 и outbox emails2 остались**, как и6 private document records/files. `specialist_retention.py` прямо сохраняет исторические документы/bytes; после unlink публичные/private author downloads404, reviewer/admin200 с private headers. Не объявляю это leak или автоматически ошибкой удаления: audit/history/document retention policy требует отдельного решения; org invitation на simulated deadline уже старше7-day expiry. Email-history и различие place/org cleanup — manual policy review, не доказанный живой exploit и не отдельный confirmed finding. [Processor aggregate evidence](finalize-owned.result.json).

## 5. Risks

Default inactive retention policy, TEST_POLICY и explicit future clock ограничивают выводы о настоящем внедрении удаления. Actual dispatch cadence/legal hold/backup lifecycle и восстановление инфраструктуры не проверялись. MD5/DEBUG/write gates — только QA setup. Приватный fixture byte content не доказывает проверку реальных документов. Chromium viewport не доказывает touch/Safari/Firefox/screen reader. `.mo` из WORKTREE влияет на язык; будущие locale fixes требуют сверки compiled/runtime catalogs. Production credentials/state не читались.

## 6. Dead/legacy candidates

`owner_*` route names/controller adapters сосуществуют с canonical business-team API и current fresh ACL resolver. Status: legacy compatibility / manual review, **не dead**, без рекомендаций удаления по graph. Synthetic old `/media/protected_docs/specialists/...`404 проверяет containment, не доказывает отсутствие старых реальных файлов. Ничего не удалялось из приложения/DB структуры; только canonical removal/deletion на своих fixtures.

## 7. Tests gaps

Честные NOT RUN: real Google/email/SDK; production; натуральный30-day deadline/backup deletion; real touch/Safari/Firefox/assistive technology; reconciliation body после Windows preflight; native owner-transfer screen и missing team UI controls; org reject/cancel HTTP; full register/delete transition path при360/768/1024/1280; profile email-change verification lifecycle; весь cross product roles×transitions×widths; default inactive deletion-policy UI на этом configured stand; natural password-reset TTL. Полный backend suite проекта не запускался:13 targeted relevant suites, не проектный green. Структурированный scope: [coverage-gaps.json](coverage-gaps.json).

Own QA corrections: hidden desktop logout locator на mobile заменён реальным mobile drawer; hidden reset submit selector ограничен visible auth form; email upper password добавлен только к fixture password для frontend validator; initial seed field mismatch исправлен только в own seed. Admin business edit302 — запрет без business grant, не admin-editor redirect; volunteer doc403 — middleware boundary, не leak. Hidden avatar img src="" не означает visible broken image. Escape измерен после settled transition. Stale place save — AJAX photo-save403, не page navigation. Org409 checked after refresh/finally, не фиксированные350ms. Raw ошибки сохранены и не скрыты: [exclusions](excluded-observations.json), [QA corrections](CORRECTIONS.md). Новые проверки не заменяли существующие assertions.

## 8. Recommendations

Сначала согласовать узкие scopes пяти repair prompts; нынешний запуск заканчивается отчётом. UX управления командами связать с существующим backend, не создавать альтернативную ACL. Исправление локализации делать точечно с isolated runtime catalogs. Затем свежо повторить соответствующие native paths и negative ACL; не считать этот отчёт автоматическим доказательством исправлений.

[01 modal focus](repair-ACCESS-QA-01.txt), [02 recipient decline](repair-ACCESS-QA-02.txt), [03 network team management](repair-ACCESS-QA-03.txt), [04 mobile team clipping](repair-ACCESS-QA-04.txt), [05 deletion localization](repair-ACCESS-QA-05.txt). Отдельно оформить решение retention owner по historical private bytes/email intents и согласовать portable test launcher, сохраняя строгую isolation проверку. При13 свести common locale causes и межмодульные gaps.

Финальная сверка [verification.json](verification.json) фиксирует исходники, HEAD/branch, foreign file hashes, active_run, foreign PIDs/containers, own volume, syntax, links, credential scan и diff-check. Финальная верификация exit0:2784 source files без изменений/добавлений;6341 чужой файл вне журнала byte-identical; active_run NONE; прежние шесть HTTP PID и восемь контейнеров сохранены; links/QA syntax/credential scan/diff-check PASS. Из журнала изменена только строка07 (line27). Собственный стенд оставлен для просмотра; чужие стенды не перезапускались/не закрывались. No commit/push/deploy/production. Следующий модуль08,13 после остальных. [Готовый текст следующего чата](next-chat.txt).

## 9. P0/P1/P2/P3

P0:0; P1:0; **P2:5**; P3:0 confirmed findings. Внедрение ремонта не выполнено. Итог **FAIL**, audit DONE с ограничениями; общий PASS проекта не заявляется. Недоступные проверки остаются NOT RUN.
