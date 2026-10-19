# SOCIAL-QA-03 — исправление и локальная приёмка

**SOCIAL-QA-03 CLOSED LOCAL в согласованном функциональном scope. Module09 OPEN.** 2026-10-16, Asia/Baku. Исполнитель `/root`; канонические роли Django/frontend/browser/security выполнены последовательно одним исполнителем, независимых субагентов не было.

При конфликте редактирования настоящий HTTP409 теперь возвращает страницу KidsMap: введённые оценка и текст B остаются в форме, актуальная редакция A показана рядом. Автор может явно отправить B с новым токеном версии либо загрузить A по GET-ссылке с предупреждением о сбросе B. Новая конкурентная редакция C снова приводит к409. Отправка на модерацию сохраняет прежнюю публичную редакцию до одобрения.

## Разрешение и проверенный snapshot

Пользователь одобрил последний конкретный [трёхфайловый план](../module09-pc-resume-2026-10-16-r1/IMPLEMENTATION_PLAN.md): «Давай одобряй и начинай работать.» [approval.json](approval.json) содержит сообщение, scope и SHA плана. Прежние документы с `approval PENDING` остаются историей до этого одобрения.

Checkout `C:\kidsmap`, branch `codex/module09-transfer-2026-10-16-r1`, HEAD `852938d96764ae315b92859e3651e5ea62054a36` + approved dirty WORKTREE. `task33-progress` сохранён на `e4e05cc213b34e2d771ecb854901bfd016d1db51`; index/HEAD/branch и `active_run: NONE` не менялись. [Entry](entry.json), [GREEN source1020](green-source.json), [preservation](preservation.json), [итоговые результаты](verification.json).

Исправлены ровно три application файла, совпадающие с одобренными кандидатами после нормализации переводов строк:

| Файл | Изменение |
|---|---|
| `src/catalog/controllers/typed_reviews.py` | Вместо раннего raw409 — общий author-owned render со status409 и validated payload B; success message/redirect только после сохранения |
| `src/catalog/templates/catalog/typed_reviews.html` | Alert/latestA, editorB, свежий CAS token, явный retry, GET discard/reload, labels/description/autofocus |
| `src/catalog/testcases/test_social_qa03_conflict_recovery.py` | Новый regression:6 методов, исходные approved assertions сохранены |

[Applied diff](applied.diff), [сверка кандидатов](patch-scope.json). Services/schema/PO/JS/CSS и существующие тестовые assertions не менялись. Неприменённые прошлые предложения и архивные результаты не переписаны. Исторические SOCIAL01–02 scoped LOCAL результаты сохранены; свежие четыре affected checks проверили затронутые контракты.

## RED → GREEN

Перед controller/template patch новый тест размещён в настоящем app test path и запущен на неизменённом приложении: **6 методов,3 failing methods,14 assertion failures,0errors, exit1**,8.811s. Причина: прежний ранний `except ReviewConflict` возвращал одну строку, без формы и B. [RED log](red.log), [RED source](red-source.json).

После patch один targeted GREEN: **10 unique methods,0failures,0errors, exit0**,9.808s. Шесть новых regression + affected rating readback, author-only rejection feedback, PostgreSQL compare-and-swap/concurrent approval, persisted cooldown. [GREEN log](green.log), [точные команды и exits](commands.md). CAS unit cases с cooldown0 явно ограничены; отдельный120s guard проверяет429. Полные неизменившиеся наборы не повторялись.

## Настоящий браузер и readback

Native Chromium155.0.8059.12 через Playwright CLI, actual SSR/routes и собственные fictional fixtures. Вход в роли подготовлен QA-only login; реальный password/OAuth flow этим не проверен. Save/reload/approval выполнялись через настоящие элементы интерфейса. Guard HTTP probes и транспортные симуляции ниже выделены отдельно.

| Проверка | Охват | Итог |
|---|---|---|
| [Основная матрица](matrix.json) | Place/Activity/Specialist/Event × RU/AZ/EN ×360/390/768/1024/1280/1440 |72 настоящих409,17 checks на cell,1224PASS/0FAIL |
| [Повторная гонка](race.json) |4типа ×3языка ×390/1440 |24 случая,314PASS; один text check использует явно помеченный HTTP supplement |
| [Privacy/CSRF guards](guards.json) |Та же24cell выборка; browser GET + явные HTTP probes |264PASS; чужой/гость не видят privateA/C/B; missingCSRF403, foreign token409 без раскрытия |
| [Явный retry → approval](retry.json) |Та же24cell выборка |222PASS; pendingB/public4 → approveB/public2,count1; первая отправка имеет отдельную attribution ниже |

