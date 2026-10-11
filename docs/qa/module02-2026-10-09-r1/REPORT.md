# Модуль 02 — Организации, готовые места и сотрудники

2026-10-09 UTC / Asia/Baku; точное время финальной проверки в verification.json. Run `module02-2026-10-09-r1`, AUDIT ONLY. Решение: **FAIL**, аудит завершён в обозначенных границах. Приложение не исправлено. Роли domain/security/integration/browser выполнены последовательно одним `/root`, независимое исполнение специалистами не заявляется. Каноническая роль: `.agents/agents/kidsmap-orchestrator/agent.md`.

Checkout `C:\kidsmap`, branch `task33-progress`, LOCAL HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`. При входе: изменён журнал и untracked пакет module01; во время начального hash capture уже существовал собственный пакет module02. Это **dirty WORKTREE**, не clean HEAD. `active_run=NONE`; файл task33 не изменён. Production не подключалась и не проверялась. Git synchronization/commit/push/deploy не выполнялись в силу текущего ограниченного задания.

Стенд: `http://localhost:8812`, новая WSL Docker PG17 `kidsmap-module02-20261009-r1`, только loopback `55432`, DB `module02`, test DB `test_module02`. Свои cache/media/private-media/session cookies и LocMem mail; DJANGO_TESTING=1; credential environment очищается; socket guard и browser routes ограничивают исходящие запросы. Действующие source hashes и сохранность предыдущих материалов: [snapshot](snapshot.json), [финальная сверка](verification.json). `/qa/version/` + финальное повторное хеширование подтверждают соответствие исходников. Endpoint сам отдаёт первоначальный digest; он не заменяет повторное сравнение файлов.

## 1. Состояние области

Использован существующий контракт: Organization — сеть, Place — отдельная карточка филиала. Business affiliation действует после согласий актуальных владельцев. Informational affiliation отдельно и не выдаёт сетевые права. Preview фиксирует состояние; confirm обрабатывает строки независимо, хранит receipt и идемпотентность. Прямые и сетевые grants различаются; публикация через candidate/review не равна рабочему ServerDraft.

Созданы только вымышленные данные: 7 акторов, 32 исходно самостоятельных места, фотографии собственного изготовления, занятия/группы/тарифы/расписание; новый филиал №33 создан через реальный интерфейс. Organizations 1–4 создавались через UI/канонический API. Подключения, переносы, согласия и grants проверялись реальными transports, не подстановкой FK. Общая программа для проверки detach и истёкшее приглашение — явно отдельные **fixture setup / SIMULATED time**, не UI acceptance их создания. Реальный email не отправлялся.

| Сценарий | Свежий результат и доказательство |
|---|---|
| Организация без филиалов, partial/error/draft/reload/edit, review, публичная версия | [lifecycle](lifecycle.result.txt), [admin UI](admin-flow.result.txt), [published edit / return](published-roundtrip.result.txt), [correction / resubmit / approve](continue-published.result.txt). Серверное autosave после approve FAIL — ORG-QA-01 |
| Поиск готовых карточек по названию и адресу | [bulk](bulk.result.txt), [receipt/search continuation](bulk-finish.result.txt). Видны текущая сеть и состояние |
| Подключение десяти существующих богатых карточек | PASS; IDs 1–10; реальные confirm/receipt; [proof](connection-proof.json), [before](observation-before.json), [after](observation-after-bulk.json). Все сравниваемые rich records/порядок/байты фото совпали |
| Согласия разных владельцев, отказ, отмена устаревшего запроса, повтор после смены владельца | PASS [API/legacy/privacy](api-core.result.txt), [recovery](recovery-lost.result.txt) |
| Новый филиал отдельно от готового места | PASS, ID33, [detach/transfer/branch](detach-transfer.result.txt) |
| Admin выбор → организация → preview → informational confirm → per-card receipt | PASS [admin-flow](admin-flow.result.txt). Администратор не подменяет business consent владельцев |
| Другая сеть, changed-after-preview, mixed batch, двойное подтверждение | PASS canonical results [connection-proof](connection-proof.json): already_connected/other_network/changed/connected/requested; [raw transport](advanced-connections.result.txt) |
| Потеря ответа / повтор с тем же ключом | PASS [receipt/retry](recovery-lost.result.txt). SIMULATED browser delivery loss; серверная операция реальная |
| Отвязка с общей программой, прямыми и сетевыми grants; согласованный перенос A→B | PASS [UI](detach-transfer.result.txt), [database proof](detach-proof.json). Program reference становится локальным snapshot, группы/тарифы/media/владелец/статус сохранены; прямой доступ действует, сетевой к отвязанному месту прекращается |
| Приглашение, описание роли/scope, pending без доступа, реальное принятие | PASS [team UI](team.result.txt); raw reset assertion исправлен по фактическому начальному EDITOR: [team-api](team-api.result.txt) |
| Отказ/отмена/истечение, отзыв активного сетевого grant и доступ после отзыва | API PASS [team-api](team-api.result.txt), [revoke result](final-access.result.txt), [corrected supported-route proof](access-proof.result.txt), [informational scope / accept / revoke](informational-access.result.txt); доступ по прямому grant сохранён. Owner UI revoke FAIL — ORG-QA-02 |
| Legacy endpoints, CSRF, guessed private place, недостаточные права, receipt другого актора, no-JS | PASS [api-core](api-core.result.txt), [nojs-security](nojs-security.result.txt). Private ID не даёт metadata/access |

