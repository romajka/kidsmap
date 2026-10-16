# Module08 — MOD-QA-09–11 LOCAL PASS; модуль LOCAL FAIL

2026-10-16. Выполнено одобрение трёх планов из module08-full-2026-10-16-r1/findings. MOD09–11 закрыты только в проверенном scope. Остались новые [MOD12/13 и два точных плана](FINDINGS.md). Их candidates не применены. Это локальная проверка, не production evidence.

## Снимок и граница

Checkout /home/ramin/kidsmap; HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, branch task33-progress, dirty WORKTREE, active_run: NONE. [Entry](entry.json), [approval](approval.json), [final gate](final-gate.json), [preservation](preservation.json).

Application/test scope:9уникальных файлов =6существующих +3новых test modules. [Собственный diff](approved-implementation.diff), [отдельное дополнение status guide](status-update.diff). Чужие предыдущие правки внутри этих6файлов проверены обратным применением собственного patch и сравнением с entry SHA. Reset/clean/stash не применялись.

Полный ACCEPT-08 уже выполнен **один раз**,261/261backendPASS: [исторический REPORT](../module08-full-2026-10-16-r1/REPORT.md). Полный корпус не повторяли. После patch проверены только новые regression и смежные сценарии. [Текущие964source hashes работающего процесса](runtime-source-final.json), loaded modules/template origins/actual openedMO; [изоляция](runtime-info.json). HEAD не подменяет dirty source evidence.

## Что исправлено

| ID | Причина и правка | Итог |
|---|---|---|
| MOD-QA-09 | AZ/EN fuzzy count и «создано» не входили в MO; count имел неправильный placeholder. Исправлены только2PO entries в AZ/EN: active translations с %(count)s и существующие Created/Yaradılıb безfuzzy | CLOSED LOCAL |
| MOD-QA-10 |4RUliteral loading/success заменены4server labels в существующем i18n node;4PO entries в3языках; безопасная function replacement имени | CLOSED LOCAL в scope переводов; визуальная рамка/capacity отдельно OPEN |
| MOD-QA-11 | Terminal detail не выводил имеющийся review_note. Добавлен read-only section для content approved/declined/rejected с непустой причиной, autoescaping и linebreaksbr | CLOSED LOCAL |

Четыре новых атрибута MOD10 названы data-publication-*, чтобы сохранить точный прежний контракт пяти data-unpublish-* подтверждений. Старые assertions не менялись; MOD06 regression прошёл. Это уточнение имён внутри одобренных файлов, без расширения scope. Fetch/CSRF/URL/backend/row-state/errors/retry/permissions/schema/CSS не менялись. [Пояснение](implementation-note.md).

## Изоляция

DJANGO_TESTING=1; runtime очищает env перед Django import, checkout .env/production credentials не загружает. Новые собственные DB mod0911_fix_r1 и test_mod0911_fix_r1, locmem cache/media/private-media/file email/cookies. Данные вымышленные. Свой PostgreSQL проверен по exactcontainerID b4e125832fb38463089194b973c7bd25f61d3f4534d19bf6e079b6d1acb94766, loopback47955, ownrole mod03_columns_fix_r1; чужие DB не менялись. [Profile/dependency reuse audit](profile-reuse.json). Новый HTTP loopback57737; текущие PID/argv/source проверены.

RU/AZ/EN из текущих PO собраны scripts/build_isolated_locales.py native compiler: RED в собственный locales, GREEN в отдельный locales-green. [RED manifest](locale-manifest.json), [GREEN manifest](locale-manifest-green.json). Manifest проверен, единственный LOCALE_PATHS установлен до django.setup. Общие MO не перезаписывались. Server socket guard разрешает только свой PG; browser route отклоняет внешние обращения. Отказы внешних fonts/resources отдельно в diagnostics, не выданы за успешные интеграции.

## Проверки

[Точные команды/exits/durations](commands.jsonl), [verification](verification.json), [accepted native observations](accepted-browser.json), [CSV](accepted-browser.csv), [PNG SHA/dimensions manifest](PNG-manifest.json). CLI exit0 без semantic complete не считался PASS.

