# SOCIAL-QA-05 — свежая проверка и план

2026-10-17, Asia/Baku. **CONFIRMED OPEN / P2. PLAN COMPLETE; implementation approval PENDING.** Application changes этого запуска: **0**. SOCIAL01–04 сохраняют ранее записанные scoped LOCAL closures; весь module09 остаётся OPEN.

Проверка воспроизвела расширение документа с768 до822px у вошедшего автора во всех трёх языках. Причина — общая grid с тремя жёсткими минимальными колонками для двух полей. Подготовлен [план на один файл](IMPLEMENTATION_PLAN.md), [неприменённый diff](proposed.diff), [полные candidate rules](candidate-rules.css) и [хеши](candidate-manifest.json). Предлагается page-specific двухколоночная grid с minmax(0,1fr), сохраняющая одну колонку при≤760px. Изменение static/css/site.css ещё не применено; apply-check завершился0.

## Снимок и границы

C:\kidsmap, branch codex/module09-transfer-2026-10-16-r1; LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36. task33-progress=e4e05cc213b34e2d771ecb854901bfd016d1db51; index tree881e0c48c7d557c46221beb3b2410a157982f861, staged diff пуст. Фактический dirty WORKTREE включает одобренные SOCIAL03–04; он сохранён. Проверены1021 исходника/PO и текущие shared MO; [entry](source-entry.json), [final](source-final.json), [preservation](preservation.json). active_run:NONE не назначался автоматически. Production не исследовался.

Один lead последовательно выполнял канонические frontend-reviewer/browser-qa/Django checks. Независимых subagents не запускалось. Применены writing-plans, systematic-debugging, verification-before-completion, KidsMap UI/frontend rules, accessibility и CLI-first native browser workflow. Проверка source/UI правил не заменяет rendered evidence.

Перед source discovery проверен C-kidsmap graph: ready, generation2026-10-16T18:56:53Z, есть partial/unavailable/metadata_changed coverage. Targeted SiteReviewsController search/trace сопоставлены с исходниками; ложные inferred doc/db/count/get связи отклонены. Template coverage неполна, список gaps не заявлен исчерпывающим; дополнительно выполнен literal search active templates/CSS/JS и просмотр необходимых файлов. Reindex/cache artifacts в репозиторий не сохранялись.

## Fresh native baseline

Новый изолированный runtime m09s05-plan-r1-app/pg, internal Docker network, отдельные fictional DB/testDB/cache/media/private-media/email; DJANGO_TESTING=1 до setup, очищенный env без .env/production credentials. Собственные fresh RU/AZ/EN MO построены из текущих PO, проверены перед setup и являются sole LOCALE_PATHS. Shared MO не пересобирались. Browser ограничен localhost; реальные внешние интеграции не проверялись.

Loopback127.0.0.1:33325, отдельная CLI Chromium155.0.8059.12 session social05-pc-plan-r1; Python3.12.15/Django6.0.2/PostgreSQL17.11. Actual template/static origins и live hashes соответствуют source1021: [runtime-info](runtime-info.json), [live-final](live-final.json), [locale manifest](locale-manifest.json). QA auth setup использован только для fictional ролей; пароль/OAuth NOT RUN.

| Проверка | Фактический результат |
|---|---|
| Author/guest × RU/AZ/EN ×360/390/768/1024/1280/1440 |36 native cells|
| Controls: HTTP/canonical/locale/form/cards/CSRF/CSS/DB state |324 PASS|
| Layout |210 PASS /24 FAIL|
| Source failures |3 author cells на768px, по8 layout FAIL|
| Guest cells / остальные author widths |Помещаются в viewport|
| Captured unhandled pageerrors / failed local HTTP / request failures |0 /0 /0|
| Existing affected backend methods |3 unique PASS,0F/0E, exit0,0.381s|
| PNG |44:36 baseline,7 accepted SIMULATED preview,1 retained attempt|

Counts рассчитаны из [matrix.json](matrix.json), [baseline.log](baseline.log), [PNG manifest](png-manifest.json). Это свежая ограниченная matrix; старые counts finding не переносятся на неё. Девять controls на cell проверяют фактические роли/данные; guest отсутствующая форма проверяется как ожидаемое состояние. Нажатия submit/sort/vote эта baseline matrix не выполняла.

В read-only aggregate endpoint до/после каждого случая неизменны:2 approved nonblank reviews,0 pending, ratings4/5,0 reaction records, counters[0,0] и[1,0]. Все данные fictional; реальные записи/секреты в evidence не копировались. Endpoint использует read-only transaction и timeouts5s/2s.

## Подтверждённая причина