288 свежих rendered states (261 PASS / 27 FAIL), 308 PNG. Матрица с языком/шириной/ролью/сценой/HTTP/geometry/status: [matrix.csv](matrix.csv), [raw](visual-matrix.result.txt). RU/AZ/EN ×360/390/768/1024/1280/1440; owner, guest, moderator/admin. Скриншоты настоящего Chromium: [manifest](screenshots-manifest.json), [contact sheets](contact-sheets/), [visual review](visual-review.md). Статус геометрии не является функциональным PASS всех операций на каждой комбинации. Изменяющие бизнес-сценарии выполнялись главным образом RU; переводы AZ/EN прошли rendered coverage, не все повторные mutation flows.

## 2. Сильные стороны

Сохранность десяти карточек доказана сравнением записей и SHA файлов. Частичные результаты не откатывают успешные строки и не переподключают конфликтующие места. Повтор receipt/confirm не создаёт дубликаты. Старое согласие после смены владельца отклоняется; восстановление запросов позволяет отменить и запросить новое согласие. Отвязка показывает последствия и сохраняет независимый прямой доступ. GET/CSRF guards работают. Admin labels переводятся в текущем процессе; API и UI не подменяются ORM-сценарием.

## 3. Реальные проблемы

- [ORG-QA-01 / P2](findings/ORG-QA-01.md): устаревший ServerDraft после approval вызывает HTTP409 вместо свежего серверного autosave; независимая сессия не восстанавливает изменение.
- [ORG-QA-02 / P2](findings/ORG-QA-02.md): кабинет владельца не предлагает отзыв активного сетевого доступа и отмену pending приглашения, хотя APIs поддерживают эти действия.
- [ORG-QA-03 / P2](findings/ORG-QA-03.md): toolbar административного выбора карточек переполняет документ на1024px на трёх языках.
- [ORG-QA-04 / P3](findings/ORG-QA-04.md): часть заголовков admin организации остаётся русской наAZ/EN при корректных переведённых labels полей.

Подтверждённые визуальные findings и ограничения указаны в visual-review; недоказанные геометрические кандидаты не превращены автоматически в дефекты. Regression по сравнению с предыдущим релизом не установлена. Старые отчёты не использованы как свежие доказательства.

## 4. Tech debt

Параллельное существование ServerDraft и submitted candidate требует явного выбора актуальной базы. Поддержанные team endpoints опережают доступный UI. Локальный native test contract hardcode `csrftoken` требует настройки собственного test process. Репозиторные ignored `.mo` от прежнего локального окружения отставали от `.po`; в собственном стенде переводы пересобраны в ignored scratch, исходные `.mo` не затронуты.

## 5. Risks