- RED:7новых backend methods,41failed subtests по ожидаемым причинам: [final RED](targeted-red-final.txt), exit1. Count0/1/2 на3очередях AZ/EN, отсутствующие4labels RU/AZ/EN, terminal reason admin/reviewer в3языках. Native перед patch:3sourceFAIL ([result](red-native.js.result.json)). Filename/rows исправлены на фактический default viewport1280, [QA note](RED-harness-note.md).
- GREEN: **13/13methods**, exit0,17.455s исполнения ([output](targeted-green.txt)).7новых +3старых MOD06 locale methods +existing repeated approval/GET guard +hub stale AJAX/version guard +status-chip/Reset guard. Existing assertions не ослаблялись.
- Native **433accepted PASS /0productFAIL в утверждённом scope**. RU/AZ/EN×360/390/768/1024/1280/1440: actual publish↔draft, translated loading (SIMULATED response delay; настоящий POST пропускается потом), actual success/persisted status, literal HTML-like/quotes/$& name, confirmation keyboard/Tab/reload. Между действиями уведомления явно закрывались, чтобы отделить новый capacity дефект MOD13.
- MOD09: AZ/EN×Place/Event/Specialist×360/1440, actual native search0/1/2 и rowcount, metadata, keyboard reachability, selection/auto-navigation/Reset; RU390 shared control.
- MOD11:18cells уadmin и18уreviewer; каждыйapprove/return/reject через canonical synthetic decisions и пользовательскую ссылку из hub. Точная длинная/HTML-like причина, переносы/escaping, отсутствие повторных action controls/overflow. Volunteer/bare staff403, anonymous login redirect в браузере; backend negative controls. Terminal notes/organizations не менялись отGET.
- Native guards19PASS ([result](green-guards-v4.js.result.json)):3языка, Escape/Cancel безPOST с возвратом фокуса, SIMULATED network abort и освобождениеbusy, настоящий retry draft/published, настоящий disabled incomplete guard безPOST, non-target domain unchanged.6local diagnostics здесь ожидаемы:3abort requestfailed +3ERR_FAILED console; в остальных accepted groups local errors0.
- Самостоятельный реальный backend validation error в этом scoped recheck не вызывался: UI блокирует incomplete карточку доPOST; это **не** заявлено как проверенная backend error branch.
- JS syntax node --check exit0; GREEN locale build/verify exit0; runtime-info exit0.

294PNG включают primary GREEN, RED, partial/harness history и pending candidate feasibility. Candidate PNG **не считаются application GREEN**. Геометрия/escaping проверены в настоящем Chromium; визуально просмотрены representative count, terminal note, settled actual toast и candidate. Все294PNG вручную не просмотрены.

## QA corrections и ограничения

Toast helper передаёт строку в title, не message; inline filter disclosure не обязан перемещать initialfocus какmodal; status URL имеет status__exact; select автоматически navigates. Ошибочные ожидания/таймауты сохранены вv1/v2/v3 outputs, повторены затронутые проверки. Accepted selection указан в package.py. [QA corrections](harness-corrections.md).

AZ whole-revision comparison дал1falseFAIL из-за нашей одновременной публикации **другой** synthetic live card: revision1 pending→approved. Terminal note revisions иorganizations неизменны: [разбор](AZ-domain-concurrency.json). Independent reviewer GET matrix PASS безdomain writes. Незавершённые guard runs сохранены, итоговыйv4 дал19PASS. Полные неизменившиеся наборы не повторялись.

## Новые причины

**MOD12 OPEN**: actual settled success toast RU390 тёмный на тёмном, title72.875px выходит за fixed44px. [Evidence](settled-toast.js.result.json), [PNG](screenshots/SETTLED-success-ru-390.png). Legacy .km-toast конфликтует с unified engine. [План1CSSфайл](findings/MOD-QA-12-PLAN.md). Candidate namespace+long-titlewrap проверен только SIMULATED response override:18corrected long-title cells +domain controlPASS; прежние18loading controls сохранены.

**MOD13 OPEN**: настоящий текущий notification engine на4м уведомлении не возвращает управление за1501ms; первые3рендерятся. Вход уведомлений SIMULATED, domainPOST0. [Native bounded repro](toast-capacity-native.js.result.json). while(children>=3) вызываетdismiss с удалением через220ms: eventloop не получает управление. Controlled VM actual source:1controlPASS/3overflowFAIL timeout250ms; candidate внеприложения4PASS. Исторический AZrendererUNKNOWN не объявлен задним числом доказанным. [ПланJS+NEWtest](findings/MOD-QA-13-PLAN.md).

Candidate patches/test не применены, sourceSHA этихCSS/JS неизменны. Это новые причины вне одобренных9файлов; по правилу пользователя необходим отдельный approval. Вместе3уникальных app/testfiles. После approval толькоtargeted/affected проверки; совместить native уведомления, не повторять261корпус.

## Сохранность и дальнейшая работа

[Final gate](final-gate.json):7изменённых entryfiles =6approved appfiles +status guide; обратное применение собственного diff даёт entrySHA.3новых tests не существовали при entry. Остальные entryfiles, общие MO/HEAD/branch/active_runNONE сохранены.3чужих QA HTTP проверены поPID/argv/cwd,74контейнера поID/портам/state. Capacity repro закрывал только свой context.

NOT RUN: повторный full261, global всехмодулей, module09, production verification, cross-browser/physical devices, screenreader, отдельный stress/load corpus, новыеCSS/queuepatches в приложении. Сохраняются границы исторического ACCEPT-08 и соседние editor/home-recommendation locale observations вне этихпланов.

Пользователь разрешил Git push и применение на сервере **после готовности модуля**. Сейчас module08 LOCALFAIL из-заMOD12/13, условие не выполнено. Commit/push/deploy/production не выполнялись; credentials не включены в отчёт, artifacts или Git. После новых согласованных задач проверить Git package и фактический server/release/recovery перед разрешённой выкладкой.
