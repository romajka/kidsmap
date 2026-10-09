# Приёмка постоянных мест KidsMap — 2026-10-09, stand 8792

**Вердикт: FAIL. Подтверждены 7 дефектов P2.** Успешные сценарии и 226 проходящих серверных тестов не дают полной приёмки модуля.

Роль: kidsmap-orchestrator, execution identity `/root`; definition `.agents/agents/kidsmap-orchestrator/agent.md`. Один support `/root/place_contract`, django-reviewer, definition `.agents/agents/django-reviewer/agent.md`: независимая сверка кода и уже полученного evidence, собственный [отчёт](place-acceptance-contract-2026-10-09-review.md). Support не запускал браузер, не подключался к DB и не выполнял тесты. Браузерные проверки, чтение synthetic DB и тесты выполнял root. Прочитаны AGENTS.md, canonical README/registry, architecture/source-of-truth/audit contract/orchestration и `content-entry-audit-2026-10-06.md`; старые выводы перепроверены, не перенесены как результат.

AUDIT ONLY. Application, бизнес-правила, чужой active_run, commit/push/deploy не менялись. Новые deliverables — этот отчёт, support report и отдельный evidence package. Production **NOT CONTACTED**, его версия **UNKNOWN**. Внешние интеграции **NOT RUN**.

## 1. Состояние области и выполненная приёмка

### Snapshot и изоляция

- LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`; branch `task33-progress`.
- WORKTREE dirty: 225 исходных строк status; полный исходный `git status --porcelain` и SHA256 списка приложения в [runtime-source.json](place-acceptance-2026-10-09-8792/runtime-source.json). Это запуск **WORKTREE**, не чистого HEAD.
- `docs/task33/implementation-status.md`: `active_run: NONE` до и после, lock не занимался.
- Источник: 2778 файлов src/static/config/locale, digest `f4b4af0eb8ba30322f5fe7cfe35bdf8742c8782ec9233af8a120cc2e9808e888`. Включены compiled locale MO и существующие грязные файлы.
- Runtime: [acceptance-version](http://localhost:8792/qa/acceptance-version/), старт `2026-10-09T11:19:31.880290+00:00` (15:19:31 Baku). Endpoint отдаёт тот же HEAD/digest, TESTING=true и isolated backend flags. Финальная сверка 2778 файлов и всех 1933 исходных modified/untracked файлов: без чужих изменений; исключён только заранее созданный и затем дополненный собственный support report. [preservation-final.json](place-acceptance-2026-10-09-8792/preservation-final.json).
- Новый собственный Docker `kidsmap-place-acceptance-20261009-8792`, отдельный volume `...-data`, `NetworkMode=none`, без опубликованных DB ports; PostgreSQL17 через собственный Unix socket `.tmp/kidsmap-task33-qa04-socket-place-acceptance-20261009-8792`.
- Только синтетическая копия DB существующего изолированного стенда с проверенным QA label, streamed pg_dump→новый psql. Ни production, ни пользовательские records не копировались. Исходные стенды 8788/8790 не менялись. При первичном старте readiness временного bootstrap PostgreSQL дал ложный сигнал; импорт не состоялся, новый DB имел 0 таблиц. После завершения bootstrap synthetic import успешно повторён. Это ошибка setup harness, не приложения.
- Sanitized process environment, `DJANGO_TESTING=1`, DATABASE_URL/legacy URL/Redis/Google credentials пустые; отдельные media/private-media/temp; LocMem cache/email; guard запрещает внешний Python transport/libpq. Chromium contexts пропускают только localhost:8792, все иные запросы abort. Browser reduced motion; Chromium153.0.8010.36; версия сохранена в browser-version.json. Ключи/пароли/fixtures login JSON/environment/server request log в deliverables не включены.
- Исходные screenshots, скрипты и JSON: [evidence package](place-acceptance-2026-10-09-8792/). Все DB чтения: `transaction.atomic()` + `SET TRANSACTION READ ONLY`, statement_timeout20000, lock_timeout2000. Прямых ORM writes для проверяемого пути не было.

### UI-путь и сверка данных

**Place 158, самостоятельное EDU/107:** новое место → частичное заполнение AZ/RU → ServerDraft → reload → logout/login → продолжение → explicit materialized draft → возраст 13>12 даёт ошибку, текст сохранён, переход к ошибке фокусирует поле → исправление → отправка → отказ с причиной → исправление/повторная отправка → одобрение → public → изменение опубликованного. Первичная цена 15, затем 18; RU имя/адрес остались старыми до approval, часы by_appointment и сумма 18 обновились сразу. Последующий approve заблокирован ложным baseline conflict (PLACE-QA-01); возврат через UI, rebase, новая отправка и approval доведены до конца. Финальная карточка показывает новые утверждённые имя/адрес,18. Причина отказа сохранена в revision, но не видна владельцу (PLACE-QA-02). Evidence: lifecycle, moderation, moderation-resume, review-inspect, recover-lifecycle, state-conflict, state-current, public-parity JSON.

**Place 159, филиал organization 71:** native branch-create → branch workspace → owner editor. ART/106 → SPRT1 очищает чужую subcategory → ART/106. Free tariff → repeated free/paid/admission/event → final common admission 12; отдельное занятие/группа с ценой 20 и временем Saturday 14–15; часы Place Mon–Fri 09–18. Cover+2 gallery → reorder → replacement/delete → promote gallery image to main, readback и сравнение изображения после canonical copy (mean pixel delta<8), AZ/RU/EN названия сохранены. Invalid coords,0/0,half pair перепроверены. Отправка через UI создала pending revision 20, затем отдельный reviewer UI approval → public. Три перевода реально записаны и опубликованы. Для valid map point resolver уточнил district с Yasamal до Narimanov: сравнение с данными, а не ожидание неизменного района. Числовое расписание/цены раздельны; подпись публичных часов ошибочна (PLACE-QA-07).

`branch-publish` harness завис после успешной отправки/перехода на dashboard; его дочерний context закрыт и own CLI process остановлен. Сам факт pending подтверждён read-only DB и native POST. Продолжение вынесено в `branch-review-public`: approval/public 3 PASS; исходный зависший прогон не объявлен PASS.

**Place 160, admin standalone:** native admin add → AZ/EDU → черновик → reload → main photo+2 gallery → ready → publish-confirmation → public без точки, free. Политики free/free_entry_paid_services/events/tariffs переключены 12 раз без hang; public full roundtrip завершён для free. Category picker, errors, media, keyboard, geolocation feedback проверены. После матрицы bound invalid admin POST оставил synthetic pending candidate; public live160 остаётся исходным approved content. Это не свидетельство публикации ошибок. Record160 не принадлежит demo_owner.

**Place 161, owner:** потеря ответа сервера photo-save, уже обработанного успешно, эмулирована 503 → preview сохранён → retry → один materialized Place 161 → reload cover+2 gallery → submit. Отказ с уникальной причиной `QA PLACE 161 причина: уточните вход` → owner/reload/logout-login: причина не видна. [state-rejection.json](place-acceptance-2026-10-09-8792/state-rejection.json) доказывает сохранённый review_note. Финально Place161 — draft с rejected candidate, приватен; не публиковался.

**Place 162, owner event venue:** AZ-only частичный draft/reload → полный draft/event ticket30/events schedule → cover → submit → reviewer approve → public RU/AZ/EN. [venue.json](place-acceptance-2026-10-09-8792/venue.json), [venue-publish.json](place-acceptance-2026-10-09-8792/venue-publish.json). Никакого реального Event/external checkout не создано; тариф event является проверяемой ценой по мероприятию.

Финальная DB-сверка только собственных 158–162: [state-final.json](place-acceptance-2026-10-09-8792/state-final.json). Place158/159/160/162 опубликованы; Place161 — draft с rejected candidate и приватен. У Place158 после завершённого lifecycle approval остался draft candidate от последующих негативных проверок координат и первого foreign-POST harness, который фактически сохранил собственный endpoint. Его утверждённые имя, адрес и цена 18 остались публичными. Revision159 и 162 — approved;160 — pending после проверки ошибок admin matrix. Пять новых materialized Places; retry161 не размножил запись. EN158/160/162 пустой: AZ fallback на public не записал перевод. EN159 содержит собственный английский текст; public h1 имеет lang=en. Поля нового черновика часто находятся в `VolunteerPlaceRevision.payload`, а не в live Place: чтение только Place до одобрения ошибочно выглядело бы потерей данных.

### Функциональная матрица

PASS означает только указанное проверенное поведение, а не всю подсистему. Source/targeted tests и rendered UI различаются.

| Проверка | Итог | Доказательство / предел |
|---|---|---|
| Owner самостоятельное место, полный lifecycle | FAIL | 158 путь завершён; отказ без причины + ложный approval conflict, PLACE-QA-01/02 |
| Филиал organization→Place→approved public | PASS | branch-create/fill/final/review-public JSON; org71/Place159 |
| Admin add/draft/reload/publish/public | PASS | admin-create8PASS, public-parity;160 |
| EDU/ART и зависимая subcategory при переключении SPRT | PASS | lifecycle + branch-fill; не все категории каталога |
| AZ/RU/EN записаны отдельно и опубликованы | PASS | branch-final2PASS + branch-public-languages language3PASS;159 |
| Пустой RU/EN, source language fallback, переводы не появляются сами | PASS | state-final/public-parity20PASS;158/160/162 |
| Description/age/website/phone/address/locality roundtrip | PASS | 158/159/160; фиктивные контакты, без вызовов/WhatsApp |
| No pin допускается; manual valid pair roundtrip/resolution | PASS | admin-create + coordinates + state-final159 |
| 0/0 draft не считается valid publish point; half pair | PASS | coordinates: zero draft+blocked submit+pair422 |
| lat999 rejected, input retained | PASS | coordinate-range1PASS native422; быстрый предыдущий probe имел timing false negative |
| Owner no SDK clear/locate | FAIL | coordinates: кнопки активны/no-op; PLACE-QA-03 |
| Admin denied/unsupported/granted geolocation feedback/manual | PASS | admin-geolocation9PASS: denied/unsupported JSstubs, granted Chromium synthetic API |
| Настоящий GPS, Google/Leaflet SDK/geocoding, карта markers/drag | NOT RUN | external transport запрещён, физическая геолокация не использовалась |
| Free / paid admission / common ticket / event ticket public | PASS | 160free,15818,15912+20,16230; отдельно actual UI/native approval |
| Повтор переключений и reload prices | PASS | owner8 + admin12 переходов, branch-fill/admin-create/venue |
| Free_entry_paid_services полный public roundtrip | NOT RUN | UI переключён, server tests PASS; published final этого режима не проверялся |
| Place hours и group schedule, числовая persistence | PASS | branch review/public:09–18 vsSaturday14–15 |
| Public semantic разделение расписаний | FAIL | RU/AZ/EN Place hours названы Class schedule; PLACE-QA-07 |
| Owner cover/gallery upload/order/replacement/delete/promote/readback | PASS | branch-fill/media-map первые успешные шаги + branch-final pixel check |
| Owner txt/corrupt/empty/oversize errors, сохранённое фото не потеряно | PASS | media-errors8PASS, reload после каждого invalid file |
| Admin mainphoto/new gallery draft→publish | PASS | admin-create160; целевые CandidateMedia/AdminGallery tests |
| Admin reorder/delete/replace каждого media варианта через UI | NOT RUN | только upload/publish/gallery render, не выдавать backendtests за UI |
| Owner error summary / jump / entered text / saving status | PASS | lifecycle/error-probe; native422, focus target |
| Owner desktop/mobile section navigation | PASS | focus-final owner18×section + keyboard forward/reverse |
| Owner Tab фокус полностью виден | FAIL | stickyfooter768 скрываетdescription; PLACE-QA-05 |
| Admin desktop nav / mobile visible picker | FAIL | desktopPASS; mobile Select2 no navigation, PLACE-QA-06 |
| Foreign ID GET: outsider/parent/manager; admin privilege denied | PASS | negative.json первые6rows, redirects; последующий harness timeout не отменяет эти checks |
| Foreign ID POST через изменённый UI upload endpoint | PASS | foreign-post-final request160/save-photos403, input остаётся158; admin160 live не изменён |
| Two-tabs ServerDraft CAS, winning data retained | PASS | negative-final:409/stale text retained/new context readback |
| Offline input + reload/browser recovery | PASS | negative-final:2PASS; browser LocStorage, не серверный save |
| Double draft activation | PASS | negative-final posts1, nohang; не доказательство произвольного POST replay idempotency |
| Save processed but response lost→retry photos/materialize | PASS | response-loss4PASS;161 одна запись |
| Exact native create-form POST replay, multi-user published edits | NOT RUN | отдельные threat scenarios; source review не доказал защищённость всех replay |
| Production/real roles/real files/email/payment/external integrations | NOT RUN | только synthetic isolated stand |

### Реальный браузер и визуальная матрица

Chromium Playwright CLI, actual pages/navigation/fill/keypress/select/upload, НЕ HTML/source вместо rendering. Матрица **198 состояний:195PASS/3 FAIL**, все страницы HTTP200. Owner/admin: empty,filled,errors,open taxonomy select,gallery ×RU/AZ/EN×6 widths; public approved18. Height950 CSSpx, desktop viewport emulation, не физическое mobile устройство. [matrix.json](place-acceptance-2026-10-09-8792/matrix.json). FAIL only admin open custom taxonomy at360 (scrollWidth 373), PLACE-QA-04. Эти PASS проверяют document width/response/DOM/state, **не** гарантируют отсутствие overlay всех controls: отдельный focus-probe обнаружил PLACE-QA-05.

Основной matrix:0 pageerror;18 expected422 owner error POST,0 server500. Отдельные негативные сценарии ожидаемо дают 400location resolve/422/409/403/503; console/network сохранены в JSON соответствующего script. Global «console clean при всех ошибках» не заявляется. Public-parity:0 consoleerror/0 pageerror/0 HTTPerror. SDK requests blocked и отсутствие provider являются тестовым состоянием.

Keyboard forward/reverse + visible focus outline, section nav: [focus-final.json](place-acceptance-2026-10-09-8792/focus-final.json)99 PASS/9FAIL, затем фактический Select2 click [nav-ui.json](place-acceptance-2026-10-09-8792/nav-ui.json)3 FAIL и occlusion [focus-probe.json](place-acceptance-2026-10-09-8792/focus-probe.json)3 PASS/1 FAIL. Admin generic focus probe строгого viewport threshold первоначально ложно считал partially-visible textarea FAIL; elementFromPoint подтвердил, что выбранные control points не перекрыты. Owner native select раскрывался Alt+ArrowDown/Escape; внешний OS popup не попадает в page screenshot, исчерпывающая визуальная приёмка native OS menu **NOT RUN**.

Сохранён 101 screenshot: PC1440/mobile390 во всех языках и основных состояниях; отдельно — переполнение на 360, фокус и навигация на 768, публичные часы филиала. [screenshots index](place-acceptance-2026-10-09-8792/screenshots.md). Автоматические layout checks всей матрицы и ручная сверка выбранных PC/mobile/tablet снимков; pixel-level оценка каждого control на каждом screenshot, screen reader, Firefox/WebKit/реальный touch **NOT RUN**. Открытые custom picker/Select2 проверялись actual UI, длинная форма и галерея присутствуют в снимках.

#### Полная матрица geometry/state

| Роль / состояние / язык |360|390|768|1024|1280|1440|
|---|---|---|---|---|---|---|
|owner/empty/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/filled/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/errors/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/select/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/gallery/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/empty/az|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/filled/az|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/errors/az|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/select/az|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/gallery/az|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/empty/en|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/filled/en|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/errors/en|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/select/en|PASS|PASS|PASS|PASS|PASS|PASS|
|owner/gallery/en|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/empty/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/filled/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/errors/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/select/ru|FAIL|PASS|PASS|PASS|PASS|PASS|
|moderator/gallery/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/empty/az|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/filled/az|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/errors/az|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/select/az|FAIL|PASS|PASS|PASS|PASS|PASS|
|moderator/gallery/az|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/empty/en|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/filled/en|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/errors/en|PASS|PASS|PASS|PASS|PASS|PASS|
|moderator/select/en|FAIL|PASS|PASS|PASS|PASS|PASS|
|moderator/gallery/en|PASS|PASS|PASS|PASS|PASS|PASS|
|guest/public/ru|PASS|PASS|PASS|PASS|PASS|PASS|
|guest/public/az|PASS|PASS|PASS|PASS|PASS|PASS|
|guest/public/en|PASS|PASS|PASS|PASS|PASS|PASS|

## 2. Сильные стороны

Candidate/live boundary сохранил старую public identity/address до approval; immediate hours/amounts действительно обновляются при explicit save. Partialdraft и logout/login recovery работают. CAS сохраняет winning draft и введённый stale текст; offline reload восстанавливает локальный ввод. Invalid upload не удаляет сохранённую cover. AZfallback отмечен языком и не превращается в stored translation. No pin — допустимый сценарий: не добавлен выдуманный marker. Branch link и group/price/hour данные дошли через native forms и approval до public.

## 3. Реальные проблемы

Все findings ниже: environment LOCAL dirty WORKTREE/stand 8792, confidence HIGH, воспроизводимость fresh browser+source review. Production impact не утверждается. Исправления **не выполнялись**; prompts — отдельные будущие scopes, требующие согласования.

### PLACE-QA-01 — собственное обновление цены создаёт ложный conflict одобрения — P2

- Роль: owner→moderator. URL [editor158](http://localhost:8792/ru/account/places/158/edit/), [review158](http://localhost:8792/admin/volunteer/review/158/). Текущая fixture уже прошла rebase/approval, историческое broken state в artifact.
- Шаги: approved exact admission 15 → изменить тариф 15→18 вместе с gated RU name/address → Apply changes → reload → submit → открыть review.
- Ожидание: сумма 18 immediate, имя/адрес до approval старые; reviewer может одобрить собственную pending редакцию без стороннего изменения. Факт: «Карточка изменилась после отправки», approve отсутствует; base scalar15, incoming18. Возврат/rebase восстанавливает возможность approval, значит candidate не потерян.
- Evidence: moderation-resume/review-inspect/recover-lifecycle JSON, state-conflict (base15/payload18), state-current + public (live18 readback после восстановления). Snapshot live scalar в момент conflict не выгружался отдельно; immediate18 подтверждён браузером, поздний readback согласуется.
- Первопричина: `src/catalog/services/publication.py:355-357` обновляет base только immediate keys; `pricing_plans.py:349-350,603-627` также меняет производные price_from/to. Следующий full snapshot приносит 18 против stale base15; `volunteer_places.py:61-67`/publication382-383 корректно по своему контракту блокируют diff.
- Impact/scope: approval опубликованного обновления блокируется; исправлять baseline/projection после собственного immediate apply. Owner django-reviewer; depends price projection/CAS. Не отключать проверку настоящего stale editor.
- Самостоятельный prompt: «В /home/ramin/kidsmap исправь только PLACE-QA-01. Сначала предложи конкретный план обновления publication baseline для производных price_from/to после собственного немедленного изменения тарифа. После согласования добавь изолированный regression: опубликованный тариф 15→18 вместе с изменением имени и адреса, затем explicit draft → submit → approve. До одобрения текст остаётся прежним, сумма 18 появляется сразу, после одобрения появляется новый текст. Настоящее устаревшее сохранение из второй вкладки должно по-прежнему отклоняться; изменение структуры тарифа остаётся под модерацией. Другие правила цен и публикации не менять. Используй DJANGO_TESTING=1 и отдельные DB/cache/media, подтверди путь через настоящий UI. Без commit/push/deploy».

### PLACE-QA-02 — владелец не видит сохранённую причину отказа — P2

- Роль: moderator→owner. URL [review161](http://localhost:8792/admin/volunteer/review/161/), [editor161](http://localhost:8792/ru/account/places/161/edit/).
- Шаги: submit 161 → reject с «QA PLACE 161 причина: уточните вход» → owner editor → reload → logout/login. Ожидание: причина видна рядом со статусом/действием исправления. Факт: Needs changes виден, причина отсутствует во всех 3 проверках.
- Evidence: rejection-roundtrip 3 FAIL + state-rejection сохранённый review_note; также 158 отказ/rebase.
- Первопричина: `publication.py:408` сохраняет revision.review_note, `views.py:1384-1387` передаёт revision, но `owner_place_continuous.html:7` показывает только lifecycle, note не рендерится; `owner_places.html:401` читает другое Place.rejection_reason.
- Scope/owner: owner continuous template/copy, frontend-reviewer + django contract; escaped reason, rejected/declined states, public content untouched.
- Самостоятельный prompt: «Исправь только PLACE-QA-02. Сначала согласуй текст и расположение причины отказа в редакторе Place владельца. Показывай сохранённый revision.review_note с безопасным экранированием для соответствующих состояний отказа. Проверь RU/AZ/EN, ширины 390/768/1440, обновление страницы, выход и вход, исправление и повторную отправку. Историю решений модератора и публичную версию сохранить. Добавь regression с уникальной причиной и сверкой UI с сохранёнными данными. Без commit/push/deploy».

### PLACE-QA-03 — кнопки карты при отсутствии SDK активны и ничего не делают — P2

- Роль: owner. URL [editor159](http://localhost:8792/ru/account/places/159/edit/).
- Шаги: provider unavailable, manual 40.4093/49.8671 → Clear → Locate. Ожидание: clear очищает обе координаты; locate выполняет доступный fallback либо объясняет недоступность/disabled. Факт: пара не меняется, status не меняется, кнопки enabled.
- Evidence: coordinates 2 explicit FAIL, [mobile map](place-acceptance-2026-10-09-8792/screenshots/owner-map-no-sdk-390.png). Valid/manual save отдельно PASS,0/0 publication blocked.
- Причина: `static/js/owner_place_map_picker.js:474-480` unavailable отключает только search; clear/locate binding живёт внутри provider init; `owner_place_map_picker.html:43-44` кнопки остаются active.
- Scope/owner: provider-independent manual clear/feedback, frontend-reviewer. Не требовать координаты, не подставлять 0/0, не подключать real SDK/key.
- Самостоятельный prompt: «Исправь только PLACE-QA-03 после согласования поведения карты при недоступном SDK. Кнопка Clear должна очищать lat и lng и позволять сохранить черновик. Locate должна показывать понятное состояние недоступности либо использовать допустимый fallback с обработкой отказа и отсутствия геолокации. Сохрани необязательность точки и серверную проверку географии. Проверь RU/AZ/EN на шести заданных ширинах, отсутствие SDK, ручной ввод, позднюю загрузку SDK и отказ геолокации. Остальные поля должны сохраняться. Без внешних интеграций и commit/push/deploy.».

### PLACE-QA-04 — admin taxonomy dropdown выходит за экран 360 — P2

- Роль: administrator. URL [admin160](http://localhost:8792/admin/catalog/place/160/change/).
- Шаги: viewport 360×950 → открыть custom category picker RU/AZ/EN. Ожидание: options/count/search полностью внутри viewport. Факт: scrollWidth 373, dropdown left53+min width320=373; правые подписи обрезаны.390 контроль PASS.
- Evidence: matrix 3 FAIL + dropdown 3 FAIL/3 PASS; [RU360](place-acceptance-2026-10-09-8792/screenshots/admin-open-category-ru-360.png), AZ/EN аналоги.
- Причина: `static/admin/css/pages/kidsmap_place_form.css:1104-1110` absolute left0/min-width320; JS 1153-1155,1285-1311 не clamp к viewport. Это custom taxonomy, не Select2.
- Scope/owner: frontend-admin, responsive custom picker width/position/options; не скрывать overflow всей страницы.
- Самостоятельный prompt: «Исправь только PLACE-QA-04. Предложи минимальный план адаптации custom picker категории и подкатегории в админке. После согласования список, поиск и подписи должны помещаться на ширине 360 без горизонтального переполнения. Не скрывай проблему глобальным overflow:hidden. Проверь RU/AZ/EN × 360/390/768/1024/1280/1440, мышь, клавиатуру, длинные подписи, сохранение category→subcategory и фокус. Приложи снимки PC/mobile до и после. Без изменения бизнес-правил и commit/push/deploy.».

### PLACE-QA-05 — sticky footer скрывает поле с клавиатурным фокусом — P2

- Роль: owner. URL [editor159](http://localhost:8792/ru/account/places/159/edit/).
- Шаги: viewport768×950 → фокус на имени AZ → Tab → описание AZ. Ожидание: поле видно между закреплёнными панелями. Факт: textarea top882.59/bottom952.59; точка384,912.59 перекрыта footer.pc-actions. Фокус есть, но поле закрыто. Контроль owner390 и admin — PASS.
- Evidence: focus-probe 1 FAIL/3 PASS, [tablet screenshot](place-acceptance-2026-10-09-8792/screenshots/owner-focus-probe-768.png). Отдельное overlay evidence, geometry matrix этот дефект не ловит.
- Причина: `static/css/pages/owner_place_continuous.css:13-14,21` sticky bottom/actions и scroll margin; `owner_place_continuous.html:39`. JS 177-181 explicit goTo центрирует, ordinary Tab 254 не учитывает занятый viewport. CSS scroll margin недостаточен.
- Scope/owner: frontend-reviewer/accessibility, динамическая свободная область/focus scroll; не менять Tab order/CAS.
- Самостоятельный prompt: «Исправь только PLACE-QA-05 после согласования плана UI. При Tab и ShiftTab поле с фокусом должно оставаться видимым между закреплёнными header/savebar и footer с динамической высотой. Проверь 768×950 и RU/AZ/EN на шести заданных ширинах, textarea, details, переходы по разделам и ошибкам, reduced motion. Подтверди отсутствие перекрытия через bounding rect, elementFromPoint и screenshot. Не допускай скачков при вводе и не меняй порядок Tab, бизнес-правила, autosave или CAS. Без commit/push/deploy».

### PLACE-QA-06 — мобильная навигация admin Select2 не работает — P2

- Роль: administrator. URL [admin160](http://localhost:8792/admin/catalog/place/160/change/).
- Шаги: viewport360/390/768 → открыть видимый combobox разделов → выбрать «Локация». Ожидание: переход к началу Location с правильным фокусом. Факт: scrollY0, selector возвращается в basics, Location top5880/5587/3325. Программный native change тоже работает неверно: центрирует целый section высотой1998–2547, заголовок и region оказываются выше viewport. Контроль desktop navigation — PASS.
- Evidence: nav-ui 3 FAIL actual click, nav-probe 3 FAIL secondary, focus-final 9 navigation FAIL RU/AZ/EN. [360 screenshot](place-acceptance-2026-10-09-8792/screenshots/admin-nav-probe-360.png) снят финальным actual UI probe.
- Причина: `static/admin/js/kidsmap_place_form.js:29,76-77` native change listener; установленный Jazzmin `change_form.js:113-117,120,137` оборачивает select в Select2. Select2 emit jQuery synthetic change, native handler не вызывается. Scrollspy 229/246-248 возвращает basics. Вторично focusTarget 268-306 block center на целой section, section не focusable.
- Scope/owner: frontend-admin, native/Select2 events+scrollspy+heading focus; double fire исключить, vendor не переписывать.
- Самостоятельный prompt: «Исправь только PLACE-QA-06 после согласования плана. Согласуй выбор раздела через видимый Select2 и native fallback со scrollspy: переход должен срабатывать один раз, открывать раздел и показывать его начало с правильным фокусом. Программный selectOption скрытого элемента не считать доказательством работы видимого UI. Проверь RU/AZ/EN × 360/390/768 и desktop 1024/1280/1440, реальные клики и клавиатуру, длинные разделы, accordion и ссылки на ошибки. Vendor-код, бизнес-правила и публикацию не менять. Без commit/push/deploy».

### PLACE-QA-07 — часы постоянного места названы расписанием занятий — P2

- Роль: public visitor. URL [public159](http://localhost:8792/ru/place/159-qa-place-branch-8792/), AZ/EN аналоги.
- Шаги: постоянный филиал ART с часами Place Mon–Fri09–18 и занятием группы Saturday14–15 → одобрение и public → раздел Schedule. Ожидание: «Часы работы» для Place, «Расписание занятий» только для группы. Факт: badge «Расписание занятий»/«Dərs cədvəli»/«Class schedule» стоит над09–18 и закрытыми выходными; настоящее занятие в Saturday14–15 показано отдельно. Числа сохранены, но подпись вводит посетителя в заблуждение.
- Evidence: branch-review-public data 3 PASS, branch-public-languages semantic 3 FAIL; [RU390](place-acceptance-2026-10-09-8792/screenshots/public-branch-hours-ru-390.png), AZ/EN/PC аналоги.
- Причина: `src/catalog/services/pricing_plans.py:1157-1168` working hours label зависит от категории (PARK/BEACH/FUN/CAMP/WATERPARK/ZOO), ART/EDU получают class label, хотя rows из Place hours. `place_detail.html:424-425` безусловно рендерит badge. Group `public_offerings.html:10` корректно подписан отдельно.
- Scope/owner: public presentation labels/RU/AZ/EN, django-reviewer+frontend-reviewer; не переносить hours/group данные и не менять модерацию.
- Самостоятельный prompt: «Исправь только PLACE-QA-07 после согласования текста. Часы работы постоянного Place должны называться часами места независимо от категории ART/EDU; расписание группы остаётся расписанием занятий. Сохрани существующие режимы always_open/by_appointment/events, числовые данные и проверки публикации. Добавь regression для ART/EDU: Place работает Mon–Fri 09–18, группа занимается Sat 14–15. Проверь RU/AZ/EN, ширины 390/1440, DOM и screenshots. Правила категорий не подменять. Без commit/push/deploy».

## 4. Tech debt

Есть два интерфейса проверки: legacy volunteer review и новый moderation hub. Причины отказа хранятся и читаются двумя разными способами; scalar-проекции цены сосуществуют с каноническими тарифами, а legacy-подпись расписания зависит от категории. Это темы для будущего плана, не разрешение на удаление или переписывание. Гипотеза повторного create-form POST не назначена подтверждённым дефектом: retry сохранения фото проверен, точный повтор legacy form POST — нет. Support report содержит контракты по коду и hashes.

## 5. Risks

Ложный конфликт блокирует нормальное одобрение, скрытая причина отказа мешает понять требуемое исправление, мобильная навигация и выбор категории в админке осложняют ввод. Sticky footer перекрывает поле при работе клавиатурой; неверная подпись часов вводит родителей в заблуждение. P1, нарушение безопасности и потеря данных не подтверждены. Сохранённые live/candidate и проверки прав выдержали выполненные негативные сценарии. Поведение production неизвестно; локальный HTTP200 не означает приёмку production.

### Какие изменения ждут модерации

Код `publication.py:305-316,350-360`: при explicit save сразу применяются часы Place, schedule_mode, notes и structured_schedule; scalar-суммы цены и суммы тарифов — при неизменной структуре и условиях и отсутствии кандидата цены, ожидающего модерации; также OfferingGroup.schedule_text. Даже Apply changes или explicit draft может обновить эти live-поля. Отдельная отправка существующего черновика с explicit_save=False их не применяет.

Модерации ждут названия и описания AZ/RU/EN, taxonomy, возраст, контакты, адрес/район/координаты, main/cover/gallery, nature/operating_state, price_mode, структура тарифов, условия, форматы, длительность, частота и nested pricing, а также остальные content-поля whitelist. Если условия изменяются или уже находятся в pending candidate, суммы тоже ждут модерации. Новое место пока приватно. Контракт по коду не проверен через UI для каждого поля: на Place 158 проверены имя, адрес, цены и часы; отдельно проверены галерея и создание нового места. Остальные группы полей покрыты чтением кода и целевыми тестами.

## 6. Dead/legacy candidates — без удаления

Legacy review route и зависящая от категории подпись расписания: **manual_review**. Их использование в этом аудите подтверждено; считать их dead code нельзя. Старые wizard/photo/state compatibility paths: **NOT ASSESSED**, удаление не рассматривалось. Списка «можно удалить» по одному coverage нет.

## 7. Tests gaps и точные команды

Все команды выполнены из `/home/ramin/kidsmap`. Wrapper `run_unit.py` очищает environment и использует собственные sanitized settings/guards. Тесты создают отдельную test_qa_stage04 и удаляют её после suite; media/cache/private/email изолированы. Assertions не менялись.

```bash
git rev-parse HEAD
git branch --show-current
git status --porcelain
rg -n 'active_run' docs/task33/implementation-status.md
.venv/bin/python .tmp/place-acceptance-20261009-8792/setup.py
.venv/bin/python .tmp/place-acceptance-20261009-8792/resume.py
bash .tmp/place-acceptance-20261009-8792/run-targets.sh
.venv/bin/python .tmp/place-acceptance-20261009-8792/run_unit.py catalog.testcases.test_task33_publication catalog.testcases.place_readiness catalog.testcases.test_location_assignment catalog.testcases.photo_workflow catalog.testcases.image_uploads catalog.testcases.test_task33_r1_owner_safety catalog.testcases.test_task33_pricing catalog.testcases.test_task33_drafts
playwright-cli -s=place-acceptance-8792 open http://localhost:8792/qa/
.venv/bin/python .tmp/place-acceptance-20261009-8792/run_browser.py lifecycle
.venv/bin/python .tmp/place-acceptance-20261009-8792/run_browser.py matrix
.venv/bin/python .tmp/place-acceptance-20261009-8792/run_browser.py negative-final
.venv/bin/python .tmp/place-acceptance-20261009-8792/run_browser.py focus-probe
.venv/bin/python .tmp/place-acceptance-20261009-8792/run_browser.py nav-ui
.venv/bin/python .tmp/place-acceptance-20261009-8792/run_unit.py --script probe_state.py
.venv/bin/python .tmp/place-acceptance-20261009-8792/preservation.py
```

Setup/resume перечислены как выполненные команды, а не инструкция повторно перезаписать или клонировать существующий стенд. Для перезапуска собственного стенда: `.venv/bin/python .tmp/place-acceptance-20261009-8792/start_existing.py`; helper безопасно использует сохранённый изолированный environment. Не запускай bare serve.py с унаследованным environment. Контейнер должен быть запущен; синтетические роли доступны через [QA login](http://localhost:8792/qa/). Не запускай второй процесс на том же порту. Скрипты изменения фикстур зависят от IDs и состояния этого запуска: их нельзя вслепую повторять без нового собственного стенда. Даже matrix отправляет ошибки на тестовые формы, поэтому нужно учитывать версии candidate.

- Suite1 `run-targets.sh`: **77 PASS**, 33.318s. [server-tests.log](place-acceptance-2026-10-09-8792/server-tests.log). Labels: continuous/permanentwizard/placejsonpricingmodes/CandidateMediaTests/AdminCandidateGalleryTests/LegacyReviewProjectionTests/SourceLanguageDisplayTests/admincandidatecover.
- Suite2: **149 PASS**, 35.244s. [domain-tests.log](place-acceptance-2026-10-09-8792/domain-tests.log). Преднамеренный traceback ошибки mock storage в log не означает отказ suite: итог OK.
- Всего **226 PASS**, это не полный suite репозитория. После аудита тесты не повторялись, поскольку приложение не менялось.
- Полные браузерные команды для каждого script и завершённые строки проверок сохранены в [execution-ledger.json](place-acceptance-2026-10-09-8792/execution-ledger.json); скрипты — в scripts/. JS передавался через настоящий `playwright-cli ... run-code`, wrapper сохранял Result JSON. Повторные прогоны нельзя суммировать как независимые тесты.
- Ошибки harness сохранены. Глобальные URL/setTimeout недоступны в CLI JS sandbox; скрытый select цены заменён действиями через видимые кнопки. Неверный selector кнопки существующего черновика исправлен в QA-скрипте. Неравенство URL после canonical copy изображения заменено сравнением pixels; быстрые probes с 600ms заменены ожиданиями. Скрытая admin anchor не выдаётся за мобильный UI. Исходные partial JSON и timing failures не удалены. В `foreign-post` менялся form action, но endpoint сохранения фото оставался собственным Place 158: forged request в этом прогоне — NOT RUN. `foreign-post-final` изменил фактический UI endpoint и получил 403. Зависший branch CLI остановлен только в собственном QA-процессе.
- NOT RUN: production, настоящий GPS/SDK/geocoding, доставка email и платежи, полный suite, screen reader и инструментальное измерение контраста, реальные мобильные устройства и другие browser engines, все taxonomy options, каждый media error/admin variant, произвольный POST replay и CAS опубликованного места между разными пользователями. Исторически зелёные прогоны не выдаются за свежую приёмку.

## 8. Recommendations и handoff

Не принимать модуль целиком. Последовательно согласовать семь отдельных областей: baseline и проекции цены, причина отказа, fallback карты, ширина custom picker, видимость фокуса владельца, навигация по разделам админки и публичная подпись часов. После исправления повторить каждый негативный сценарий с сохранёнными live/candidate и действиями через видимый UI. Затем повторить 198 состояний и проверки клавиатуры и перекрытий; отдельно закрыть NOT RUN в согласованном scope. В рамках этого поручения ничего не выполнять на production.

Этот отчёт — новый ограниченный материал для orchestrator/MASTER_AUDIT. Существующий MASTER_AUDIT и чужие отчёты не менялись. Стенд 8792 оставлен для просмотра. Приложение и бизнес-правила не исправлялись.

## 9. P0/P1/P2/P3

| Приоритет | Подтверждено | IDs |
|---|---:|---|
|P0|0|—|
|P1|0|—|
|P2|7|PLACE-QA-01…PLACE-QA-07|
|P3|0|—|

Матрица показывает локальные PASS/FAIL/NOT RUN, а не обещание исправности production или всего модуля.