Для ORG-QA-01 same-tab browser recovery маскирует отсутствие серверного сохранения. Отсутствие revoke UI оставляет владельцу практическую зависимость от администратора/API. Внешние assets блокировались в test contexts; визуал внешнего font/SDK не подтверждается. No production impact/эксплуатация не заявляются.

## 6. Dead/legacy candidates

Legacy attach/detach transports существуют и свежо проверены: прямой detach требует review/confirmation (API409/HTMLredirect), private draft не раскрывается. Это поддержанные совместимые пути, не основания для удаления. Codebase-memory `C-kidsmap` ready, partial parses74, skipped0; сервер не сообщал время индексации. Graph использован как исследовательская подсказка; важные edges сверены с source. Полного dead-code/database audit не выполнялось.

## 7. Tests gaps

**216 существующих профильных Django tests — OK, exit0**, [test.log](test.log), [exact argv/native exits](setup-ledger.jsonl). Набор охватывает ownership/permissions/connections/concurrency/workspace/privacy/recovery/detach/create/editor/errors/copy/admin labels/invitations/drafts/program dependency. Полная suite, production, реальный SMTP/внешние SDK, другие browsers/OS и assistive technology — NOT RUN. Последствия detach Program проверены; полноценный UI lifecycle программ относится к модулю05 и здесь не принят.

Первая попытка 216 tests закончилась75 failures/6 errors из-за stale local translations и другого cookie name в собственной обвязке. Исправлено **только QA окружение**: test process использует cookie contract существующих тестов, переводы `.po` собраны WSL msgfmt в собственную LOCALE_PATHS. Assertions/application не менялись. [Initial log](test.attempt1.log), [locale build commands/hashes](locale-build.json), [setup](setup-ledger.jsonl). Это environment failure, не216 подтверждённых app failures.

Ошибки harness: native confirm ошибочно ожидался как navigation в bulk (сама операция успешна, подтверждена receipt/proof); case-sensitive mixed-row текстовый assertion; ожидание MANAGER вместо начального EDITOR; hidden admin tab; invalid fixture model fields; singular вместо поддержанного plural edit URL; невидимое description_en поле вместо реально поддержанного description_az; параллельные CLI команды общей сессии смешали результат длительного matrix. Предварительные попытки сохранены; обнаруженные hidden CSRF/recovery values в собственном первоначальном test failure log заменены [REDACTED], [redaction-log.json](redaction-log.json); matrix повторена в отдельной сессии. Не засчитывались как product FAIL. Native confirm-loading capture не удалось завершить корректно: NOT RUN; вместо него свежее [team loading](team-loading.result.txt) со [screenshots](screenshots/team-loading-390.png) доказывает observable loading, disabled controls и реальный результат при SIMULATED response latency.

## 8. Recommendations

Выполнить следующий незавершённый модуль03 на новом стенде. Findings этого запуска исправлять только отдельным согласованным scope, по [готовым repair prompts](repair-prompts.md). Не отключать CAS и не создавать вторую модель прав. Новый acceptance после repair нужен на фактическом HEAD/WORKTREE; нынешний FAIL не становится PASS по обещанному исправлению.

Существующий module01, его стенд8811/PG55431 и другие прежние стенды сохранены. Собственный стенд8812/PG55432 оставлен для просмотра; browser sessions текущего запуска закрываются отдельно. Пароль находится только в ignored scratch и не включён в отчёт. [Handoff](next-chat.txt).

## 9. P0/P1/P2/P3

P0/P1 не подтверждены в этой ограниченной локальной проверке. P2: ORG-QA-01, ORG-QA-02, ORG-QA-03. P3: ORG-QA-04. Это не оценка всей KidsMap и не production security clearance.

Команды: [browser ledger](command-ledger.jsonl), [setup/test ledger](setup-ledger.jsonl), [стенд и запуск](STAND.md); воспроизводимая обвязка сохранена здесь. Native CLI exit0 сам по себе не означает PASS: учитываются rows/error и финальные source/data proofs. [Финальная сверка](verification.json) фиксирует counts, снимок WORKTREE, сохранность предыдущих файлов и отсутствие app changes.
