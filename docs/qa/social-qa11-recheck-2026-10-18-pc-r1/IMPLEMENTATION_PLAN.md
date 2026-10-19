# PLAN SOCIAL-QA-11 — 2026-10-18 pc-r1

Статус: кандидат вне приложения; IMPLEMENT-APPROVAL ожидается. Module09 OPEN.

## Цель и причина

Убрать вложенный landmark main на typed reviews и inbox. Общий base.html уже содержит внешний main; два дочерних шаблона добавляют второй. P3, точное введение UNKNOWN, production UNKNOWN. Это семантический дефект; затруднение работы реального screen reader не измерялось.

Простая замена тега теряет применяемые свойства static/css/site.css:1953: margin-top:14px, flex:1, position:relative, z-index:var(--layer-page-content). Поэтому scope уточнён до трёх файлов. Кандидат сохраняет существующие значения через дополнительный селектор, без дублирования CSS.

## Точный scope

1. src/catalog/templates/catalog/typed_reviews.html: внутренний main → div; добавить km-page-content к сохранённым container typed-reviews; заменить соответствующий закрывающий тег.
2. src/catalog/templates/pages/account_notifications.html: внутренний main → div; добавить km-page-content к сохранённому account-main-content; сохранить id=main-content и заменить соответствующий закрывающий тег.
3. static/css/site.css: расширить существующий селектор main до main, .km-page-content. Все декларации правила оставить байт-в-байт по смыслу.

Точный кандидат: proposed.diff, candidate-manifest.json и candidate/ с SHA-256. Новых role=main/landmarks не добавлять. Внешний main в base.html остаётся единственным.

Все тела шаблонов, labels, headings, form names/actions, CSRF, data attributes, alert/status, тексты, ACL/CAS, POST/method semantics и состояния SOCIAL01–10 сохраняются. Контроллеры/services/schema/PO/shared JS не входят в scope. Новый селектор отсутствует в текущем приложении. Account profile CSS загружается позднее и сохраняет собственный flex:1 1 0. Living-map JS содержит main selectors, но не подключается для typed_reviews/account_notifications по allowlist context processor; проверяется и в rendered DOM.

## Порядок после approval

1. Заново проверить source-entry, refs/index/active_run, сохранность prior packages, exact diff hash; при существенном source drift остановить применение и обновить кандидат.
2. Применить ровно три согласованных изменения, сохранив существующие dirty changes. Без commit/push/deploy/production и назначения active_run.
3. Создать отдельный docs/qa/social-qa11-fix-2026-10-18-pc-r1 и собственные runtime/locale/cache/media/private-media. Повторно подтвердить ownership PG и internal network. Не перезапускать старые профили.
4. Rendered Chromium: четыре типа отзывов × guest/author/moderator × RU/AZ/EN × 360/390/768/1024/1280/1440; авторизованный inbox на тех же 18 cells. Проверить единственный main, отсутствие nested main, сохранность headings/controls/геометрии/фокуса/overflow, браузерные console/network и native PNG.
5. Обоснованный affected subset: настоящий 409 редактора (сохранение B и сравнение A) и отказ 403 отозванного приглашения с alert, guest redirect inbox; проверить их landmarks и keyboard. Данные только fictional, изменения только в собственном QA. Сохранять статусы/ACL/CAS/CSRF; существующие assertions не ослаблять.
6. Для низкорисковой замены HTML-тега не добавлять backend tests, зеркалящие реализацию. Поведение проверять native UI; предыдущий полный 169-method acceptance не повторять без новой причины и не объявлять соответствующим новому source.
7. Зафиксировать exact source hashes, commands/exits/counts, PNG manifest, NOTRUN/SIMULATED, refs/index/sharedMO/prior packages/guide-prefix/container identities. Обновить guide append-only. Закрыть только SOCIAL11 в доказанных LOCAL границах; затем оценить остаток module09, module10 автоматически не начинать.

## Границы и rollback

Candidate preview в scratch не является применением или GREEN текущего приложения. Baseline source1025 сохраняется. Реальные screen readers/physical devices/cross-browser/external services/global suite/production NOT RUN. При регрессии отредактировать только собственные три hunks обратно с проверкой исходных hashes; без reset/clean/stash.

Правило approval: AGENTS.md требует concrete plan и user approval для scope реализации. Предыдущие approvals SOCIAL01–10 сохраняются; этот трёхфайловый кандидат требует нового решения пользователя.