static/css/site.css около6160 задаёт minmax(220px,1fr), minmax(260px,1.55fr), minmax(200px,auto) с двумя gaps14px: минимум708px. В src/catalog/templates/pages/site_reviews.html около158 внутри grid только rating/name labels; textarea размещена снаружи. Generic media collapse начинается при≤760px. Literal search текущих active templates нашёл этот grid consumer в site_reviews.html; это не доказательство отсутствия любых динамических consumers.

На768px documentWidth=822, hero/toolbar right=821.625, sort right=804.625, grid right=784.59375. Все три author locale клетки воспроизводят одну причину. Guest формы не имеет и помещается. При этом body уже имеет overflow-x:hidden; root и panel visible. Предложение не добавляет и не меняет clipping.

Существующий controller/site-review model контракт просмотрен: approved nonblank public queryset, sorting, paginator12, ratings/counters/reaction helper, author form. Предложенный diff не меняет этот контракт, template/JS/маршруты/PO/schema.

## SIMULATED проверка гипотезы

Временный page.addStyleTag применял ровно candidate rules, затем style удалялся. В принятых7 случаях (RU/AZ/EN768 и RU360/760/761/1024) получено49 PASS: документ/grid/hero/toolbar помещаются, overflow properties прежние, исходная геометрия после удаления полностью восстановлена, DB aggregate неизменен. На768 documentWidth стал768, grid right691.40625, tracks300.406px+300.406px; после удаления снова822px. [Accepted probe](probe.json).

Это client-side root-cause experiment с атрибуцией **SIMULATED**, не application patch и не post-patch GREEN/acceptance. В первом RU1024 случае strict restore comparison дал FALSE из-за0.0327px изменения размера во время finite entry animation. [Исходные7rows/48PASS/1FAIL](probe-attempt1.json), [raw CLI](probe-run-cli.txt) и PNG сохранены. Повторён только RU1024 после ожидания finite animations, сравнение осталось строгим; [helper](probe-stable.js), [raw replay](probe-stable-cli.txt). Остальная matrix и backend suite не повторялись.

Вручную просмотрены baseline RU author768 и его SIMULATED preview. Fullpage screenshots содержат offscreen элементы с motion reveal; наличие DOM cards и геометрия buttons не означают визуальную приёмку всех карточек/подвала. В плане actual GREEN предусмотрены реальный scroll, viewport PNG и ожидание finite animations; motion CSS вне scope.

## Попытки и ограничения

PG readiness в prepare потребовал два not-ready наблюдения, затем ready; bounded prepare в целом завершился0. Backend сообщил предупреждение об отсутствующем отдельном staticfiles directory; actual browser static CSS200/hash подтверждён, suite завершился OK.

Промежуточная запись плана была отклонена JS parser из-за Markdown backticks до выполнения; повтор с tilde fences успешен. Из-за этого accepted probe.json первоначально не был собран, первый publisher завершился1/FileNotFoundError; после явной сборки из сохранённых raw результатов повтор завершился0. Read-only metadata summary один раз завершился1/KeyError из-за неверного предположения о ключе matrix; структура прочитана и запрос исправлен. Эти ошибки orchestration не меняли application source, existing assertions или результаты product checks; учтены в [verification](verification.json) и [commands](commands.md).

Текущие32 ранее существовавших Docker container IDs/states совпадают с entry snapshot; foreign restart commands0. Добавлены только собственные app/PG. Полная непрерывность всех процессов машины **NOT VERIFIED**; снимок Docker не доказывает её. Старые43/181/149/212 artifact-manifest entries перепроверены по хешам, файлы сохранены. Новая guide note добавляется отдельно от прежней истории.

**NOT RUN:** application patch, post-patch GREEN/acceptance, actual native submit/sort/vote и loading/error flows, full ACCEPT09/global corpus, SOCIAL06–09/module10, physical/cross-browser/real screenreader/full WCAG, real external integrations, production, GitHub mutations/commit/push/deploy. Без reset/clean/stash и смены dirty checkout. Старые PNG не догружались.

## Следующее действие

После одобрения [точного однофайлового плана](IMPLEMENTATION_PLAN.md) проверить source/runtime/locale gates, использовать сохранённый неизменившийся RED и применить только proposed.diff. Затем actual native GREEN на тех же36cell,760/761 boundary, keyboard/long input/scroll и реальные fictional actions/guards; три affected backend methods одним запуском и небольшой shared smoke. Утверждения existing tests не менять; новый app regression test для CSS-only scope не требуется, outcome browser regression уже задан.

При новой причине/дополнительном application файле — отдельный scope/approval. SOCIAL05 закрывать только по post-patch evidence. SOCIAL06/full ACCEPT09/global автоматически не начинать. [Next prompt](next-prompt.txt), [commands](commands.md), [final verification](verification.json), [artifact manifest](artifact-manifest.json).
