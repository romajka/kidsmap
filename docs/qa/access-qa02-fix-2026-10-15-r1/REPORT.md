# ACCESS-QA-02 — scoped LOCAL PASS

2026-10-15, `/home/ramin/kidsmap`. Закрыт только **ACCESS-QA-02**: получатель теперь может отклонить приглашение места или организации прямо из уведомлений. Отказ не выдаёт доступ; устаревшая открытая форма не меняет решение и показывает понятную ошибку. Полный **ACCEPT-07 NOT RUN**. Итог действителен с [verification.json](verification.json), завершённым gate exit0 и совпадающим source; это не production acceptance.

## Scope и snapshot

- Одобрен [конкретный implementation plan](../access-qa02-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md); ответ пользователя «дальше» на вопрос об одобрении именно этого документа записан в [approval.json](approval.json), включая SHA плана. Новых причин в приложение не добавляли.
- Entry/final root `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` **+ dirty WORKTREE**, `active_run: NONE`. Подробный вход: [entry.json](entry.json). HEAD не содержит локальный patch.
- Один исполнитель: канонические orchestrator, Django, security, frontend и browser роли выполнены последовательно. Независимые subagents не запускались. Применены writing-plans/systematic-debugging/TDD, UI/accessibility, playwright и verification-before-completion; исходные регрессии и native результаты сохранены.
- [Свежий recheck](../access-qa02-recheck-2026-10-15-r1/REPORT.md) подтвердил отсутствие decline обоих типов:36FAIL в18RU/AZ/EN cells, тогда как существующий HTTP business reject работал. Исторический module07 не использовался как доказательство нынешнего состояния.

## Причина и изменения

В inbox были accept/read/join, но не было native decline и notification-scoped POST adapter. Existing business reject проверяет actor/email/PENDING, однако новый adapter обязан отдельно проверить expiry и текущего владельца под canonical locks.

Точные файлы ([diff относительно entry WORKTREE](repair.diff), не относительно clean HEAD):

| Файл | Изменение |
|---|---|
| `src/catalog/controllers/workflow_notifications.py` | Общая сборка inbox context; strict notification-scoped reject POST, native form MIME/CSRF/field validation, свежий recipient/currentness под parent→invitation locks, существующий canonical decide_invitation, localized400/409 и success после atomic |
| `src/catalog/templates/pages/account_notifications.html` | Отдельная localized native decline form для текущего invitation, enum error с role=alert |
| `src/catalog/urls.py` | Один reject route рядом с accept/read |
| `src/catalog/testcases/test_access_qa02_invitation_decline.py` | Новый модуль25 meaningful methods:2core,18boundary,5реальных PG concurrency |

Services/models/migrations/JS/CSS/PO/существующие test assertions не менялись. Accept/read/join алгоритмы сохранены. Браузерный ввод не выбирает entity/target; неизвестные поля, JSON и files получают400. Неправильные recipient/type/version, изменившиеся email/owner/ownership_version, удалённый/архивный target, истечение/terminal invitation не создают decision/grant. NULL expiry legacy проверен для Place; у Organization поле NOT NULL, недопустимую fixture не создавали. Существующий grant при отказе от нового invite остаётся побайтно прежним.

## Регрессии и команды

[Полный журнал фактических argv/exits](commands.jsonl), [RED receipt](core-red-r2.status.json), [GREEN receipt](targeted-green.status.json), [format RED](json-format-red.status.json), [narrow GREEN](format-guard-green.status.json). Команды запускаются через собственный `runtime.py`, который ставит DJANGO_TESTING=1 до settings/setup; не через manage.py/.env.

| Команда / артефакт | Фактический результат |
|---|---|
| `.venv/bin/python .../runtime.py test catalog.testcases.test_access_qa02_invitation_decline.InvitationDeclineTests` до patch | [core-red-r2.txt](core-red-r2.txt):2methods,5assertionFAIL,0errors, exit1; отсутствующие кнопки3locales и POST404 обоих типов |
| `.venv/bin/python .../runtime.py test catalog.testcases.test_access_qa02_invitation_decline catalog.testcases.test_task33_notifications catalog.testcases.test_task33_permissions` | [targeted-green.txt](targeted-green.txt):69PASS, exit0,84.333s;23new+46unchanged |
| Новый JSON boundary до MIME guard | [json-format-red.txt](json-format-red.txt):1method,2assertionFAIL (302 вместо400), exit1 |
| Только2core +unknown-fields +JSON +files после guard | [format-guard-green.txt](format-guard-green.txt):5PASS, exit0,39.665s |
| `node --check` собственных native scripts, compile изменённыхPython, `git diff --check` | Точные counts/exits в финальном [gate](verification.json) |
| `.venv/bin/python .../assemble_evidence.py` |953selected observationsPASS,0FAIL;48additional setup/HTTP/state checks; exit0 |
| `.venv/bin/python .../audit_final.py` |76latest state checks, historical event uniqueness, mail/egress checks; exit0 |
| `.venv/bin/python .../verify.py` | Source/locale/WORKTREE/container identity/secret/PNG/link gate; окончательный exit/counts в [verification.json](verification.json) |

