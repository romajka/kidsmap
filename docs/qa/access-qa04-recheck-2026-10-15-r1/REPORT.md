# ACCESS-QA-04 — свежий recheck и implementation plan

2026-10-15, Asia/Baku. **PLAN COMPLETE; ACCESS-QA-04 OPEN, application implementation NOT RUN.** Подтверждена одна причина обрезки карточек команды места. [Конкретный план](IMPLEMENTATION_PLAN.md) ожидает отдельного approval; единственный будущий application файл — `static/css/site.css`, два ограниченных owner-team grid/wrap правила. Текущий source приложения не менялся. Итоговая сохранность/source проверяется [verification.json](verification.json), native exit gate — [verify.status.json](verify.status.json).

## Snapshot, авторизация и владельцы

Фактический checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` **+dirty WORKTREE**, `active_run: NONE`. [Entry hashes/status/stands](entry.json):28354baseline files, включая3shared MO;58foreign containers,1учтённый foreign QA HTTP process. Исторические Windows paths/SHA/порты не использовались как параметры нынешнего стенда. Production UNKNOWN/NOT RUN.

Ответ «продолжи» разрешил следующий fresh PLAN04, не patch ещё не показанного scope. Предыдущие approvals01/02 на04 не распространяются. Канонические orchestrator/frontend-reviewer/browser-qa обязанности выполнены одним `/root` последовательно; независимых специалистов не было. Применены systematic-debugging/writing-plans, KidsMap UI+frontend/accessibility, playwright и verification-before-completion. Прочитаны только входные инструкции, status/rules и относящиеся к04 материалы; вся библиотека PLAN заранее не загружалась.

## Подтверждённый дефект

**ACCESS-QA-04, P2, confidence HIGH**, LOCAL WORKTREE. Владелец открывает `/ru/account/places/team/` или AZ/EN вариант. Grid `.owner-team-list` и `.owner-team-item` не ограничивает min-content; `h3` и metadata имеют `overflow-wrap:normal`. Непрерывный email/username растягивает карточку, её содержимое и role form. Глобальные mobile overflow:hidden скрывают выход, поэтому root/body scrollWidth не доказывает отсутствие clipping.

**Отдельный current historical trigger**, без длинной соседней карточки: owner отправил и отменил через UI `cancelled07@example.invalid`; единственная карточка после завершения entry animations имеет **x21..399.375**. Это воспроизведено **RU/AZ/EN×360/390**, шесть rendered FAIL случаев. На360 root/body scrollWidth360, на390 —390; panel right354/384. Исторические x380.1875 и390PASS не перенесены на текущий runtime: свежие числа имеют приоритет. [Полная geometry](observations.json), [RU360 PNG](screenshots/historical-solo-ru-360.png), [RU390 PNG](screenshots/historical-solo-ru-390.png).

В filled fixture с допустимыми длинными email и username та же причина подтверждена во всех18cells: RU/AZ/EN×360/390/768/1024/1280/1440. На узком экране не виден также центр растянутой role button; на desktop длинный member card выходит за panel/viewport. [Mobile](screenshots/filled-ru-360.png), [desktop EN1440](screenshots/filled-en-1440.png). RU long-cohort measurements сделаны во время конечной entry animation; большой overflow и settled PNG достоверны, а точные settled bounds отдельно подтверждены isolated short case и AZ/EN. До approval CSS/DOM style injection не выполнялась.

## Source/impact и минимальное решение

- `static/css/site.css:9724` list grid;`:9730` item grid;`:9740` headings;`:9753` role form и responsive block`:12468`. Все оставлены без patch.
- `src/catalog/templates/pages/owner_team.html:10` уже содержит корневой `.owner-team`;`:64`/`:94` list,`:66`/`:96` item,`:67` member username,`:97` invitation email. Разметка достаточна, её изменение не нужно.
- Source chain: `views.owner_team_dashboard/owner_team_invite` →`OwnerTeamController.build_manager_context` →`pages/owner_team.html` →base/static CSS. Graph inbound trace подтвердил2consumers; actual routes/template/source проверены.
- Graph actual project `home-ramin-kidsmap`, root текущего checkout, status ready/full. Для CSS/controller/views/review template metadata_match/no_recorded_issue; owner_team template partial line74 проверена напрямую. Coverage best-effort, не доказательство полного индекса; исторический `C-kidsmap` не актуальное имя. Graph cache не копировался.
- Общие `.owner-review-list/.owner-review-item` CSS определения менять не надо. Bounded template literal check не нашёл таких классов в текущих project templates; настоящий owner-review dashboard использует новую account разметку, отдельно от `.owner-team`. Его реальные6smoke states сохранены, полный review lifecycle не заявляется.

[План](IMPLEMENTATION_PLAN.md) предлагает scoped min-width0/minmax(0,1fr) на list/item и overflow-wrap:anywhere на h3/.meta. Полный текст сохраняется; typography/padding/бизнес-правила не меняются. Это рекомендация, **не проверенный post-patch GREEN**. Нет изменений template/JS/backend/PO/models/schema/CI/existing assertions. Draft scope: один CSS файл плюс собственный fix evidence и одна текущая status note.

## Реальный браузер и фактические counts

Chromium **149.0.7827.55**, native Playwright CLI, отдельная session `accessqa04recheckr1`. [Command/exits](commands.jsonl), `*.js.status.json` и `*.js.result.json`, [selected observations](observations.json). CLI exit0 не равен semantic success: failed helpers и completed partial evidence разделены.

| Сценарий | Current coverage |
|---|---|
| Filled member+pending/accepted/canceled invitation cards |18cells, все ширины/языки; card/text/control bounds, root/body и keyboard Tab visible focus |
| Реальная self-invite server error | RU/AZ/EN360; native POST200+flash-error, состояние команды до/после одинаковое, текущая обрезка сохраняется |
| Empty owner team | RU/AZ/EN360, реальные пустые section states |
| Shared current owner reviews | RU/AZ/EN360/1440,6GET/render/root smoke PASS; не тест модерации/ответов |
| Historical short email alone | RU/AZ/EN360/390,6settled cases, card overflow FAIL |
| Настройка проверяемых состояний |3native invites,1recipient native accept,1owner native cancel; позже отдельный fourth invite/cancel на прежнем empty-owner place |

**198observations:111PASS/87FAIL**, не198независимых E2E тестов. Все87FAIL — current layout oracle: card/text/controls/root. Основная36state selection:18filled+3error+3empty+6reviews+6short. Main matrix153rows =78PASS/75layoutFAIL; historical-solo36rows =24PASS/12layoutFAIL; initial fixture checks9PASS. ROLE focus достигается нативной клавиатурой, но растянутые/обрезанные controls не объявляются пригодными только по focus=true.

PNG **39**, оригиналы [manifest с SHA/размерами](png-manifest.json); [выборочный просмотр](visual-review.json): filledRU360, isolatedRU360, errorEN360, filledEN1440. Не все39кадров просмотрены вручную. Full-page screenshot может быть шире установленного viewport при desktop overflow — это доказательство дефекта, не другая viewport настройка. Source/jsdom/HTTP200 не заменяли rendered evidence.

**Console/network:** выбранные native результаты имеют0pageerrors/необъяснённых local failures/badResponses/static404. External Google/fonts/CDN requests заблокированы и отмечены external-blocked, не заявлены успешными интеграциями. EN self-invite error и отдельный form label сохраняют существующий русский fallback; это не исправлялось и не принимается как полная локализация04/05.

## Изолированный runtime, locales и данные

Свои PostgreSQL17/container+volume `access-qa04-recheck-2026-10-15-r1-pg`, loopback54687; DB/user `access_qa04_recheck_r1`, testDB namespace `test_access_qa04_recheck_r1` зарезервирован, backend suites не запускались. HTTP38085. [Actual PID/argv](server.json), [runtime source/template/sole locales](runtime-source-final.json). Перед любым повторным использованием их проверить заново. Только verified собственный HTTP process был один раз перезапущен для QA checkpoint handler до native work; чужие процессы/контейнеры/session не трогались.

`runtime.py` очищает inherited env, включает DJANGO_TESTING=1 до settings/setup, не импортирует manage.py и не загружает checkout.env. Собственные LocMem/cache/cookies/media/private-media/filebased email, cleared Google/analytics settings, browser block external, backend egress только ownPG. Никаких productioncredentials или production действий. ORM использован только для3fictional users/2places; все приглашения, принятие и отмены созданы реальными формами. У empty-owner были настоящие пустые snapshots **до** поздней isolated historical invite; его финальное состояние уже не пустое.

[Fresh locale build](locales-build.txt), [verify](locales-verify.txt), [manifest](locale-manifest.json): текущие RU/AZ/EN PO скопированы и скомпилированы scripts/build_isolated_locales.py в новый собственный `.tmp/access-qa04-recheck-2026-10-15-r1/locales`, build/verify exits0. Manifest/source/MO проверяются до django.setup, единственный LOCALE_PATHS указывает туда. Shared3MO не перезаписывались. Наличие fresh MO не выдаётся за исправление всех fuzzy/missing переводов.

[READ ONLY final aggregate](readback-final.json), statement10s/lock2s:4invitations (ACCEPTED1/CANCELED2/PENDING1),1active EDITOR membership version1,5notifications/outbox rows. Outbox **sent2/suppressed3**: pending invitation+decision sent, accepted invitation+two canceled invitations suppressed текущим delivery guard.2реальных local filebased letters/2files, все адресаты fictitious@example.invalid, failed/retry0; scheduler tick явно **SIMULATED**, SMTP NOT RUN. External socket probe отвергнут до connect.

## Harness failures, команды и сохранность

[Все notes](harness-notes.md) и raw failures сохранены. Ничего не «позеленено» изменением приложения/существующих test assertions:

- RU matrix завершила49rows/8states, затем QA helper предположил optional review link и получил evaluateAll(undefined). Native CLI0, semantic error сохранён. Законченные filled/error/empty states не повторены; только2missing review states дополнены `reviews-ru-r2.js`.
- Первый reviews-only retry имел0rows: существующая own auth session перенаправила login до id_username. После очистки cookies только своего context выполнены2missing states; старый timeout сохранён.
- Collector first exit1 ошибочно ожидал все5outbox rows sent. Current source `_invitation_current/_delivery_allowed/deliver_batch` и READONLY join показывают suppression уже consumed/canceled invitations. Теперь проверяется строгая cross-tab именно этих состояний и2actualletters; [первый FAIL](collect-first-failure.txt) сохранён, никаких transitions не повторяли. Отдельный metadata-query сначала вызван system python без psycopg, затем own .venv; app/DB mutation0.

| Команда | Native результат |
|---|---|
| `.venv/bin/python .../launch.py` | locale build0, verify0; docker run --pull=never0/14.009s; own migrate/prepare0/40.739s; source match |
| `playwright_cli.sh -s=accessqa04recheckr1 open about:blank --config=<own browser.json>` |0, свежая own session, без чужой auth state |
| `.venv/bin/python .../browser_run.py <setup/matrix/reviews/solo>.js` | Actual individual exits/semantic errors/cells в receipts и commands; RED geometry ожидаема до patch |
| `.venv/bin/python .../collect.py` | First1 сохранён; final0,198observations/39PNG/READONLY/source/mail aggregate |
| `.venv/bin/python .../verify.py` | Финальный PLAN/source/preservation gate в [receipt](verify.status.json), точные counts в verification.json |

Final gate сравнивает28354entry files,3sharedMO, HEAD/branch/active_run, известный foreign HTTP process и58foreign container IDs/names/ports/states. Разрешены только свой QA каталог и **одна добавленная текущая guide04 note** ([точный текст](guide-addition.txt)); удаление её из bytes обязано давать entry guide hash. Предыдущие accepted01/02 и module02 отчёты/артефакты не переписаны. Это не гарантия availability всех произвольных host processes: entry process inventory ограничен известным QA HTTP; чужих сигналов/restarts/session manipulation0. Прежние уже остановленные контейнеры из02 не поднимались и не объявляются здоровыми.

## NOT RUN и следующий шаг

Application patch/post-patch GREEN **NOT RUN, нужен approval [точного плана](IMPLEMENTATION_PLAN.md)**. Только ACCESS-QA-04 OPEN; closed_ids пусто. Полные18cells empty/error, deep select interaction/role change/remove и post-patch reviews — обязательная будущая acceptance из плана, сейчас не выполнены. Новый CSS unit/mirror test и backend suites не запускались для PLAN/чистой visual причины. Full ACCEPT07, global corpus, production/deploy/commit/push/module08 NOT RUN.

ACCESS01/02 сохраняют своё scoped acceptance;03=ORG02 уже принят [свежим module02 report](../module02-full-2026-10-13-r2/REPORT.md), старый FAIL не переоткрывался.05 потребует отдельного fresh PLAN/approval. [Handoff](next-prompt.txt). После всех задач07 — один полный ACCEPT07 по guide, отдельно от этих целевых проверок.