Это counts наблюдений, а не количество независимых тестовых методов. `raceprep.json` хранит подготовку C и повторно в totals не суммируется. `retry_after` меняется со временем и исключён только из сравнения снимков; author head/current/candidate/history/public сравниваются по значениям.

Основные72cells подтвердили B2/latestA5/freshCAS, сохранность current/public4,count1 и отсутствие записи review/history при409. Проверены alert/labels/ARIA description, autofocus, keyboard submit, предупреждение GET reload, достижимость элементов прокруткой и отсутствие горизонтального overflow. Контраст текста сообщения около14.59:1. Для Place выдержан реальный120s cooldown; новый серверный service order не вводился. Activity/Event и Specialist проверены с их настоящими правилами.

24 lifecycle проверили загрузку A со сбросом B, следующую редакцию C1, повторный stale long/scriptB409, буквальное отображение script без исполнения, fresh token C, явное сохранение B2, native reviewer approval и повторный авторский readback. Public current4 остаётся до модерации; после неё public2/count1. READ ONLY snapshots используют statement_timeout5s/lock_timeout2s.

В принятых обычных matrix/raceprep/race/guards/retry результатах **0 unhandled pageerrors**; прежняя сигнатура `ViewTransition opt-in disabled` не воспроизвелась на исправленном409. Ожидаемые console/network409 не называются чистой консолью. HTTP журнал также содержит ожидаемые403 и три429 из ошибочных preconditions QA; это не новые product failures. Полный [HTTP log](http.log) относится только к собственному fictional стенду.

Дополнительно [extra.json](extra.json): одна native SpecialistRU360409 проверка достижимости заголовка прокруткой/отсутствия записи и четыре **SIMULATED** abort POST до доставки серверу — по одному на тип, RU360, одна явная попытка/отсутствие записи. Ожидаемые `net::ERR_FAILED` этих симуляций отделены от обычных pageerrors. Четыре конечные **SIMULATED500ms** задержки POST проверили сохранение payload/отсутствие ранней review-записи; они не моделируют все возможные сетевые сбои.

## Неудачные QA-попытки и ограничения атрибуции

[failed-attempts.json](failed-attempts.json) сохраняет классификацию ошибок среды/QA, без замены их на PASS. Менялись только собственные QA helpers, приложение после approved patch оставалось на том же SHA. Ранее успешная полная матрица повторно не запускалась; до её завершения переиграны только затронутые preconditions/cells.

1. Inline reload-link переносится на две строки. Первый hit-test попал в пустой промежуток bounding box; native `getClientRects` подтвердили попадания по обеим строкам. Исходные [matrix-attempt1](matrix-attempt1.json)/PNG сохранены. Диагностическая Windows UTF-8 ошибка и удаляемый canonical middleware `qa_case` query также исправлены только в helper.
2. Ранний replay A и первый stale PlaceB после C получили законный429. До повторной попытки проверен фактический302/new candidate и выдержан реальный cooldown. A/C timestamps не переписывались; только начальные fictional current4 fixtures до первых операций были состарены на10минут. Первое C и последующее native C сохранены без reset.
3. Long/scriptB заканчивался пробелом; service `review_use_cases.py:53` штатно применяет `.strip()`. Исходная raw-space проверка FALSE сохранена в [race-attempt1](race-attempt1.json). Первый accepted text check явно ссылается на [один supplementary HTTP409](normalization-supplement.json):1289 raw →1288 validated/returned символов, protected review без записи. Остальные23 native cases сравнивают validated text; их native evidence не подменено HTTP. Approved application assertions не изменены.
4. Первая бесконечная loading gate вызвала30s timeout QA при чтении navigating DOM. Cleanup `unrouteAll` **освободил исходный native B POST**; поэтому restore checks «server unchanged/C pending» были FALSE и остаются такими в [raw output](restore-after-loading-harness-cli.txt). Точный собственный driver остановлен до второй отправки. [Readback/approval](finish-queued-retry-cli.txt) подтвердил одну B revision: C38/history4 → B44/history5, public4 до native approval; исходный POST302 записан23:30:49 Asia/Baku. Второго B POST для этого случая не было. Первая строка `retry.json` имеет7 отдельных accepted checks и явную queued-action attribution;23 обычные строки используют обычный submit flow. Четыре успешные finite500ms loading cases выполнены отдельно.