**71 уникальный method ID покрыт**:25new+46unchanged.69+5 запусков дают74исполнения, из них3повторных; это не74уникальных теста. После единственного MIME/file guard delta повторён только затронутый subset; [provenance](format-guard-provenance.json) и [controller before guard](controller-before-format-guard.py) подтверждают неизменность locking/mutation/ACL code и valid multipart path. Полный модуль/общий корпус повторно не запускались.

PG concurrency:5methods×оба типа, разные connections/threads, настоящие canonical locks, ожидание подтверждено `pg_stat_activity.wait_event_type=Lock`. Accept/cancel/owner transfer перед reject; два reject; reject перед accept. Проверены один terminal transition, уникальный decision, неизменный grant, отсутствие выданного доступа после reject; outcomes не мокались.

## Настоящий браузер

Chromium **149.0.7827.55**, native Playwright CLI; [selected observations](observations.json), [исходные команды](commands.jsonl), `*.js.status.json` и `*.js.result.json`. Exit0 сам по себе не считается PASS: gate проверяет rows, semantic error, network и pageerrors с явной классификацией ниже.

| Сценарий | Покрытие / наблюдения |
|---|---|
| Owner UI invite →recipient keyboard decline→302success→reload→READ ONLY state | RU/AZ/EN×360/390/768/1024/1280/1440, оба типа;18cells,306PASS |
| Owner UI cancel после открытия старой формы →native decline409 | Та же18cell matrix, оба типа;360PASS после10точечных settled-alert замен |
| Сохранённый native accept →reload→grant | RU/AZ/EN×390/1440, оба типа;12переходов,60PASS |
| Две вкладки, второй submit409, один decision | RU/AZ/EN390, оба типа;66PASS |
| SIMULATED network abort→native back/retry | RU/AZ/EN390, оба типа;42PASS; до retry PENDING/0decision, после один REJECTED |
| Явно SIMULATED stale email/expiry setup →нативный submit | RU/AZ/EN390, оба типа;93PASS; email404, expiry409, ни grant, ни ложного success |
| JS disabled; реальная owner transfer через existing protected HTTP API | AZ390noJS и RU390transfer, оба типа;26PASS. Это не owner-transfer UI certification |

Всего **953observationsPASS**, не953независимых end-to-end теста. Нативные invites всегда отправлялись владельцем через реальные формы, decision выполнялся пользователем/клавиатурой; ORM не заменяла проверяемые normal transitions. Контроль видимого keyboard focus/Tab/Enter/Space и геометрии выполнен в18cells; long fictional email/username не обрезает новую кнопку. Текущий простой вид account navigation/inbox сохранён; redesign и полная UI сертификация сюда не входят.

RU cancel первоначально имел110PASS/10FAIL: QA читал старый DOM до завершения409navigation. Product source не менялся. После регистрации domcontentloaded **до** keypress проверены ровно10несовпавших полей; [effective RU](cancel-ru-effective.json) сохраняет110старыхPASS и10fresh replacements с исходными ссылками. Выбор:1первый durable native checkpoint +1полный r2 capture +8r3rows. Один дополнительный390Place повторён только из-за отсутствующего PNG после screenshot timeout.48support checks не прибавляются к953. Старые FAIL/timeout/interrupted receipts не удалены и не превращены в успешный native exit.

**Console/network:** normal/other selected scripts требуют ноль необъяснённых pageerrors/local failures/static errors; expected404/409, external blocked и SIMULATED aborted POST классифицированы отдельно. В no-JS batch зафиксированы3`AbortError: Transition was skipped`. [Узкая native диагностика](nojs-post-diagnostic.js.result.json) воспроизвела те же3ошибки с пустым stack на unchanged no-JS login и двух mark-read POST, вообще без нового decline/invite/accept/transfer; JS-enabled/disabled read-only GET дали0. [Source/AST proof](nojs-motion-provenance.json) подтверждает неизменные motion.js/motion.css/base.html и mark_read. Это известная унаследованная no-JS animation anomaly, оставлена видимой для итогового module review, **не исправлена и не выдана за чистый console**. Новая причина/расширение потребует отдельного плана. Необъяснённых ошибок новой операции0.

PNG: **228** native current captures +24excluded interrupted RU frames. [PNG manifest](png-manifest.json) содержит путь/SHA/размер/classification, в том числе raw timing/partial-paint evidence; все кадры не называются GREEN и не все просмотрены вручную. [Выборочный просмотр originals](visual-review.json): mobile focus/success/error, desktop EN, no-JS; реальные изображения: [RU error360](screenshots/cancel-stale-recheck-ru-360-place-error.png), [EN focus1440](screenshots/decline-en-1440-place-focus.png), [AZ noJS390](screenshots/nojs-az-390-place-success.png).

## Изоляция, текущий source и данные

Собственные PostgreSQL17/container+volume `access-qa02-fix-2026-10-15-r1-pg`, loopback59709, DB/user `access_qa02_fix_r1`, testDB `test_access_qa02_fix_r1`; HTTP44245. [server.json](server.json) — текущий PID/argv, перед дальнейшим использованием перепроверить `/proc`/cwd/port/source. Python3.12.3, Django6.0.2. Точные imported module paths, cached template origin/SHA,14file runtime hashes и единственный LOCALE_PATHS: [final runtime source](runtime-source-final.json).

Env очищается до setup; checkout .env/productioncredentials не загружались. Свои LocMem cache/cookies/media/private-media/filebased email; fixture users только `@example.invalid`. Egress backend разрешает только ownPG, browser routes блокируют внешние обращения. External denied probe подтверждён до socket connect. Унаследованные productionenv/SMTP/SDK не использовались.41fictional users,4fictional targets; invitations не seed-ились.

Текущие RU/AZ/EN PO собраны через `scripts/build_isolated_locales.py` в собственный `.tmp/access-qa02-fix-2026-10-15-r1/locales`; [build](locales-build.txt), [manifest](locale-manifest.json), [verify](locales-verify.txt). Manifest/source/MO hashes проверяются **до django.setup**, подключён только свой locale_root. Общие3MO побайтно сохранены. Старые fuzzy/untranslated totals не объявляются исправленными; новые02строки используют существующий inline RU/AZ/EN pattern.

[READ ONLY final audit](readback-final.json), transaction READ ONLY, statement10s/lock2s:76latest checks; Place31REJECTED/25CANCELED/6ACCEPTED/6PENDING, Organization31REJECTED/24CANCELED/6ACCEPTED/6PENDING; grants6+6только от12native accepts. Каждый historical accepted/rejected имеет ровно1decision, остальные0.213notifications/outbox sent,213реальных local filebased letters в194files,0failed/0retry, все адресаты fictional. Scheduler tick **SIMULATED**, сами локальные письма настоящие; SMTP delivery не заявляется. После диагностических read_at transitions invitation/grant/event invariants повторно сверены.

## Прерывания и сохранность

[Harness notes](harness-notes.md) сохраняют foreground143 без RED receipt, launcher config sequencing, QA-only key301→500, missing-script native1, RU old-DOM timing, explicit interruptions, screenshot timeout и неверное имя browserconfig. Эти ошибки не скрыты и не считаются applicationFAIL либо GREEN. Предыдущие исторические/recheck/accepted01 отчёты сохранены. Старые24RU frames/DBreadback отделены от accepted native assertions.

Entry27911baseline files включают3ignoredsharedMO; финальный gate сравнивает каждый hash. Разрешённые дельты только3application files +новый test +собственный QA каталог и **одна** текущая guide02 note; [before](guide-note-before.txt)/[after](guide-note-after.txt) позволяют восстановить entry hash без изменения файла. Чужие dirty/untracked source и артефакты не правились, HEAD/branch/active_run не менялись. Не выполнялись reset/clean/stash/commit/push/deploy/production и сигналы чужим процессам.

У57foreign containers проверены те же IDs/names/ports. После прерываний7прежних running containers найдены exited;4остались running,46как были exited. **Сохранность их состояния NOT VERIFIED**, причина остановки UNKNOWN; чужие контейнеры не стартовали/не перезапускались. Прежний чужой QA PID2046143 исчез: process preservation **NOT VERIFIED**, он не восстанавливался автоматически. [Observed discontinuity](containers-after-interruption-r3.json). OwnPG найден exited255/OOMKilled=false; перезапущен только проверенный ownID с прежним volume, без reseed/migrate. [Own record](own-pg-discontinuity-r3.json). Файлы/identity/ports не смешиваются с доказательством process availability.

## Остаток и NOT RUN

- ACCESS-QA-01 [LOCAL PASS](../access-qa01-fix-2026-10-14-r1/REPORT.md) сохранён; password mail/newpassword/replay принадлежит его6проверенным flows, повторять весь01 ради02не требовалось.
- ACCESS-QA-02 CLOSED LOCAL только в описанном одобренном scope.
- ACCESS-QA-03=ORG-QA-02 — одна ранее принятая причина; [свежий ACCEPT-02](../module02-full-2026-10-13-r2/REPORT.md) имеет приоритет над старым module07FAIL, повторной правки не было.
- ACCESS-QA-04/05 OPEN: отдельные fresh PLAN/approval ещё нужны; [next prompt](next-prompt.txt) начинает только PLAN04.
- Full ACCEPT-07, остальные module suites, общий13module corpus, реальный screen reader/cross-browser, SMTP, real OAuth/внешние интеграции, production/deployment, module08 **NOT RUN**. Module07 в целом не закрыт.