Некоторые первоначальные helper error files были перезаписаны ограниченным replay; соответствующие ошибки сохранены в failed-attempts, tool history и HTTP журнале. Полный побайтный архив каждой первоначальной ошибки не заявляется. Два retained-attempt PNG отделены от accepted screenshots.

Первый metadata verifier завершился exit1: `race-attempt1.json` прочитан как объект вместо списка. Исправлен обход сохранённых строк в собственном verifier, underlying FALSE evidence оставлено; следующий запуск exit0. Это QA schema error, не повторный product regression.

## Изоляция и сохранность

Python3.12.15/Django6.0.2/PostgreSQL17.11; собственные `m09s03-fix-r1-app`/`m09s03-fix-r1-pg`, internal Docker network и persistent PG volume, DB `m09s03_fix_r1`/test DB `test_m09s03_fix_r1`. Репозиторий bind read-only, собственный scratch writable; `DJANGO_TESTING=1`, очищенный env, отдельные cache/media/private-media/email. `.env` и production credentials не загружались. Browser allowlist только `127.0.0.1:33271`; реальные внешние интеграции не выполнялись. QA settings/profile/secrets в evidence package не копировались.

RU/AZ/EN собраны штатным builder из текущих PO в новый собственный каталог; verify и единственный LOCALE_PATHS до каждого django.setup. [Locale manifest](locale-manifest.json), [runtime info](runtime-info.json), финальный live/source gate в verification. Общие MO сохранены. Fresh source manifest1020 совпадает с GREEN; все entry1019 источники вне разрешённых двух правок сохранены, новый тест добавлен отдельно.

Во время WSL discontinuity после RED остановились собственные текущие app/PG и **два QA контейнера предыдущего запуска этого чата** `m09pc-r1-app`/`m09pc-r1-pg`. Возобновлены только два контейнера текущего запуска; его persistent volume сохранил test DB.24 ранее остановленных чужих контейнера сохранили ID/state. Предыдущие два не перезапускались; их runtime continuity/данные прежнего tmpfs **NOT VERIFIED**. Сохранность всех процессов компьютера не заявляется. [Entry](containers-entry.txt)/[final](containers-final.txt), [preservation](preservation.json). Для нового proxy использован собственный hidden WSL helper.

Прочие tracked изменения не вводились, index не staging; `active_run` не создавался. Неотслеживаемый `.cbmignore` замечен при финализации, отсутствовал в entry status; оставлен как есть, его происхождение/непрерывность от entry не утверждается. Предыдущий QA package/plan сохранён по manifest. Новая запись guide добавлена к истории. Commit/push/deploy/reset/clean/stash/production не выполнялись; недостающие старые PNG не догружались.

## Открытое наблюдение и граница решения

[Контраст общей кнопки](style-observation.json): белый текст16px400 на `#4CAF50` даёт **2.78:1**, ниже QA порога4.5. Native обычная и conflict формы имеют один и тот же стиль; `static/css/pages/typed_reviews.css:15` совпадает с entry SHA. Это существующая общая проблема стиля вне одобренного SOCIAL03 scope; CSS не исправлялся. Полный WCAG/UI PASS не заявлен. Для исправления нужен отдельный конкретный plan/scope.

[127 native PNG](png-manifest.json):121 accepted UI (72conflict +24race +24approved +1heading),4 SIMULATED transport,2 retained QA attempts. Реальные размеры и SHA проверяются verifier; изображения не DERIVED. Выборочно визуально просмотрены mobile ActivityRU390 и desktop EventEN1440; остальные имеют browser geometry/DOM assertions, отдельный визуальный просмотр каждого PNG не заявлен.

**Не запускались:** full ACCEPT09, global project corpus, SOCIAL04–09, module10, production, GitHub execution, реальные внешние сервисы/доставка, физические устройства, другие браузеры, реальный screenreader и полный WCAG audit. Module09 остаётся OPEN; full ACCEPT09 — один раз после завершения всех SOCIAL tasks. Следующая работа — отдельный свежий PLAN SOCIAL-QA-04 по поручению пользователя; автоматического перехода нет.

Финальный read-only [verifier](verify_artifacts.py) проверяет текущий scoped source, approved candidates, prior evidence, index/refs/active_run/MO, matrix uniqueness/counts, retained failed-attempt attribution, PNG SHA/dimensions, links и `git diff --check`; обновляет только собственные metadata/manifest. Его результат в [verification.json](verification.json) относится к целостности evidence и сохранности snapshot; не превращает NOT RUN области в PASS.
